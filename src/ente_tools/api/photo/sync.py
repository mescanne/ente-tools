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
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import humanize
from jinja2 import Environment
from pydantic import BaseModel

from ente_tools.api.core import EnteAPI
from ente_tools.api.core.account import EnteAccount
from ente_tools.api.core.api import EnteAPIError
from ente_tools.api.photo.file_metadata import Media, refresh
from ente_tools.api.photo.photo_file import RemotePhotoFile

if TYPE_CHECKING:
    from ente_tools.api.core.types_crypt import EnteKeys
    from ente_tools.api.core.types_file import File

log = logging.getLogger("sync")


class EnteData(BaseModel):
    """Data managed by the Ente client, including accounts and local files."""

    accounts: list[EnteAccount] = []
    local: list[Media] = []


class EnteClient:
    """Client for interacting with the Ente API and managing local and remote files."""

    EnteApiUrl = "https://api.ente.io"
    EnteAccountUrl = "https://accounts.ente.io"
    EnteDownloadUrl = "https://files.ente.io/?fileID="

    def __init__(
        self,
        data: EnteData,
        api_url: str = EnteApiUrl,
        api_account_url: str = EnteAccountUrl,
        api_download_url: str = EnteDownloadUrl,
    ) -> None:
        """Initialize the EnteClient with the given data and API URLs."""
        self.data = data
        self.api = EnteAPI(
            pkg="io.ente.photos",
            api_url=api_url,
            api_account_url=api_account_url,
            api_download_url=api_download_url,
        )

    def get_data(self) -> EnteData:
        """Return the EnteData object managed by this client."""
        return self.data

    def info(self) -> None:
        """Display information about the linked accounts and the status of local and remote files."""
        for acc in self.data.accounts:
            log.info("Account %s has collections %d, files %d", acc.email, len(acc.collections), len(acc.files))

        def calc_files(desc: str, files: list[Media], t: Callable[[Media], bool]) -> str:
            files = [f for f in files if t(f)]
            fsize = sum(f.media.file.size for f in files)
            return f"{desc} {len(files)} ({humanize.naturalsize(fsize)})"

        def show_files(desc: str, files: list[Media]) -> None:
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

        show_files("All", self.data.local)

        rfiles = {
            f.metadata.get("hash", ""): f for acc in self.data.accounts for c, files in acc.files.items() for f in files
        }

        show_files("Sync'd:", [f for f in self.data.local if f.media.hash in rfiles])
        show_files("Needs to be uploaded:", [f for f in self.data.local if f.media.hash not in rfiles])

        lfiles = {f.media.hash: f for f in self.data.local}

        show_files(
            "Duplicated:",
            [
                f
                for f in self.data.local
                if f.media.hash in lfiles and f.media.file.fullpath != lfiles[f.media.hash].media.file.fullpath
            ],
        )

        lfiles = {f.media.data_hash: f for f in self.data.local}

        show_files(
            "Data Duplicated:",
            [
                f
                for f in self.data.local
                if f.media.data_hash in lfiles
                and f.media.file.fullpath != lfiles[f.media.data_hash].media.file.fullpath
            ],
        )

        for acc in self.data.accounts:
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
        emails = {acc.email for acc in self.data.accounts}

        if unlink:
            if email not in emails:
                msg = f"Email {email} is is not linked"
                raise EnteAPIError(msg)
            self.data.accounts = [acc for acc in self.data.accounts if acc.email != email]
        else:
            if email in emails:
                msg = f"Email {email} is already linked"
                raise EnteAPIError(msg)
            self.data.accounts.append(EnteAccount.authenticate(self.api, email))
            self.remote_refresh(email=email)

    def remote_refresh(self, *, email: str | None = None, force_refresh: bool = False) -> None:
        """Refresh the remote data for the specified account(s) from the Ente API."""
        for acc in self.data.accounts:
            if email and acc.email != email:
                continue
            log.info("Refreshing account %s", acc.email)
            acc.refresh(self.api, force_refresh=force_refresh)
            log.info(
                "Refreshed account %s with %d collections and %d files.",
                acc.email,
                len(acc.collections),
                len(acc.files),
            )

    def local_export(self) -> None:
        """Export the local files."""

    def local_refresh(self, sync_dir: str, *, force_refresh: bool = False, workers: int | None = None) -> None:
        """Refresh the local data by scanning the specified directory for media files."""
        previous = self.data.local
        if force_refresh:
            previous = None

        log.info("Refreshing dir %s", sync_dir)
        self.data.local = refresh(sync_dir, previous, workers=workers)
        log.info("Refreshed dir %s", sync_dir)

    # TODO(scannell): Jinja template needs a way to deal with duplicates, e.g., making it unique
    def download_missing(self, jinja_template: str = "{{file.get_filename()}}") -> None:
        """Download files present in the remote storage but not locally.

        This method identifies files that exist in the remote Ente storage but are not
        present in the local sync directory. It uses a Jinja template to determine the
        local filename for each file to be downloaded.

        Args:
            jinja_template: A Jinja template string used to generate the local filename
                for each file to be downloaded. The template has access to a `file`
                variable, which is an instance of `RemotePhotoFile`. Defaults to
                "{{file.get_filename()}}".

        """
        # for those files, figure out using the template the target name
        # download them in parallel by some configuration to the local filename

        # Find local hashes
        local_hashes = {f.media.hash for f in self.data.local}

        # Find remote groups of files by hash that aren't already local
        file_groups: dict[str, list[File]] = defaultdict(list)
        for acc in self.data.accounts:
            for files in acc.files.values():
                for f in files:
                    if not f.metadata or "hash" not in f.metadata:
                        continue
                    if f.metadata["hash"] in local_hashes:
                        continue
                    file_groups[f.metadata["hash"]].append(f)

        ftemplate = Environment(autoescape=True).from_string(jinja_template)

        # Show what's to be downloaded
        log.info("To be downloaded:")
        for h, g in file_groups.items():
            log.info("Hash %s, files %s", h, ", ".join(x.metadata["title"] for x in g))
            # Grab first and feed through template? Or just generate it as-is?
            fname = ftemplate.render(file=RemotePhotoFile(g[0]))
            log.info("Download file: %s", fname)

    def download(self, path: str) -> None:  # noqa: C901
        """Download a specific file from the remote storage to the local filesystem.

        This method downloads a file from the remote Ente storage to the local
        filesystem. The file is identified by its path (which corresponds to the
        file's title in the remote storage).

        Args:
            path: The path (title) of the file to download.

        Raises:
            EnteAPIError: If the file is not found, or if multiple files match the given path.

        """
        found_files: list[File] = []
        keys: EnteKeys | None = None
        for acc in self.data.accounts:
            for files in acc.files.values():
                for f in files:
                    if not f.metadata:
                        continue
                    if "title" not in f.metadata:
                        continue
                    if f.metadata["title"] != path:
                        continue
                    keys = acc.keys()
                    found_files.append(f)

        for f in found_files:
            log.info("Found file: %s", f.metadata["title"])

        if len(found_files) > 1:
            err = "Found multiple files"
            raise EnteAPIError(err)

        if len(found_files) == 0:
            err = "Found no files"
            raise EnteAPIError(err)

        if keys is None:
            err = "Found no keys"
            raise EnteAPIError(err)

        self.api.set_token(keys.token)

        self.api.download_file(found_files[0], Path(found_files[0].metadata["title"]))
