"""
Theme Manager for ArrowFlow Desktop Application
Provides centralized Dark Mode and Light Mode color palettes, preference persistence,
TTK style configuration, and dynamic theme switching listeners.
"""

import os
import json
from typing import Dict, Any, Optional, Callable, List
import tkinter as tk
from tkinter import ttk

THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg_color": "#090C15",
        "card_bg": "#121625",
        "card_sec_bg": "#192035",
        "input_bg": "#0E121E",
        "border_color": "#242E48",
        "accent_blue": "#00D2FF",
        "accent_blue_hover": "#33DDFF",
        "accent_green": "#00E5A3",
        "accent_red": "#FF4D6D",
        "fg_color": "#F0F4FF",
        "sec_fg": "#8E9BB5",
        "muted_fg": "#5C6B8A",
        "progress_bg": "#1C253B",
        "disabled_bg": "#192035",
        "disabled_fg": "#424E68",
        "btn_text": "#090C15",
    },
    "light": {
        "bg_color": "#F4F6F9",
        "card_bg": "#FFFFFF",
        "card_sec_bg": "#E9ECEF",
        "input_bg": "#FFFFFF",
        "border_color": "#D0D7DE",
        "accent_blue": "#007ACC",
        "accent_blue_hover": "#005999",
        "accent_green": "#00A86B",
        "accent_red": "#E53935",
        "fg_color": "#1F2328",
        "sec_fg": "#57606A",
        "muted_fg": "#6E7781",
        "progress_bg": "#E1E4E8",
        "disabled_bg": "#E9ECEF",
        "disabled_fg": "#8C959F",
        "btn_text": "#FFFFFF",
    }
}

class ThemeManager:
    """Centralized theme manager for ArrowFlow application state and persistence."""

    def __init__(self):
        self._current_theme: str = "dark"
        self._listeners: List[Callable[[str], None]] = []
        self._settings_file = self._get_settings_file_path()
        self._load_preference()

    def _get_settings_file_path(self) -> str:
        """Get path to the local settings.json configuration file."""
        app_data = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or os.path.expanduser("~")
        arrow_dir = os.path.join(app_data, "ArrowFlow")
        os.makedirs(arrow_dir, exist_ok=True)
        return os.path.join(arrow_dir, "settings.json")

    def _load_preference(self):
        """Load theme preference from settings file. Defaults to 'dark' if missing or invalid."""
        try:
            if os.path.exists(self._settings_file):
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    theme = data.get("theme", "dark")
                    if theme in THEMES:
                        self._current_theme = theme
                    else:
                        self._current_theme = "dark"
            else:
                self._current_theme = "dark"
        except Exception:
            self._current_theme = "dark"

    def _save_preference(self):
        """Persist current theme preference to settings file."""
        try:
            data = {}
            if os.path.exists(self._settings_file):
                try:
                    with open(self._settings_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data["theme"] = self._current_theme
            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @property
    def current_theme(self) -> str:
        return self._current_theme

    def get_color(self, key: str) -> str:
        """Get color value for the specified key in the current theme."""
        palette = THEMES.get(self._current_theme, THEMES["dark"])
        return palette.get(key, THEMES["dark"].get(key, "#000000"))

    def get_colors(self) -> Dict[str, str]:
        """Get full color dictionary for current theme."""
        return THEMES.get(self._current_theme, THEMES["dark"]).copy()

    def set_theme(self, theme_name: str):
        """Switch active theme ('dark' or 'light'), persist choice, and notify listeners."""
        if theme_name not in THEMES:
            return
        if self._current_theme == theme_name:
            self._save_preference()
            return

        self._current_theme = theme_name
        self._save_preference()

        for listener in list(self._listeners):
            try:
                listener(theme_name)
            except Exception:
                pass

    def add_listener(self, callback: Callable[[str], None]):
        """Register a callback listener to be notified when theme changes."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str], None]):
        """Unregister a theme change callback listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def apply_ttk_styles(self, style: ttk.Style, root: tk.Tk):
        """Configure central TTK widget styles and Tk option database for current theme."""
        colors = self.get_colors()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Root style
        style.configure(
            ".",
            background=colors["bg_color"],
            foreground=colors["fg_color"],
            font=("Segoe UI", 9)
        )

        # Combobox style
        style.configure(
            "TCombobox",
            fieldbackground=colors["input_bg"],
            background=colors["card_sec_bg"],
            foreground=colors["fg_color"],
            arrowcolor=colors["accent_blue"],
            bordercolor=colors["border_color"],
            lightcolor=colors["border_color"],
            darkcolor=colors["border_color"],
            padding=5
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["input_bg"])],
            foreground=[("readonly", colors["fg_color"])]
        )

        # Update Combobox Listbox dropdown popup colors
        root.option_add("*TCombobox*Listbox.background", colors["input_bg"])
        root.option_add("*TCombobox*Listbox.foreground", colors["fg_color"])
        root.option_add("*TCombobox*Listbox.selectBackground", colors["accent_blue"])
        root.option_add("*TCombobox*Listbox.selectForeground", colors["btn_text"])
        root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 9))

        # Progressbar style
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=colors["progress_bg"],
            background=colors["accent_blue"],
            thickness=14,
            bordercolor=colors["card_bg"],
            lightcolor=colors["accent_blue"],
            darkcolor=colors["accent_blue"]
        )

        # Vertical Scrollbar style
        style.configure(
            "Vertical.TScrollbar",
            troughcolor=colors["bg_color"],
            background=colors["card_sec_bg"],
            bordercolor=colors["border_color"],
            arrowcolor=colors["accent_blue"],
            lightcolor=colors["border_color"],
            darkcolor=colors["card_sec_bg"]
        )
        style.map("Vertical.TScrollbar", background=[("active", colors["accent_blue"])])

# Global singleton instance
theme_manager = ThemeManager()
