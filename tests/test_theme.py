"""
Unit Tests for ArrowFlow Theme Manager
Tests default theme state, palette retrieval, preference persistence, and listener callbacks.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock
from theme_manager import ThemeManager, THEMES

class TestThemeManager(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.tmp_dir, "settings.json")
        self.tm = ThemeManager()
        self.tm._settings_file = self.settings_file

    def test_default_theme_is_dark(self):
        self.tm._load_preference()
        self.assertEqual(self.tm.current_theme, "dark")
        self.assertEqual(self.tm.get_color("bg_color"), THEMES["dark"]["bg_color"])

    def test_switch_theme_persists_preference(self):
        self.tm.set_theme("light")
        self.assertEqual(self.tm.current_theme, "light")
        self.assertEqual(self.tm.get_color("bg_color"), THEMES["light"]["bg_color"])
        
        # Instantiate a new manager reading from the same file
        new_tm = ThemeManager()
        new_tm._settings_file = self.settings_file
        new_tm._load_preference()
        self.assertEqual(new_tm.current_theme, "light")

    def test_listener_notified_on_theme_change(self):
        callback = MagicMock()
        self.tm.add_listener(callback)
        self.tm.set_theme("light")
        callback.assert_called_once_with("light")

        callback.reset_mock()
        self.tm.set_theme("dark")
        callback.assert_called_once_with("dark")

    def test_invalid_theme_name_ignored(self):
        self.tm.set_theme("invalid_theme_mode")
        self.assertIn(self.tm.current_theme, ["dark", "light"])

if __name__ == "__main__":
    unittest.main()
