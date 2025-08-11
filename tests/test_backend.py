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
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0].email, "test@example.com")

    def test_local_refresh(self) -> None:
        """Test the local_refresh method."""
        # Create some dummy image files
        img1_path = Path(self.tmpdir.name) / "img1.jpg"
        img2_path = Path(self.tmpdir.name) / "img2.png"
        Image.new("RGB", (100, 100), color="red").save(img1_path)
        Image.new("RGB", (100, 100), color="blue").save(img2_path)

        # Initial refresh
        self.backend.local_refresh(sync_dir=self.tmpdir.name)
        media = self.backend.get_local_media()
        self.assertEqual(len(media), 2)
        self.assertEqual({m.media.file.fullpath for m in media}, {str(img1_path), str(img2_path)})

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
        self.backend.local_refresh(sync_dir=self.tmpdir.name)
        media = self.backend.get_local_media()
        self.assertEqual(len(media), 2)

        paths = {m.media.file.fullpath for m in media}
        self.assertIn(str(img2_path), paths)
        self.assertIn(str(img3_path), paths)
        self.assertNotIn(str(img1_path), paths)


if __name__ == "__main__":
    unittest.main()
