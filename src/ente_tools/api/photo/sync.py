# Copyright 2024 Mark Scannell
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
"""DocString."""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import humanize
from pydantic import BaseModel

from ente_tools.api.core import EnteAPI
from ente_tools.api.core.account import EnteAccount
from ente_tools.api.core.api import EnteAPIError
from ente_tools.api.photo.local_file import LocalFile, LocalFileSet

if TYPE_CHECKING:
    from ente_tools.api.core.types_crypt import EnteKeys
    from ente_tools.api.core.types_file import File

log = logging.getLogger("sync")


class EnteData(BaseModel):
    """DocString."""

    accounts: list[EnteAccount] = []
    local: LocalFileSet


class EnteClient:
    """DocString."""

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
        """DocString."""
        self.data = data
        self.api = EnteAPI(
            pkg="io.ente.photos",
            api_url=api_url,
            api_account_url=api_account_url,
            api_download_url=api_download_url,
        )

    def get_data(self) -> EnteData:
        """DocString."""
        return self.data

    def info(self) -> None:
        """DocString."""
        for acc in self.data.accounts:
            log.info("Account %s has collections %d, files %d", acc.email, len(acc.collections), len(acc.files))

        def calc_files(desc: str, files: list[LocalFile], t: Callable[[LocalFile], bool]) -> str:
            files = [f for f in files if t(f)]
            fsize = sum(f.size for f in files)
            return f"{desc} {len(files)} ({humanize.naturalsize(fsize)})"

        def show_files(desc: str, files: list[LocalFile]) -> None:
            s = ", ".join(
                [
                    calc_files("images", files, lambda f: f.mime_type is not None and f.mime_type.startswith("video/")),
                    calc_files("videos", files, lambda f: f.mime_type is not None and f.mime_type.startswith("image/")),
                ],
            )
            log.info("%s %s", desc, s)

        show_files("All", self.data.local.files)

        rfiles = {f.metadata["hash"]: f for acc in self.data.accounts for f in acc.files}

        show_files("Sync'd:", [f for f in self.data.local.files if f.hash in rfiles])
        show_files("Needs to be uploaded:", [f for f in self.data.local.files if f.hash not in rfiles])

        lfiles = {f.hash: f for f in self.data.local.files}
        for acc in self.data.accounts:
            log.info(
                "Account %s files to download: %d",
                acc.email,
                len([f for f in acc.files if f.metadata["hash"] not in lfiles]),
            )

    def link(self, email: str, *, unlink: bool = False) -> None:
        """DocString."""
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
        """DocString."""
        for acc in self.data.accounts:
            if email and acc.email != email:
                continue
            acc.refresh(self.api, force_refresh=force_refresh)
            log.info("Saving for %s %d collections, %d files.", acc.email, len(acc.collections), len(acc.files))

    def local_refresh(self, sync_dir: str, *, force_refresh: bool = False) -> None:
        """DocString."""
        self.data.local.refresh(sync_dir, force_refresh=force_refresh)

    def download(self, path: str) -> None:
        """DocString."""
        found_files: list[File] = []
        keys: EnteKeys | None = None
        for acc in self.data.accounts:
            for f in acc.files:
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
