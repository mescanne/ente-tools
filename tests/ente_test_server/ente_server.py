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
import os
import re
from http import HTTPStatus
from pathlib import Path
from time import sleep

import httpx
import keyring.backend
import pytest
from testcontainers.compose import DockerCompose

from ente_tools.api.photo.sync import EnteClient, EnteData

log = logging.getLogger(__name__)


TEST_ADMIN_EMAIL = "ente-tools@test.com"
TEST_ADMIN_PASSWORD = "32lj4h5iuhe"  # noqa: S105
TEST_COMPOSE_DIR = Path(__file__).parent


class EnteServer(DockerCompose):
    """DocString."""

    def __init__(self, state: str = "base") -> None:
        """DocString."""
        os.environ["STATE"] = state

        # set the keyring for test device key
        keyring.set_keyring(TestKeyring())

        log.info("Starting ente test server with state %s", state)

        super().__init__(context=TEST_COMPOSE_DIR, compose_file_name="compose.yaml")

    def _wait_for_ping(self) -> None:
        """Wait for the ping on the Ente API URL."""
        api_url = self.get_api_url()

        attempts = 12
        while attempts:
            log.info("Connecting to %s/ping", api_url)
            try:
                r = httpx.get(f"{api_url}/ping")
                if r.status_code == HTTPStatus.OK:
                    break
            except httpx.ConnectError:
                log.info("Server not yet up, trying ping again")
            attempts -= 1
            sleep(0.250)

        if attempts == 0:
            pytest.fail("unable to connect to container")

    def start(self) -> None:
        """DocString."""
        super().start()

        self._wait_for_ping()

    def get_client(self, data: EnteData) -> EnteClient:
        """DocString."""
        return EnteClient(
            data=data,
            api_url=self.get_api_url(),
            api_account_url=self.get_api_url(),
            api_download_url=self.get_api_url() + "/files/download/",
        )

    def get_otp(self) -> str:
        """DocString."""
        stdout, stderr = self.get_logs("museum")
        m = re.search(r"Verification code: ([0-9]{6,6})", stdout)
        if not m:
            pytest.fail("No OTP found")
        return m.group(1)

    def get_api_url(self) -> str:
        """DocString."""
        host, port = self.get_service_host_and_port("museum", 8080)
        log.info("api url host and port: %s %d", host, port)
        return f"http://{host}:{port}"

    def get_object_url(self) -> str:
        """DocString."""
        host, port = self.get_service_host_and_port("minio", 3200)
        log.info("object url host and port: %s %d", host, port)
        return f"http://{host}:{port}"


TEST_DEVICE_KEY = "BNhV7EEi9HxaCRzDLM/EHprdxTIabqiw+Jv3kEilA/Q="


class TestKeyring(keyring.backend.KeyringBackend):
    """A test keyring which always outputs the same password."""

    priority = 1.0  # pyright: ignore [reportAssignmentType]

    def set_password(self, service: str, username: str, password: str) -> None:
        """DocString."""

    def get_password(self, service: str, username: str) -> str:  # noqa: ARG002
        """DocString."""
        return TEST_DEVICE_KEY

    def delete_password(self, service: str, username: str) -> None:
        """DocString."""
