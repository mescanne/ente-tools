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
"""Core API module for interacting with Ente.

This module provides the main API client and core data types for interacting with
the Ente service. It includes the EnteAPI client class, error handling, and
data models for collections and files.
"""

from .api import EnteAPI, EnteAPIError
from .types_collection import Collection
from .types_file import File

__all__ = [
    "Collection",
    "EnteAPI",
    "EnteAPIError",
    "File",
]
