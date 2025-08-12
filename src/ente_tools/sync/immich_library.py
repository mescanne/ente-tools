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
"""An implementation of the Library abstract base class for Immich."""

import httpx

from ente_tools.sync.library import Library
from ente_tools.sync.photo import Photo


class ImmichLibrary(Library):
    """An implementation of the Library abstract base class for Immich."""

    def __init__(self, api_url: str, api_key: str) -> None:
        """Initialize the ImmichLibrary."""
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._headers = {
            "x-api-key": self._api_key,
            "Accept": "application/json",
        }
        self._client = httpx.Client(headers=self._headers)

    def get_photos(self) -> list[Photo]:
        """Get a list of all photos in the Immich library."""
        url = f"{self._api_url}/api/search"
        photos = []
        page = 1
        while True:
            response = self._client.post(url, json={"page": page, "size": 1000})
            response.raise_for_status()
            data = response.json()
            assets = data.get("assets", {}).get("items", [])
            if not assets:
                break

from dateutil.parser import isoparse


            photos.extend(
                Photo(
                    id=asset["id"],
                    sha1_hash=asset["checksum"],
                    original_filename=asset["originalFileName"],
                    created_at=isoparse(asset["fileCreatedAt"]),
                    modified_at=isoparse(asset["fileModifiedAt"]),
                )
                for asset in assets
            )
            page += 1
        return photos

    @property
    def name(self) -> str:
        """Get the name of the library."""
        return f"Immich({self._api_url})"
