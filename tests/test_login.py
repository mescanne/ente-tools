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

import getpass
import logging
from collections.abc import Generator

import pytest

from ente_tools.api.photo.sync import EnteData

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
    ente_client = ente_server.get_client(data=EnteData())

    # Get the OTP from the server logs
    monkeypatch.setattr("builtins.input", lambda _: ente_server.get_otp())

    # Requests for password are the admin password
    monkeypatch.setattr(getpass, "getpass", lambda: TEST_ADMIN_PASSWORD)

    # If no exception is thrown, then this works
    ente_client.link(email=TEST_ADMIN_EMAIL)
