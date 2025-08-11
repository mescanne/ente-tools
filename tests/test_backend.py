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
"""Tests for the database backends."""

import tempfile
import time
import unittest
from pathlib import Path

from PIL import Image

from ente_tools.api.core.account import EnteAccount
from ente_tools.api.core.types_crypt import (
    AuthorizationResponse,
    EnteEncKeys,
    KeyAttributes,
    SecretPair,
    SPRAttributes,
)
from ente_tools.db.sqlite import SQLiteBackend


class TestSQLiteBackend(unittest.TestCase):
    """Tests for the SQLiteBackend."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.db_path = "test.db"
        self.backend = SQLiteBackend(db_path=self.db_path)
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        """Tear down the test case."""
        if Path(self.db_path).exists():
            Path(self.db_path).unlink()
        self.tmpdir.cleanup()

    def test_add_and_get_account(self) -> None:
        """Test adding and getting an account."""
        attributes = SPRAttributes(
            srpUserID="test_user",
            srpSalt="salt",
            memLimit=1,
            opsLimit=1,
            kekSalt="salt",
            isEmailMFAEnabled=False,
        )
        key_attributes = KeyAttributes(
            kekSalt="salt",
            encryptedKey="key",
            keyDecryptionNonce="nonce",
            publicKey="key",
            encryptedSecretKey="key",
            secretKeyDecryptionNonce="nonce",
            memLimit=1,
            opsLimit=1,
        )
        auth_response = AuthorizationResponse(
            id=1,
            keyAttributes=key_attributes,
            encryptedToken="token",
        )
        encrypted_keys = EnteEncKeys(
            user_id=1,
            master_key=SecretPair(encrypted="key", nonce="nonce"),
            secret_key=SecretPair(encrypted="key", nonce="nonce"),
            token=SecretPair(encrypted="key", nonce="nonce"),
            public_key="key",
        )
        account = EnteAccount(
            email="test@example.com",
            attributes=attributes,
            auth_response=auth_response,
            encrypted_keys=encrypted_keys,
            collections=[],
            files={},
        )
        self.backend.add_account(account)
        accounts = self.backend.get_accounts()
        assert len(accounts) == 1
        assert accounts[0].email == "test@example.com"

    def test_local_refresh(self) -> None:
        """Test the local_refresh method."""
        # Create some dummy image files
        initial_file_count = 2
        img1_path = Path(self.tmpdir.name) / "img1.jpg"
        img2_path = Path(self.tmpdir.name) / "img2.png"
        Image.new("RGB", (100, 100), color="red").save(img1_path)
        Image.new("RGB", (100, 100), color="blue").save(img2_path)

        # Initial refresh
        self.backend.local_refresh(sync_dir=self.tmpdir.name)
        media = self.backend.get_local_media()
        assert len(media) == initial_file_count
        assert {m.media.file.fullpath for m in media} == {str(img1_path), str(img2_path)}

        # Modify a file, add a file, delete a file
        img1_path.unlink()  # Delete img1
        img3_path = Path(self.tmpdir.name) / "img3.gif"
        Image.new("RGB", (100, 100), color="green").save(img3_path)  # Add img3

        # To simulate modification, we need to ensure mtime changes.
        # Re-saving with PIL might not be enough on fast filesystems.
        # A more reliable way is to touch the file after modification.
        Image.new("RGB", (120, 120), color="blue").save(img2_path)
        img2_path.touch()

        # Refresh again
        final_file_count = 2
        self.backend.local_refresh(sync_dir=self.tmpdir.name)
        media = self.backend.get_local_media()
        assert len(media) == final_file_count

        paths = {m.media.file.fullpath for m in media}
        assert str(img2_path) in paths
        assert str(img3_path) in paths
        assert str(img1_path) not in paths

    def test_local_refresh_with_sidecar(self) -> None:
        """Test the local_refresh method with sidecar files."""
        img_path = Path(self.tmpdir.name) / "img.jpg"
        Image.new("RGB", (100, 100), color="red").save(img_path)

        # Initial refresh
        self.backend.local_refresh(sync_dir=self.tmpdir.name)
        media = self.backend.get_local_media()
        assert len(media) == 1
        assert media[0].xmp_sidecar is None

        # Add a sidecar
        xmp_path = Path(self.tmpdir.name) / "img.xmp"
        xmp_path.write_text("<x:xmpmeta xmlns:x='adobe:ns:meta/'/>")

        self.backend.local_refresh(sync_dir=self.tmpdir.name)
        media = self.backend.get_local_media()
        assert len(media) == 1
        assert media[0].xmp_sidecar is not None
        original_sidecar_mtime = media[0].xmp_sidecar.file.st_mtime_ns

        # Modify only the sidecar
        time.sleep(0.01)  # Ensure mtime is different
        xmp_path.touch()

        self.backend.local_refresh(sync_dir=self.tmpdir.name)
        media = self.backend.get_local_media()
        assert len(media) == 1
        assert media[0].xmp_sidecar is not None
        new_sidecar_mtime = media[0].xmp_sidecar.file.st_mtime_ns
        assert new_sidecar_mtime > original_sidecar_mtime

        # Delete the sidecar
        xmp_path.unlink()

        self.backend.local_refresh(sync_dir=self.tmpdir.name)
        media = self.backend.get_local_media()
        assert len(media) == 1
        assert media[0].xmp_sidecar is None


if __name__ == "__main__":
    unittest.main()
