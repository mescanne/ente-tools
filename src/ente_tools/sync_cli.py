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
"""Command-line interface for the synchronization tool."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.progress import Progress

from ente_tools.sync.ente_library import EnteLibrary
from ente_tools.sync.ingestor import ImmichIngestor
from ente_tools.sync.local_library import LocalLibrary
from ente_tools.sync.sync import Sync

app = typer.Typer()
log = logging.getLogger(__name__)


@app.command()
def run(
    ente_email: Annotated[str, typer.Option(help="Ente email address")],
    immich_lib_dir: Annotated[Path, typer.Option(help="Path to the Immich library on disk")],
    immich_url: Annotated[str, typer.Option(help="Immich server URL")],
    immich_api_key: Annotated[str, typer.Option(help="Immich API key")],
) -> None:
    """Synchronize photos from an Ente account to an Immich library."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log.info("Starting synchronization...")

    ente_library = EnteLibrary(email=ente_email)
    local_library = LocalLibrary(directory=immich_lib_dir)

    sync = Sync(source=ente_library, dest=local_library)
    missing_photos = sync.get_missing_photos()

    if not missing_photos:
        log.info("No missing photos found. Libraries are in sync.")
        return

    ingestor = ImmichIngestor(api_url=immich_url, api_key=immich_api_key)

    with Progress() as progress:
        task = progress.add_task("[cyan]Ingesting missing photos...", total=len(missing_photos))
        for photo in missing_photos:
            ingestor.ingest(photo, ente_library)
            progress.update(task, advance=1)

    log.info("Synchronization complete.")


if __name__ == "__main__":
    app()
