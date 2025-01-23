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

import json
import logging
from base64 import b64decode
from typing import Any

from pydantic import BaseModel, Field

from ente_tools.api.core.device import DeviceSecret
from ente_tools.api.core.ente_crypt import decrypt, decrypt_blob
from ente_tools.api.core.types_collection import MagicMetadata

log = logging.getLogger(__name__)


class FileInfo(BaseModel):
    """DocString."""

    file_size: int = Field(alias="fileSize")
    thumb_size: int = Field(alias="thumbSize")


class FileAttributes(BaseModel):
    """DocString."""

    encrypted_data: str | None = Field(default=None, alias="encryptedData")
    decryption_header: str = Field(alias="decryptionHeader")

    def decrypt(self, key: bytes) -> dict[str, Any]:
        """DocString."""
        if not self.encrypted_data:
            return {}

        blob = decrypt_blob(b64decode(self.encrypted_data), b64decode(self.decryption_header), key)

        return json.loads(str(blob, "utf-8"))


class File(BaseModel):
    """DocString."""

    id: int
    owner_id: int
    enc_file_key: DeviceSecret
    collection_id: int
    collection_owner_id: int
    file: FileAttributes
    thumbnail: FileAttributes
    metadata: dict[str, Any]
    is_deleted: bool
    update_time: int
    magic_metadata: dict[str, Any]
    pub_magic_metadata: dict[str, Any]
    info: FileInfo


class EncryptedFile(BaseModel):
    """DocString."""

    id: int
    owner_id: int = Field(alias="ownerID")
    collection_id: int = Field(alias="collectionID")
    collection_owner_id: int = Field(alias="collectionOwnerID")
    encrypted_key: str = Field(alias="encryptedKey")
    key_decryption_nonce: str = Field(alias="keyDecryptionNonce")
    file: FileAttributes
    thumbnail: FileAttributes
    metadata: FileAttributes
    is_deleted: bool = Field(alias="isDeleted")
    update_time: int = Field(alias="updationTime")
    magic_metadata: MagicMetadata | None = Field(default=None, alias="magicMetadata")
    pub_magic_metadata: MagicMetadata | None = Field(default=None, alias="pubMagicMetadata")
    info: FileInfo

    def file_key(self, collection_key: bytes) -> bytes:
        """DocString."""
        return decrypt(collection_key, b64decode(self.key_decryption_nonce), b64decode(self.encrypted_key))

    def to_file(self, collection_key: bytes) -> File:
        """DocString."""
        key = self.file_key(collection_key)

        metadata = self.metadata.decrypt(key) if self.metadata else {}
        pub_metadata = self.pub_magic_metadata.decrypt(key) if self.pub_magic_metadata else {}
        magic_metadata = self.magic_metadata.decrypt(key) if self.magic_metadata else {}

        return File(
            id=self.id,
            owner_id=self.owner_id,
            enc_file_key=DeviceSecret.encrypt(key),
            collection_id=self.collection_id,
            collection_owner_id=self.collection_owner_id,
            file=self.file,
            thumbnail=self.thumbnail,
            metadata=metadata,
            is_deleted=self.is_deleted,
            update_time=self.update_time,
            magic_metadata=magic_metadata,
            pub_magic_metadata=pub_metadata,
            info=self.info,
        )
