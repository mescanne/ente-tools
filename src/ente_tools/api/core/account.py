# Copyright 2024 Mark Scannell
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Core functionality for managing Ente accounts and authentication."""

import getpass
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import BaseModel

from ente_tools.api.core.api import EnteAPI, EnteAPIError
from ente_tools.api.core.device import get_device_key
from ente_tools.api.core.types_collection import Collection
from ente_tools.api.core.types_crypt import AuthorizationResponse, EnteEncKeys, EnteKeys, SPRAttributes
from ente_tools.api.core.types_file import File

log = logging.getLogger(__name__)


def retry[T](f: Callable[[], T], onretry: Callable[[], None] | None = None, retries: int = 3) -> T:
    """Retry a function call multiple times if it raises an EnteAPIError.

    This function attempts to call the provided function `f` up to `retries` times.
    If `f` raises an `EnteAPIError`, the `onretry` callback is called (if provided),
    and the function is retried. If the function still fails after the specified
    number of retries, the last exception is raised.

    Args:
        f: The function to call.
        onretry: An optional callback function to call on each retry.
        retries: The maximum number of retries.

    """
    for _ in range(1, retries):
        try:
            return f()
        except EnteAPIError:
            if onretry:
                onretry()
    return f()


class EnteAccount(BaseModel):
    """Represents an authenticated Ente account.

    This class encapsulates the state of an authenticated Ente account, including
    user details, cryptographic keys, and synchronized collections and files.

    """

    email: str
    """The email address associated with the account."""
    attributes: SPRAttributes
    """The SRP attributes for the account."""
    auth_response: AuthorizationResponse
    """The authorization response from the server."""
    encrypted_keys: EnteEncKeys
    """The device-encrypted Ente keys."""
    collections: list[Collection]
    """The list of collections in the account."""
    files: dict[int, list[File]]
    """The files in the account, organized by collection ID."""

    def keys(self) -> EnteKeys:
        """Retrieve the decrypted Ente keys for the account.

        This method decrypts the device-encrypted Ente keys using the device key.

        Returns:
            The decrypted EnteKeys.

        """
        return self.encrypted_keys.to_keys(get_device_key())

    @staticmethod
    def authenticate(api: EnteAPI, email: str) -> "EnteAccount":
        """Authenticate an Ente account and create an EnteAccount instance.

        This method handles the authentication process with the Ente API, including
        sending an email OTP, verifying the OTP, and retrieving the user's keys.

        Args:
            api: The EnteAPI client.
            email: The email address of the account.

        """
        # Get attributes of the account. This is public.
        attributes = api.attributes(email)

        log.info("Sending email verification.")
        api.send_email_otp(email)

        # TODO(scannell): Exit early if there's any other process in here!

        auth_response = retry(
            lambda: api.verify_email_otp(email, input("Enter OTP: ")),
            lambda: log.warning("OTP failed. Try again."),
        )

        log.debug("auth_response: %s", auth_response)

        keys = retry(
            lambda: EnteKeys.from_auth(auth_response, getpass.getpass()),
            lambda: log.warning("Password failed. Try again."),
        )

        return EnteAccount(
            email=email,
            attributes=attributes,
            auth_response=auth_response,
            encrypted_keys=EnteEncKeys.from_keys(get_device_key(), keys),
            collections=[],
            files={},
        )

    def refresh(self, api: EnteAPI, *, force_refresh: bool = False) -> None:
        """Refresh the account's collections and files from the Ente API.

        This method synchronizes the local state of the account with the remote
        state on the Ente servers. It fetches updated collections and files,
        decrypts them, and updates the local data structures.

        Args:
            api: The EnteAPI client.
            force_refresh: If True, forces a full refresh, ignoring any
                previous update times.

        Raises:
            EnteAPIError: If there is an error communicating with the Ente API.

        """
        cmap = {c.id: c for c in self.collections} if not force_refresh else {}

        # Fetch the clear-text keys (in-memory only)
        keys = self.keys()

        # Set the token for the API
        api.set_token(keys.token)

        # Find the last update time
        update_time = 0
        if not force_refresh:
            for collection in self.collections:
                update_time = max(collection.update_time, update_time)

        # Fetch the updated collections
        log.info(
            "Requesting updates since %s",
            datetime.fromtimestamp(update_time / 1000000, tz=UTC).strftime("%Y/%m/%d %H:%M:%S"),
        )
        updated_collections = [c.to_collection(keys) for c in api.get_collections(since=update_time)]

        # Update
        for c in updated_collections:
            # Skip if deleted and never seen before!
            if c.id not in cmap and c.is_deleted:
                continue

            # Create filemap of existing files
            fmap = {}
            if c.id in self.files and not force_refresh:
                fmap = {f.id: f for f in self.files[c.id]}

            # Decrypt the collection key
            ckey = c.enc_collection_key.decrypt()

            # Find out last update time for collection
            file_update_time = 0
            if c.id in cmap:
                file_update_time = cmap[c.id].update_time

            has_more = True
            while has_more:
                (files, has_more) = api.get_files(since=file_update_time, collection_id=c.id)
                for f in files:
                    file_update_time = max(f.update_time, file_update_time)
                    fmap[f.id] = f.to_file(ckey)

            # Save it
            cmap[c.id] = c
            self.files[c.id] = list(fmap.values())

        self.collections = list(cmap.values())
