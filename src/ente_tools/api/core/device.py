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
"""Docstring."""

from base64 import b64decode, b64encode
from functools import cache

import keyring
from nacl.secret import SecretBox
from nacl.utils import random
from pydantic import BaseModel

SERVICE = "ente-tool"
USER = "device-key"


@cache
def get_device_key() -> bytes:
    """DocString."""
    encoded = keyring.get_password(SERVICE, USER)
    if not encoded:
        device_key = random(SecretBox.KEY_SIZE)
        encoded = str(b64encode(device_key), "utf8")
        keyring.set_password(SERVICE, USER, encoded)
    return b64decode(bytes(encoded, "utf8"))


class DeviceSecret(BaseModel):
    """DocString."""

    encrypted: str
    nonce: str

    @staticmethod
    def encrypt(msg: bytes) -> "DeviceSecret":
        """DocString."""
        nonce = random(SecretBox.NONCE_SIZE)
        return DeviceSecret(
            encrypted=str(b64encode(SecretBox(get_device_key()).encrypt(msg, nonce).ciphertext), "utf-8"),
            nonce=str(b64encode(nonce), "utf-8"),
        )

    def decrypt(self) -> bytes:
        """DocString."""
        return SecretBox(get_device_key()).decrypt(
            b64decode(self.encrypted),
            nonce=b64decode(self.nonce),
        )
