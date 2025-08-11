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

import getpass
import logging
from collections.abc import Generator

import pytest

from ente_tools.api.photo.sync import EnteClient
from ente_tools.db.in_memory import InMemoryBackend

from .ente_test_server.ente_server import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD, EnteServer

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def ente_server_download() -> Generator[EnteServer]:
    """DocString."""
    server = EnteServer(state="some_files")
    server.start()
    yield server
    server.stop()


@pytest.fixture
def ente_client(monkeypatch: pytest.MonkeyPatch, ente_server_download: EnteServer) -> EnteClient:
    """DocString."""
    ente_client = ente_server_download.get_client(backend=InMemoryBackend())

    # Get the OTP from the server logs
    monkeypatch.setattr("builtins.input", lambda _: ente_server_download.get_otp())

    # Requests for password are the admin password
    monkeypatch.setattr(getpass, "getpass", lambda: TEST_ADMIN_PASSWORD)

    # If no exception is thrown, then this works
    ente_client.link(email=TEST_ADMIN_EMAIL)

    return ente_client


def test_download(ente_client: EnteClient) -> None:
    """DocString."""
    # refresh cache
    ente_client.remote_refresh()

    log.info(ente_client.backend.get_accounts())

    ente_client.download(path="Sony_HDR-HC3.jpg")

    ente_client.info()
