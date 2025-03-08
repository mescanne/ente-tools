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
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Self

from pydantic import BaseModel

log = logging.getLogger(__name__)


class NewLocalDiskFile(BaseModel):
    """DocString."""

    mime_type: str | None
    fullpath: str
    st_mtime_ns: int
    size: int

    @classmethod
    def from_path(cls, *, path: Path, mime_type: str | None = None) -> Self:
        """DocString."""
        stat = path.stat()
        return cls(
            mime_type=mime_type,
            fullpath=str(path),
            st_mtime_ns=stat.st_mtime_ns,
            size=stat.st_size,
        )


class MetadataModel(BaseModel, ABC):
    """DocString."""

    file: NewLocalDiskFile

    @abstractmethod
    def get_createtime(self) -> datetime | None:
        """DocString."""

    @abstractmethod
    def get_location(self) -> str | None:
        """DocString."""
