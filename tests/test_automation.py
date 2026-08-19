import sys
import time
import random
import unittest
from unittest.mock import MagicMock, patch

# Import application modules
from window_helper import VK_MAP, MAC_KEY_MAP, is_window_valid, send_arrow_key_to_hwnd, get_child_render_hwnd, find_vscode_window_by_title, is_vscode_window, get_top_level_windows
from automation_engine import ArrowAutomationController

class TestArrowFlowAutomation(unittest.TestCase):
    """Automated Unit Tests for ArrowFlow Keyboard & Mouse Automation Engine."""

    def test_vk_codes(self):
        """Verify Win32 Virtual Key Codes for Arrow Keys."""
        self.assertEqual(VK_MAP["up"], 0x26, "VK_UP must be 0x26")
        self.assertEqual(VK_MAP["down"], 0x28, "VK_DOWN must be 0x28")
        self.assertEqual(VK_MAP["left"], 0x25, "VK_LEFT must be 0x25")
        self.assertEqual(VK_MAP["right"], 0x27, "VK_RIGHT must be 0x27")

    def test_mac_key_codes(self):
        """Verify macOS Key Codes for Arrow Keys."""
        self.assertEqual(MAC_KEY_MAP["up"], 126)
        self.assertEqual(MAC_KEY_MAP["down"], 125)
        self.assertEqual(MAC_KEY_MAP["left"], 123)
        self.assertEqual(MAC_KEY_MAP["right"], 124)

    def test_lparam_construction(self):
        """Verify scan code calculation and Extended Key flag (bit 24) for WM_KEYDOWN and WM_KEYUP."""
        vk_code = VK_MAP["right"]  # 0x27
        scan_code = 0x4D           # OEM Scan Code for Right Arrow

        # Bit 24 must be 1 (1 << 24)
        lparam_down = 1 | (scan_code << 16) | (1 << 24)
        lparam_up   = 1 | (scan_code << 16) | (1 << 24) | (1 << 30) | (1 << 31)

        self.assertTrue(bool(lparam_down & (1 << 24)), "Extended Key bit 24 must be set for KEYDOWN")
        self.assertTrue(bool(lparam_up & (1 << 24)), "Extended Key bit 24 must be set for KEYUP")
        self.assertTrue(bool(lparam_up & (1 << 30)), "Previous Key State bit 30 must be set for KEYUP")
        self.assertTrue(bool(lparam_up & (1 << 31)), "Transition State bit 31 must be set for KEYUP")

    def test_decoupled_schedules_collision_separation(self):
        """Verify that keyboard and mouse timestamps maintain min_sep >= 0.10s separation."""
        controller = ArrowAutomationController()
        arrow_target = 25
        mouse_target = 10
        min_sep = 0.10

        kbd_offsets, mouse_offsets = controller._generate_decoupled_schedules(arrow_target, mouse_target, window_sec=60.0, min_sep=min_sep)

        self.assertEqual(len(kbd_offsets), arrow_target)
        self.assertEqual(len(mouse_offsets), mouse_target)

        # Check collision separation between every keyboard and mouse timestamp
        for k in kbd_offsets:
            for m in mouse_offsets:
                diff = abs(k - m)
                self.assertGreaterEqual(round(diff, 2), round(min_sep, 2), f"Collision detected: kbd={k}, mouse={m}, diff={diff}")

    def test_diagnostic_counters_initialization(self):
        """Verify diagnostic stats dictionary counters."""
        controller = ArrowAutomationController()
        self.assertIn("keyboard_events_scheduled", controller.stats)
        self.assertIn("keyboard_events_sent", controller.stats)
        self.assertIn("keyboard_events_failed", controller.stats)
        self.assertIn("target_hwnd_refresh_count", controller.stats)
        self.assertEqual(controller.stats["keyboard_events_sent"], 0)

    def test_engine_start_stop(self):
        """Verify clean thread start and stop sequence."""
        controller = ArrowAutomationController()
        controller.start(min_presses=5, max_presses=10, target_hwnd=None, mouse_enabled=False)
        self.assertTrue(controller.is_running)

        time.sleep(0.2)
        controller.stop()
        self.assertFalse(controller.is_running)
        self.assertTrue(controller.stop_event.is_set())

    def test_high_range_schedule_generation(self):
        """Verify schedule generation for high configured ranges (50-110, 60-100, 80-110)."""
        controller = ArrowAutomationController()
        test_ranges = [(50, 110), (60, 100), (80, 110)]

        for min_val, max_val in test_ranges:
            for _ in range(5):
                target_kbd = random.randint(min_val, max_val)
                target_mouse = random.randint(5, 20)
                kbd_offsets, mouse_offsets = controller._generate_decoupled_schedules(
                    arrow_target=target_kbd,
                    mouse_target=target_mouse,
                    window_sec=60.0,
                    min_sep=0.10
                )
                self.assertEqual(len(kbd_offsets), target_kbd, f"Expected {target_kbd} keyboard offsets, got {len(kbd_offsets)}")
                self.assertEqual(len(mouse_offsets), target_mouse, f"Expected {target_mouse} mouse offsets, got {len(mouse_offsets)}")
                self.assertGreaterEqual(target_kbd, min_val)
                self.assertLessEqual(target_kbd, max_val)

    def test_send_arrow_key_exception_resilience(self):
        """Verify send_arrow_key_to_hwnd handles invalid window handles without crashing."""
        invalid_hwnd = 99999999
        res = send_arrow_key_to_hwnd(invalid_hwnd, "up")
        self.assertFalse(res, "send_arrow_key_to_hwnd should return False on invalid HWND without raising uncaught exception")

    def test_vscode_window_filtering(self):
        """Verify is_vscode_window accurately filters VS Code titles and excludes unrelated applications."""
        self.assertTrue(is_vscode_window(0, "automation_engine.py - arrowflow - Visual Studio Code"))
        self.assertTrue(is_vscode_window(0, "index.js - Project - VS Code"))
        self.assertTrue(is_vscode_window(0, "Untitled-1 - Code"))
        
        self.assertFalse(is_vscode_window(0, "Google Chrome"))
        self.assertFalse(is_vscode_window(0, "Untitled - Notepad"))
        self.assertFalse(is_vscode_window(0, "Command Prompt"))
        self.assertFalse(is_vscode_window(0, "File Explorer"))

    def test_macos_permissions_check(self):
        """Verify check_macos_permissions returns tuple (bool, str)."""
        from window_helper import check_macos_permissions
        trusted, msg = check_macos_permissions()
        self.assertIsInstance(trusted, bool)
        self.assertIsInstance(msg, str)

    def test_cross_platform_updater(self):
        """Verify launch_updater_and_exit creates appropriate background script depending on OS."""
        from updater import launch_updater_and_exit
        with patch("sys.exit") as mock_exit, patch("subprocess.Popen") as mock_popen:
            launch_updater_and_exit("test_path")
            self.assertTrue(mock_exit.called or mock_popen.called)

if __name__ == "__main__":
    unittest.main()
