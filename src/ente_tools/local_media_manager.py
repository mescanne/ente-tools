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
"""Manages the local media library."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ente_tools.api.local_media.file_metadata import Media
    from ente_tools.db.base import Backend

log = logging.getLogger(__name__)


class LocalMediaManager:
    """Manages the local media library."""

    def __init__(self, backend: "Backend") -> None:
        """Initialize the LocalMediaManager."""
        self.backend = backend

    def local_refresh(self, sync_dir: str, *, force_refresh: bool = False) -> None:
        """Refresh the local data by scanning the specified directory for media files."""
        self.backend.local_refresh(sync_dir, force_refresh=force_refresh)

    def get_local_media(self) -> list["Media"]:
        """Get all local media from the backend."""
        return self.backend.get_local_media()

    def local_export(self) -> None:
        """Export local data."""
        log.info("Exporting")
        for m in self.get_local_media():
            log.info(m.media.file.fullpath)
            log.info(m.media.hash)
            log.info(m.media.data_hash)
            log.info(m.media.media_type)
