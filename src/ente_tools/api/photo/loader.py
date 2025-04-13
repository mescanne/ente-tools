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
"""Module for loading and parsing metadata from media files."""

import hashlib
import logging
from base64 import urlsafe_b64encode
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Self
from xml.etree import ElementTree as ET

import av
from PIL import ExifTags, Image
from pillow_heif import register_heif_opener

from ente_tools.api.photo.local_file import MetadataModel, NewLocalDiskFile

log = logging.getLogger(__name__)


register_heif_opener()

type BaseTypes = str | float | bool
type DictTypes = dict[str, BaseTypes] | list[BaseTypes] | BaseTypes


class NewImageFile(MetadataModel):
    """Represents a new image file with its metadata."""

    hash: str
    data_hash: str | None
    media_type: Literal["image"] = "image"
    metadata: Mapping[str, DictTypes]

    @classmethod
    def from_file(cls, file: NewLocalDiskFile) -> Self | None:
        """Create a NewImageFile instance from a local disk file.

        Args:
            file: The local disk file to process.

        Returns:
            A NewImageFile instance if successful, None otherwise.

        """
        try:
            with Image.open(file.fullpath) as img:
                # Extract metadata
                metadata: dict[str, DictTypes] = {}
                assign_to_dict(metadata, "XMP", img.getxmp())
                exif_data = img.getexif()
                metadata.update({f"Base:{ExifTags.TAGS.get(k, k)}": str(v) for k, v in exif_data.items()})
                metadata.update(
                    {
                        f"GPS:{ExifTags.GPSTAGS.get(k, k)}": str(v)
                        for k, v in exif_data.get_ifd(
                            ExifTags.IFD.GPSInfo,
                        ).items()
                    },
                )
                metadata.update(
                    {
                        f"Extra:{ExifTags.TAGS.get(k, k)}": str(v)
                        for k, v in exif_data.get_ifd(
                            ExifTags.IFD.Exif,
                        ).items()
                        if not isinstance(v, bytes | bytearray)
                    },
                )

                # Hash the data
                m = hashlib.sha256()
                m.update(img.tobytes())

                return cls(
                    file=file,
                    hash=hash_file(file.fullpath),
                    data_hash=m.hexdigest(),
                    metadata=metadata,
                )

        except Exception as e:  # noqa: BLE001
            log.warning("failed extracting image metadata from '%s': %s", file.fullpath, e)
            log.critical(e, exc_info=True)

        return None

    def get_location(self) -> str | None:
        """Get the location metadata of the image.

        Returns:
            The location string if available, None otherwise.

        """
        return None

    def get_createtime(self) -> datetime | None:
        """Get the creation time metadata of the image.

        Returns:
            The creation time as a datetime object if available, None otherwise.

        """
        return None


class NewAVFile(MetadataModel):
    """DocString."""

    hash: str
    data_hash: str | None
    media_type: Literal["video"] = "video"
    metadata: Mapping[str, DictTypes]

    @classmethod
    def from_file(cls, file: NewLocalDiskFile) -> Self | None:
        """Create a NewAVFile instance from a local disk file.

        Args:
            file: The local disk file to process.

        Returns:
            A NewAVFile instance if successful, None otherwise.

        """
        try:
            with av.open(file.fullpath) as f:
                # Calculate internal hash
                m = hashlib.sha256()
                for packet in f.demux():
                    m.update(bytes(packet))

                return cls(
                    file=file,
                    hash=hash_file(file.fullpath),
                    data_hash=m.hexdigest(),
                    metadata=f.metadata,
                )

        except Exception as e:  # noqa: BLE001
            log.warning("Failed parsing video metadata from %s: %s", file.fullpath, e)
            log.critical(e, exc_info=True)

        return None

    def get_location(self) -> str | None:
        """Get the location metadata of the video.

        Returns:
            The location string if available, None otherwise.

        """
        return None

    def get_createtime(self) -> datetime | None:
        """Get the creation time metadata of the video.

        Returns:
            The creation time as a datetime object if available, None otherwise.

        """
        return None


class NewXMPDiskFile(MetadataModel):
    """DocString."""

    metadata: dict[str, DictTypes]

    @classmethod
    def from_file(cls, sidecar: NewLocalDiskFile) -> Self:
        """Create a NewXMPDiskFile instance from a sidecar file.

        Args:
            sidecar: The sidecar file to process.

        Returns:
            A NewXMPDiskFile instance.

        """
        metadata: dict[str, DictTypes] = {}

        assign_to_dict_element(metadata, "XMP", ET.parse(sidecar.fullpath).getroot())  # noqa: S314

        return cls(
            file=sidecar,
            metadata=metadata,
        )

    def get_location(self) -> str | None:
        """Get the location metadata from the XMP file.

        Returns:
            The location string if available, None otherwise.

        """
        return None

    def get_createtime(self) -> datetime | None:
        """Get the creation time metadata from the XMP file.

        Returns:
            The creation time as a datetime object if available, None otherwise.

        """
        # Extract XMP information
        datetime_original_keys = [k for k in self.metadata if k.startswith("XMP:") and "DateTimeOriginal" in k]

        if len(datetime_original_keys) > 1:
            log.warning("File has multiple XMP DateTimeOriginal keys: %s", ", ".join(datetime_original_keys))

        ## What to do now?
        for d in datetime_original_keys:
            log.info("Merging in datetime original value: %s", self.metadata[d])

        # Fix this
        return datetime.now(tz=UTC)


type MediaTypes = NewImageFile | NewAVFile


def identify_media_type(mime_type: str) -> type[MediaTypes] | None:
    """Identify the media type based on the MIME type.

    Args:
        mime_type: The MIME type string.

    Returns:
        The corresponding media type class if recognized, None otherwise.

    """
    if mime_type.startswith("image/"):
        return NewImageFile
    if mime_type.startswith("video/"):
        return NewAVFile
    return None


def hash_file(path: str) -> str:
    """Calculate the hash of a file.

    Args:
        path: The path to the file.

    Returns:
        The hash of the file as a string.

    """
    with Path(path).open("rb") as f:
        return str(
            urlsafe_b64encode(hashlib.file_digest(f, "blake2b").digest()),
            "utf8",
        )


def get_unique_key(new_dict: dict[str, DictTypes], key: str) -> str:
    """Generate a unique key for a dictionary.

    Args:
        new_dict: The dictionary to check for key uniqueness.
        key: The base key to make unique.

    Returns:
        A unique key string.

    """
    new_key = key
    idx = 0
    while True:
        if new_key not in new_dict:
            break
        new_key = key + str(idx)
        idx += 1
    return new_key


def assign_to_dict_element(new_dict: dict[str, DictTypes], key: str, value: ET.Element) -> None:
    """Assign an XML element's data to a dictionary.

    Args:
        new_dict: The dictionary to assign data to.
        key: The base key for the element.
        value: The XML element to process.

    Returns:
        None.

    """
    # Build the new key
    new_key = get_unique_key(new_dict, key + ":" + value.tag.strip())

    # Add direct text (and tail)
    text = str(value.text.strip()) if value.text else ""
    for c in value:
        if c.tail and c.tail.strip() != "":
            text += "<...>" + str(c.tail.strip())
    if text:
        new_dict[new_key] = text

    # Add attributes
    for k, v in value.attrib.items():
        if v.strip():
            new_dict[new_key + "[" + k.strip() + "]"] = str(v.strip())

    # Process children
    for child in value:
        assign_to_dict_element(new_dict, new_key, child)


def assign_to_dict(new_dict: dict[str, DictTypes], key: str, value: DictTypes) -> None:
    """Assign data to a dictionary, handling nested dictionaries and lists.

    Args:
        new_dict: The dictionary to assign data to.
        key: The base key for the data.
        value: The data to assign.

    Returns:
        None.

    """
    if isinstance(value, dict):
        for k, v in value.items():
            assign_to_dict(new_dict, key + ":" + str(k), v)

    elif isinstance(value, list):
        for i in range(len(value)):
            assign_to_dict(new_dict, key + ":" + str(i), value[i])

    else:
        new_dict[get_unique_key(new_dict, key)] = value
