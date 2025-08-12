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
"""Abstract base classes for photo ingestion."""

import hashlib
import logging
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import httpx

from ente_tools.sync.library import Library
from ente_tools.sync.photo import Photo

log = logging.getLogger(__name__)


class Ingestor(ABC):
    """An abstract base class for ingesting photos."""

    @abstractmethod
    def ingest(self, photo: Photo, source_library: Library) -> None:
        """Ingest a single photo."""
        raise NotImplementedError


class ImmichIngestor(Ingestor):
    """An ingestor for uploading photos to Immich."""

    def __init__(self, api_url: str, api_key: str) -> None:
        """Initialize the ImmichIngestor."""
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._headers = {
            "x-api-key": self._api_key,
            "Accept": "application/json",
        }
        self._client = httpx.Client(headers=self._headers, timeout=60)

    def ingest(self, photo: Photo, source_library: Library) -> None:
        """Ingest a single photo into Immich."""
        temp_dir = Path(tempfile.gettempdir())
        local_path = temp_dir / photo.original_filename

        try:
            # Download the file from the source library
            log.info("Downloading %s from %s...", photo.original_filename, source_library.name)
            source_library.download_photo(photo, local_path)

            # Upload to Immich
            log.info("Uploading %s to Immich...", photo.original_filename)
            self._upload_asset(local_path, photo.created_at, photo.modified_at)
        finally:
            if local_path.exists():
                local_path.unlink()

    def _upload_asset(
        self,
        file_path: Path,
        created_at: datetime,
        modified_at: datetime,
    ) -> bool:
        """Upload a single asset to Immich."""
        url = f"{self._api_url}/api/assets"
        device_asset_id = f"{file_path.name}-{int(modified_at.timestamp())}"

        try:
            with file_path.open("rb") as f:
                file_content = f.read()
                # Immich uses SHA1 for checksums, which is not ideal, but required by the API.
                sha1 = hashlib.sha1(file_content).hexdigest()  # noqa: S324

                files = {
                    "assetData": (file_path.name, file_content, "application/octet-stream"),
                }
                data = {
                    "deviceAssetId": device_asset_id,
                    "deviceId": "ente-importer",
                    "fileCreatedAt": created_at.isoformat(),
                    "fileModifiedAt": modified_at.isoformat(),
                    "isFavorite": "false",
                }
                headers = {"x-immich-checksum": sha1}

                response = self._client.post(url, files=files, data=data, headers=headers)
                response.raise_for_status()

                response_data = response.json()
                if response_data.get("duplicate"):
                    log.info("  -> %s was a duplicate.", file_path.name)
                else:
                    log.info("Successfully uploaded %s", file_path.name)
                return True
        except httpx.HTTPStatusError:
            log.exception("Failed to upload %s", file_path.name)
            return False
        except OSError:
            log.exception("Failed to read file %s", file_path.name)
            return False
