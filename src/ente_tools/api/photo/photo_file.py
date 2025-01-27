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

from datetime import UTC, datetime

from ente_tools.api.core.types_file import File


class RemotePhotoFile:
    """DocString."""

    def __init__(self, ente_file: File) -> None:
        """DocString."""
        self.ente_file = ente_file

    def filename(self) -> str:
        """DocString."""
        return self.ente_file.metadata["title"]

    def source_id(self) -> str:
        """DocString."""
        return str(self.ente_file.metadata["deviceFolder"])

    def folder(self) -> str:
        """DocString."""
        return str(self.ente_file.id)

    def create_time(self) -> datetime:
        """DocString."""
        return datetime.fromtimestamp(self.ente_file.metadata["creationTime"] / 1e6, tz=UTC)

    def modify_time(self) -> datetime:
        """DocString."""
        return datetime.fromtimestamp(self.ente_file.metadata["modificationTime"] / 1e6, tz=UTC)

    def update_time(self) -> datetime:
        """DocString."""
        return datetime.fromtimestamp(self.ente_file.metadata["updateTime"] / 1e6, tz=UTC)

    def size(self) -> int:
        """DocString."""
        return self.ente_file.info.file_size

    def hash(self) -> int:
        """DocString."""
        return self.ente_file.metadata["hash"]
