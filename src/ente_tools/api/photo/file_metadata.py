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
from concurrent.futures import ThreadPoolExecutor
from mimetypes import guess_type
from pathlib import Path

from pydantic import BaseModel, Field
from rich.progress import track

from ente_tools.api.photo.loader import MediaTypes, NewLocalDiskFile, NewXMPDiskFile, identify_media_type

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


def scan_media(sync_dir: str, workers: int | None = None) -> Iterator[Media]:  # noqa: C901
    """DocString."""
    scan_files: dict[type[MediaTypes], list[tuple[NewLocalDiskFile, NewLocalDiskFile | None]]] = {}

    log.info("Scanning files %s", sync_dir)
    for root, _, files in Path(sync_dir).walk():
        # set of files
        files_set = set(files)

        for file in files:
            # Skip non-media files
            mime_type = guess_type(file, strict=False)[0]
            if not mime_type:
                continue
            media_type = identify_media_type(mime_type)
            if not media_type:
                continue

            # Capture stats and basic information
            media_file = NewLocalDiskFile.from_path(path=root / file, mime_type=mime_type)

            # Identify the XMP sidecars
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
                    "WARNING: %s has multiple XMP sidecars: %s",
                    media_file.fullpath,
                    ", ".join(s.fullpath for s in xmp_sidecars),
                )

            xmp_sidecars.sort(key=lambda f: f.st_mtime_ns)
            xmp_sidecar = xmp_sidecars[-1] if len(xmp_sidecars) > 0 else None

            # Mark file as needed to re-scan image or video
            if media_type not in scan_files:
                scan_files[media_type] = []

            scan_files[media_type].append((media_file, xmp_sidecar))

    for subtype, tasks in scan_files.items():
        log.info("Found new %d %s files", len(tasks), subtype.__name__)

    # Process each type
    for subtype, tasks in scan_files.items():
        log.info("Found new %d %s files", len(tasks), subtype.__name__)

        def run_task(task: tuple[NewLocalDiskFile, NewLocalDiskFile | None]) -> Media | None:
            media = subtype.from_file(task[0])  # noqa: B023
            if not media:
                log.warning("failed processing %s", task[0].fullpath)
                return None
            return Media(
                media=media,
                xmp_sidecar=NewXMPDiskFile.from_file(task[1]) if task[1] else None,
            )

        with ThreadPoolExecutor(max_workers=workers) as e:
            yield from (
                r
                for r in track(
                    e.map(run_task, tasks),
                    description="Processing",
                    total=len(tasks),
                )
                if r
            )
