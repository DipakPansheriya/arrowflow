"""
GUI Theme Integration Test
Tests GUI initialization with default Dark Mode, switching to Light Mode,
verifying widget colors, and checking persistent storage.
"""

import os
import json
import tempfile
import unittest
import tkinter as tk
from theme_manager import theme_manager, THEMES
from gui import ArrowAutomationGUI

class TestGUIThemeIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.tmp_dir, "settings.json")
        theme_manager._settings_file = self.settings_file
        theme_manager.set_theme("dark")

        # Headless root window
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = ArrowAutomationGUI(self.root)

    def tearDown(self):
        try:
            self.app.on_closing()
        except Exception:
            pass

    def test_gui_starts_in_dark_mode_by_default(self):
        self.assertEqual(theme_manager.current_theme, "dark")
        self.assertEqual(self.app.bg_color, THEMES["dark"]["bg_color"])

    def test_gui_switches_to_light_mode_immediately(self):
        theme_manager.set_theme("light")
        self.assertEqual(theme_manager.current_theme, "light")
        self.assertEqual(self.app.bg_color, THEMES["light"]["bg_color"])
        
        # Verify persistence file contents
        with open(self.settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("theme"), "light")

    def test_gui_switches_back_to_dark_mode(self):
        theme_manager.set_theme("light")
        self.assertEqual(self.app.bg_color, THEMES["light"]["bg_color"])
        
        theme_manager.set_theme("dark")
        self.assertEqual(self.app.bg_color, THEMES["dark"]["bg_color"])
        
        with open(self.settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("theme"), "dark")

if __name__ == "__main__":
    unittest.main()
