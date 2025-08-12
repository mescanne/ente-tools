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
"""Abstract base classes for photo libraries."""

from abc import ABC, abstractmethod
from pathlib import Path

from ente_tools.sync.photo import Photo


class Library(ABC):
    """An abstract base class for a photo library."""

    @abstractmethod
    def get_photos(self) -> list[Photo]:
        """Get a list of all photos in the library."""
        raise NotImplementedError

    @abstractmethod
    def download_photo(self, photo: Photo, dest_path: Path) -> None:
        """Download a photo to the given destination path."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the library."""
        raise NotImplementedError
