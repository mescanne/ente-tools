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
"""Cryptographic types and utilities for Ente's encryption system."""

import logging
from base64 import urlsafe_b64decode, urlsafe_b64encode

from nacl.bindings import (
    crypto_box_seal_open,
)
from nacl.pwhash.argon2id import kdf
from nacl.secret import SecretBox
from nacl.utils import random
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class SPRAttributes(BaseModel):
    """Key attributes for a user attempting to login."""

    srp_user_id: str = Field(alias="srpUserID")
    srp_salt: str = Field(alias="srpSalt")
    mem_limit: int = Field(alias="memLimit")
    ops_limit: int = Field(alias="opsLimit")
    kek_salt: str = Field(alias="kekSalt")
    is_email_mfa_enabled: bool = Field(alias="isEmailMFAEnabled")


class KeyAttributes(BaseModel):
    """Encrypted master key, encrypted private key, and associated public key."""

    kek_salt: str = Field(alias="kekSalt")
    kek_hash: str | None = Field(default="", alias="kekHash")
    encrypted_key: str = Field(alias="encryptedKey")
    key_decryption_nonce: str = Field(alias="keyDecryptionNonce")
    public_key: str = Field(alias="publicKey")
    encrypted_secret_key: str = Field(alias="encryptedSecretKey")
    secret_key_decryption_nonce: str = Field(alias="secretKeyDecryptionNonce")
    mem_limit: int = Field(alias="memLimit")
    ops_limit: int = Field(alias="opsLimit")


class AuthorizationResponse(BaseModel):
    """Encrypted keys and tokens for the user after server authorization."""

    id: int
    key_attributes: KeyAttributes = Field(alias="keyAttributes")
    encrypted_token: str = Field(alias="encryptedToken")
    token: str | None = Field(default="", alias="token")
    accounts_url: str | None = Field(default="", alias="accountsUrl")
    two_factor_session_id: str | None = Field(
        default="",
        alias="twoFactorSessionID",
    )
    two_factor_session_idv2: str | None = Field(
        default="",
        alias="twoFactorSessionIDV2",
    )
    passkey_session_id: str | None = Field(
        default="",
        alias="passkeySessionID",
    )


class EnteKeys(BaseModel):
    """Core encryption keys for an Ente account."""

    user_id: int
    master_key: bytes
    secret_key: bytes
    token: bytes
    public_key: bytes

    def unseal(self, data: bytes) -> bytes:
        """Unseal data using the public and secret keys."""
        return crypto_box_seal_open(
            data,
            self.public_key,
            self.secret_key,
        )

    @staticmethod
    def from_auth(auth: AuthorizationResponse, password: str) -> "EnteKeys":
        """DocString."""
        key_enc_key = kdf(
            SecretBox.KEY_SIZE,
            bytes(password, "utf8"),
            urlsafe_b64decode(bytes(auth.key_attributes.kek_salt, "utf8")),
            opslimit=auth.key_attributes.ops_limit,
            memlimit=auth.key_attributes.mem_limit,
        )

        master_key = SecretBox(key_enc_key).decrypt(
            urlsafe_b64decode(auth.key_attributes.encrypted_key),
            urlsafe_b64decode(auth.key_attributes.key_decryption_nonce),
        )

        secret_key = SecretBox(master_key).decrypt(
            urlsafe_b64decode(auth.key_attributes.encrypted_secret_key),
            urlsafe_b64decode(auth.key_attributes.secret_key_decryption_nonce),
        )

        token = crypto_box_seal_open(
            urlsafe_b64decode(auth.encrypted_token),
            urlsafe_b64decode(auth.key_attributes.public_key),
            secret_key,
        )

        return EnteKeys(
            user_id=auth.id,
            master_key=master_key,
            secret_key=secret_key,
            token=token,
            public_key=urlsafe_b64decode(auth.key_attributes.public_key),
        )


class SecretPair(BaseModel):
    """An encrypted secret and its associated nonce."""

    encrypted: str
    nonce: str

    @staticmethod
    def encrypt(key: bytes, msg: bytes) -> "SecretPair":
        """Encrypt a message with a given key and generate a nonce."""
        nonce = random(SecretBox.NONCE_SIZE)
        return SecretPair(
            encrypted=str(urlsafe_b64encode(SecretBox(key).encrypt(msg, nonce).ciphertext), "utf-8"),
            nonce=str(urlsafe_b64encode(nonce), "utf-8"),
        )

    def decrypt(self, key: bytes) -> bytes:
        """DocString."""
        return SecretBox(key).decrypt(urlsafe_b64decode(self.encrypted), nonce=urlsafe_b64decode(self.nonce))


class EnteEncKeys(BaseModel):
    """Device-encrypted version of EnteKeys for secure storage."""

    user_id: int
    master_key: SecretPair
    secret_key: SecretPair
    token: SecretPair
    public_key: str

    @staticmethod
    def from_keys(device_key: bytes, keys: EnteKeys) -> "EnteEncKeys":
        """Encrypt EnteKeys using a device key for secure storage."""
        return EnteEncKeys(
            user_id=keys.user_id,
            master_key=SecretPair.encrypt(device_key, keys.master_key),
            secret_key=SecretPair.encrypt(device_key, keys.secret_key),
            token=SecretPair.encrypt(device_key, keys.token),
            public_key=str(urlsafe_b64encode(keys.public_key), "utf-8"),
        )

    def to_keys(self, device_key: bytes) -> EnteKeys:
        """DocString."""
        return EnteKeys(
            user_id=self.user_id,
            master_key=self.master_key.decrypt(device_key),
            secret_key=self.secret_key.decrypt(device_key),
            token=self.token.decrypt(device_key),
            public_key=urlsafe_b64decode(self.public_key),
        )
