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
"""SQLite backend for the database."""

import logging

from sqlmodel import Session, SQLModel, create_engine, delete, select

from ente_tools.api.core.account import EnteAccount
from ente_tools.api.photo.file_metadata import Media, scan_media
from ente_tools.db.base import Backend
from ente_tools.db.models import EnteAccountDB, MediaDB

log = logging.getLogger(__name__)


class SQLiteBackend(Backend):
    """SQLite backend for the database."""

    def __init__(self, db_path: str = "ente.db") -> None:
        """Initialise the SQLite backend."""
        self.engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(self.engine)

    def get_accounts(self) -> list[EnteAccount]:
        """Get all accounts from the backend."""
        with Session(self.engine) as session:
            return [EnteAccount(**acc.model_dump(by_alias=True)) for acc in session.exec(select(EnteAccountDB)).all()]

    def add_account(self, account: EnteAccount) -> None:
        """Add an account to the backend."""
        with Session(self.engine) as session:
            account_data = account.model_dump(by_alias=True)
            db_account = EnteAccountDB(**account_data)
            session.add(db_account)
            session.commit()

    def remove_account(self, email: str) -> None:
        """Remove an account from the backend by email."""
        with Session(self.engine) as session:
            account = session.exec(
                select(EnteAccountDB).where(EnteAccountDB.email == email),
            ).first()
            if account:
                session.delete(account)
                session.commit()

    def get_local_media(self) -> list[Media]:
        """Get all local media from the backend."""
        with Session(self.engine) as session:
            # The `media` field in MediaDB is a dict representation of a Media object.
            return [Media(**db_media.media) for db_media in session.exec(select(MediaDB)).all()]

    def local_refresh(self, sync_dir: str, *, force_refresh: bool = False, workers: int | None = None) -> None:
        """Refresh the local data by scanning the specified directory for media files."""
        if force_refresh:
            self._clear_local_media()

        with Session(self.engine) as session:
            all_disk_paths = set()
            processed_count = 0

            db_media_dict = {media.fullpath: media for media in session.exec(select(MediaDB)).all()}

            for media in scan_media(sync_dir, workers=workers):
                all_disk_paths.add(media.media.file.fullpath)

                existing_media_db = db_media_dict.get(media.media.file.fullpath)

                if existing_media_db is None:
                    # New file
                    db_media = MediaDB(
                        media=media.model_dump(),
                        xmp_sidecar=media.xmp_sidecar.model_dump() if media.xmp_sidecar else None,
                        fullpath=media.media.file.fullpath,
                    )
                    session.add(db_media)
                    processed_count += 1
                else:
                    # Existing file, check for modification
                    if (
                        existing_media_db.media["media"]["file"]["st_mtime_ns"]
                        != media.media.file.st_mtime_ns
                        or existing_media_db.media["media"]["file"]["size"] != media.media.file.size
                    ):
                        # Modified
                        existing_media_db.media = media.model_dump()
                        existing_media_db.xmp_sidecar = (
                            media.xmp_sidecar.model_dump() if media.xmp_sidecar else None
                        )
                        session.add(existing_media_db)
                        processed_count += 1

                if processed_count > 0 and processed_count % 100 == 0:
                    session.commit()

            session.commit()  # commit any remaining changes

            # Handle deletions
            db_paths = set(db_media_dict.keys())
            deleted_paths = db_paths - all_disk_paths
            if deleted_paths:
                log.info("Deleting %d files from DB", len(deleted_paths))
                for path in deleted_paths:
                    session.delete(db_media_dict[path])
                session.commit()

    def _clear_local_media(self) -> None:
        with Session(self.engine) as session:
            session.exec(delete(MediaDB))
            session.commit()
