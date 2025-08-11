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
# Copyright 2025 Mark Scannell
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not- use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""In-memory backend for the database."""

import logging

from ente_tools.api.core.account import EnteAccount
from ente_tools.api.photo.file_metadata import Media, scan_media
from ente_tools.db.base import Backend

log = logging.getLogger(__name__)


class InMemoryBackend(Backend):
    """In-memory backend for the database."""

    def __init__(self) -> None:
        """Initialise the in-memory backend."""
        self._accounts: list[EnteAccount] = []
        self._local_media: list[Media] = []

    def get_accounts(self) -> list[EnteAccount]:
        """Get all accounts from the backend."""
        return self._accounts

    def add_account(self, account: EnteAccount) -> None:
        """Add an account to the backend."""
        self._accounts.append(account)

    def remove_account(self, email: str) -> None:
        """Remove an account from the backend by email."""
        self._accounts = [acc for acc in self._accounts if acc.email != email]

    def get_local_media(self) -> list[Media]:
        """Get all local media from the backend."""
        return self._local_media

    def local_refresh(self, sync_dir: str, *, force_refresh: bool = False, workers: int | None = None) -> None:  # noqa: ARG002
        """Refresh the local data by scanning the specified directory for media files."""
        # For the in-memory backend, a refresh is always a full refresh.
        # The `force_refresh` parameter is ignored but kept for compatibility.
        log.info("Refreshing dir %s", sync_dir)
        self.get_local_media().clear()
        self.get_local_media().extend(list(scan_media(sync_dir, workers=workers)))
        log.info("Refreshed dir %s", sync_dir)
