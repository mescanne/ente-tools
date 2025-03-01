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
from pathlib import Path
from typing import Annotated

import typer
from platformdirs import user_cache_dir, user_config_dir
from rich.logging import RichHandler
from typer_config.callbacks import toml_conf_callback

from ente_tools.api.core.api import EnteAPIError
from ente_tools.api.photo.sync import EnteClient, EnteData
from ente_tools.filestat import load

APP_NAME = "ente_tool2"

app = typer.Typer()

log = logging.getLogger(__name__)

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()],
)


def get_toml_config(app_name: str) -> str:
    """DocString."""
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
    """DocString."""
    if not config:
        return config
    log.info("Loading config file %s", config)
    return toml_conf_callback(ctxt, param, config)


def get_client(ctxt: typer.Context, data: EnteData) -> EnteClient:
    """DocString."""
    return EnteClient(
        data,
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
    """DocString."""
    with load(ctxt.obj["database"], EnteData) as data:
        client = get_client(ctxt, data)
        client.link(email, unlink=unlink)


@app.command()
def info(ctxt: typer.Context) -> None:
    """DocString."""
    with load(ctxt.obj["database"], EnteData, skip_save=True) as data:
        client = get_client(ctxt, data)
        client.info()


@app.command()
def refresh(
    ctxt: typer.Context,
    force_refresh: Annotated[bool, typer.Option()] = False,  # noqa: FBT002
    email: Annotated[str | None, typer.Option()] = None,
) -> None:
    """DocString."""
    log.info("Refreshing")
    with load(ctxt.obj["database"], EnteData) as data:
        client = get_client(ctxt, data)
        client.remote_refresh(email=email, force_refresh=force_refresh)
        client.local_refresh(ctxt.obj["sync_dir"], force_refresh=force_refresh)


@app.command()
def upload(ctxt: typer.Context, file: str) -> None:
    """DocString."""
    log.info("sync_dir: %s database: %s", ctxt.obj["sync_dir"], ctxt.obj["database"])
    log.info("Uploading file %s", file)


@app.command()
def download(ctxt: typer.Context, file: str) -> None:
    """DocString."""
    with load(ctxt.obj["database"], EnteData) as data:
        client = get_client(ctxt, data)
        client.download(file)


@app.callback()
def app_main(  # noqa: PLR0913
    ctxt: typer.Context,
    sync_dir: Annotated[Path, typer.Option()] = Path.home(),  # noqa: B008
    api_url: Annotated[str, typer.Option()] = EnteClient.EnteApiUrl,
    api_account_url: Annotated[str, typer.Option()] = EnteClient.EnteAccountUrl,
    api_download_url: Annotated[str, typer.Option()] = EnteClient.EnteDownloadUrl,
    database: Annotated[Path, typer.Option()] = Path(user_cache_dir()) / f"{APP_NAME}.json.gz",  # noqa: B008
    debug: Annotated[bool, typer.Option()] = False,  # noqa: FBT002
    config: Annotated[  # noqa: ARG001
        str,
        typer.Option(
            callback=load_toml_config,
            is_eager=True,
        ),
    ] = get_toml_config(APP_NAME),
) -> None:
    """DocString."""
    if debug:
        logging.getLogger().setLevel("DEBUG")

    ctxt.ensure_object(dict)

    if not sync_dir.exists():
        log.error("Sync directory %s does not exist.", sync_dir)
        raise typer.Exit(1)

    log.info("Database: %s", database)
    ctxt.obj["sync_dir"] = sync_dir
    ctxt.obj["database"] = database
    ctxt.obj["api_url"] = api_url
    ctxt.obj["api_account_url"] = api_account_url
    ctxt.obj["api_download_url"] = api_download_url


def main() -> None:
    """DocString."""
    try:
        app()
    except EnteAPIError as e:
        log.error("Error: %s", e)  # noqa: TRY400
        raise typer.Exit(1) from None


if __name__ == "__main__":
    main()
