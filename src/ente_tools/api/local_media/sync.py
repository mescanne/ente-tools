# Copyright 2025 Mark Scannell
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
"""Module for synchronizing local and remote photo files with the Ente API."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ente_tools.api.core import EnteAPI
from ente_tools.api.core.account import EnteAccount
from ente_tools.api.core.api import EnteAPIError

if TYPE_CHECKING:
    from ente_tools.api.core.types_file import File

log = logging.getLogger("sync")


class EnteClient:
    """Client for interacting with the Ente API."""

    EnteApiUrl = "https://api.ente.io"
    EnteAccountUrl = "https://accounts.ente.io"
    EnteDownloadUrl = "https://files.ente.io/?fileID="

    def __init__(
        self,
        api_url: str = EnteApiUrl,
        api_account_url: str = EnteAccountUrl,
        api_download_url: str = EnteDownloadUrl,
    ) -> None:
        """Initialize the EnteClient with the given API URLs."""
        self.api = EnteAPI(
            pkg="io.ente.photos",
            api_url=api_url,
            api_account_url=api_account_url,
            api_download_url=api_download_url,
        )

    def authenticate(self, email: str) -> EnteAccount:
        """Authenticate with Ente and return an EnteAccount."""
        return EnteAccount.authenticate(self.api, email)

    def refresh_account(self, account: EnteAccount, *, force_refresh: bool = False) -> None:
        """Refresh the remote data for the specified account from the Ente API."""
        log.info("Refreshing account %s", account.email)
        account.refresh(self.api, force_refresh=force_refresh)
        log.info(
            "Refreshed account %s with %d collections and %d files.",
            account.email,
            len(account.collections),
            len(account.files),
        )

    def download_file(self, account: EnteAccount, file: "File", destination: Path) -> None:
        """Download a specific file from the remote storage to the local filesystem."""
        keys = account.keys()
        if not keys:
            msg = "Account keys not found"
            raise EnteAPIError(msg)
        self.api.set_token(keys.token)
        self.api.download_file(file, destination)
