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
"""In-memory backend for the database."""

import logging
from mimetypes import guess_type

from ente_tools.api.core.account import EnteAccount
from ente_tools.api.local_media.file_metadata import Media, scan_disk
from ente_tools.api.local_media.loader import NewXMPDiskFile, identify_media_type
from ente_tools.db.base import Backend

log = logging.getLogger(__name__)


class InMemoryBackend(Backend):
    """In-memory backend for the database."""

    def __init__(self) -> None:
        """Initialise the in-memory backend."""
        self.accounts: dict[str, EnteAccount] = {}
        self.local_media: list[Media] = []

    def get_accounts(self) -> list[EnteAccount]:
        """Get all accounts from the backend."""
        return list(self.accounts.values())

    def add_account(self, account: EnteAccount) -> None:
        """Add an account to the backend."""
        self.accounts[account.email] = account

    def remove_account(self, email: str) -> None:
        """Remove an account from the backend by email."""
        if email in self.accounts:
            del self.accounts[email]

    def get_local_media(self) -> list[Media]:
        """Get all local media from the backend."""
        return self.local_media

    def local_refresh(self, sync_dir: str, *, force_refresh: bool = False) -> None:
        """Refresh the local data by scanning the specified directory for media files."""
        if force_refresh:
            self.local_media = []
        # The in-memory backend doesn't support incremental scanning,
        # so we just rescan everything.
        self.local_media = []
        for media_file, xmp_sidecar in scan_disk(sync_dir):
            mime_type, _ = guess_type(media_file.fullpath)
            if not mime_type:
                continue
            media_type_class = identify_media_type(mime_type)
            if not media_type_class:
                continue
            media = media_type_class.from_file(media_file)
            if not media:
                continue
            xmp = NewXMPDiskFile.from_file(xmp_sidecar) if xmp_sidecar else None
            self.local_media.append(Media(media=media, xmp_sidecar=xmp))
