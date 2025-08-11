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
"""SQLModel definitions for the database."""

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel

from ente_tools.api.core.types_collection import Collection
from ente_tools.api.core.types_crypt import AuthorizationResponse, EnteEncKeys, SPRAttributes
from ente_tools.api.core.types_file import File


class EnteAccountDB(SQLModel, table=True):
    """Represents an authenticated Ente account in the database."""

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    attributes: SPRAttributes = Field(sa_column=Column(JSON))
    auth_response: AuthorizationResponse = Field(sa_column=Column(JSON))
    encrypted_keys: EnteEncKeys = Field(sa_column=Column(JSON))
    collections: list[Collection] = Field(sa_column=Column(JSON))
    files: dict[int, list[File]] = Field(sa_column=Column(JSON))


class MediaDB(SQLModel, table=True):
    """Represents a media file in the database."""

    id: int | None = Field(default=None, primary_key=True)
    media: dict = Field(sa_column=Column(JSON))
    xmp_sidecar: dict | None = Field(default=None, sa_column=Column(JSON))
    fullpath: str = Field(unique=True)
