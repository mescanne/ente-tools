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
"""Device-specific encryption key management for Ente."""

from base64 import urlsafe_b64decode, urlsafe_b64encode
from functools import cache

import keyring
from nacl.secret import SecretBox
from nacl.utils import random
from pydantic import BaseModel

SERVICE = "ente-tool"
USER = "device-key"


@cache
def get_device_key() -> bytes:
    """Retrieve the device-specific encryption key.

    This function retrieves the device key from the system's keyring. If the key
    does not exist, it generates a new one, stores it in the keyring, and then
    returns it.

    Returns:
        bytes: The device-specific encryption key.

    """
    encoded = keyring.get_password(SERVICE, USER)
    if not encoded:
        device_key = random(SecretBox.KEY_SIZE)
        encoded = str(urlsafe_b64encode(device_key), "utf8")
        keyring.set_password(SERVICE, USER, encoded)
    return urlsafe_b64decode(bytes(encoded, "utf8"))


class DeviceSecret(BaseModel):
    """Encrypted data that can only be decrypted using the device key."""

    encrypted: str
    """The encrypted data, base64 encoded."""
    nonce: str
    """The nonce used for encryption, base64 encoded."""

    @staticmethod
    def encrypt(msg: bytes) -> "DeviceSecret":
        """Encrypt a message using the device key.

        This method encrypts the provided message using the device-specific
        encryption key and a randomly generated nonce.

        Args:
            msg (bytes): The message to encrypt.

        Returns:
            DeviceSecret: An object containing the encrypted message and the nonce.

        """
        nonce = random(SecretBox.NONCE_SIZE)
        return DeviceSecret(
            encrypted=str(urlsafe_b64encode(SecretBox(get_device_key()).encrypt(msg, nonce).ciphertext), "utf-8"),
            nonce=str(urlsafe_b64encode(nonce), "utf-8"),
        )

    def decrypt(self) -> bytes:
        """Decrypt the encrypted data using the device key.

        This method decrypts the encrypted data using the device-specific
        encryption key and the stored nonce.

        Returns:
            bytes: The decrypted message.

        Raises:
            nacl.exceptions.CryptoError: If the decryption fails.

        """
        return SecretBox(get_device_key()).decrypt(
            urlsafe_b64decode(self.encrypted),
            nonce=urlsafe_b64decode(self.nonce),
        )
