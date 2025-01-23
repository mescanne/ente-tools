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

import gzip
import hashlib
import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from pydantic import BaseModel

log = logging.getLogger(__name__)


@contextmanager
def load[T: BaseModel](dbfile: str, model: type[T], *, skip_save: bool = False, max_vers: int = 10) -> Generator[T]:
    """DocString."""
    path = Path(dbfile)

    data: T
    if not path.is_file():
        data = model.model_construct()
    else:
        with gzip.open(path, "rt") as f:
            data = model.model_validate_json(f.read())
        log.info("Loaded data from %s", path)

    # Yield to the context
    # If there is an exception, it won't be saved
    yield data

    if skip_save:
        return

    tmp_data_path = Path(str(path) + ".tmp")

    # Remove temporary file if it exists
    if tmp_data_path.exists():
        tmp_data_path.unlink()

    # Write out the data to temporary file
    with gzip.open(tmp_data_path, "xt", compresslevel=1) as f:
        f.write(data.model_dump_json(by_alias=True))

    # Rotate database if it exists
    if path.exists():
        # Check to see if the file is new
        with path.open("rb") as old, tmp_data_path.open("rb") as new:
            # Exit early if the hash is the same
            if hashlib.file_digest(old, "md5").hexdigest() == hashlib.file_digest(new, "md5").hexdigest():
                log.info("No data changed.")
                tmp_data_path.unlink()
                return

        # Delete max version if it exists
        max_path = Path(str(path) + f".{max_vers}")
        if max_path.exists():
            max_path.unlink()

        # Rename previous versions
        for ver in list(reversed(range(1, max_vers))):
            vpath = Path(str(path) + f".{ver}")
            if vpath.exists():
                vpath.rename(Path(str(path) + f".{ver + 1}"))

        # Rename first one
        path.rename(Path(str(path) + ".1"))

    # Rename temporary path
    log.info("Saved data to %s", path)
    tmp_data_path.rename(path)
