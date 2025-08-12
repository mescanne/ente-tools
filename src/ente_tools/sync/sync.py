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
"""The core synchronization logic."""

import logging

from ente_tools.sync.library import Library
from ente_tools.sync.photo import Photo

log = logging.getLogger(__name__)


class Sync:
    """Orchestrates the synchronization between two libraries."""

    def __init__(self, source: Library, dest: Library) -> None:
        """Initialize the Sync object."""
        self._source = source
        self._dest = dest

    def get_missing_photos(self) -> list[Photo]:
        """Get photos in the source library but not the destination."""
        log.info("Fetching photos from source library: %s", self._source.name)
        source_photos = self._source.get_photos()
        log.info("Found %d photos in source library.", len(source_photos))

        log.info("Fetching photos from destination library: %s", self._dest.name)
        dest_photos = self._dest.get_photos()
        log.info("Found %d photos in destination library.", len(dest_photos))

        dest_hashes = {photo.blake2b_hash for photo in dest_photos}
        missing_photos = [photo for photo in source_photos if photo.blake2b_hash not in dest_hashes]

        log.info("Found %d missing photos.", len(missing_photos))
        return missing_photos
