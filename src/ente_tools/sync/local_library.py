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
"""An implementation of the Library abstract base class for a local directory."""

import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path

from platformdirs import user_cache_dir

from ente_tools.api.photo.sync import EnteClient
from ente_tools.db.sqlite import SQLiteBackend
from ente_tools.sync.library import Library
from ente_tools.sync.photo import Photo

log = logging.getLogger(__name__)


class LocalLibrary(Library):
    """An implementation of the Library abstract base class for a local directory."""

    def __init__(self, directory: Path) -> None:
        """Initialize the LocalLibrary."""
        self._directory = directory
        db_path = Path(user_cache_dir()) / f"local_library_{directory.name}.db"
        self._backend = SQLiteBackend(db_path=str(db_path))
        self._client = EnteClient(backend=self._backend)

    def get_photos(self) -> list[Photo]:
        """Get a list of all photos in the local directory."""
        log.info("Scanning local directory: %s", self._directory)
        self._client.local_refresh(str(self._directory))

        return [
            Photo(
                id=media.media.file.fullpath,
                blake2b_hash=media.media.hash,
                original_filename=Path(media.media.file.fullpath).name,
                created_at=datetime.fromtimestamp(
                    media.media.file.st_mtime_ns / 1e9,
                    tz=UTC,
                ),
                modified_at=datetime.fromtimestamp(
                    media.media.file.st_mtime_ns / 1e9,
                    tz=UTC,
                ),
            )
            for media in self._backend.get_local_media()
        ]

    def download_photo(self, photo: Photo, dest_path: Path) -> None:
        """Copy a local photo to the given destination path."""
        source_path = Path(photo.id)
        shutil.copy(source_path, dest_path)

    @property
    def name(self) -> str:
        """Get the name of the library."""
        return f"Local({self._directory})"
