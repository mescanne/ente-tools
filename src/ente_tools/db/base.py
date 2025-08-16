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
"""Base class for database backends."""

from abc import ABC, abstractmethod

from ente_tools.api.core.account import EnteAccount
from ente_tools.api.local_media.file_metadata import Media


class Backend(ABC):
    """Abstract base class for database backends."""

    @abstractmethod
    def get_accounts(self) -> list[EnteAccount]:
        """Get all accounts from the backend."""
        raise NotImplementedError

    @abstractmethod
    def add_account(self, account: EnteAccount) -> None:
        """Add an account to the backend."""
        raise NotImplementedError

    @abstractmethod
    def remove_account(self, email: str) -> None:
        """Remove an account from the backend by email."""
        raise NotImplementedError

    @abstractmethod
    def get_local_media(self) -> list[Media]:
        """Get all local media from the backend."""
        raise NotImplementedError

    @abstractmethod
    def local_refresh(self, sync_dir: str, *, force_refresh: bool = False) -> None:
        """Refresh the local data by scanning the specified directory for media files."""
        raise NotImplementedError
