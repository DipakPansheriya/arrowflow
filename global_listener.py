from pynput import keyboard

class GlobalHotkeyListener:
    """
    Global keyboard listener using pynput to intercept:
    - ESC key -> Trigger automation Start/Stop toggle callback
    - ALT + SPACE -> Trigger application window visibility toggle callback
    """
    def __init__(self, on_esc_pressed=None, on_alt_space_pressed=None):
        self.on_esc_pressed = on_esc_pressed
        self.on_alt_space_pressed = on_alt_space_pressed
        self.listener = None
        self.pressed_keys = set()

    def start(self):
        if self.listener is not None and self.listener.running:
            return
        
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.daemon = True
        self.listener.start()

    def stop(self):
        if self.listener is not None:
            self.listener.stop()
            self.listener = None

    def _on_press(self, key):
        self.pressed_keys.add(key)

        # 1. ESC Key check
        if key == keyboard.Key.esc:
            if self.on_esc_pressed:
                self.on_esc_pressed()
            return

        # 2. ALT + SPACE Key check
        has_alt = any(
            k in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr)
            for k in self.pressed_keys
        )
        if key == keyboard.Key.space and has_alt:
            if self.on_alt_space_pressed:
                self.on_alt_space_pressed()

    def _on_release(self, key):
        self.pressed_keys.discard(key)

class GlobalEscListener(GlobalHotkeyListener):
    def __init__(self, on_esc_pressed=None, on_alt_space_pressed=None):
        super().__init__(on_esc_pressed=on_esc_pressed, on_alt_space_pressed=on_alt_space_pressed)
