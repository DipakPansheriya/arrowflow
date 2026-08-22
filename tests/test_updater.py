import os
import json
import shutil
import tempfile
import unittest

from version import CURRENT_VERSION, parse_version, is_newer_version
from update_checker import fetch_update_manifest, normalize_manifest, calculate_sha256, download_file_with_progress

class TestArrowFlowUpdater(unittest.TestCase):
    """Automated Unit Tests for ArrowFlow Semantic Versioning, Manifest Checker & Downloader."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_semantic_version_parsing(self):
        """Verify semantic version parsing and comparison logic."""
        self.assertEqual(parse_version("1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("1.10.0"), (1, 10, 0))
        self.assertEqual(parse_version("V2.0.0-beta"), (2, 0, 0))

        # Semantic comparison checks
        self.assertTrue(is_newer_version("1.0.0", "1.1.0"))
        self.assertTrue(is_newer_version("1.9.0", "1.10.0"))
        self.assertTrue(is_newer_version("1.0.0", "2.0.0"))

        # Non-update / downgrade checks
        self.assertFalse(is_newer_version("1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("1.1.0", "1.0.0"))
        self.assertFalse(is_newer_version("1.10.0", "1.9.0"))

    def test_manifest_parsing_from_local_file(self):
        """Verify fetching and parsing update manifest from local file path."""
        manifest_data = {
            "version": "1.1.0",
            "download_url": "https://arrowflow.web.app/downloads/ArrowFlow-1.1.0.exe",
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "mandatory": False,
            "release_notes": "Added TOTP 2FA and Auto-Updater features."
        }
        manifest_path = os.path.join(self.temp_dir, "latest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f)

        parsed = fetch_update_manifest(manifest_path)
        self.assertEqual(parsed["version"], "1.1.0")
        self.assertEqual(parsed["sha256"], "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def test_github_release_normalization(self):
        """Verify normalizing GitHub Releases API JSON payload."""
        github_payload = {
            "tag_name": "v1.0.8",
            "body": "Fixed update check and added OTP warnings.",
            "assets": [
                {
                    "name": "ArrowFlow.dmg",
                    "browser_download_url": "https://github.com/DipakPansheriya/arrowflow/releases/download/v1.0.8/ArrowFlow.dmg",
                    "digest": "sha256:35128c368876de1136113a4832e7b3a7d1dab5f9851ab3ea31674e1121d26488"
                },
                {
                    "name": "ArrowFlow.exe",
                    "browser_download_url": "https://github.com/DipakPansheriya/arrowflow/releases/download/v1.0.8/ArrowFlow.exe",
                    "digest": "sha256:d93d5adfcc3c0dc17c93e6082ffe2e9cdbd0177dc645e5c28a3bf76c4b1ab028"
                }
            ]
        }
        normalized = normalize_manifest(github_payload)
        self.assertEqual(normalized["version"], "1.0.8")
        self.assertIn("ArrowFlow", normalized["download_url"])
        self.assertEqual(normalized["release_notes"], "Fixed update check and added OTP warnings.")

    def test_sha256_calculation_and_verification(self):
        """Verify SHA-256 hash calculation for downloaded files."""
        test_file = os.path.join(self.temp_dir, "test_binary.bin")
        content = b"ArrowFlow Binary Test Payload"
        with open(test_file, "wb") as f:
            f.write(content)

        calculated = calculate_sha256(test_file)
        import hashlib
        expected = hashlib.sha256(content).hexdigest()
        self.assertEqual(calculated, expected)

    def test_download_file_with_local_source(self):
        """Verify file download logic using a local file source."""
        src_path = os.path.join(self.temp_dir, "source.exe")
        dst_path = os.path.join(self.temp_dir, "downloaded.exe")

        content = b"Dummy Executable Content 1234567890" * 100
        with open(src_path, "wb") as f:
            f.write(content)

        progress_calls = []
        def progress_cb(dl, total):
            progress_calls.append((dl, total))

        success = download_file_with_progress(src_path, dst_path, progress_callback=progress_cb)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(dst_path))
        self.assertEqual(calculate_sha256(src_path), calculate_sha256(dst_path))
        self.assertGreater(len(progress_calls), 0)

if __name__ == "__main__":
    unittest.main()
