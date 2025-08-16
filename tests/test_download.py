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
from collections.abc import Generator

import pytest

from ente_tools.db.in_memory import InMemoryBackend
from ente_tools.local_media_manager import LocalMediaManager
from ente_tools.synchronizer import Synchronizer

from .ente_test_server.ente_server import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD, EnteServer


@pytest.fixture(scope="module")
def ente_server_with_some_files() -> Generator[EnteServer, None, None]:
    """DocString."""
    server = EnteServer(state="some_files")
    server.start()
    yield server
    server.stop()


def test_download(
    monkeypatch: pytest.MonkeyPatch,
    ente_server_with_some_files: EnteServer,
) -> None:
    """DocString."""
    backend = InMemoryBackend()
    client = ente_server_with_some_files.get_client()
    local_media_manager = LocalMediaManager(backend)
    synchronizer = Synchronizer(client, local_media_manager, backend)

    # Get the OTP from the server logs
    monkeypatch.setattr("builtins.input", lambda _: ente_server_with_some_files.get_otp())

    # Requests for password are the admin password
    monkeypatch.setattr(getpass, "getpass", lambda: TEST_ADMIN_PASSWORD)

    synchronizer.link(email=TEST_ADMIN_EMAIL)

    synchronizer.remote_refresh()

    assert len(backend.get_accounts()) == 1

    synchronizer.download(10000000)

    synchronizer.info()
