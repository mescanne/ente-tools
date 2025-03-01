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
# Base Python
"""DocString."""

import logging
from base64 import urlsafe_b64decode, urlsafe_b64encode
from collections.abc import Callable
from http import HTTPStatus
from pathlib import Path
from typing import Any

import httpx

from ente_tools.api.core.ente_crypt import CHUNK_SIZE, decrypt_stream_to_file
from ente_tools.api.core.types_collection import EncryptedCollection
from ente_tools.api.core.types_crypt import AuthorizationResponse, SPRAttributes
from ente_tools.api.core.types_file import EncryptedFile, File

log = logging.getLogger(__name__)


class EnteAPIError(Exception):
    """DocString."""


class EnteAPI:
    """DocString."""

    def __init__(
        self,
        pkg: str,
        api_url: str,
        api_account_url: str,
        api_download_url: str,
        token: bytes | None = None,
    ) -> None:
        """DocString."""
        self.pkg = pkg
        self.api_url = api_url
        self.api_account_url = api_account_url
        self.api_download_url = api_download_url
        self.token = token
        self._update_headers()

    def set_token(self, token: bytes | None = None) -> None:
        """DocString."""
        self.token = token
        self._update_headers()

    def _update_headers(self) -> None:
        self.headers = {"X-Client-Package": self.pkg}
        if self.token:
            self.headers["X-Auth-Token"] = str(urlsafe_b64encode(self.token), "utf-8")
        log.debug("Headers are now %s", str(self.headers))

    def _get(self, path: str, data: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> Any:  # noqa: ANN401
        url = f"{self.api_url}{path}"
        if not data:
            data = {}
        if not headers:
            headers = self.headers
        else:
            headers.update(self.headers)
        if log.isEnabledFor(logging.DEBUG):
            log.debug("Requesting %s (headers %s)", url, headers)
        r = httpx.get(url, params=data, headers=headers)
        # TODO(scannell): 404 is what?
        if r.status_code != HTTPStatus.OK:
            log.info("Invalid status from %s of %d: %s", url, r.status_code, str(r.content, "utf"))
            msg = f"invalid status from URL {url}: {r.status_code}"
            raise EnteAPIError(msg)
        if log.isEnabledFor(logging.DEBUG):
            log.debug("Result: %s", r.content)
        if r.content:
            return r.json()
        return None

    def _post(self, path: str, data: dict[str, str] | None = None) -> Any:  # noqa: ANN401
        url = f"{self.api_url}{path}"
        if not data:
            data = {}
        r = httpx.post(url, json=data, headers=self.headers)
        if r.status_code != HTTPStatus.OK:
            msg = f"invalid status from URL {url}: {r.status_code}"
            raise EnteAPIError(msg)
        if r.content:
            return r.json()
        return None

    def send_email_otp(self, email: str) -> None:
        """DocString."""
        self._post("/users/ott", data={"email": email})

    def verify_email_otp(self, email: str, otp: str) -> AuthorizationResponse:
        """DocString."""
        return AuthorizationResponse.model_validate(
            self._post("/users/verify-email", data={"email": email, "ott": otp}),
        )

    def get_user_details(self) -> None:
        """DocString."""
        log.info("User details: %s", str(self._get("/users/details/v2", {})))

    def attributes(self, email: str) -> SPRAttributes:
        """DocString."""
        return SPRAttributes.model_validate(self._get("/users/srp/attributes", data={"email": email})["attributes"])

    def get_collections(self, since: int = 0) -> list[EncryptedCollection]:
        """DocString."""
        # Get list of collections
        collections = self._get("/collections/v2", data={"sinceTime": str(since)})["collections"]

        # Convert and return
        return [EncryptedCollection.model_validate(c) for c in collections]

    def get_files(self, collection_id: int, since: int) -> tuple[list[EncryptedFile], bool]:
        """DocString."""
        # Get list of files
        result = self._get(
            "/collections/v2/diff",
            data={
                "sinceTime": str(since),
                "collectionID": str(collection_id),
            },
        )

        files = [EncryptedFile.model_validate(f) for f in result["diff"]]

        # Convert and return
        return (files, result["hasMore"])

    def get_file(self, collection_id: int, file_id: int) -> EncryptedFile:  # noqa: ARG002
        """DocString."""
        msg = "unimplemented"
        raise EnteAPIError(msg)

    # TODO(scannell): Handle retries with status code 429, >= 500.
    def _download_file(self, file_id: int, handle: Callable[[bytes], None], chunk_size: int | None = None) -> None:
        """DocString."""
        url = f"{self.api_download_url}{file_id}"
        with httpx.stream("GET", url, headers=self.headers) as r:
            for data in r.iter_bytes(chunk_size=chunk_size):
                if r.status_code != HTTPStatus.OK:
                    msg = f"invalid status from URL {url}: {r.status_code}: {str(data, 'utf-8')}"
                    raise EnteAPIError(msg)
                handle(data)

    # TODO(scannell): Handle retries with status code 429, >= 500.
    def download_file(self, file: File, dest: Path) -> None:
        """DocString."""
        with decrypt_stream_to_file(
            dest,
            key=file.enc_file_key.decrypt(),
            header=urlsafe_b64decode(file.file.decryption_header),
        ) as handler:
            self._download_file(file.id, handler, chunk_size=CHUNK_SIZE)
