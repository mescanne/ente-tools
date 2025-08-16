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

from ente_tools.db.in_memory import InMemoryBackend
from ente_tools.local_media_manager import LocalMediaManager
from ente_tools.synchronizer import Synchronizer

from .ente_test_server.ente_server import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD, EnteServer

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def ente_server() -> Generator[EnteServer]:
    """DocString."""
    server = EnteServer()
    server.start()
    yield server
    server.stop()


def test_login(monkeypatch: pytest.MonkeyPatch, ente_server: EnteServer) -> None:
    """DocString."""
    backend = InMemoryBackend()
    client = ente_server.get_client()
    local_media_manager = LocalMediaManager(backend)
    synchronizer = Synchronizer(client, local_media_manager, backend)

    # Get the OTP from the server logs
    monkeypatch.setattr("builtins.input", lambda _: ente_server.get_otp())

    # Requests for password are the admin password
    monkeypatch.setattr(getpass, "getpass", lambda: TEST_ADMIN_PASSWORD)

    # If no exception is thrown, then this works
    synchronizer.link(email=TEST_ADMIN_EMAIL)

    accounts = backend.get_accounts()
    assert len(accounts) == 1
    assert accounts[0].email == TEST_ADMIN_EMAIL
