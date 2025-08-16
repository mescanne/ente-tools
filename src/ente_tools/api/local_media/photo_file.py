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
"""DocString."""

from datetime import UTC, datetime

from ente_tools.api.core.types_file import File


class RemotePhotoFile:
    """DocString."""

    def __init__(self, file: File) -> None:
        """DocString."""
        self.file = file

    def get_filename(self) -> str:
        """DocString."""
        return self.file.metadata["title"]

    def get_source_id(self) -> str:
        """DocString."""
        return str(self.file.metadata["deviceFolder"])

    def get_folder(self) -> str:
        """DocString."""
        return str(self.file.id)

    def get_create_time(self) -> datetime:
        """DocString."""
        return datetime.fromtimestamp(self.file.metadata["creationTime"] / 1e6, tz=UTC)

    def get_modify_time(self) -> datetime:
        """DocString."""
        return datetime.fromtimestamp(self.file.metadata["modificationTime"] / 1e6, tz=UTC)

    def get_update_time(self) -> datetime:
        """DocString."""
        return datetime.fromtimestamp(self.file.metadata["updateTime"] / 1e6, tz=UTC)

    def get_size(self) -> int:
        """DocString."""
        return self.file.info.file_size if self.file.info else 0

    def get_hash(self) -> int:
        """DocString."""
        return self.file.metadata["hash"]
