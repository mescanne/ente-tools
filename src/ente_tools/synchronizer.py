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
"""Orchestrates the synchronization between local and remote media."""

import logging
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import humanize
from jinja2 import Environment

from ente_tools.api.core.api import EnteAPIError
from ente_tools.api.local_media.photo_file import RemotePhotoFile

if TYPE_CHECKING:
    from ente_tools.api.core.account import EnteAccount
    from ente_tools.api.core.types_file import File
    from ente_tools.api.local_media.file_metadata import Media
    from ente_tools.api.local_media.sync import EnteClient
    from ente_tools.db.base import Backend
    from ente_tools.local_media_manager import LocalMediaManager


log = logging.getLogger(__name__)


class Synchronizer:
    """Orchestrates the synchronization between local and remote media."""

    def __init__(self, client: "EnteClient", local_manager: "LocalMediaManager", backend: "Backend") -> None:
        """Initialize the Synchronizer."""
        self.client = client
        self.local_manager = local_manager
        self.backend = backend

    def info(self) -> None:
        """Display information about the linked accounts and the status of local and remote files."""
        accounts = self.backend.get_accounts()
        for acc in accounts:
            log.info("Account %s has collections %d, files %d", acc.email, len(acc.collections), len(acc.files))

        def calc_files(desc: str, files: list["Media"], t: Callable[["Media"], bool]) -> str:
            files = [f for f in files if t(f)]
            fsize = sum(f.media.file.size for f in files)
            return f"{desc} {len(files)} ({humanize.naturalsize(fsize)})"

        def show_files(desc: str, files: list["Media"]) -> None:
            s = ", ".join(
                [
                    calc_files(
                        "images",
                        files,
                        lambda f: f.media.file.mime_type is not None and f.media.file.mime_type.startswith("video/"),
                    ),
                    calc_files(
                        "videos",
                        files,
                        lambda f: f.media.file.mime_type is not None and f.media.file.mime_type.startswith("image/"),
                    ),
                ],
            )
            log.info("%s %s", desc, s)

        local_media = self.local_manager.get_local_media()
        show_files("All", local_media)

        rfiles = {f.metadata.get("hash", ""): f for acc in accounts for c, files in acc.files.items() for f in files}

        show_files("Sync'd:", [f for f in local_media if f.media.hash in rfiles])
        show_files("Needs to be uploaded:", [f for f in local_media if f.media.hash not in rfiles])

        lfiles = {f.media.hash: f for f in local_media}

        show_files(
            "Duplicated:",
            [
                f
                for f in local_media
                if f.media.hash in lfiles and f.media.file.fullpath != lfiles[f.media.hash].media.file.fullpath
            ],
        )

        lfiles = {f.media.data_hash: f for f in local_media}

        show_files(
            "Data Duplicated:",
            [
                f
                for f in local_media
                if f.media.data_hash in lfiles
                and f.media.file.fullpath != lfiles[f.media.data_hash].media.file.fullpath
            ],
        )

        for acc in accounts:
            to_download = [
                f for c, files in acc.files.items() for f in files if f.metadata.get("hash", "") not in lfiles
            ]
            to_size = sum([f.info.file_size for f in to_download if f.info is not None])
            log.info(
                "Account %s files to download %d (%s)",
                acc.email,
                len(to_download),
                humanize.naturalsize(to_size),
            )

    def link(self, email: str, *, unlink: bool = False) -> None:
        """Link or unlink an Ente account with the given email address."""
        emails = {acc.email for acc in self.backend.get_accounts()}

        if unlink:
            if email not in emails:
                msg = f"Email {email} is is not linked"
                raise EnteAPIError(msg)
            self.backend.remove_account(email)
        else:
            if email in emails:
                msg = f"Email {email} is already linked"
                raise EnteAPIError(msg)
            account = self.client.authenticate(email)
            self.backend.add_account(account)
            self.remote_refresh(email=email)

    def remote_refresh(self, *, email: str | None = None, force_refresh: bool = False) -> None:
        """Refresh the remote data for the specified account(s) from the Ente API."""
        for acc in self.backend.get_accounts():
            if email and acc.email != email:
                continue
            self.client.refresh_account(acc, force_refresh=force_refresh)
            # After refreshing, we need to update the account in the backend
            self.backend.remove_account(acc.email)
            self.backend.add_account(acc)

    def download_missing(self, jinja_template: str = "{{file.get_filename()}}") -> None:
        """Download files present in the remote storage but not locally."""
        local_hashes = {f.media.hash for f in self.local_manager.get_local_media()}

        file_groups: dict[str, list[File]] = defaultdict(list)
        for acc in self.backend.get_accounts():
            for files in acc.files.values():
                for f in files:
                    if not f.metadata or "hash" not in f.metadata:
                        continue
                    if f.metadata["hash"] in local_hashes:
                        continue
                    file_groups[f.metadata["hash"]].append(f)

        ftemplate = Environment(autoescape=True).from_string(jinja_template)

        log.info("To be downloaded:")
        for h, g in file_groups.items():
            log.info("Hash %s, files %s", h, ", ".join(x.metadata["title"] for x in g))
            fname = ftemplate.render(file=RemotePhotoFile(g[0]))
            log.info("Download file: %s", fname)

    def download(self, file_id: int) -> None:
        """Download a specific file from the remote storage to the local filesystem."""
        found_file: "File" | None = None
        account: EnteAccount | None = None
        for acc in self.backend.get_accounts():
            for files in acc.files.values():
                for f in files:
                    if f.id == file_id:
                        found_file = f
                        account = acc
                        break
                if found_file:
                    break
            if found_file:
                break

        if not found_file:
            err = "File not found"
            raise EnteAPIError(err)

        if not account:
            err = "Could not find account for file"
            raise EnteAPIError(err)

        destination = Path(str(found_file.id))
        self.client.download_file(account, found_file, destination)
