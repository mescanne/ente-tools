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
from mimetypes import guess_type
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, delete, select

from ente_tools.api.core.account import EnteAccount
from ente_tools.api.local_media.file_metadata import Media, scan_disk
from ente_tools.api.local_media.loader import NewLocalDiskFile, NewXMPDiskFile, identify_media_type
from ente_tools.db.base import Backend
from ente_tools.db.models import EnteAccountDB, MediaDB, MediaStatus

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
            return [
                Media(**db_media.media)
                for db_media in session.exec(select(MediaDB).where(MediaDB.status == MediaStatus.PROCESSED)).all()
                if db_media.media is not None
            ]

    def local_refresh(self, sync_dir: str, *, force_refresh: bool = False) -> None:
        """Refresh the local data by scanning the specified directory for media files."""
        if force_refresh:
            self._clear_local_media()

        with Session(self.engine) as session:
            self._scan_and_update_db(session, sync_dir)
            self._process_new_files(session)
            self._handle_deletions(session, sync_dir)

    def _scan_and_update_db(self, session: Session, sync_dir: str) -> None:
        db_media_dict = {media.fullpath: media for media in session.exec(select(MediaDB)).all()}
        for media_file, xmp_sidecar in scan_disk(sync_dir):
            existing_media_db = db_media_dict.get(media_file.fullpath)
            sidecar_path = xmp_sidecar.fullpath if xmp_sidecar else None
            if existing_media_db is None:
                db_media = MediaDB(
                    fullpath=media_file.fullpath,
                    sidecar_path=sidecar_path,
                    status=MediaStatus.NEW,
                )
                session.add(db_media)
            else:
                # Check for modification of media file or sidecar
                media_modified = False
                if existing_media_db.media:
                    media_modified = (
                        existing_media_db.media["media"]["file"]["st_mtime_ns"] != media_file.st_mtime_ns
                        or existing_media_db.media["media"]["file"]["size"] != media_file.size
                    )

                sidecar_modified = existing_media_db.sidecar_path != sidecar_path
                if xmp_sidecar and existing_media_db.xmp_sidecar:
                    sidecar_modified = (
                        existing_media_db.xmp_sidecar["file"]["st_mtime_ns"] != xmp_sidecar.st_mtime_ns
                        or existing_media_db.xmp_sidecar["file"]["size"] != xmp_sidecar.size
                    )

                if media_modified or sidecar_modified:
                    existing_media_db.status = MediaStatus.NEW
                    existing_media_db.sidecar_path = sidecar_path
                    session.add(existing_media_db)
        session.commit()

    def _process_new_files(self, session: Session) -> None:
        while True:
            new_files = session.exec(select(MediaDB).where(MediaDB.status == MediaStatus.NEW).limit(100)).all()
            if not new_files:
                break
            for db_media in new_files:
                self._process_single_file(db_media)
                session.add(db_media)
            session.commit()

    def _process_single_file(self, db_media: MediaDB) -> None:
        try:
            mime_type, _ = guess_type(db_media.fullpath, strict=False)
            if not mime_type:
                db_media.status = MediaStatus.ERROR
                db_media.last_error = "Could not identify media type"
                return
            media_type_class = identify_media_type(mime_type)
            if not media_type_class:
                db_media.status = MediaStatus.ERROR
                db_media.last_error = "Could not identify media type"
                return

            media_file = NewLocalDiskFile.from_path(path=Path(db_media.fullpath))
            media = media_type_class.from_file(media_file)
            if not media:
                db_media.status = MediaStatus.ERROR
                db_media.last_error = "Failed to process media file"
                return

            xmp_sidecar = None
            if db_media.sidecar_path:
                xmp_sidecar = NewXMPDiskFile.from_file(
                    NewLocalDiskFile.from_path(path=Path(db_media.sidecar_path)),
                )

            media_obj = Media(media=media, xmp_sidecar=xmp_sidecar)

            db_media.media = media_obj.model_dump()
            db_media.xmp_sidecar = xmp_sidecar.model_dump() if xmp_sidecar else None
            db_media.status = MediaStatus.PROCESSED
        except Exception as e:
            log.exception("Error processing %s", db_media.fullpath)
            db_media.status = MediaStatus.ERROR
            db_media.last_error = str(e)

    def _handle_deletions(self, session: Session, sync_dir: str) -> None:
        all_disk_paths = {mf.fullpath for mf, _ in scan_disk(sync_dir)}
        db_paths = {p.fullpath for p in session.exec(select(MediaDB)).all()}
        deleted_paths = db_paths - all_disk_paths
        if deleted_paths:
            log.info("Deleting %d files from DB", len(deleted_paths))
            statement = select(MediaDB).where(MediaDB.fullpath.in_(deleted_paths))
            results = session.exec(statement)
            for media_db in results:
                session.delete(media_db)
            session.commit()

    def _clear_local_media(self) -> None:
        with Session(self.engine) as session:
            session.exec(delete(MediaDB))
            session.commit()
