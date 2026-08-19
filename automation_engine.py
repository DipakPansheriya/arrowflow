import sys
import time
import random
import threading
from pynput.keyboard import Key, Controller
from pynput.mouse import Controller as MouseController, Button
from window_helper import is_window_valid, send_arrow_key_to_hwnd, bring_window_to_front, get_vscode_editor_bounds, find_vscode_window_by_title, find_chrome_window, is_chrome_window

class ArrowAutomationController:
    """Manages per-minute randomized arrow-key press scheduling, dynamic file switching, mouse automation, and Chrome alternating mode for a target HWND."""
    
    def __init__(self, on_stats_update=None, on_stopped=None, on_target_lost=None):
        self.keyboard = Controller()
        self.mouse = MouseController()

        # Keyboard Arrow Press Range
        self.min_presses = 10
        self.max_presses = 40

        # Independent Mouse Event Range
        self.mouse_min = 5
        self.mouse_max = 20
        self.mouse_enabled = True

        self.target_hwnd = None
        
        # Dynamic File Switching options
        self.file_min = 1
        self.file_max = 5
        self.file_switching_enabled = False
        self.file_switch_count = 0

        # Google Chrome Alternating Mode options
        self.chrome_enabled = False
        self.chrome_min = 5
        self.chrome_max = 10
        self.current_mode = "VS_CODE"
        
        self.stop_event = threading.Event()
        self.is_running = False
        
        self.on_stats_update = on_stats_update
        self.on_stopped = on_stopped
        self.on_target_lost = on_target_lost
        
        self.arrow_thread = None
        
        # Live stats & Diagnostics
        self.total_presses = 0
        self.stats = {
            "keyboard_events_scheduled": 0,
            "keyboard_events_attempted": 0,
            "keyboard_events_sent": 0,
            "keyboard_events_failed": 0,
            "mouse_events_scheduled": 0,
            "mouse_events_attempted": 0,
            "mouse_events_sent": 0,
            "mouse_events_failed": 0,
            "target_hwnd_refresh_count": 0,
            "keyboard_last_success_time": None,
            "keyboard_last_failure_time": None,
            "last_error": None
        }

    def _log_diag(self, msg: str):
        """Internal diagnostic logger with precise timestamps."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}", flush=True)

    def _validate_or_recover_target_hwnd(self) -> bool:
        """
        Validates target HWND. If invalid, attempts automatic re-discovery of VS Code window.
        Returns True if target HWND is valid or recovered, False otherwise.
        """
        if not self.target_hwnd:
            return True

        if is_window_valid(self.target_hwnd):
            return True

        self._log_diag(f"[TargetHWnd] Target HWND={self.target_hwnd} invalid or closed. Attempting auto-recovery...")
        new_hwnd, display_title = find_vscode_window_by_title()
        if new_hwnd:
            self.target_hwnd = new_hwnd
            self.stats["target_hwnd_refresh_count"] += 1
            self._log_diag(f"[TargetHWnd] Recovered active VS Code window HWND={new_hwnd} ({display_title})")
            return True

        self._log_diag(f"[TargetHWnd] Target window recovery failed.")
        return False

    def start(self, min_presses: int = 10, max_presses: int = 40, target_hwnd: int = None,
              file_min: int = 1, file_max: int = 5, file_switching_enabled: bool = False,
              mouse_min: int = 5, mouse_max: int = 20, mouse_enabled: bool = True,
              chrome_enabled: bool = False, chrome_min: int = 5, chrome_max: int = 10):
        if self.is_running:
            return

        self.min_presses = min_presses
        self.max_presses = max_presses
        self.mouse_min = mouse_min
        self.mouse_max = mouse_max
        self.mouse_enabled = mouse_enabled
        self.target_hwnd = target_hwnd
        self.file_min = file_min
        self.file_max = file_max
        self.file_switching_enabled = file_switching_enabled
        self.file_switch_count = 0

        self.chrome_enabled = chrome_enabled
        self.chrome_min = chrome_min
        self.chrome_max = chrome_max
        self.current_mode = "VS_CODE"

        self.stop_event.clear()
        self.is_running = True
        self.total_presses = 0

        self._log_diag(f"[Engine] Starting automation loop. Target HWND={target_hwnd}, Chrome Enabled={chrome_enabled}")

        # Launch background worker thread
        self.arrow_thread = threading.Thread(target=self._arrow_scheduler_loop, daemon=True)
        self.arrow_thread.start()


    def stop(self):
        if not self.is_running and self.stop_event.is_set():
            return
            
        self.stop_event.set()
        self.is_running = False
        self._log_diag("[Engine] Stopping automation loop...")
        
        # Ensure worker thread terminates cleanly
        if self.arrow_thread and self.arrow_thread.is_alive() and threading.current_thread() != self.arrow_thread:
            self.arrow_thread.join(timeout=0.5)
        
        if self.on_stopped:
            self.on_stopped()

    def _send_ctrl_shift_tab(self):
        """Sends Ctrl+Shift+Tab shortcut sequence to target window or active system."""
        try:
            self.keyboard.press(Key.ctrl)
            self.keyboard.press(Key.shift)
            self.keyboard.press(Key.tab)
            time.sleep(0.02)
            self.keyboard.release(Key.tab)
            self.keyboard.release(Key.shift)
            self.keyboard.release(Key.ctrl)
        except Exception as e:
            self._log_diag(f"[TabSwitch] Exception: {e}")

    def _execute_mouse_click(self):
        """Executes a single left mouse click inside active editor bounds."""
        if not self.mouse_enabled:
            return

        if self.target_hwnd:
            bounds = get_vscode_editor_bounds(self.target_hwnd)
            if bounds:
                ed_left, ed_top, ed_right, ed_bottom = bounds
                click_x = (ed_left + ed_right) // 2
                click_y = (ed_top + ed_bottom) // 2

                # Bring target window to front ONLY if not already foreground window
                if sys.platform == "win32":
                    try:
                        import win32gui
                        if win32gui.GetForegroundWindow() != self.target_hwnd:
                            bring_window_to_front(self.target_hwnd)
                    except Exception:
                        pass
                else:
                    bring_window_to_front(self.target_hwnd)

                # Check current mouse cursor position; ONLY set position if cursor is outside bounds
                try:
                    if sys.platform == "win32":
                        import ctypes
                        class POINT(ctypes.Structure):
                            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
                        pt = POINT()
                        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                        cur_x, cur_y = pt.x, pt.y
                    else:
                        cur_x, cur_y = self.mouse.position
                except Exception:
                    cur_x, cur_y = -1, -1

                if not (ed_left <= cur_x <= ed_right and ed_top <= cur_y <= ed_bottom):
                    self.mouse.position = (click_x, click_y)
                    time.sleep(0.02)

                if not self.stop_event.is_set():
                    self.mouse.click(Button.left, 1)
        else:
            if not self.stop_event.is_set():
                self.mouse.click(Button.left, 1)

    def _generate_decoupled_schedules(self, arrow_target, mouse_target, window_sec=60.0, min_sep=0.10):
        """
        Generate two independent randomized offset lists (Keyboard and Mouse)
        with arrow_target and mouse_target offsets across [0.10, window_sec - 0.20]
        ensuring no Keyboard timestamp and Mouse timestamp are closer than min_sep seconds.
        Dynamically adjusts min_sep if event density is high (e.g. 50-110+ events).
        """
        total_events = arrow_target + mouse_target
        eff_min_sep = min(min_sep, max(0.02, (window_sec - 2.0) / max(1, total_events * 2)))

        for attempt in range(200):
            kbd_offsets = sorted([round(random.uniform(0.10, window_sec - 0.20), 3) for _ in range(arrow_target)])
            mouse_offsets = sorted([round(random.uniform(0.10, window_sec - 0.20), 3) for _ in range(mouse_target)])

            valid = True
            adjusted_mouse = []
            for m in mouse_offsets:
                m_val = m
                conflict = True
                shifts = 0
                while conflict and shifts < 10:
                    conflict = False
                    for k in kbd_offsets:
                        if abs(m_val - k) < eff_min_sep:
                            m_val += eff_min_sep + 0.01
                            conflict = True
                            shifts += 1
                            break
                if m_val >= window_sec - 0.10:
                    valid = False
                    break
                adjusted_mouse.append(round(m_val, 3))

            if valid:
                return kbd_offsets, sorted(adjusted_mouse)

        # Fallback deterministic schedule if random placement fails
        step_kbd = (window_sec - 0.5) / max(1, arrow_target)
        step_mouse = (window_sec - 0.5) / max(1, mouse_target)
        kbd_offsets = [round(0.10 + i * step_kbd, 3) for i in range(arrow_target)]
        mouse_offsets = [round(0.15 + i * step_mouse, 3) for i in range(mouse_target)]
        return kbd_offsets, mouse_offsets

    def _send_chrome_tab_switch(self, forward: bool = True):
        """Sends Ctrl+Tab (forward) or Ctrl+Shift+Tab (backward) to switch open Chrome tabs using keyboard shortcuts."""
        try:
            self.keyboard.press(Key.ctrl)
            if not forward:
                self.keyboard.press(Key.shift)
            self.keyboard.press(Key.tab)
            time.sleep(0.03)
            self.keyboard.release(Key.tab)
            if not forward:
                self.keyboard.release(Key.shift)
            self.keyboard.release(Key.ctrl)
            self._log_diag(f"[ChromeTabSwitch] Sent {'Ctrl+Tab' if forward else 'Ctrl+Shift+Tab'}")
        except Exception as e:
            self._log_diag(f"[ChromeTabSwitch] Exception: {e}")

    def _run_chrome_cycle(self, duration_sec: float):
        """
        Executes Google Chrome automation for duration_sec seconds.
        Finds open Chrome window, brings it to front, performs arrow/scroll actions,
        and periodically switches between open Chrome tabs using Ctrl+Tab / Ctrl+Shift+Tab.
        """
        self._log_diag(f"[ChromeCycle] Starting Chrome cycle for {duration_sec / 60:.2f} minutes ({duration_sec:.0f} seconds)")
        
        chrome_hwnd, chrome_title = find_chrome_window()
        if not chrome_hwnd:
            self._log_diag("[ChromeCycle] Google Chrome window not found. Reporting status and safely returning.")
            if self.on_stats_update:
                self.on_stats_update(
                    arrow_done=0, arrow_target=0, mouse_done=0, mouse_target=0,
                    total_presses=self.total_presses, file_switch_count=0,
                    file_switching_enabled=self.file_switching_enabled,
                    current_mode="Google Chrome (Not Open - Skipping)",
                    remaining_sec=0
                )
            self.stop_event.wait(timeout=3.0)
            return

        # Bring Chrome window to front
        bring_window_to_front(chrome_hwnd)
        time.sleep(0.2)

        start_time = time.monotonic()
        end_time = start_time + duration_sec
        chrome_arrow_keys = ["up", "down", "left", "right", "page_up", "page_down"]
        pynput_chrome_keys = [Key.up, Key.down, Key.left, Key.right, Key.page_up, Key.page_down]

        tab_action_count = 0
        actions_until_tab_switch = random.randint(3, 6)

        while time.monotonic() < end_time and not self.stop_event.is_set():
            remaining_sec = max(0.0, end_time - time.monotonic())
            
            # Send status update
            if self.on_stats_update:
                self.on_stats_update(
                    arrow_done=0, arrow_target=0, mouse_done=0, mouse_target=0,
                    total_presses=self.total_presses, file_switch_count=0,
                    file_switching_enabled=self.file_switching_enabled,
                    current_mode="Google Chrome",
                    remaining_sec=int(remaining_sec)
                )

            # Re-verify Chrome window focus
            if chrome_hwnd and is_window_valid(chrome_hwnd):
                if sys.platform == "win32":
                    try:
                        import win32gui
                        if win32gui.GetForegroundWindow() != chrome_hwnd:
                            bring_window_to_front(chrome_hwnd)
                    except Exception:
                        pass

            # Pick a random key / scroll action
            chosen_key = random.choice(chrome_arrow_keys)
            try:
                if chrome_hwnd and sys.platform == "win32" and chosen_key in ["up", "down", "left", "right"]:
                    send_arrow_key_to_hwnd(chrome_hwnd, chosen_key)
                else:
                    idx = chrome_arrow_keys.index(chosen_key)
                    pkey = pynput_chrome_keys[idx]
                    self.keyboard.press(pkey)
                    time.sleep(0.02)
                    self.keyboard.release(pkey)
                self.total_presses += 1
                tab_action_count += 1
            except Exception as e_c:
                self._log_diag(f"[ChromeCycle] Exception sending key: {e_c}")

            # Check if it's time to switch open Chrome tab using Ctrl+Tab or Ctrl+Shift+Tab
            if tab_action_count >= actions_until_tab_switch:
                if chrome_hwnd and is_window_valid(chrome_hwnd):
                    bring_window_to_front(chrome_hwnd)
                    time.sleep(0.1)
                
                # Switch tab (randomly forward Ctrl+Tab or backward Ctrl+Shift+Tab)
                forward = random.choice([True, True, True, False])  # Mostly forward tab cycling
                self._send_chrome_tab_switch(forward=forward)
                
                tab_action_count = 0
                actions_until_tab_switch = random.randint(3, 6)
                time.sleep(0.3)

            # Sleep a random interval between 1.2 and 3.5 seconds between scroll actions
            wait_time = random.uniform(1.2, 3.5)
            if self.stop_event.wait(timeout=wait_time):
                break


    def _arrow_scheduler_loop(self):
        """Loop that generates decoupled random schedules for arrow keys, mouse automation, and Chrome alternating mode."""
        arrow_keys = ["up", "down", "left", "right"]
        pynput_keys = [Key.up, Key.down, Key.left, Key.right]

        self.current_mode = "VS_CODE"
        vs_code_cycle_end = 0.0

        if self.chrome_enabled:
            dur_min = random.randint(self.chrome_min, self.chrome_max)
            dur_sec = dur_min * 60.0
            vs_code_cycle_end = time.monotonic() + dur_sec
            self._log_diag(f"[Scheduler] Chrome Alternating Mode ON. Starting VS Code cycle for {dur_min} minutes ({dur_sec:.0f}s)")

        while not self.stop_event.is_set():
            # Check if Chrome mode is enabled and if VS Code cycle time has elapsed
            if self.chrome_enabled and time.monotonic() >= vs_code_cycle_end:
                self._log_diag("[Scheduler] VS Code cycle completed. Switching to CHROME mode...")
                self.current_mode = "CHROME"
                
                # Generate a NEW random duration for Chrome cycle
                chrome_dur_min = random.randint(self.chrome_min, self.chrome_max)
                chrome_dur_sec = chrome_dur_min * 60.0
                self._log_diag(f"[Scheduler] Generated fresh Chrome cycle duration: {chrome_dur_min} minutes ({chrome_dur_sec:.0f}s)")
                
                # Run Chrome cycle
                self._run_chrome_cycle(chrome_dur_sec)

                if self.stop_event.is_set():
                    break

                # After Chrome cycle finishes, switch back to VS Code
                self._log_diag("[Scheduler] Chrome cycle completed. Switching to VS CODE mode...")
                self.current_mode = "VS_CODE"
                
                # Generate a NEW random duration for next VS Code cycle
                vs_dur_min = random.randint(self.chrome_min, self.chrome_max)
                vs_dur_sec = vs_dur_min * 60.0
                vs_code_cycle_end = time.monotonic() + vs_dur_sec
                self._log_diag(f"[Scheduler] Generated fresh VS Code cycle duration: {vs_dur_min} minutes ({vs_dur_sec:.0f}s)")
                
                # Re-focus VS Code window
                if self.target_hwnd and is_window_valid(self.target_hwnd):
                    bring_window_to_front(self.target_hwnd)
                    time.sleep(0.2)

            window_start = time.monotonic()

            # Validate or auto-recover target HWND before starting minute
            if self.target_hwnd and not self._validate_or_recover_target_hwnd():
                self._log_diag("[TargetHWnd] Target HWND check failed before minute start. Attempting auto-recovery...")
                if not self._validate_or_recover_target_hwnd():
                    self.stop_event.set()
                    self.is_running = False
                    if self.on_target_lost:
                        self.on_target_lost()
                    break

            # Generate independent per-minute targets respecting configured min-max range
            arrow_target = random.randint(self.min_presses, self.max_presses)
            mouse_target = random.randint(self.mouse_min, self.mouse_max) if self.mouse_enabled else 0

            self.stats["keyboard_events_scheduled"] += arrow_target
            self.stats["mouse_events_scheduled"] += mouse_target
            self._log_diag(f"[Scheduler] New minute targets: Keyboard={arrow_target} (range {self.min_presses}-{self.max_presses}), Mouse={mouse_target} (range {self.mouse_min}-{self.mouse_max})")

            # Generate file-switch count for this minute if file switching is enabled
            if self.file_switching_enabled:
                self.file_switch_count = random.randint(self.file_min, self.file_max)
            else:
                self.file_switch_count = 0

            # Immediately update GUI with new minute's targets & status
            if self.on_stats_update:
                rem_sec = int(max(0.0, vs_code_cycle_end - time.monotonic())) if self.chrome_enabled else 0
                self.on_stats_update(
                    arrow_done=0,
                    arrow_target=arrow_target,
                    mouse_done=0,
                    mouse_target=mouse_target,
                    total_presses=self.total_presses,
                    file_switch_count=self.file_switch_count,
                    file_switching_enabled=self.file_switching_enabled,
                    current_mode="VS Code" if not self.chrome_enabled else "VS Code (Alternating)",
                    remaining_sec=rem_sec
                )

            # Generate TWO independent randomized offset lists with collision separation
            kbd_offsets, mouse_offsets = self._generate_decoupled_schedules(arrow_target, mouse_target, window_sec=60.0, min_sep=0.10)

            # Build merged chronological event queue
            events = []
            for offset in kbd_offsets:
                events.append({
                    "type": "keyboard",
                    "offset": offset,
                    "key": random.choice(arrow_keys),
                    "pynput_key": random.choice(pynput_keys)
                })
            for offset in mouse_offsets:
                events.append({
                    "type": "mouse",
                    "offset": offset
                })

            # Sort events chronologically by offset
            events.sort(key=lambda x: x["offset"])

            kbd_done = 0
            mouse_done = 0

            for event in events:
                if self.stop_event.is_set():
                    break

                target_time = window_start + event["offset"]
                wait_duration = target_time - time.monotonic()

                if wait_duration > 0:
                    if self.stop_event.wait(timeout=wait_duration):
                        break

                if self.stop_event.is_set():
                    break

                if event["type"] == "keyboard":
                    self.stats["keyboard_events_attempted"] += 1
                    try:
                        if self.target_hwnd:
                            success = send_arrow_key_to_hwnd(self.target_hwnd, event["key"])
                            if success:
                                self.stats["keyboard_events_sent"] += 1
                                self.stats["keyboard_last_success_time"] = time.monotonic()
                            else:
                                self.stats["keyboard_events_failed"] += 1
                                self.stats["keyboard_last_failure_time"] = time.monotonic()
                                self._log_diag(f"[Keyboard] Failed sending key '{event['key']}' to HWND={self.target_hwnd}")
                        else:
                            self.keyboard.press(event["pynput_key"])
                            time.sleep(0.02)
                            self.keyboard.release(event["pynput_key"])
                            self.stats["keyboard_events_sent"] += 1
                            self.stats["keyboard_last_success_time"] = time.monotonic()
                    except Exception as e_k:
                        self.stats["keyboard_events_failed"] += 1
                        self.stats["keyboard_last_failure_time"] = time.monotonic()
                        self._log_diag(f"[Keyboard] Exception sending key '{event['key']}': {e_k}")

                    kbd_done += 1

                elif event["type"] == "mouse":
                    self.stats["mouse_events_attempted"] += 1
                    try:
                        self._execute_mouse_click()
                        self.stats["mouse_events_sent"] += 1
                    except Exception as e_m:
                        self.stats["mouse_events_failed"] += 1
                        self._log_diag(f"[Mouse] Click failed: {e_m}")
                    mouse_done += 1

                # Update progress tracking
                self.total_presses += 1

                if self.on_stats_update:
                    rem_sec = int(max(0.0, vs_code_cycle_end - time.monotonic())) if self.chrome_enabled else 0
                    self.on_stats_update(
                        arrow_done=kbd_done,
                        arrow_target=arrow_target,
                        mouse_done=mouse_done,
                        mouse_target=mouse_target,
                        total_presses=self.total_presses,
                        file_switch_count=self.file_switch_count,
                        file_switching_enabled=self.file_switching_enabled,
                        current_mode="VS Code" if not self.chrome_enabled else "VS Code (Alternating)",
                        remaining_sec=rem_sec
                    )

            # Wait out remainder of 60-second window before starting next minute
            window_end = window_start + 60.0
            remaining = window_end - time.monotonic()
            if remaining > 0 and not self.stop_event.is_set():
                self.stop_event.wait(timeout=remaining)

            # Minute transition: execute Ctrl+Shift+Tab file switching if enabled
            if self.file_switching_enabled and not self.stop_event.is_set() and self.file_switch_count > 0:
                if self.target_hwnd:
                    if not self._validate_or_recover_target_hwnd():
                        self.stop_event.set()
                        self.is_running = False
                        if self.on_target_lost:
                            self.on_target_lost()
                        break
                    bring_window_to_front(self.target_hwnd)
                    time.sleep(0.15)

                for _ in range(self.file_switch_count):
                    if self.stop_event.is_set():
                        break
                    self._send_ctrl_shift_tab()
                    time.sleep(0.1)

