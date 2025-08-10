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
"""Data models for Ente collections and their encrypted variants."""

import json
import logging
from base64 import urlsafe_b64decode
from typing import Any

from pydantic import BaseModel, Field

from ente_tools.api.core.device import DeviceSecret
from ente_tools.api.core.ente_crypt import EnteCryptError, decrypt, decrypt_blob
from ente_tools.api.core.types_crypt import EnteKeys

log = logging.getLogger(__name__)


class CollectionUser(BaseModel):
    """User information associated with a collection."""

    id: int
    email: str
    role: str


class MagicMetadata(BaseModel):
    """Encrypted metadata associated with collections and files."""

    version: int
    count: int
    data: str
    header: str

    def decrypt(self, key: bytes) -> dict[str, Any]:
        """DocString."""
        blob = decrypt_blob(urlsafe_b64decode(self.data), urlsafe_b64decode(self.header), key)

        return json.loads(str(blob, "utf-8"))


class Collection(BaseModel):
    """Decrypted collection information."""

    id: int
    owner: CollectionUser
    enc_collection_key: DeviceSecret
    name: str
    type: str
    sharees: list[CollectionUser]
    update_time: int
    is_deleted: bool = False
    magic_metadata: dict[str, Any]
    pub_magic_metadata: dict[str, Any]
    shared_magic_metadata: dict[str, Any]


class EncryptedCollection(BaseModel):
    """Encrypted collection information as received from the server."""

    id: int
    owner: CollectionUser
    encrypted_key: str = Field(alias="encryptedKey")
    key_decryption_nonce: str | None = Field(default=None, alias="keyDecryptionNonce")
    name_decryption_nonce: str | None = Field(default=None, alias="nameDecryptionNonce")
    name: str
    encrypted_name: str = Field(default="", alias="encryptedName")
    type: str
    sharees: list[CollectionUser]
    update_time: int = Field(alias="updationTime")
    is_deleted: bool = Field(default=False, alias="isDeleted")
    magic_metadata: MagicMetadata | None = Field(default=None, alias="magicMetadata")
    pub_magic_metadata: MagicMetadata | None = Field(default=None, alias="pubMagicMetadata")
    shared_magic_metadata: MagicMetadata | None = Field(default=None, alias="sharedMagicMetadata")

    def collection_key(self, key: EnteKeys) -> bytes:
        """DocString."""
        if self.owner.id == key.user_id:
            if not self.key_decryption_nonce:
                msg = "missing keyDecryptionNonce"
                raise EnteCryptError(msg)

            # Decrypt it with the master key
            return decrypt(
                key.master_key,
                urlsafe_b64decode(self.key_decryption_nonce),
                urlsafe_b64decode(self.encrypted_key),
            )

        # Unseal it as a shared key
        return key.unseal(urlsafe_b64decode(self.encrypted_key))

    def to_collection(self, ente_key: EnteKeys) -> Collection:
        """DocString."""
        key = self.collection_key(ente_key)

        name = self.name
        if self.encrypted_name and self.name_decryption_nonce:
            name = str(
                decrypt(key, urlsafe_b64decode(self.name_decryption_nonce), urlsafe_b64decode(self.encrypted_name)),
                "utf-8",
            )

        metadata = self.magic_metadata.decrypt(key) if self.magic_metadata else {}
        pub_metadata = self.pub_magic_metadata.decrypt(key) if self.pub_magic_metadata else {}
        shared_metadata = self.shared_magic_metadata.decrypt(key) if self.shared_magic_metadata else {}

        return Collection(
            id=self.id,
            owner=self.owner,
            enc_collection_key=DeviceSecret.encrypt(key),
            name=name,
            type=self.type,
            sharees=self.sharees,
            update_time=self.update_time,
            is_deleted=self.is_deleted,
            magic_metadata=metadata,
            pub_magic_metadata=pub_metadata,
            shared_magic_metadata=shared_metadata,
        )
