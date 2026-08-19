import sys
import time
import subprocess

if sys.platform == "win32":
    try:
        import win32gui
        import win32con
        import win32api
    except ImportError:
        win32gui = None
        win32con = None
        win32api = None
else:
    win32gui = None
    win32con = None
    win32api = None

# Virtual key codes for Arrow keys (Windows Win32)
VK_MAP = {
    "up": 0x26,      # VK_UP
    "down": 0x28,    # VK_DOWN
    "left": 0x25,    # VK_LEFT
    "right": 0x27    # VK_RIGHT
}

# Key codes for Arrow keys (macOS Quartz / osascript)
MAC_KEY_MAP = {
    "up": 126,
    "down": 125,
    "left": 123,
    "right": 124
}

def get_child_render_hwnd(parent_hwnd):
    """
    Locates active child rendering window (e.g., Chrome_RenderWidgetHostHWND)
    inside a top-level Visual Studio Code window handle.
    """
    if sys.platform != "win32" or not win32gui or not parent_hwnd:
        return parent_hwnd

    child_hwnds = []
    def enum_child_cb(child_hwnd, param):
        try:
            class_name = win32gui.GetClassName(child_hwnd)
            if "Chrome_RenderWidgetHostHWND" in class_name or "Render" in class_name:
                child_hwnds.append(child_hwnd)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumChildWindows(parent_hwnd, enum_child_cb, None)
        if child_hwnds:
            return child_hwnds[0]
    except Exception:
        pass

    return parent_hwnd

def is_vscode_window(hwnd, title):
    """
    Determines if a window handle / title belongs to a Visual Studio Code process
    using process executable inspection (win32process / QueryFullProcessImageNameW)
    and window title matching.
    """
    if sys.platform == "win32":
        try:
            import win32process
            import win32api
            import ctypes
            import os
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid:
                hProc = win32api.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
                if hProc:
                    try:
                        buf = ctypes.create_unicode_buffer(1024)
                        size = ctypes.c_uint(1024)
                        if ctypes.windll.kernel32.QueryFullProcessImageNameW(int(hProc), 0, buf, ctypes.byref(size)):
                            exe_name = os.path.basename(buf.value).lower()
                            known_exes = ("code.exe", "code - insiders.exe", "code-insiders.exe", "vscodium.exe")
                            if any(k in exe_name for k in known_exes):
                                return True
                    finally:
                        win32api.CloseHandle(hProc)
        except Exception:
            pass

    title_lower = str(title).lower()
    if "visual studio code" in title_lower or "vs code" in title_lower or title_lower.endswith(" - code"):
        return True
    return False

def find_vscode_window_by_title(target_title=None):
    """
    Searches visible top-level windows for an active Visual Studio Code window.
    If target_title is provided, attempts exact or substring match.
    Returns (hwnd, display_title) or (None, None).
    """
    windows = get_top_level_windows()
    if not windows:
        return None, None

    if target_title:
        for w in windows:
            if target_title in w["title"] or target_title in w["display"]:
                return w["hwnd"], w["display"]

    return windows[0]["hwnd"], windows[0]["display"]

def get_top_level_windows():
    """
    Enumerate visible top-level application windows and return ONLY Visual Studio Code windows.
    Returns a list of dicts: [{'hwnd': int/str, 'title': str, 'display': str}, ...]
    """
    if sys.platform == "win32":
        if not win32gui:
            return []

        windows = []
        def enum_windows_callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title and title not in ("Program Manager", "Settings", "Microsoft Text Input Application"):
                    if is_vscode_window(hwnd, title):
                        windows.append((hwnd, title))
            return True

        win32gui.EnumWindows(enum_windows_callback, None)

        title_counts = {}
        for hwnd, title in windows:
            title_counts[title] = title_counts.get(title, 0) + 1

        result = []
        title_index = {}

        for hwnd, title in windows:
            if title_counts[title] > 1:
                title_index[title] = title_index.get(title, 0) + 1
                display_name = f"{title} (Window {title_index[title]})"
            else:
                display_name = title

            result.append({
                "hwnd": hwnd,
                "title": title,
                "display": display_name
            })

        return result

    elif sys.platform == "darwin":
        windows = []
        try:
            cmd = "osascript -e 'tell application \"System Events\" to get name of every process whose visible is true'"
            out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            app_names = [name.strip() for name in out.strip().split(',') if name.strip()]
            
            vscode_apps = []
            
            for idx, app in enumerate(app_names, 1):
                if "Code" in app or "Visual Studio" in app or "VSCode" in app or "VSCodium" in app:
                    win_item = {
                        "hwnd": idx,
                        "title": f"Visual Studio Code - ({app})",
                        "display": f"Visual Studio Code - ({app})",
                        "app_name": app
                    }
                    vscode_apps.append(win_item)
                    
            return vscode_apps
        except Exception:
            return [{"hwnd": 1, "title": "Visual Studio Code", "display": "Visual Studio Code (Default)", "app_name": "Visual Studio Code"}]

    else:
        return []

def is_window_valid(hwnd):
    """Check if the specified HWND / window reference is still a valid and visible window."""
    if not hwnd:
        return False

    if sys.platform == "win32":
        if not win32gui:
            return False
        try:
            return bool(win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd))
        except Exception:
            return False

    elif sys.platform == "darwin":
        return True

    return False

def bring_window_to_front(hwnd):
    """
    Safely bring the target window to the active foreground on Windows or macOS.
    Handles iconic (minimized) windows and Windows API foreground permissions.
    """
    if not is_window_valid(hwnd):
        return False

    if sys.platform == "win32":
        if not win32gui:
            return False
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            else:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

            try:
                if win32api and win32con:
                    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                win32gui.BringWindowToTop(hwnd)
                win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            return False

    elif sys.platform == "darwin":
        try:
            cmd = "osascript -e 'tell application \"Visual Studio Code\" to activate'"
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    return False

def send_arrow_key_to_hwnd(hwnd, key_name):
    """
    Send an arrow key event (up/down/left/right) to a target window HWND / app
    on Windows or macOS using hardware-level input injection (keybd_event / SendInput)
    so low-level OS hooks (like Upwork activity tracker) and target windows process all events.
    Returns True on clean dispatch, False on failure.
    """
    if sys.platform == "win32":
        if not win32api or not win32gui or not win32con:
            return False
        if hwnd and not is_window_valid(hwnd):
            return False

        key_clean = str(key_name).lower().replace("key.", "")
        vk_code = VK_MAP.get(key_clean)
        if not vk_code:
            return False

        # Calculate OEM Scan Code
        scan_code = 0
        try:
            scan_code = win32api.MapVirtualKey(vk_code, 0)
        except Exception:
            scan_code = 0

        # Bring target window to foreground if valid and not currently foreground
        if hwnd and is_window_valid(hwnd):
            try:
                if win32gui.GetForegroundWindow() != hwnd:
                    bring_window_to_front(hwnd)
            except Exception:
                pass

        try:
            # Extended key flag (0x0001) is REQUIRED for Windows Arrow Keys
            flags_down = win32con.KEYEVENTF_EXTENDEDKEY
            flags_up   = win32con.KEYEVENTF_EXTENDEDKEY | win32con.KEYEVENTF_KEYUP

            # Send hardware-level KEYDOWN event to Windows OS Input Queue (triggers WH_KEYBOARD_LL)
            win32api.keybd_event(vk_code, scan_code, flags_down, 0)
            
            # Short inter-press delay
            time.sleep(0.015)

            # Send hardware-level KEYUP event to Windows OS Input Queue
            win32api.keybd_event(vk_code, scan_code, flags_up, 0)

            # Secondary WM_KEYDOWN/WM_KEYUP backup for specific child targets
            if hwnd:
                child_target = get_child_render_hwnd(hwnd)
                lparam_down = 1 | (scan_code << 16) | (1 << 24)
                lparam_up   = 1 | (scan_code << 16) | (1 << 24) | (1 << 30) | (1 << 31)
                try:
                    if child_target and win32gui.IsWindow(child_target):
                        win32api.PostMessage(child_target, win32con.WM_KEYDOWN, vk_code, lparam_down)
                        win32api.PostMessage(child_target, win32con.WM_KEYUP, vk_code, lparam_up)
                except Exception:
                    pass

            return True
        except Exception:
            return False

    elif sys.platform == "darwin":
        try:
            key_clean = str(key_name).lower().replace("key.", "")
            mac_code = MAC_KEY_MAP.get(key_clean, 126)
            cmd = f"osascript -e 'tell application \"System Events\" to key code {mac_code}'"
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    return False

def get_vscode_editor_bounds(hwnd):
    """
    Dynamically determine the active editor bounds (screen left, top, right, bottom)
    for a given VS Code window on Windows or macOS.
    """
    if sys.platform == "win32":
        if not win32gui or not is_window_valid(hwnd):
            return None
        try:
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            width = max(1, right - left)
            height = max(1, bottom - top)

            ed_left = left + int(width * 0.22)
            ed_top = top + int(height * 0.18)
            ed_right = right - int(width * 0.10)
            ed_bottom = bottom - int(height * 0.12)

            if ed_right > ed_left and ed_bottom > ed_top:
                return (ed_left, ed_top, ed_right, ed_bottom)
            return (left + 50, top + 50, right - 50, bottom - 50)
        except Exception:
            return None

    elif sys.platform == "darwin":
        try:
            return (200, 150, 800, 600)
        except Exception:
            return (100, 100, 500, 500)

    return None

def set_taskbar_visibility(root, hide: bool):
    """
    Hide or show the application's root window button in the Windows Taskbar
    or macOS Dock.
    """
    if sys.platform == "win32":
        if not win32gui:
            return False
        try:
            if hasattr(root, "update_idletasks"):
                root.update_idletasks()
            wid = root.winfo_id()
            if not wid:
                return False

            import ctypes
            hwnd = ctypes.windll.user32.GetAncestor(wid, 2)
            if not hwnd or not win32gui.IsWindow(hwnd):
                hwnd = win32gui.GetParent(wid) or wid

            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if hide:
                new_style = (style & ~win32con.WS_EX_APPWINDOW) | win32con.WS_EX_TOOLWINDOW
            else:
                new_style = (style & ~win32con.WS_EX_TOOLWINDOW) | win32con.WS_EX_APPWINDOW

            if new_style != style:
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_style)
                flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED | win32con.SWP_NOACTIVATE
                win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0, flags)
            return True
        except Exception:
            return False

    elif sys.platform == "darwin":
        return True

    return False

def check_macos_permissions():
    """
    Check if process has macOS Accessibility permissions required for input listeners & automation.
    Returns (is_granted: bool, user_message: str)
    """
    if sys.platform != "darwin":
        return True, ""

    try:
        import ctypes
        import ctypes.util
        app_services_path = ctypes.util.find_library("ApplicationServices")
        if app_services_path:
            app_services = ctypes.cdll.LoadLibrary(app_services_path)
            is_trusted = getattr(app_services, "AXIsProcessTrusted", None)
            if is_trusted:
                is_trusted.restype = ctypes.c_bool
                is_trusted.argtypes = []
                if not is_trusted():
                    return False, "macOS Accessibility permission is required for global ESC shortcuts and input automation. Please enable ArrowFlow under System Settings > Privacy & Security > Accessibility."
    except Exception:
        pass

    return True, ""
