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

import hashlib
import logging
from base64 import urlsafe_b64encode
from mimetypes import guess_type
from multiprocessing.pool import ThreadPool
from pathlib import Path

from pydantic import BaseModel
from rich.progress import track

log = logging.getLogger(__name__)


class LocalFile(BaseModel):
    """DocString."""

    fullpath: str
    st_mtime_ns: int
    size: int
    mime_type: str | None = None
    hash: str


class LocalFileSet(BaseModel):
    """DocString."""

    files: list[LocalFile] = []

    def refresh(self, sync_dir: str, *, force_refresh: bool = False) -> None:
        """DocString."""
        # Index existing files
        existing_files = {}
        if not force_refresh and self.files:
            existing_files = {f.fullpath: f for f in self.files}
            log.info("Reusing existing %d files", len(existing_files))

        reused: list[LocalFile] = []
        to_be_hashed: list[LocalFile] = []
        log.info("Scanning %s", sync_dir)
        for root, _, files in Path(sync_dir).walk():
            for file in files:
                fullpath = root / file
                stat = fullpath.stat()
                fname = str(fullpath)
                if (
                    fname in existing_files
                    and existing_files[fname].size == stat.st_size
                    and existing_files[fname].st_mtime_ns == stat.st_mtime_ns
                ):
                    reused.append(existing_files[fname])
                    continue

                to_be_hashed.append(
                    LocalFile(
                        fullpath=fname,
                        st_mtime_ns=stat.st_mtime_ns,
                        size=stat.st_size,
                        mime_type=guess_type(fname, strict=False)[0],
                        hash="",
                    ),
                )

        log.info("To be hashed %d, reused %d", len(to_be_hashed), len(reused))

        def hash_file(h: LocalFile) -> LocalFile:
            with Path(h.fullpath).open("rb") as f:
                h.hash = str(
                    urlsafe_b64encode(hashlib.file_digest(f, "blake2b").digest()),
                    "utf8",
                )
                return h

        hashed: list[LocalFile] = []
        if to_be_hashed:
            with ThreadPool() as pool:
                for r in track(
                    pool.imap(hash_file, to_be_hashed, 1),
                    description="Hashing",
                    total=len(to_be_hashed),
                ):
                    hashed.append(r)  # noqa: PERF402

        # TODO(mescanne): Add in metadata extraction, including from xmp

        self.files = reused + hashed

        log.info("%d analyzed local files", len(self.files))
