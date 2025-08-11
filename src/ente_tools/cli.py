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
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from platformdirs import user_cache_dir, user_config_dir
from rich.logging import RichHandler
from typer_config.callbacks import toml_conf_callback

from ente_tools.api.core.api import EnteAPIError
from ente_tools.api.photo.sync import EnteClient
from ente_tools.db.in_memory import InMemoryBackend
from ente_tools.db.sqlite import SQLiteBackend

if TYPE_CHECKING:
    from ente_tools.db.base import Backend


APP_NAME = "ente_tool2"

app = typer.Typer(rich_markup_mode=None)

log = logging.getLogger(__name__)

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()],
)


class BackendChoice(str, Enum):
    """Enum for the available backends."""

    IN_MEMORY = "in-memory"
    SQLITE = "sqlite"


def get_toml_config(app_name: str) -> str:
    """Fetch TOML configuration file to load."""
    filename = f"{app_name}.toml"

    potential_paths = [
        Path(user_config_dir(app_name)) / filename,
        Path.home() / filename,
        Path.home() / filename,
        Path(filename),
    ]

    for path in potential_paths:
        if path.exists():
            return str(path)

    return ""


def load_toml_config(ctxt: typer.Context, param: typer.CallbackParam, config: str) -> str:
    """Load TOML configuration file."""
    if not config:
        return config
    log.info("Loading config file %s", config)
    return toml_conf_callback(ctxt, param, config)


def get_client(ctxt: typer.Context) -> EnteClient:
    """Create EnteClient using the command line arguments."""
    return EnteClient(
        ctxt.obj["backend"],
        api_url=ctxt.obj["api_url"],
        api_account_url=ctxt.obj["api_account_url"],
        api_download_url=ctxt.obj["api_download_url"],
    )


@app.command()
def link(
    ctxt: typer.Context,
    email: str,
    unlink: Annotated[bool, typer.Option()] = False,  # noqa: FBT002
) -> None:
    """Link or unlink email with local database."""
    client = get_client(ctxt)
    client.link(email, unlink=unlink)


@app.command()
def info(ctxt: typer.Context) -> None:
    """Fetch general information about the database."""
    client = get_client(ctxt)
    client.info()


@app.command()
def refresh(
    ctxt: typer.Context,
    force_refresh: Annotated[bool, typer.Option()] = False,  # noqa: FBT002
    email: Annotated[str | None, typer.Option()] = None,
    workers: Annotated[int | None, typer.Option()] = None,
) -> None:
    """Refresh both remote and local data."""
    client = get_client(ctxt)
    client.remote_refresh(email=email, force_refresh=force_refresh)
    client.local_refresh(ctxt.obj["sync_dir"], force_refresh=force_refresh, workers=workers)


@app.command()
def export(ctxt: typer.Context) -> None:
    """Export local data."""
    client = get_client(ctxt)
    log.info("Exporting")
    for m in client.backend.get_local_media():
        log.info(m.media.file.fullpath)
        log.info(m.media.hash)
        log.info(m.media.data_hash)
        log.info(m.media.media_type)


@app.command()
def upload(ctxt: typer.Context, file: str) -> None:
    """Upload local file."""
    log.info("sync_dir: %s database: %s", ctxt.obj["sync_dir"], ctxt.obj["database"])
    log.info("Uploading file %s", file)


@app.command()
def download_missing(ctxt: typer.Context) -> None:
    """Download any files that are not local."""
    client = get_client(ctxt)
    client.download_missing()


@app.command()
def download(ctxt: typer.Context, file: str) -> None:
    """Download a remote file."""
    client = get_client(ctxt)
    client.download(file)


@app.callback()
def app_main(  # noqa: PLR0913
    ctxt: typer.Context,
    sync_dir: Annotated[Path, typer.Option(help="Local synchronization directory")] = Path.home(),  # noqa: B008
    backend: Annotated[BackendChoice, typer.Option(help="Database backend to use")] = BackendChoice.IN_MEMORY,
    max_vers: Annotated[int, typer.Option(help="Maximum backup versions of database (0 = disable)")] = 10,
    api_url: Annotated[str, typer.Option(help="API URL for Ente")] = EnteClient.EnteApiUrl,
    api_account_url: Annotated[str, typer.Option(help="API Account URL for Ente")] = EnteClient.EnteAccountUrl,
    api_download_url: Annotated[str, typer.Option(help="Download API URL")] = EnteClient.EnteDownloadUrl,
    database: Annotated[Path, typer.Option(help="Database file")] = Path(user_cache_dir()) / f"{APP_NAME}.db",  # noqa: B008
    debug: Annotated[bool, typer.Option(help="Enable debug logging")] = False,  # noqa: FBT002
    config: Annotated[  # noqa: ARG001
        str,
        typer.Option(
            callback=load_toml_config,
            is_eager=True,
            help="TOML configuration file to load",
        ),
    ] = get_toml_config(APP_NAME),
) -> None:
    """Ente tool utility for synchronizing local files with Ente."""
    if debug:
        logging.getLogger().setLevel("DEBUG")

    ctxt.ensure_object(dict)

    if not sync_dir.exists():
        log.error("Sync directory %s does not exist.", sync_dir)
        raise typer.Exit(1)

    backend_instance: Backend = (
        SQLiteBackend(db_path=str(database)) if backend == BackendChoice.SQLITE else InMemoryBackend()
    )

    ctxt.obj["backend"] = backend_instance
    ctxt.obj["max_vers"] = max_vers
    ctxt.obj["sync_dir"] = sync_dir
    ctxt.obj["database"] = database
    ctxt.obj["api_url"] = api_url
    ctxt.obj["api_account_url"] = api_account_url
    ctxt.obj["api_download_url"] = api_download_url


def main() -> None:
    """Launch main application for Ente tool."""
    try:
        app()
    except EnteAPIError as e:
        log.error("Error: %s", e)  # noqa: TRY400
        raise typer.Exit(1) from None


if __name__ == "__main__":
    main()
