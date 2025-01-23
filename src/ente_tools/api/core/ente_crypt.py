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
"""My Docstring."""

import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path

from nacl.bindings import (
    crypto_secretstream_xchacha20poly1305_ABYTES,
    crypto_secretstream_xchacha20poly1305_HEADERBYTES,
    crypto_secretstream_xchacha20poly1305_init_pull,
    crypto_secretstream_xchacha20poly1305_KEYBYTES,
    crypto_secretstream_xchacha20poly1305_pull,
    crypto_secretstream_xchacha20poly1305_state,
    crypto_secretstream_xchacha20poly1305_TAG_FINAL,
    crypto_secretstream_xchacha20poly1305_TAG_MESSAGE,
)
from nacl.secret import SecretBox

log = logging.getLogger(__name__)


class EnteCryptError(Exception):
    """DocString."""


StreamEncryptionSize = 4 * 1024 * 1024
CHUNK_SIZE = StreamEncryptionSize + crypto_secretstream_xchacha20poly1305_ABYTES


class EnteEncryptionError(Exception):
    """DocString."""


def decrypt(key: bytes, nonce: bytes, data: bytes) -> bytes:
    """DocString."""
    return SecretBox(key).decrypt(data, nonce)


def decrypt_blob(data: bytes, header: bytes, key: bytes) -> bytes:
    """DocString."""
    if len(key) != crypto_secretstream_xchacha20poly1305_KEYBYTES:
        msg = "invalid key length"
        raise EnteEncryptionError(msg)

    if len(header) != crypto_secretstream_xchacha20poly1305_HEADERBYTES:
        msg = "invalid header length"
        raise EnteEncryptionError(msg)

    state = crypto_secretstream_xchacha20poly1305_state()

    crypto_secretstream_xchacha20poly1305_init_pull(state, header, key)

    result = crypto_secretstream_xchacha20poly1305_pull(state, data, None)

    return result[0]


@contextmanager
def decrypt_stream_to_file(
    dest: Path,
    key: bytes,
    header: bytes,
    progress: Callable[[int], None] | None = None,
) -> Generator[Callable[[bytes], None]]:
    """DocString."""
    state = crypto_secretstream_xchacha20poly1305_state()
    crypto_secretstream_xchacha20poly1305_init_pull(state, header, key)

    with Path(dest).open("wb") as f:
        tag = crypto_secretstream_xchacha20poly1305_TAG_MESSAGE

        def handle_data(data: bytes) -> None:
            nonlocal tag
            (msg, tag) = crypto_secretstream_xchacha20poly1305_pull(state, data, None)
            f.write(msg)
            if progress:
                progress(len(msg))

        yield handle_data

        if tag != crypto_secretstream_xchacha20poly1305_TAG_FINAL:
            msg = f"unfinished decryption stream: {tag}"
            raise EnteCryptError(msg)
