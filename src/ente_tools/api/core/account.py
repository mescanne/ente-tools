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
"""DocString."""

import logging
from collections.abc import Callable
from getpass import getpass

from pydantic import BaseModel

from ente_tools.api.core.api import EnteAPI, EnteAPIError
from ente_tools.api.core.device import get_device_key
from ente_tools.api.core.types_collection import Collection
from ente_tools.api.core.types_crypt import AuthorizationResponse, EnteEncKeys, EnteKeys, SPRAttributes
from ente_tools.api.core.types_file import File

log = logging.getLogger(__name__)


def retry[T](f: Callable[[], T], onretry: Callable[[], None] | None = None, retries: int = 3) -> T:
    """DocString."""
    for _ in range(1, retries):
        try:
            return f()
        except EnteAPIError:
            if onretry:
                onretry()
    return f()


class EnteAccount(BaseModel):
    """DocString."""

    email: str
    attributes: SPRAttributes
    auth_response: AuthorizationResponse
    encrypted_keys: EnteEncKeys
    collections: list[Collection]
    files: list[File]

    def keys(self) -> EnteKeys:
        """DocString."""
        return self.encrypted_keys.to_keys(get_device_key())

    @staticmethod
    def authenticate(api: EnteAPI, email: str) -> "EnteAccount":
        """DocString."""
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
            lambda: EnteKeys.from_auth(auth_response, getpass()),
            lambda: log.warning("Password failed. Try again."),
        )
        return EnteAccount(
            email=email,
            attributes=attributes,
            auth_response=auth_response,
            encrypted_keys=EnteEncKeys.from_keys(get_device_key(), keys),
            collections=[],
            files=[],
        )

    def refresh(self, api: EnteAPI, *, force_refresh: bool = False) -> None:
        """DocString."""
        cmap = {c.id: c for c in self.collections} if not force_refresh else {}
        fmap = {f.id: f for f in self.files} if not force_refresh else {}

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
        log.info("Requesting updates since %d", update_time)
        updated_collections = [c.to_collection(keys) for c in api.get_collections(since=update_time)]

        # Update
        for c in updated_collections:
            # Skip if deleted and never seen before!
            if c.id not in cmap and c.is_deleted:
                continue

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

        self.collections = list(cmap.values())
        self.files = list(fmap.values())
