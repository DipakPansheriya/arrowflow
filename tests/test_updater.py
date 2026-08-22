"""
Unit tests for ArrowFlow auto-update system.
"""

import os
import sys
import tempfile
import unittest

# Ensure root directory is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from version import parse_version, is_newer_version
from updater.manifest import UpdateManifest
from updater.verifier import calculate_sha256, verify_sha256, verify_authenticode_signature
from updater.client import get_updates_dir, get_staging_dir, UpdateClient
from updater_app import is_process_running, calculate_file_sha256


class TestVersionUtils(unittest.TestCase):
    def test_parse_version(self):
        self.assertEqual(parse_version("1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("V2.0"), (2, 0, 0))
        self.assertEqual(parse_version("1.1.0-beta1"), (1, 1, 0))
        self.assertEqual(parse_version("invalid"), (0, 0, 0))
        self.assertEqual(parse_version(""), (0, 0, 0))

    def test_is_newer_version(self):
        self.assertTrue(is_newer_version("1.0.0", "1.0.1"))
        self.assertTrue(is_newer_version("1.0.0", "v1.1.0"))
        self.assertTrue(is_newer_version("v1.2.3", "v2.0.0"))
        self.assertFalse(is_newer_version("1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("1.1.0", "1.0.9"))


class TestUpdateManifest(unittest.TestCase):
    def test_valid_manifest_parsing(self):
        sample_json = """{
            "version": "1.1.0",
            "release_date": "2026-08-22",
            "url": "https://example.com/ArrowFlow.exe",
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "updater_url": "https://example.com/ArrowFlowUpdater.exe",
            "changelog": "Test update"
        }"""
        manifest = UpdateManifest.from_json(sample_json)
        self.assertEqual(manifest.version, "1.1.0")
        self.assertEqual(manifest.url, "https://example.com/ArrowFlow.exe")
        self.assertEqual(manifest.sha256, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        self.assertEqual(manifest.updater_url, "https://example.com/ArrowFlowUpdater.exe")

    def test_invalid_manifest_missing_version(self):
        sample_json = """{
            "url": "https://example.com/ArrowFlow.exe",
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }"""
        with self.assertRaises(ValueError):
            UpdateManifest.from_json(sample_json)

    def test_invalid_manifest_bad_sha256(self):
        sample_json = """{
            "version": "1.1.0",
            "url": "https://example.com/ArrowFlow.exe",
            "sha256": "invalid_hash"
        }"""
        with self.assertRaises(ValueError):
            UpdateManifest.from_json(sample_json)


class TestVerifierUtils(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode="wb")
        self.temp_file.write(b"Hello ArrowFlow Test Binary Payload!")
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_sha256_calculation(self):
        # sha256 of "Hello ArrowFlow Test Binary Payload!"
        # e3b0c442... empty file vs actual content
        calculated_hash = calculate_sha256(self.temp_file.name)
        self.assertEqual(len(calculated_hash), 64)
        self.assertTrue(verify_sha256(self.temp_file.name, calculated_hash))
        self.assertFalse(verify_sha256(self.temp_file.name, "0000000000000000000000000000000000000000000000000000000000000000"))

    def test_authenticode_signature(self):
        valid, msg = verify_authenticode_signature(self.temp_file.name)
        # Unsigned test payload returns False on Windows or True on non-Windows
        if sys.platform == "win32":
            self.assertFalse(valid)
        else:
            self.assertTrue(valid)


class TestUpdateDirectories(unittest.TestCase):
    def test_directories(self):
        updates_dir = get_updates_dir()
        staging_dir = get_staging_dir()
        self.assertTrue(os.path.isdir(updates_dir))
        self.assertTrue(os.path.isdir(staging_dir))

    def test_process_running_check(self):
        current_pid = os.getpid()
        self.assertTrue(is_process_running(current_pid))
        self.assertFalse(is_process_running(99999999))


if __name__ == "__main__":
    unittest.main()
