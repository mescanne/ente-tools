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
"""DocString."""

import logging
from collections.abc import Iterator
from mimetypes import guess_type
from pathlib import Path

from pydantic import BaseModel, Field

from ente_tools.api.local_media.loader import MediaTypes, NewLocalDiskFile, NewXMPDiskFile, identify_media_type

log = logging.getLogger(__name__)


class Media(BaseModel):
    """DocString."""

    media: MediaTypes = Field(discriminator="media_type")
    xmp_sidecar: NewXMPDiskFile | None

    # this needs to be simplified
    def is_xmp_sidecar_uptodate(self, existing_sidecar: NewLocalDiskFile) -> bool:
        """DocString."""
        return (
            self.xmp_sidecar is not None
            and self.xmp_sidecar.file.fullpath == existing_sidecar.fullpath
            and self.xmp_sidecar.file.st_mtime_ns == existing_sidecar.st_mtime_ns
            and self.xmp_sidecar.file.size == existing_sidecar.size
        )

    # this needs to operate load and reload xmp (same for video vs image)
    def load_xmp_sidecars(self, sidecar: NewLocalDiskFile) -> None:
        """DocString."""
        self.xmp_sidecar = NewXMPDiskFile.from_file(sidecar)


def scan_disk(sync_dir: str) -> Iterator[tuple[NewLocalDiskFile, NewLocalDiskFile | None]]:
    """Scan a directory for media files and their corresponding XMP sidecars."""
    log.info("Scanning files in %s", sync_dir)
    for root, _, files in Path(sync_dir).walk():
        files_set = set(files)
        for file in files:
            mime_type = guess_type(file, strict=False)[0]
            if not mime_type or not identify_media_type(mime_type):
                continue

            media_file = NewLocalDiskFile.from_path(path=root / file, mime_type=mime_type)

            xmp_sidecars = [
                NewLocalDiskFile.from_path(path=Path(root / f))
                for f in [
                    file + ".XMP",
                    file + ".xmp",
                    Path(file).stem + ".XMP",
                    Path(file).stem + ".xmp",
                ]
                if f in files_set
            ]

            if len(xmp_sidecars) > 1:
                log.warning(
                    "Found multiple XMP sidecars for %s: %s",
                    media_file.fullpath,
                    ", ".join(s.fullpath for s in xmp_sidecars),
                )

            xmp_sidecars.sort(key=lambda f: f.st_mtime_ns)
            xmp_sidecar = xmp_sidecars[-1] if xmp_sidecars else None
            yield media_file, xmp_sidecar
