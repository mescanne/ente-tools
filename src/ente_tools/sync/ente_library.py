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
"""An implementation of the Library abstract base class for Ente."""

import logging
from pathlib import Path

from platformdirs import user_cache_dir

from ente_tools.api.photo.photo_file import RemotePhotoFile
from ente_tools.api.photo.sync import EnteClient
from ente_tools.db.sqlite import SQLiteBackend
from ente_tools.sync.library import Library
from ente_tools.sync.photo import Photo

log = logging.getLogger(__name__)


class EnteLibrary(Library):
    """An implementation of the Library abstract base class for Ente."""

    def __init__(self, email: str) -> None:
        """Initialize the EnteLibrary."""
        self._email = email
        db_path = Path(user_cache_dir()) / f"ente_library_{email}.db"
        self._backend = SQLiteBackend(db_path=str(db_path))
        self._client = EnteClient(backend=self._backend)

    def get_photos(self) -> list[Photo]:
        """Get a list of all photos in the Ente library."""
        if not any(acc.email == self._email for acc in self._backend.get_accounts()):
            log.info("Linking Ente account: %s", self._email)
            self._client.link(self._email)
        else:
            log.info("Ente account already linked: %s", self._email)

        log.info("Refreshing remote files from Ente...")
        self._client.remote_refresh(email=self._email)

        photos = []
        accounts = self._backend.get_accounts()
        for acc in accounts:
            if acc.email == self._email:
                for collection in acc.files.values():
                    for remote_file_data in collection:
                        remote_file = RemotePhotoFile(remote_file_data)
                        title = remote_file.get_filename()
                        if not title:
                            continue
                        photos.append(
                            Photo(
                                id=str(remote_file_data.id),
                                blake2b_hash=remote_file_data.metadata.get("hash"),
                                original_filename=title,
                                created_at=remote_file.get_create_time(),
                                modified_at=remote_file.get_modify_time(),
                            ),
                        )
        return photos

    def download_photo(self, photo: Photo, dest_path: Path) -> None:
        """Download a photo from Ente to the given destination path."""
        self._client.download(photo.original_filename)
        # The download method in EnteClient downloads to the current directory,
        # so we need to move the file to the destination path.
        downloaded_file = Path(photo.original_filename)
        if downloaded_file.exists():
            downloaded_file.rename(dest_path)

    @property
    def name(self) -> str:
        """Get the name of the library."""
        return f"Ente({self._email})"
