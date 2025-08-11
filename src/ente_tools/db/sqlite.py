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

from sqlmodel import Session, SQLModel, create_engine, select

from ente_tools.api.core.account import EnteAccount
from ente_tools.api.photo.file_metadata import Media, refresh
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
            return [Media(**media.model_dump()) for media in session.exec(select(MediaDB)).all()]

    def local_refresh(self, sync_dir: str, *, force_refresh: bool = False, workers: int | None = None) -> None:
        """Refresh the local data by scanning the specified directory for media files."""
        # For SQLite backend, we can't just pass the list of previous media objects
        # because they are not in memory. We can retrieve them from the DB if needed.
        # For now, we will follow a simple approach: we get the refreshed list of media
        # and then update the database. A more optimized approach would be to check
        # each file against the DB.

        if force_refresh:
            self._clear_local_media()

        previous_media = self.get_local_media()
        refreshed_media_list = refresh(sync_dir, previous_media, workers=workers)

        with Session(self.engine) as session:
            # A simple way to handle this is to clear the table and insert the new data.
            # This is not efficient for large datasets but is simple to implement.
            self._clear_local_media()
            for media in refreshed_media_list:
                db_media = MediaDB(
                    media=media,
                    xmp_sidecar=media.xmp_sidecar.model_dump() if media.xmp_sidecar else None,
                    fullpath=media.media.file.fullpath,
                )
                session.add(db_media)
            session.commit()

    def _clear_local_media(self) -> None:
        with Session(self.engine) as session:
            for media in session.exec(select(MediaDB)).all():
                session.delete(media)
            session.commit()
