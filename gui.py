import os
import sys
import hashlib
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from automation_engine import ArrowAutomationController
from global_listener import GlobalEscListener
from window_helper import get_top_level_windows, is_window_valid, bring_window_to_front, set_taskbar_visibility, check_macos_permissions
from version import CURRENT_VERSION
from update_checker import check_for_updates_async, download_file_with_progress, calculate_sha256
from updater import launch_updater_and_exit
from auth.auth_service import AuthService
from auth.totp_manager import TOTPManager
from PIL import Image, ImageTk

# Compact Spacing Design System Constants for 540x660 Layout
OUTER_PAD = 18            # Left & Right outer window padding
OUTER_TOP = 16            # Top outer window padding
OUTER_BOTTOM = 14         # Bottom outer window padding
CARD_GAP = 10             # Vertical gap between major card sections
CARD_PAD_X = 16           # Inner horizontal padding inside cards
CARD_PAD_Y = 12           # Inner vertical padding inside cards
CONTROL_GAP = 6           # Vertical gap between controls within a card

class ArrowAutomationGUI:
    PASSWORD_HASH = "16d7b5441cd65b3092ed27778f745f923689228012408b8af981f44de1958dec"

    def __init__(self, root):
        self.root = root
        self.root.title("ArrowFlow")
        
        # Load window icon if available
        ico_path = os.path.join(os.path.dirname(__file__), "arrowflow.ico")
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass

        # Color Palette - Electric Cyan / Neon Blue ArrowFlow Theme (Matching App Icon Logo)
        self.bg_color = "#090C15"            # Deep midnight space background
        self.card_bg = "#121625"             # Dark navy charcoal card container
        self.card_sec_bg = "#192035"         # Metallic navy panel section
        self.input_bg = "#0E121E"            # Dark sunken input field background
        self.border_color = "#242E48"        # Subdued cyan-tinted border
        self.accent_blue = "#00D2FF"         # Electric Cyan / Neon Blue (ArrowFlow Logo Accent)
        self.accent_blue_hover = "#33DDFF"   # Bright cyan hover
        self.accent_green = "#00E5A3"        # Vibrant Electric Teal-Green (Action / Success)
        self.accent_red = "#FF4D6D"          # Neon Red Glow (Stop / Danger)
        self.fg_color = "#F0F4FF"            # Primary text (Crisp cool white)
        self.sec_fg = "#8E9BB5"              # Secondary text
        self.muted_fg = "#5C6B8A"            # Muted helper text
        self.progress_bg = "#1C253B"        # Progress bar trough
        self.disabled_bg = "#192035"         # Disabled control background
        self.disabled_fg = "#424E68"         # Disabled text
        
        self.root.configure(bg=self.bg_color)
        self._center_window(420, 480)
        self.root.resizable(True, True)
        self.root.minsize(500, 680)
        
        # Configure TTK Styles
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Root & Component Styles
        self.style.configure(".", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 9))
        
        # Custom TTK Combobox Styling with constrained dropdown height
        self.style.configure(
            "TCombobox",
            fieldbackground=self.input_bg,
            background=self.card_sec_bg,
            foreground=self.fg_color,
            arrowcolor=self.accent_blue,
            bordercolor=self.border_color,
            lightcolor=self.border_color,
            darkcolor=self.border_color,
            padding=5
        )
        self.style.map("TCombobox", fieldbackground=[("readonly", self.input_bg)], foreground=[("readonly", self.fg_color)])
        
        # Fix Combobox dropdown popup window colors & max scrollbar height (6 items max)
        self.root.option_add("*TCombobox*Listbox.background", self.input_bg)
        self.root.option_add("*TCombobox*Listbox.foreground", self.fg_color)
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.accent_blue)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#090C15")
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 9))
        
        # Custom Progressbar Style - Electric Cyan Glow
        self.style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=self.progress_bg,
            background=self.accent_blue,
            thickness=14,
            bordercolor=self.card_bg,
            lightcolor=self.accent_blue,
            darkcolor=self.accent_blue
        )
        
        # Windows Map: {display_title: hwnd}
        self.windows_map = {}
        
        # Automation Controller & ESC Listener Init
        self.controller = ArrowAutomationController(
            on_stats_update=self._on_stats_update,
            on_stopped=self._on_stopped_callback,
            on_target_lost=self._on_target_lost_callback
        )
        
        self.esc_listener = GlobalEscListener(
            on_esc_pressed=self._on_global_esc,
            on_alt_space_pressed=self._on_global_alt_space
        )
        self.esc_listener.start()

        # Intercept ALT+SPACE system key in Tkinter to suppress Windows system menu
        self.root.bind_all("<Alt-space>", self._on_tkinter_alt_space)
        self.root.bind_all("<Alt-Key-space>", self._on_tkinter_alt_space)
        
        self.is_authenticated = False
        self.file_switch_enabled = False
        self.chrome_enabled = False
        self.is_window_hidden = False
        self.last_esc_time = 0.0
        self.last_alt_space_time = 0.0
        
        # 2FA Authentication Service & Image References
        self.auth_service = AuthService()
        self.auth_frame = None
        self.qr_img_ref = None
        
        # Build Password Lock Screen initially
        self._build_login_ui()

    def _center_window(self, width, height):
        """Center the root window on the screen cleanly."""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _clean_auth_frames(self):
        """Destroy any active authentication frames."""
        if hasattr(self, "login_frame") and self.login_frame:
            try:
                self.login_frame.destroy()
            except Exception:
                pass
            self.login_frame = None
        if self.auth_frame:
            try:
                self.auth_frame.destroy()
            except Exception:
                pass
            self.auth_frame = None

    def _build_login_ui(self):
        """Build professional password lock screen interface (420x500)."""
        self._clean_auth_frames()
        self._center_window(420, 500)
        self.login_frame = tk.Frame(self.root, bg=self.bg_color)
        self.login_frame.pack(fill="both", expand=True)
        
        card_outer = tk.Frame(self.login_frame, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        card_outer.pack(anchor="center", expand=True, padx=28, pady=28, fill="both")
        
        # Lock Icon & Title
        lbl_icon = tk.Label(card_outer, text="⚡", font=("Segoe UI", 28), bg=self.card_bg, fg=self.accent_blue)
        lbl_icon.pack(pady=(18, 2))
        
        lbl_title = tk.Label(card_outer, text="ArrowFlow", font=("Segoe UI", 16, "bold"), bg=self.card_bg, fg=self.fg_color)
        lbl_title.pack()
        
        lbl_sub = tk.Label(card_outer, text=f"v{CURRENT_VERSION} · Secure Access Required", font=("Segoe UI", 9), bg=self.card_bg, fg=self.sec_fg)
        lbl_sub.pack(pady=(2, 14))
        
        # Input Section
        lbl_pwd_tag = tk.Label(card_outer, text="ADMIN PASSWORD", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.sec_fg)
        lbl_pwd_tag.pack(anchor="w", padx=30, pady=(0, 4))
        
        self.ent_pwd = tk.Entry(
            card_outer, 
            width=22, 
            font=("Segoe UI", 12), 
            bg=self.input_bg, 
            fg=self.fg_color, 
            insertbackground=self.accent_blue,
            show="•",
            bd=1,
            relief="solid",
            highlightbackground=self.border_color,
            justify="center"
        )
        self.ent_pwd.pack(padx=30, pady=(0, 8), ipady=5)
        self.ent_pwd.focus()
        self.ent_pwd.bind("<Return>", lambda event: self._attempt_unlock())
        
        self.lbl_login_err = tk.Label(
            card_outer, 
            text="", 
            font=("Segoe UI", 9, "bold"), 
            bg=self.card_bg, 
            fg=self.accent_red
        )
        self.lbl_login_err.pack(pady=(0, 4))
        
        self.btn_unlock = tk.Button(
            card_outer,
            text="CONTINUE",
            font=("Segoe UI", 11, "bold"),
            bg=self.accent_green,
            fg="#090C15",
            activebackground=self.accent_blue_hover,
            activeforeground="#090C15",
            bd=0,
            cursor="hand2",
            height=2,
            relief="flat",
            command=self._attempt_unlock
        )
        self.btn_unlock.pack(fill="x", padx=30, pady=(0, 10))
        
        lbl_hint = tk.Label(card_outer, text="Press ENTER to continue", font=("Segoe UI", 9), bg=self.card_bg, fg=self.muted_fg)
        lbl_hint.pack(pady=(0, 14))

    def _attempt_unlock(self):
        """Validate entered password and query Firebase for 2FA state."""
        entered = self.ent_pwd.get()
        if not entered:
            self.lbl_login_err.config(text="Please enter password", fg=self.accent_red)
            return

        if not self.auth_service.verify_password(entered):
            self.ent_pwd.delete(0, tk.END)
            self.lbl_login_err.config(text="Incorrect password", fg=self.accent_red)
            self.ent_pwd.focus()
            return

        # Password is valid -> Query Firebase for authenticator secret status
        self.lbl_login_err.config(text="● Checking Firebase 2FA security...", fg=self.accent_blue)
        self.btn_unlock.config(state="disabled", text="CONNECTING...")
        self.root.update_idletasks()

        def _fetch_2fa_state():
            try:
                state = self.auth_service.initialize_authenticator_state()
                self.root.after(0, lambda: self._on_2fa_state_ready(state))
            except Exception as e:
                self.root.after(0, lambda: self._on_2fa_state_error(str(e)))

        threading.Thread(target=_fetch_2fa_state, daemon=True).start()

    def _on_2fa_state_ready(self, state):
        """Handle 2FA state transition from Firebase."""
        self._clean_auth_frames()
        if state.get("is_new"):
            # First-time registration -> Display Authenticator Setup Screen
            self._build_setup_2fa_ui(state["secret_key"])
        else:
            # Existing secret -> Display OTP Verification Screen
            self._build_verify_2fa_ui()

    def _on_2fa_state_error(self, err_msg):
        """Handle network or Firebase connectivity errors."""
        self.btn_unlock.config(state="normal", text="CONTINUE")
        self.lbl_login_err.config(text="Firebase connection error. Check internet.", fg=self.accent_red)

    def _build_setup_2fa_ui(self, secret_key: str):
        """Build initial Authenticator Setup UI with QR Code and Secret Key (480x640)."""
        self._clean_auth_frames()
        self._center_window(480, 640)
        self.auth_frame = tk.Frame(self.root, bg=self.bg_color)
        self.auth_frame.pack(fill="both", expand=True)

        card_outer = tk.Frame(self.auth_frame, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        card_outer.pack(anchor="center", expand=True, padx=20, pady=16, fill="both")

        # Header
        lbl_title = tk.Label(card_outer, text="⚡ Set Up Authenticator 2FA", font=("Segoe UI", 14, "bold"), bg=self.card_bg, fg=self.fg_color)
        lbl_title.pack(pady=(12, 2))

        lbl_sub = tk.Label(card_outer, text="Scan with Google Authenticator or Microsoft Authenticator", font=("Segoe UI", 8), bg=self.card_bg, fg=self.sec_fg)
        lbl_sub.pack(pady=(0, 8))

        # QR Code Display Container
        qr_border_frame = tk.Frame(card_outer, bg="#FFFFFF", padx=6, pady=6, bd=1, relief="solid")
        qr_border_frame.pack(anchor="center", pady=(0, 8))

        try:
            self.qr_img_ref = TOTPManager.generate_tk_qr_image(secret_key, target_size=(140, 140))
            lbl_qr = tk.Label(qr_border_frame, image=self.qr_img_ref, bg="#FFFFFF")
            lbl_qr.pack()
        except Exception:
            lbl_qr = tk.Label(qr_border_frame, text="QR Preview", font=("Segoe UI", 10), bg="#FFFFFF", fg="#090C15", width=16, height=7)
            lbl_qr.pack()

        # Secret Key (Manual Entry)
        key_box = tk.Frame(card_outer, bg=self.card_sec_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        key_box.pack(fill="x", padx=24, pady=(0, 10))

        key_inner = tk.Frame(key_box, bg=self.card_sec_bg)
        key_inner.pack(fill="x", padx=10, pady=6)

        formatted_secret = TOTPManager.format_secret_display(secret_key)
        lbl_key_val = tk.Label(key_inner, text=formatted_secret, font=("Consolas", 11, "bold"), bg=self.card_sec_bg, fg=self.accent_blue)
        lbl_key_val.pack(side="left")

        def _copy_key():
            self.root.clipboard_clear()
            self.root.clipboard_append(secret_key)
            btn_copy.config(text="✓ Copied!", bg=self.accent_green, fg="#090C15")
            self.root.after(2000, lambda: btn_copy.config(text="📋 Copy", bg=self.card_bg, fg=self.accent_blue))

        btn_copy = tk.Button(
            key_inner,
            text="📋 Copy",
            font=("Segoe UI", 8, "bold"),
            bg=self.card_bg,
            fg=self.accent_blue,
            activebackground=self.accent_blue,
            activeforeground="#090C15",
            bd=0,
            cursor="hand2",
            padx=8,
            pady=2,
            relief="flat",
            command=_copy_key
        )
        btn_copy.pack(side="right")

        # 6-Digit Verification Section
        lbl_code_tag = tk.Label(card_outer, text="ENTER 6-DIGIT CODE FROM APP", font=("Segoe UI", 8, "bold"), bg=self.card_bg, fg=self.sec_fg)
        lbl_code_tag.pack(anchor="w", padx=24, pady=(0, 3))

        self.ent_setup_otp = tk.Entry(
            card_outer,
            width=14,
            font=("Segoe UI", 16, "bold"),
            bg=self.input_bg,
            fg=self.fg_color,
            insertbackground=self.accent_blue,
            bd=1,
            relief="solid",
            highlightbackground=self.border_color,
            justify="center"
        )
        self.ent_setup_otp.pack(padx=24, pady=(0, 4), ipady=3)
        self.ent_setup_otp.focus()
        self.ent_setup_otp.bind("<Return>", lambda event: self._attempt_setup_verify())

        self.lbl_setup_err = tk.Label(
            card_outer,
            text="",
            font=("Segoe UI", 8, "bold"),
            bg=self.card_bg,
            fg=self.accent_red
        )
        self.lbl_setup_err.pack(pady=(0, 4))

        btn_confirm = tk.Button(
            card_outer,
            text="VERIFY & COMPLETE SETUP",
            font=("Segoe UI", 10, "bold"),
            bg=self.accent_green,
            fg="#090C15",
            activebackground=self.accent_blue_hover,
            activeforeground="#090C15",
            bd=0,
            cursor="hand2",
            height=2,
            relief="flat",
            command=self._attempt_setup_verify
        )
        btn_confirm.pack(fill="x", padx=24, pady=(0, 6))

        lbl_secure_note = tk.Label(
            card_outer,
            text="🔒 Key is stored in Firebase for seamless recovery.",
            font=("Segoe UI", 8),
            bg=self.card_bg,
            fg=self.muted_fg
        )
        lbl_secure_note.pack(pady=(0, 8))

    def _attempt_setup_verify(self):
        """Validate 6-digit confirmation OTP on initial setup."""
        entered = self.ent_setup_otp.get()
        if not entered:
            self.lbl_setup_err.config(text="Please enter 6-digit code")
            return

        if self.auth_service.verify_otp_code(entered):
            self.lbl_setup_err.config(text="✓ Authenticator verified!", fg=self.accent_green)
            self.root.after(400, self._unlock_and_launch_main_app)
        else:
            self.ent_setup_otp.delete(0, tk.END)
            self.lbl_setup_err.config(text="Invalid OTP code. Check your authenticator app.", fg=self.accent_red)
            self.ent_setup_otp.focus()

    def _build_verify_2fa_ui(self):
        """Build regular OTP verification UI for subsequent logins (440x510)."""
        self._clean_auth_frames()
        self._center_window(440, 510)
        self.auth_frame = tk.Frame(self.root, bg=self.bg_color)
        self.auth_frame.pack(fill="both", expand=True)

        card_outer = tk.Frame(self.auth_frame, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        card_outer.pack(anchor="center", expand=True, padx=26, pady=24, fill="both")

        # Shield Icon & Title
        lbl_icon = tk.Label(card_outer, text="🛡️", font=("Segoe UI", 26), bg=self.card_bg, fg=self.accent_blue)
        lbl_icon.pack(pady=(16, 2))

        lbl_title = tk.Label(card_outer, text="Two-Factor Authentication", font=("Segoe UI", 15, "bold"), bg=self.card_bg, fg=self.fg_color)
        lbl_title.pack()

        lbl_sub = tk.Label(card_outer, text="Enter the 6-digit code from your Authenticator app", font=("Segoe UI", 9), bg=self.card_bg, fg=self.sec_fg)
        lbl_sub.pack(pady=(2, 16))

        # OTP Entry
        lbl_otp_tag = tk.Label(card_outer, text="6-DIGIT AUTHENTICATOR CODE", font=("Segoe UI", 8, "bold"), bg=self.card_bg, fg=self.sec_fg)
        lbl_otp_tag.pack(anchor="w", padx=28, pady=(0, 4))

        self.ent_otp = tk.Entry(
            card_outer,
            width=12,
            font=("Segoe UI", 18, "bold"),
            bg=self.input_bg,
            fg=self.fg_color,
            insertbackground=self.accent_blue,
            bd=1,
            relief="solid",
            highlightbackground=self.border_color,
            justify="center"
        )
        self.ent_otp.pack(padx=28, pady=(0, 6), ipady=5)
        self.ent_otp.focus()
        self.ent_otp.bind("<Return>", lambda event: self._attempt_otp_verify())

        self.lbl_otp_err = tk.Label(
            card_outer,
            text="",
            font=("Segoe UI", 8, "bold"),
            bg=self.card_bg,
            fg=self.accent_red
        )
        self.lbl_otp_err.pack(pady=(0, 6))

        btn_verify = tk.Button(
            card_outer,
            text="VERIFY & UNLOCK",
            font=("Segoe UI", 11, "bold"),
            bg=self.accent_green,
            fg="#090C15",
            activebackground=self.accent_blue_hover,
            activeforeground="#090C15",
            bd=0,
            cursor="hand2",
            height=2,
            relief="flat",
            command=self._attempt_otp_verify
        )
        btn_verify.pack(fill="x", padx=28, pady=(0, 10))

        # Recovery & Help Link
        btn_recover = tk.Button(
            card_outer,
            text="Lost Phone or Need Setup Key? Restore 2FA Setup",
            font=("Segoe UI", 8, "underline"),
            bg=self.card_bg,
            fg=self.accent_blue,
            activebackground=self.card_bg,
            activeforeground=self.accent_blue_hover,
            bd=0,
            cursor="hand2",
            relief="flat",
            command=self._show_recovery_modal
        )
        btn_recover.pack(pady=(0, 10))

    def _attempt_otp_verify(self):
        """Validate 6-digit OTP code against the Firebase-synced secret key."""
        entered = self.ent_otp.get()
        if not entered:
            self.lbl_otp_err.config(text="Please enter 6-digit code", fg=self.accent_red)
            return

        if self.auth_service.verify_otp_code(entered):
            self.lbl_otp_err.config(text="✓ Access Granted!", fg=self.accent_green)
            self.root.after(300, self._unlock_and_launch_main_app)
        else:
            self.ent_otp.delete(0, tk.END)
            self.lbl_otp_err.config(text="Invalid OTP code. Please try again.", fg=self.accent_red)
            self.ent_otp.focus()

    def _show_recovery_modal(self):
        """Open Authenticator Recovery Dialog to view existing Firebase secret key & QR code."""
        rec_win = tk.Toplevel(self.root)
        rec_win.title("Authenticator Recovery - ArrowFlow")
        rec_win.configure(bg=self.bg_color)
        rec_win.geometry("460x560")
        rec_win.resizable(False, False)
        rec_win.transient(self.root)
        rec_win.grab_set()

        # Center relative to root
        rx = self.root.winfo_x() + (self.root.winfo_width() - 460) // 2
        ry = self.root.winfo_y() + (self.root.winfo_height() - 560) // 2
        rec_win.geometry(f"460x560+{max(0, rx)}+{max(0, ry)}")

        card = tk.Frame(rec_win, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        lbl_rtitle = tk.Label(card, text="🔑 2FA Authenticator Recovery", font=("Segoe UI", 13, "bold"), bg=self.card_bg, fg=self.fg_color)
        lbl_rtitle.pack(pady=(12, 2))

        lbl_rsub = tk.Label(card, text="Recover or add your existing secret to a new phone", font=("Segoe UI", 8), bg=self.card_bg, fg=self.sec_fg)
        lbl_rsub.pack(pady=(0, 10))

        secret = self.auth_service.get_active_secret()
        if secret:
            qr_frame = tk.Frame(card, bg="#FFFFFF", padx=6, pady=6, bd=1, relief="solid")
            qr_frame.pack(pady=(0, 10))

            try:
                rec_qr_img = TOTPManager.generate_tk_qr_image(secret, target_size=(130, 130))
                lbl_rqr = tk.Label(qr_frame, image=rec_qr_img, bg="#FFFFFF")
                lbl_rqr.image = rec_qr_img  # Prevent GC
                lbl_rqr.pack()
            except Exception:
                lbl_rqr = tk.Label(qr_frame, text="QR Unavailable", bg="#FFFFFF", fg="#090C15")
                lbl_rqr.pack()

            key_box = tk.Frame(card, bg=self.card_sec_bg, bd=1, relief="solid", highlightbackground=self.border_color)
            key_box.pack(fill="x", padx=16, pady=(0, 12))

            key_inner = tk.Frame(key_box, bg=self.card_sec_bg)
            key_inner.pack(fill="x", padx=10, pady=6)

            formatted = TOTPManager.format_secret_display(secret)
            lbl_key = tk.Label(key_inner, text=formatted, font=("Consolas", 11, "bold"), bg=self.card_sec_bg, fg=self.accent_blue)
            lbl_key.pack(side="left")

            def _copy_rec_key():
                self.root.clipboard_clear()
                self.root.clipboard_append(secret)
                btn_rec_copy.config(text="✓ Copied!", bg=self.accent_green, fg="#090C15")
                rec_win.after(2000, lambda: btn_rec_copy.config(text="📋 Copy", bg=self.card_bg, fg=self.accent_blue))

            btn_rec_copy = tk.Button(
                key_inner,
                text="📋 Copy",
                font=("Segoe UI", 8, "bold"),
                bg=self.card_bg,
                fg=self.accent_blue,
                bd=0,
                cursor="hand2",
                padx=6,
                pady=1,
                relief="flat",
                command=_copy_rec_key
            )
            btn_rec_copy.pack(side="right")
        else:
            lbl_nokey = tk.Label(card, text="No secret key found in Firebase.", font=("Segoe UI", 9), bg=self.card_bg, fg=self.accent_red)
            lbl_nokey.pack(pady=20)

        lbl_inst = tk.Label(
            card,
            text="1. Open Google / Microsoft Authenticator on your new phone.\n2. Scan the QR code or enter the secret key manually.\n3. Close this window and enter the 6-digit code on the login screen.",
            font=("Segoe UI", 8),
            bg=self.card_bg,
            fg=self.sec_fg,
            justify="left"
        )
        lbl_inst.pack(padx=16, pady=(0, 14), anchor="w")

        btn_close = tk.Button(
            card,
            text="CLOSE & RETURN TO LOGIN",
            font=("Segoe UI", 9, "bold"),
            bg=self.card_sec_bg,
            fg=self.fg_color,
            bd=0,
            cursor="hand2",
            height=2,
            relief="flat",
            command=rec_win.destroy
        )
        btn_close.pack(fill="x", padx=16, pady=(0, 8))

    def _unlock_and_launch_main_app(self):
        """Unlock application, destroy auth frames, resize window, and build main dashboard."""
        self.is_authenticated = True
        self._clean_auth_frames()
        self._center_window(560, 680)
        self._build_main_ui()

        if sys.platform == "darwin":
            trusted, perm_msg = check_macos_permissions()
            if not trusted and perm_msg:
                messagebox.showwarning("macOS Permission Required", perm_msg)

        self._start_background_update_check(silent=True)

    def _build_main_ui(self):
        """Build main application layout with fixed header, vertical scrollable content, and sticky action bar."""
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill="both", expand=True, padx=OUTER_PAD, pady=(OUTER_TOP, OUTER_BOTTOM))

        # 1. FIXED HEADER SECTION (At Top)
        header_frame = tk.Frame(main_container, bg=self.bg_color)
        header_frame.pack(fill="x", pady=(0, CARD_GAP))
        
        hdr_left = tk.Frame(header_frame, bg=self.bg_color)
        hdr_left.pack(side="left")
        
        lbl_title = tk.Label(hdr_left, text="⚡ ArrowFlow", font=("Segoe UI", 17, "bold"), bg=self.bg_color, fg=self.fg_color)
        lbl_title.pack(anchor="w")
        
        lbl_subtitle = tk.Label(hdr_left, text=f"v{CURRENT_VERSION} · Random keyboard activity simulator", font=("Segoe UI", 9), bg=self.bg_color, fg=self.sec_fg)
        lbl_subtitle.pack(anchor="w", pady=(1, 0))
        
        # Header Right Section (Status & Updates)
        hdr_right = tk.Frame(header_frame, bg=self.bg_color)
        hdr_right.pack(side="right", anchor="ne")

        self.lbl_header_status = tk.Label(
            hdr_right,
            text="● STOPPED",
            font=("Segoe UI", 9, "bold"),
            bg=self.card_sec_bg,
            fg=self.sec_fg,
            padx=10,
            pady=3
        )
        self.lbl_header_status.pack(side="top", anchor="e")

        hdr_update_frame = tk.Frame(hdr_right, bg=self.bg_color)
        hdr_update_frame.pack(side="top", anchor="e", pady=(4, 0))

        self.lbl_update_badge = tk.Label(
            hdr_update_frame,
            text="● Up to date",
            font=("Segoe UI", 8, "bold"),
            bg=self.bg_color,
            fg=self.sec_fg
        )
        self.lbl_update_badge.pack(side="left", padx=(0, 6))

        self.btn_check_update = tk.Button(
            hdr_update_frame,
            text="Check for Updates",
            font=("Segoe UI", 8),
            bg=self.card_sec_bg,
            fg=self.accent_blue,
            activebackground=self.accent_blue,
            activeforeground="#090C15",
            bd=0,
            cursor="hand2",
            padx=6,
            pady=1,
            relief="flat",
            command=self._on_click_check_updates
        )
        self.btn_check_update.pack(side="left")

        # 2. STICKY ACTION BAR & ESC HINT (Fixed at Bottom)
        action_frame = tk.Frame(main_container, bg=self.bg_color)
        action_frame.pack(side="bottom", fill="x", pady=(CARD_GAP, 0))

        self.btn_action = tk.Button(
            action_frame,
            text="▶  START AUTOMATION",
            font=("Segoe UI", 11, "bold"),
            bg=self.accent_green,
            fg="#090C15",
            activebackground=self.accent_blue_hover,
            activeforeground="#090C15",
            bd=0,
            cursor="hand2",
            height=2,
            relief="flat",
            command=self._toggle_automation
        )
        self.btn_action.pack(fill="x", pady=(0, 4))

        lbl_esc_hint = tk.Label(
            action_frame, 
            text="ESC  Start/Stop Automation  ·  ALT+SPACE  Toggle Visibility", 
            font=("Segoe UI", 8, "bold"), 
            bg=self.bg_color, 
            fg=self.muted_fg
        )
        lbl_esc_hint.pack(anchor="center", pady=(2, 0))

        # 3. VERTICAL SCROLLABLE CONTENT CONTAINER (Middle Fill/Expand)
        scroll_outer = tk.Frame(main_container, bg=self.bg_color)
        scroll_outer.pack(fill="both", expand=True)

        # Style TTK Vertical Scrollbar to match dark theme
        self.style.configure(
            "Vertical.TScrollbar",
            troughcolor="#090C15",
            background="#192035",
            bordercolor="#242E48",
            arrowcolor=self.accent_blue,
            lightcolor="#242E48",
            darkcolor="#192035"
        )
        self.style.map("Vertical.TScrollbar", background=[("active", self.accent_blue)])

        self.canvas = tk.Canvas(scroll_outer, bg=self.bg_color, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(scroll_outer, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_color)

        self.canvas_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def _on_frame_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        def _on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_frame_id, width=event.width)

        self.scrollable_frame.bind("<Configure>", _on_frame_configure)
        self.canvas.bind("<Configure>", _on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mouse wheel binding helper
        def _on_mousewheel(event):
            if self.canvas.winfo_exists():
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel, add="+")
            for child in widget.winfo_children():
                _bind_mousewheel(child)

        self.root.bind("<MouseWheel>", _on_mousewheel, add="+")

        # CARD 1: TARGET WINDOW Card
        target_card = tk.Frame(self.scrollable_frame, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        target_card.pack(fill="x", pady=(0, CARD_GAP))
        
        target_hdr_frame = tk.Frame(target_card, bg=self.card_bg)
        target_hdr_frame.pack(fill="x", padx=CARD_PAD_X, pady=(CARD_PAD_Y, CONTROL_GAP))
        
        target_hdr_left = tk.Frame(target_hdr_frame, bg=self.card_bg)
        target_hdr_left.pack(side="left")
        
        lbl_target_title = tk.Label(target_hdr_left, text="TARGET WINDOW", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.sec_fg)
        lbl_target_title.pack(anchor="w")
        
        lbl_target_sub = tk.Label(target_hdr_left, text="Select target application window for background input", font=("Segoe UI", 8), bg=self.card_bg, fg=self.muted_fg)
        lbl_target_sub.pack(anchor="w")
        
        self.btn_refresh = tk.Button(
            target_hdr_frame,
            text="↻ Refresh Windows",
            font=("Segoe UI", 8, "bold"),
            bg=self.card_sec_bg,
            fg=self.accent_blue,
            activebackground=self.accent_blue,
            activeforeground="#090C15",
            bd=0,
            cursor="hand2",
            padx=8,
            pady=3,
            relief="flat",
            command=self._refresh_window_list
        )
        self.btn_refresh.pack(side="right")
        
        target_combo_frame = tk.Frame(target_card, bg=self.card_bg)
        target_combo_frame.pack(fill="x", padx=CARD_PAD_X, pady=(0, CONTROL_GAP))
        
        self.combo_target = ttk.Combobox(
            target_combo_frame,
            state="readonly",
            font=("Segoe UI", 9),
            height=6
        )
        self.combo_target.pack(fill="x")
        
        self.lbl_target_conn = tk.Label(
            target_card,
            text="● Select Target",
            font=("Segoe UI", 8, "bold"),
            bg=self.card_bg,
            fg=self.sec_fg
        )
        self.lbl_target_conn.pack(anchor="w", padx=CARD_PAD_X, pady=(0, CARD_PAD_Y))
        
        # CARD 2: ARROW PRESS RANGE Card
        range_card = tk.Frame(self.scrollable_frame, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        range_card.pack(fill="x", pady=(0, CARD_GAP))
        
        range_hdr = tk.Frame(range_card, bg=self.card_bg)
        range_hdr.pack(fill="x", padx=CARD_PAD_X, pady=(CARD_PAD_Y, CONTROL_GAP))
        
        lbl_range_title = tk.Label(range_hdr, text="ARROW PRESS RANGE", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.sec_fg)
        lbl_range_title.pack(anchor="w")
        
        lbl_range_sub = tk.Label(range_hdr, text="Random target generated every 60 seconds", font=("Segoe UI", 8), bg=self.card_bg, fg=self.muted_fg)
        lbl_range_sub.pack(anchor="w")
        
        range_box = tk.Frame(range_card, bg=self.card_sec_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        range_box.pack(fill="x", padx=CARD_PAD_X, pady=(0, CONTROL_GAP))
        
        range_inner = tk.Frame(range_box, bg=self.card_sec_bg)
        range_inner.pack(anchor="center", pady=6)
        
        lbl_min_tag = tk.Label(range_inner, text="MIN", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        lbl_min_tag.pack(side="left", padx=(0, 6))
        
        self.ent_min = tk.Entry(
            range_inner, 
            width=5, 
            font=("Segoe UI", 12, "bold"), 
            bg=self.input_bg, 
            fg=self.fg_color, 
            insertbackground=self.accent_blue,
            bd=1,
            relief="solid",
            highlightbackground=self.border_color,
            justify="center"
        )
        self.ent_min.insert(0, "1")
        self.ent_min.pack(side="left", ipady=2)
        
        lbl_arrow = tk.Label(range_inner, text="—", font=("Segoe UI", 12, "bold"), bg=self.card_sec_bg, fg=self.accent_blue)
        lbl_arrow.pack(side="left", padx=12)
        
        lbl_max_tag = tk.Label(range_inner, text="MAX", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        lbl_max_tag.pack(side="left", padx=(0, 6))
        
        self.ent_max = tk.Entry(
            range_inner, 
            width=5, 
            font=("Segoe UI", 12, "bold"), 
            bg=self.input_bg, 
            fg=self.fg_color, 
            insertbackground=self.accent_blue,
            bd=1,
            relief="solid",
            highlightbackground=self.border_color,
            justify="center"
        )
        self.ent_max.insert(0, "40")
        self.ent_max.pack(side="left", ipady=2)
        
        lbl_range_hint = tk.Label(
            range_card, 
            text="Each minute uses a new random target between Min and Max (e.g. 10 to 40).", 
            font=("Segoe UI", 8), 
            bg=self.card_bg, 
            fg=self.muted_fg,
            justify="left"
        )
        lbl_range_hint.pack(anchor="w", padx=CARD_PAD_X, pady=(0, CARD_PAD_Y))

        # CARD 3: MOUSE EVENT RANGE Card
        mouse_range_card = tk.Frame(self.scrollable_frame, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        mouse_range_card.pack(fill="x", pady=(0, CARD_GAP))
        
        mouse_range_hdr = tk.Frame(mouse_range_card, bg=self.card_bg)
        mouse_range_hdr.pack(fill="x", padx=CARD_PAD_X, pady=(CARD_PAD_Y, CONTROL_GAP))
        
        lbl_mrange_title = tk.Label(mouse_range_hdr, text="MOUSE EVENT RANGE", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.sec_fg)
        lbl_mrange_title.pack(anchor="w")
        
        lbl_mrange_sub = tk.Label(mouse_range_hdr, text="Independent random target generated every 60 seconds", font=("Segoe UI", 8), bg=self.card_bg, fg=self.muted_fg)
        lbl_mrange_sub.pack(anchor="w")
        
        mouse_range_box = tk.Frame(mouse_range_card, bg=self.card_sec_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        mouse_range_box.pack(fill="x", padx=CARD_PAD_X, pady=(0, CONTROL_GAP))
        
        mouse_range_inner = tk.Frame(mouse_range_box, bg=self.card_sec_bg)
        mouse_range_inner.pack(anchor="center", pady=6)
        
        lbl_mmin_tag = tk.Label(mouse_range_inner, text="MIN", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        lbl_mmin_tag.pack(side="left", padx=(0, 6))
        
        self.ent_mouse_min = tk.Entry(
            mouse_range_inner, 
            width=5, 
            font=("Segoe UI", 12, "bold"), 
            bg=self.input_bg, 
            fg=self.fg_color, 
            insertbackground=self.accent_blue,
            bd=1,
            relief="solid",
            highlightbackground=self.border_color,
            justify="center"
        )
        self.ent_mouse_min.insert(0, "5")
        self.ent_mouse_min.pack(side="left", ipady=2)
        
        lbl_marrow = tk.Label(mouse_range_inner, text="—", font=("Segoe UI", 12, "bold"), bg=self.card_sec_bg, fg=self.accent_blue)
        lbl_marrow.pack(side="left", padx=12)
        
        lbl_mmax_tag = tk.Label(mouse_range_inner, text="MAX", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        lbl_mmax_tag.pack(side="left", padx=(0, 6))
        
        self.ent_mouse_max = tk.Entry(
            mouse_range_inner, 
            width=5, 
            font=("Segoe UI", 12, "bold"), 
            bg=self.input_bg, 
            fg=self.fg_color, 
            insertbackground=self.accent_blue,
            bd=1,
            relief="solid",
            highlightbackground=self.border_color,
            justify="center"
        )
        self.ent_mouse_max.insert(0, "20")
        self.ent_mouse_max.pack(side="left", ipady=2)
        
        lbl_mouse_range_hint = tk.Label(
            mouse_range_card, 
            text="Generates an independent random target for mouse clicks every minute (e.g. 5 to 20).", 
            font=("Segoe UI", 8), 
            bg=self.card_bg, 
            fg=self.muted_fg,
            justify="left"
        )
        lbl_mouse_range_hint.pack(anchor="w", padx=CARD_PAD_X, pady=(0, CARD_PAD_Y))

        # CARD 3: FILE SWITCHING Card
        file_card = tk.Frame(self.scrollable_frame, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        file_card.pack(fill="x", pady=(0, CARD_GAP))
        
        file_hdr_frame = tk.Frame(file_card, bg=self.card_bg)
        file_hdr_frame.pack(fill="x", padx=CARD_PAD_X, pady=(CARD_PAD_Y, CONTROL_GAP))
        
        file_hdr_left = tk.Frame(file_hdr_frame, bg=self.card_bg)
        file_hdr_left.pack(side="left")
        
        lbl_file_title = tk.Label(file_hdr_left, text="FILE SWITCHING", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.sec_fg)
        lbl_file_title.pack(anchor="w")
        
        lbl_file_sub = tk.Label(file_hdr_left, text="Automatically switch VS Code files/tabs periodically", font=("Segoe UI", 8), bg=self.card_bg, fg=self.muted_fg)
        lbl_file_sub.pack(anchor="w")
        
        self.btn_file_toggle = tk.Button(
            file_hdr_frame,
            text="[ OFF ]",
            font=("Segoe UI", 8, "bold"),
            bg=self.card_sec_bg,
            fg=self.sec_fg,
            activebackground=self.card_sec_bg,
            activeforeground=self.fg_color,
            bd=0,
            cursor="hand2",
            padx=10,
            pady=3,
            relief="flat",
            command=self._toggle_file_switching
        )
        self.btn_file_toggle.pack(side="right")
        
        file_box = tk.Frame(file_card, bg=self.card_sec_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        file_box.pack(fill="x", padx=CARD_PAD_X, pady=(0, CONTROL_GAP))
        
        file_inner = tk.Frame(file_box, bg=self.card_sec_bg)
        file_inner.pack(anchor="center", pady=6)
        
        lbl_fmin_tag = tk.Label(file_inner, text="MIN", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        lbl_fmin_tag.pack(side="left", padx=(0, 6))
        
        self.ent_file_min = tk.Entry(
            file_inner, 
            width=5, 
            font=("Segoe UI", 12, "bold"), 
            bg=self.input_bg, 
            fg=self.disabled_fg, 
            insertbackground=self.accent_blue,
            bd=1,
            relief="solid",
            highlightbackground=self.border_color,
            justify="center",
            state="disabled"
        )
        self.ent_file_min.insert(0, "1")
        self.ent_file_min.pack(side="left", ipady=2)
        
        lbl_farrow = tk.Label(file_inner, text="—", font=("Segoe UI", 12, "bold"), bg=self.card_sec_bg, fg=self.accent_blue)
        lbl_farrow.pack(side="left", padx=12)
        
        lbl_fmax_tag = tk.Label(file_inner, text="MAX", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        lbl_fmax_tag.pack(side="left", padx=(0, 6))
        
        self.ent_file_max = tk.Entry(
            file_inner, 
            width=5, 
            font=("Segoe UI", 12, "bold"), 
            bg=self.input_bg, 
            fg=self.disabled_fg, 
            insertbackground=self.accent_blue,
            bd=1,
            relief="solid",
            highlightbackground=self.border_color,
            justify="center",
            state="disabled"
        )
        self.ent_file_max.insert(0, "5")
        self.ent_file_max.pack(side="left", ipady=2)
        
        lbl_file_hint = tk.Label(
            file_card, 
            text="Random Ctrl + Shift + Tab count each minute.", 
            font=("Segoe UI", 8), 
            bg=self.card_bg, 
            fg=self.muted_fg
        )
        lbl_file_hint.pack(anchor="w", padx=CARD_PAD_X, pady=(0, CARD_PAD_Y))

        # CARD 4: GOOGLE CHROME ALTERNATING MODE Card
        chrome_card = tk.Frame(self.scrollable_frame, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        chrome_card.pack(fill="x", pady=(0, CARD_GAP))
        
        chrome_hdr_frame = tk.Frame(chrome_card, bg=self.card_bg)
        chrome_hdr_frame.pack(fill="x", padx=CARD_PAD_X, pady=(CARD_PAD_Y, CONTROL_GAP))
        
        chrome_hdr_left = tk.Frame(chrome_hdr_frame, bg=self.card_bg)
        chrome_hdr_left.pack(side="left")
        
        lbl_chrome_title = tk.Label(chrome_hdr_left, text="GOOGLE CHROME BROWSER", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.sec_fg)
        lbl_chrome_title.pack(anchor="w")
        
        lbl_chrome_sub = tk.Label(chrome_hdr_left, text="Alternate between VS Code and Chrome with random durations", font=("Segoe UI", 8), bg=self.card_bg, fg=self.muted_fg)
        lbl_chrome_sub.pack(anchor="w")
        
        self.btn_chrome_toggle = tk.Button(
            chrome_hdr_frame,
            text="[ OFF ]",
            font=("Segoe UI", 8, "bold"),
            bg=self.card_sec_bg,
            fg=self.sec_fg,
            activebackground=self.card_sec_bg,
            activeforeground=self.fg_color,
            bd=0,
            cursor="hand2",
            padx=10,
            pady=3,
            relief="flat",
            command=self._toggle_chrome_mode
        )
        self.btn_chrome_toggle.pack(side="right")
        
        chrome_box = tk.Frame(chrome_card, bg=self.card_sec_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        chrome_box.pack(fill="x", padx=CARD_PAD_X, pady=(0, CONTROL_GAP))
        
        chrome_inner = tk.Frame(chrome_box, bg=self.card_sec_bg)
        chrome_inner.pack(anchor="center", pady=6)
        
        lbl_cmin_tag = tk.Label(chrome_inner, text="MIN", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        lbl_cmin_tag.pack(side="left", padx=(0, 6))
        
        self.ent_chrome_min = tk.Entry(
            chrome_inner, 
            width=5, 
            font=("Segoe UI", 12, "bold"), 
            bg=self.input_bg, 
            fg=self.disabled_fg, 
            insertbackground=self.accent_blue,
            bd=1,
            relief="solid",
            highlightbackground=self.border_color,
            justify="center",
            state="disabled"
        )
        self.ent_chrome_min.insert(0, "5")
        self.ent_chrome_min.pack(side="left", ipady=2)
        
        lbl_carrow = tk.Label(chrome_inner, text="—", font=("Segoe UI", 12, "bold"), bg=self.card_sec_bg, fg=self.accent_blue)
        lbl_carrow.pack(side="left", padx=12)
        
        lbl_cmax_tag = tk.Label(chrome_inner, text="MAX", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        lbl_cmax_tag.pack(side="left", padx=(0, 6))
        
        self.ent_chrome_max = tk.Entry(
            chrome_inner, 
            width=5, 
            font=("Segoe UI", 12, "bold"), 
            bg=self.input_bg, 
            fg=self.disabled_fg, 
            insertbackground=self.accent_blue,
            bd=1,
            relief="solid",
            highlightbackground=self.border_color,
            justify="center",
            state="disabled"
        )
        self.ent_chrome_max.insert(0, "10")
        self.ent_chrome_max.pack(side="left", ipady=2)
        
        lbl_chrome_hint = tk.Label(
            chrome_card, 
            text="Generates a NEW random duration (min) each cycle switch.", 
            font=("Segoe UI", 8), 
            bg=self.card_bg, 
            fg=self.muted_fg
        )
        lbl_chrome_hint.pack(anchor="w", padx=CARD_PAD_X, pady=(0, CARD_PAD_Y))

        # CARD 5: CURRENT TARGET Card
        target_display_card = tk.Frame(self.scrollable_frame, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        target_display_card.pack(fill="x", pady=(0, CARD_GAP))
        
        curr_hdr = tk.Frame(target_display_card, bg=self.card_bg)
        curr_hdr.pack(fill="x", padx=CARD_PAD_X, pady=(CARD_PAD_Y, 2))
        
        lbl_curr_title = tk.Label(curr_hdr, text="CURRENT TARGET", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.sec_fg)
        lbl_curr_title.pack(anchor="w")
        
        target_display_box = tk.Frame(target_display_card, bg=self.card_bg)
        target_display_box.pack(anchor="center", pady=(2, 2))
        
        self.lbl_big_target = tk.Label(
            target_display_box, 
            text="—", 
            font=("Segoe UI", 32, "bold"), 
            bg=self.card_bg, 
            fg=self.fg_color
        )
        self.lbl_big_target.pack(anchor="center")
        
        lbl_presses_sub = tk.Label(
            target_display_box, 
            text="presses target", 
            font=("Segoe UI", 8, "bold"), 
            bg=self.card_bg, 
            fg=self.sec_fg
        )
        lbl_presses_sub.pack(anchor="center")
        
        progress_container = tk.Frame(target_display_card, bg=self.card_bg)
        progress_container.pack(fill="x", padx=CARD_PAD_X, pady=(4, 2))
        
        self.progress_bar = ttk.Progressbar(
            progress_container,
            style="Custom.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            value=0,
            maximum=40
        )
        self.progress_bar.pack(fill="x")
        
        stats_row = tk.Frame(target_display_card, bg=self.card_bg)
        stats_row.pack(fill="x", padx=CARD_PAD_X, pady=(3, 3))
        
        self.lbl_presses_min = tk.Label(
            stats_row, 
            text="0 / —", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.card_bg, 
            fg=self.fg_color
        )
        self.lbl_presses_min.pack(side="left")
        
        self.lbl_percent = tk.Label(
            stats_row, 
            text="0%", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.card_bg, 
            fg=self.accent_blue
        )
        self.lbl_percent.pack(side="right")
        
        lbl_window_note = tk.Label(
            target_display_card, 
            text="Next target will be generated automatically when current 60-second window ends.", 
            font=("Segoe UI", 8, "italic"), 
            bg=self.card_bg, 
            fg=self.muted_fg
        )
        lbl_window_note.pack(anchor="w", padx=CARD_PAD_X, pady=(0, CARD_PAD_Y))

        # CARD 6: AUTOMATION STATUS Card
        status_card = tk.Frame(self.scrollable_frame, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        status_card.pack(fill="x", pady=(0, CARD_GAP))

        status_hdr = tk.Frame(status_card, bg=self.card_bg)
        status_hdr.pack(fill="x", padx=CARD_PAD_X, pady=(CARD_PAD_Y, CONTROL_GAP))

        lbl_status_title = tk.Label(status_hdr, text="AUTOMATION STATUS", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.sec_fg)
        lbl_status_title.pack(anchor="w")

        status_box = tk.Frame(status_card, bg=self.card_sec_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        status_box.pack(fill="x", padx=CARD_PAD_X, pady=(0, CARD_PAD_Y))

        status_inner = tk.Frame(status_box, bg=self.card_sec_bg)
        status_inner.pack(fill="x", padx=12, pady=10)

        self.lbl_status_target = tk.Label(status_inner, text="● Target: Select Target", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        self.lbl_status_target.pack(anchor="w", pady=(0, 4))

        self.lbl_status_arrow = tk.Label(status_inner, text="● Arrow & Mouse Automation: Ready", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        self.lbl_status_arrow.pack(anchor="w", pady=(0, 4))

        self.lbl_file_switch_status = tk.Label(status_inner, text="● File Switch: OFF", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        self.lbl_file_switch_status.pack(anchor="w", pady=(0, 4))

        self.lbl_chrome_status = tk.Label(status_inner, text="● Chrome Mode: OFF", font=("Segoe UI", 8, "bold"), bg=self.card_sec_bg, fg=self.sec_fg)
        self.lbl_chrome_status.pack(anchor="w")

        # Populate windows list
        self._refresh_window_list()

        # Recursively bind mousewheel to all scrollable_frame children
        _bind_mousewheel(self.scrollable_frame)

    def _refresh_window_list(self):
        """Enumerate visible top-level VS Code windows and update dropdown list."""
        current_sel = self.combo_target.get()
        windows_list = get_top_level_windows()
        
        self.windows_map.clear()
        display_names = []
        
        for item in windows_list:
            disp = item["display"]
            hwnd = item["hwnd"]
            self.windows_map[disp] = hwnd
            display_names.append(disp)
            
        self.combo_target['values'] = display_names
        
        if current_sel in self.windows_map and is_window_valid(self.windows_map[current_sel]):
            self.combo_target.set(current_sel)
            self.lbl_target_conn.config(text="● Connected", fg=self.accent_green)
            if hasattr(self, "lbl_status_target"):
                self.lbl_status_target.config(text=f"● Target: {current_sel}", fg=self.accent_green)
        elif display_names:
            self.combo_target.current(0)
            self.lbl_target_conn.config(text="● Ready to Connect", fg=self.sec_fg)
            if hasattr(self, "lbl_status_target"):
                self.lbl_status_target.config(text=f"● Target: {display_names[0]}", fg=self.sec_fg)
        else:
            self.combo_target.set("")
            self.lbl_target_conn.config(text="● No VS Code Windows Found", fg=self.accent_red)
            if hasattr(self, "lbl_status_target"):
                self.lbl_status_target.config(text="● Target: None (VS Code Required)", fg=self.accent_red)

    def _toggle_file_switching(self):
        """Toggle file switching state ON/OFF."""
        self.file_switch_enabled = not self.file_switch_enabled
        if self.file_switch_enabled:
            self.btn_file_toggle.config(
                text="[ ON ]",
                bg=self.accent_green,
                fg="#090C15",
                activebackground=self.accent_blue_hover,
                activeforeground="#090C15"
            )
            self.ent_file_min.config(state="normal", fg=self.fg_color)
            self.ent_file_max.config(state="normal", fg=self.fg_color)
            self.lbl_file_switch_status.config(text="● File Switch: ON (Ctrl+Shift+Tab)", fg=self.accent_blue)
        else:
            self.btn_file_toggle.config(
                text="[ OFF ]",
                bg=self.card_sec_bg,
                fg=self.sec_fg,
                activebackground=self.card_sec_bg,
                activeforeground=self.fg_color
            )
            self.ent_file_min.config(state="disabled", fg=self.disabled_fg)
            self.ent_file_max.config(state="disabled", fg=self.disabled_fg)
            self.lbl_file_switch_status.config(text="● File Switch: OFF", fg=self.sec_fg)

    def _toggle_chrome_mode(self):
        """Toggle Google Chrome Alternating mode state ON/OFF."""
        self.chrome_enabled = not self.chrome_enabled
        if self.chrome_enabled:
            self.btn_chrome_toggle.config(
                text="[ ON ]",
                bg=self.accent_green,
                fg="#090C15",
                activebackground=self.accent_blue_hover,
                activeforeground="#090C15"
            )
            self.ent_chrome_min.config(state="normal", fg=self.fg_color)
            self.ent_chrome_max.config(state="normal", fg=self.fg_color)
            if hasattr(self, "lbl_chrome_status"):
                self.lbl_chrome_status.config(text="● Chrome Mode: ON (Alternating)", fg=self.accent_blue)
        else:
            self.btn_chrome_toggle.config(
                text="[ OFF ]",
                bg=self.card_sec_bg,
                fg=self.sec_fg,
                activebackground=self.card_sec_bg,
                activeforeground=self.fg_color
            )
            self.ent_chrome_min.config(state="disabled", fg=self.disabled_fg)
            self.ent_chrome_max.config(state="disabled", fg=self.disabled_fg)
            if hasattr(self, "lbl_chrome_status"):
                self.lbl_chrome_status.config(text="● Chrome Mode: OFF", fg=self.sec_fg)

    def _toggle_hide_taskbar(self):
        """Toggle Hide from Windows Taskbar setting ON and OFF at runtime."""
        self.hide_taskbar_enabled = not self.hide_taskbar_enabled
        if self.hide_taskbar_enabled:
            self.btn_taskbar_toggle.config(
                text="[ ON ]",
                bg=self.accent_green,
                fg="#090C15",
                activebackground=self.accent_blue_hover,
                activeforeground="#090C15"
            )
            set_taskbar_visibility(self.root, hide=True)
        else:
            self.btn_taskbar_toggle.config(
                text="[ OFF ]",
                bg=self.card_sec_bg,
                fg=self.sec_fg,
                activebackground=self.card_sec_bg,
                activeforeground=self.fg_color
            )
            set_taskbar_visibility(self.root, hide=False)

    def validate_inputs(self):
        """Validate range inputs and target window selection."""
        # 1. Target Window Validation
        selected_display = self.combo_target.get().strip()
        if not selected_display or selected_display not in self.windows_map:
            messagebox.showerror("VS Code Target Required", "Please launch Visual Studio Code and select an active VS Code target window before starting.")
            self._refresh_window_list()
            return None
            
        target_hwnd = self.windows_map[selected_display]
        if not is_window_valid(target_hwnd):
            messagebox.showerror("Target Unavailable", "The selected VS Code window is no longer available. Please refresh and select an active VS Code target.")
            self._refresh_window_list()
            return None

        # 2. Arrow Range Input Validation (Allows 1 to any number)
        min_str = self.ent_min.get().strip()
        max_str = self.ent_max.get().strip()
        
        try:
            min_val = int(min_str)
            max_val = int(max_str)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integer numbers for Arrow Min and Max range (e.g. 1 to 40).")
            return None
            
        if min_val < 1:
            messagebox.showerror("Invalid Input", "Arrow minimum range value must be at least 1.")
            return None
            
        if max_val < 1:
            messagebox.showerror("Invalid Input", "Arrow maximum range value must be at least 1.")
            return None
            
        if min_val > max_val:
            messagebox.showerror("Invalid Input", "Arrow minimum value cannot be greater than Maximum value.")
            return None

        # 3. Mouse Event Range Validation
        mmin_str = self.ent_mouse_min.get().strip()
        mmax_str = self.ent_mouse_max.get().strip()
        
        try:
            mouse_min_val = int(mmin_str)
            mouse_max_val = int(mmax_str)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integer numbers for Mouse Event Min and Max range (e.g. 5 to 20).")
            return None
            
        if mouse_min_val < 1:
            messagebox.showerror("Invalid Input", "Mouse minimum range value must be at least 1.")
            return None
            
        if mouse_max_val < 1:
            messagebox.showerror("Invalid Input", "Mouse maximum range value must be at least 1.")
            return None
            
        if mouse_min_val > mouse_max_val:
            messagebox.showerror("Invalid Input", "Mouse minimum value cannot be greater than Maximum value.")
            return None

        # 4. File Switching Validation
        file_min_val, file_max_val = 1, 5
        if self.file_switch_enabled:
            fmin_str = self.ent_file_min.get().strip()
            fmax_str = self.ent_file_max.get().strip()
            try:
                file_min_val = int(fmin_str)
                file_max_val = int(fmax_str)
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid integer numbers for File Switching Min and Max range (e.g. 1 to 5).")
                return None
                
            if file_min_val < 1:
                messagebox.showerror("Invalid Input", "File switching minimum range value must be at least 1.")
                return None
                
            if file_max_val < 1:
                messagebox.showerror("Invalid Input", "File switching maximum range value must be at least 1.")
                return None
                
            if file_min_val > file_max_val:
                messagebox.showerror("Invalid Input", "File switching minimum value cannot be greater than maximum value.")
                return None

        # 5. Google Chrome Alternating Mode Validation
        chrome_min_val, chrome_max_val = 5, 10
        if self.chrome_enabled:
            cmin_str = self.ent_chrome_min.get().strip()
            cmax_str = self.ent_chrome_max.get().strip()
            try:
                chrome_min_val = int(cmin_str)
                chrome_max_val = int(cmax_str)
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid integer numbers for Chrome Min and Max minutes (e.g. 5 to 10).")
                return None

            if chrome_min_val < 1:
                messagebox.showerror("Invalid Input", "Chrome minimum minutes value must be a positive number (at least 1).")
                return None

            if chrome_max_val < 1:
                messagebox.showerror("Invalid Input", "Chrome maximum minutes value must be a positive number (at least 1).")
                return None

            if chrome_min_val > chrome_max_val:
                messagebox.showerror("Invalid Input", "Chrome minimum minutes value cannot be greater than Maximum value.")
                return None
            
        return target_hwnd, min_val, max_val, mouse_min_val, mouse_max_val, file_min_val, file_max_val, self.file_switch_enabled, self.chrome_enabled, chrome_min_val, chrome_max_val

    def _toggle_automation(self):
        """Single button toggle for START and STOP automation."""
        if self.controller.is_running:
            self.stop_automation()
        else:
            self.start_automation()

    def start_automation(self):
        res = self.validate_inputs()
        if res is None:
            return
            
        target_hwnd, min_val, max_val, mouse_min_val, mouse_max_val, file_min_val, file_max_val, file_switch_enabled, chrome_enabled, chrome_min_val, chrome_max_val = res
        
        # Bring selected VS Code window to foreground
        bring_window_to_front(target_hwnd)
        import time
        time.sleep(0.2)
        
        # Reset live indicators
        self.lbl_big_target.config(text="—")
        self.lbl_presses_min.config(text="Arrow: 0/— • Mouse: 0/—")
        self.lbl_percent.config(text="0%")
        self.progress_bar.config(value=0, maximum=max_val + mouse_max_val)
        
        # Update UI controls state to running
        self.combo_target.config(state="disabled")
        self.btn_refresh.config(state="disabled")
        self.ent_min.config(state="disabled")
        self.ent_max.config(state="disabled")
        self.ent_mouse_min.config(state="disabled")
        self.ent_mouse_max.config(state="disabled")
        self.btn_file_toggle.config(state="disabled")
        self.ent_file_min.config(state="disabled")
        self.ent_file_max.config(state="disabled")
        self.btn_chrome_toggle.config(state="disabled")
        self.ent_chrome_min.config(state="disabled")
        self.ent_chrome_max.config(state="disabled")
        
        # Action button switches to STOP
        self.btn_action.config(
            text="■  STOP AUTOMATION",
            bg=self.accent_red,
            fg="#090C15",
            activebackground="#FF7A93"
        )
        
        self.lbl_header_status.config(text="● RUNNING", fg=self.accent_green)
        self.lbl_target_conn.config(text="● Connected", fg=self.accent_green)
        if hasattr(self, "lbl_status_target"):
            self.lbl_status_target.config(text=f"● Target: {self.combo_target.get()}", fg=self.accent_green)
        if hasattr(self, "lbl_status_arrow"):
            mode_desc = "VS Code + Chrome Alternating" if chrome_enabled else "Active"
            self.lbl_status_arrow.config(text=f"● Arrow & Mouse Automation: {mode_desc}", fg=self.accent_green)
        
        # Start Controller with target HWND and options
        self.controller.start(
            min_presses=min_val,
            max_presses=max_val,
            target_hwnd=target_hwnd,
            file_min=file_min_val,
            file_max=file_max_val,
            file_switching_enabled=file_switch_enabled,
            mouse_min=mouse_min_val,
            mouse_max=mouse_max_val,
            mouse_enabled=True,
            chrome_enabled=chrome_enabled,
            chrome_min=chrome_min_val,
            chrome_max=chrome_max_val
        )

    def stop_automation(self):
        self.controller.stop()
        self._set_ui_stopped()

    def _set_ui_stopped(self):
        if not hasattr(self, "lbl_header_status"):
            return
        self.combo_target.config(state="readonly")
        self.btn_refresh.config(state="normal")
        self.ent_min.config(state="normal")
        self.ent_max.config(state="normal")
        self.ent_mouse_min.config(state="normal")
        self.ent_mouse_max.config(state="normal")
        self.btn_file_toggle.config(state="normal")
        if self.file_switch_enabled:
            self.ent_file_min.config(state="normal")
            self.ent_file_max.config(state="normal")
        self.btn_chrome_toggle.config(state="normal")
        if self.chrome_enabled:
            self.ent_chrome_min.config(state="normal")
            self.ent_chrome_max.config(state="normal")
        
        # Action button switches back to START
        self.btn_action.config(
            text="▶  START AUTOMATION",
            bg=self.accent_green,
            fg="#090C15",
            activebackground=self.accent_blue_hover
        )
        
        self.lbl_header_status.config(text="● STOPPED", fg=self.sec_fg)
        if hasattr(self, "lbl_status_arrow"):
            self.lbl_status_arrow.config(text="● Arrow & Mouse Automation: Stopped", fg=self.sec_fg)
        if self.combo_target.get() in self.windows_map and is_window_valid(self.windows_map[self.combo_target.get()]):
            self.lbl_target_conn.config(text="● Connected", fg=self.accent_green)
            if hasattr(self, "lbl_status_target"):
                self.lbl_status_target.config(text=f"● Target: {self.combo_target.get()}", fg=self.accent_green)

    def _on_target_lost_callback(self):
        """Callback invoked on main thread if target HWND closes during automation."""
        def handle_target_lost():
            self._set_ui_stopped()
            self.lbl_header_status.config(text="● TARGET CLOSED", fg=self.accent_red)
            self.lbl_target_conn.config(text="● Target unavailable", fg=self.accent_red)
            if hasattr(self, "lbl_status_target"):
                self.lbl_status_target.config(text="● Target: Unavailable", fg=self.accent_red)
            if hasattr(self, "lbl_status_arrow"):
                self.lbl_status_arrow.config(text="● Arrow & Mouse Automation: Stopped", fg=self.accent_red)
            messagebox.showwarning("Target Lost", "The selected target window was closed or became unavailable. Automation has stopped.")
            self._refresh_window_list()
            
        if self.is_authenticated:
            self.root.after(0, handle_target_lost)

    def _on_global_esc(self):
        """Triggered from pynput background listener thread. Schedule UI toggle on main Tk thread with debounce guard."""
        if not self.is_authenticated:
            return
        import time
        now = time.monotonic()
        if now - self.last_esc_time < 0.35:
            return  # Ignore rapid key repeat / duplicate key events
        self.last_esc_time = now
        self.root.after(0, self._toggle_automation)

    def _on_tkinter_alt_space(self, event=None):
        """Intercept ALT+SPACE in Tkinter, suppress system window menu, and toggle visibility."""
        if self.is_authenticated:
            self._toggle_window_visibility()
        return "break"

    def _on_global_alt_space(self):
        """Triggered from pynput background listener thread when ALT+SPACE is pressed globally."""
        if self.is_authenticated:
            self.root.after(0, self._toggle_window_visibility)

    def _toggle_window_visibility(self):
        """Toggle ArrowFlow application window and taskbar visibility (ALT+SPACE)."""
        import time
        now = time.monotonic()
        if now - self.last_alt_space_time < 0.35:
            return  # Debounce rapid key repeat
        self.last_alt_space_time = now

        if self.is_window_hidden:
            # Restore window & taskbar visibility
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.is_window_hidden = False
        else:
            # Hide window & taskbar presence completely
            self.root.withdraw()
            self.is_window_hidden = True

    def _on_stopped_callback(self):
        if self.is_authenticated:
            self.root.after(0, self._set_ui_stopped)

    def _on_stats_update(self, arrow_done=0, arrow_target=0, mouse_done=0, mouse_target=0, total_presses=0, file_switch_count=0, file_switching_enabled=False, **kwargs):
        # Handle legacy positional arguments if passed
        if "presses_this_minute" in kwargs:
            arrow_done = kwargs["presses_this_minute"]
        if "target_per_minute" in kwargs:
            arrow_target = kwargs["target_per_minute"]

        current_mode = kwargs.get("current_mode", "VS Code")
        remaining_sec = kwargs.get("remaining_sec", 0)

        def update_gui():
            if hasattr(self, "lbl_presses_min"):
                self.lbl_big_target.config(text=f"A:{arrow_target}  M:{mouse_target}")
                self.lbl_presses_min.config(text=f"Arrow: {arrow_done}/{arrow_target}   Mouse: {mouse_done}/{mouse_target}")
                tot_target = max(1, arrow_target + mouse_target)
                tot_done = arrow_done + mouse_done
                pct = int((tot_done / tot_target) * 100)
                self.progress_bar.config(value=tot_done, maximum=tot_target)
                self.lbl_percent.config(text=f"{pct}%")
                if hasattr(self, "lbl_file_switch_status"):
                    if file_switching_enabled:
                        self.lbl_file_switch_status.config(
                            text=f"● File Switch: Active ({file_switch_count} × Ctrl+Shift+Tab)",
                            fg=self.accent_blue
                        )
                    else:
                        self.lbl_file_switch_status.config(
                            text="● File Switch: OFF",
                            fg=self.sec_fg
                        )
                if hasattr(self, "lbl_chrome_status"):
                    if self.chrome_enabled:
                        mins = remaining_sec // 60
                        secs = remaining_sec % 60
                        rem_str = f"{mins}m {secs}s" if remaining_sec > 0 else "Switching..."
                        self.lbl_chrome_status.config(
                            text=f"● Mode: {current_mode} (Remaining: {rem_str})",
                            fg=self.accent_green if "Chrome" in current_mode else self.accent_blue
                        )
                    else:
                        self.lbl_chrome_status.config(
                            text="● Chrome Mode: OFF",
                            fg=self.sec_fg
                        )

        if self.is_authenticated:
            self.root.after(0, update_gui)

    # =========================================================================
    # AUTOMATIC UPDATE SYSTEM UI & HANDLERS
    # =========================================================================

    def _start_background_update_check(self, silent=True):
        """Check for updates asynchronously in a background thread without blocking the GUI."""
        if hasattr(self, "lbl_update_badge") and self.lbl_update_badge.winfo_exists():
            self.lbl_update_badge.config(text="● Checking...", fg=self.accent_blue)
        if hasattr(self, "btn_check_update") and self.btn_check_update.winfo_exists():
            self.btn_check_update.config(state="disabled")

        def on_check_finished(result, error):
            def update_ui():
                if not hasattr(self, "lbl_update_badge") or not self.lbl_update_badge.winfo_exists():
                    return
                if hasattr(self, "btn_check_update") and self.btn_check_update.winfo_exists():
                    self.btn_check_update.config(state="normal")

                if error:
                    # Connection error or offline
                    self.lbl_update_badge.config(text="● Unable to check", fg=self.sec_fg)
                    if not silent:
                        messagebox.showwarning(
                            "Unable to Check for Updates",
                            "Unable to check for updates.\n\nCould not connect to the update server. Please check your internet connection and try again."
                        )
                    return

                if result and result.get("update_available"):
                    self.latest_update_info = result
                    self.lbl_update_badge.config(text="● Update available", fg=self.accent_green)
                    self.btn_check_update.config(
                        text="[ Update Now ]",
                        bg=self.accent_green,
                        fg="#090C15",
                        activebackground=self.accent_blue_hover
                    )
                    self._show_update_dialog(result)
                else:
                    self.lbl_update_badge.config(text="● Up to date", fg=self.sec_fg)
                    self.btn_check_update.config(
                        text="Check for Updates",
                        bg=self.card_sec_bg,
                        fg=self.accent_blue,
                        activebackground=self.accent_blue
                    )
                    if not silent:
                        messagebox.showinfo(
                            "ArrowFlow Update",
                            f"You are using the latest version (v{CURRENT_VERSION})."
                        )

            try:
                if self.is_authenticated and hasattr(self, "root") and self.root.winfo_exists():
                    self.root.after(0, update_ui)
            except Exception:
                pass

        check_for_updates_async(on_check_finished)

    def _on_click_check_updates(self):
        """Manual update check button handler."""
        if hasattr(self, "controller") and self.controller.is_running:
            messagebox.showwarning(
                "Automation Active",
                "Automation is currently active. Please stop automation before checking for or applying updates."
            )
            return

        if hasattr(self, "latest_update_info") and self.latest_update_info and self.latest_update_info.get("update_available"):
            self._show_update_dialog(self.latest_update_info)
        else:
            self._start_background_update_check(silent=False)

    def _show_update_dialog(self, update_info: dict):
        """Displays custom dark-themed update dialog popup."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Available - ArrowFlow")
        dialog.configure(bg=self.bg_color)
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        rx = self.root.winfo_x()
        ry = self.root.winfo_y()
        dw, dh = 440, 360
        dx = max(0, rx + (rw - dw) // 2)
        dy = max(0, ry + (rh - dh) // 2)
        dialog.geometry(f"{dw}x{dh}+{dx}+{dy}")

        card = tk.Frame(dialog, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Header Title
        lbl_hdr = tk.Label(card, text="🚀 Update Available", font=("Segoe UI", 13, "bold"), bg=self.card_bg, fg=self.accent_blue)
        lbl_hdr.pack(anchor="w", padx=16, pady=(16, 4))

        lbl_desc = tk.Label(card, text="A new version of ArrowFlow is available for download.", font=("Segoe UI", 9), bg=self.card_bg, fg=self.sec_fg)
        lbl_desc.pack(anchor="w", padx=16, pady=(0, 12))

        # Version Info Box
        v_box = tk.Frame(card, bg=self.card_sec_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        v_box.pack(fill="x", padx=16, pady=(0, 12))

        v_inner = tk.Frame(v_box, bg=self.card_sec_bg)
        v_inner.pack(fill="x", padx=12, pady=8)

        lbl_cur = tk.Label(v_inner, text=f"Current version:  v{CURRENT_VERSION}", font=("Segoe UI", 9), bg=self.card_sec_bg, fg=self.sec_fg)
        lbl_cur.pack(anchor="w")

        lbl_new = tk.Label(v_inner, text=f"New version:      v{update_info.get('remote_version', '1.1.0')}", font=("Segoe UI", 10, "bold"), bg=self.card_sec_bg, fg=self.accent_green)
        lbl_new.pack(anchor="w", pady=(2, 0))

        # Release Notes Section
        lbl_notes_title = tk.Label(card, text="RELEASE NOTES", font=("Segoe UI", 8, "bold"), bg=self.card_bg, fg=self.sec_fg)
        lbl_notes_title.pack(anchor="w", padx=16, pady=(0, 4))

        notes_frame = tk.Frame(card, bg=self.input_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        notes_frame.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        notes_text = tk.Text(notes_frame, bg=self.input_bg, fg=self.fg_color, font=("Segoe UI", 9), bd=0, wrap="word", highlightthickness=0, height=5)
        notes_text.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        notes_scroll = ttk.Scrollbar(notes_frame, orient="vertical", command=notes_text.yview, style="Vertical.TScrollbar")
        notes_scroll.pack(side="right", fill="y")
        notes_text.configure(yscrollcommand=notes_scroll.set)

        rel_notes = update_info.get("release_notes", "• Bug fixes and performance improvements.")
        notes_text.insert("1.0", rel_notes)
        notes_text.config(state="disabled")

        # Action Buttons
        btn_box = tk.Frame(card, bg=self.card_bg)
        btn_box.pack(fill="x", padx=16, pady=(0, 16))

        btn_later = tk.Button(
            btn_box,
            text="Later",
            font=("Segoe UI", 9, "bold"),
            bg=self.card_sec_bg,
            fg=self.sec_fg,
            activebackground=self.border_color,
            activeforeground=self.fg_color,
            bd=0,
            cursor="hand2",
            padx=16,
            pady=6,
            relief="flat",
            command=dialog.destroy
        )
        btn_later.pack(side="right", padx=(8, 0))

        btn_now = tk.Button(
            btn_box,
            text="Update Now",
            font=("Segoe UI", 9, "bold"),
            bg=self.accent_green,
            fg="#090C15",
            activebackground=self.accent_blue_hover,
            activeforeground="#090C15",
            bd=0,
            cursor="hand2",
            padx=18,
            pady=6,
            relief="flat",
            command=lambda: self._confirm_and_start_update(dialog, update_info)
        )
        btn_now.pack(side="right")

    def _confirm_and_start_update(self, prompt_dialog, update_info: dict):
        """Close update prompt and launch download dialog & verification workflow."""
        if hasattr(self, "controller") and self.controller.is_running:
            messagebox.showwarning(
                "Automation Active",
                "Automation is currently active. Please stop automation before downloading and installing updates."
            )
            return

        prompt_dialog.destroy()


        # Build Download Progress Dialog
        dl_dialog = tk.Toplevel(self.root)
        dl_dialog.title("Downloading Update")
        dl_dialog.configure(bg=self.bg_color)
        dl_dialog.resizable(False, False)
        dl_dialog.transient(self.root)
        dl_dialog.grab_set()

        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        rx = self.root.winfo_x()
        ry = self.root.winfo_y()
        dw, dh = 400, 200
        dx = max(0, rx + (rw - dw) // 2)
        dy = max(0, ry + (rh - dh) // 2)
        dl_dialog.geometry(f"{dw}x{dh}+{dx}+{dy}")

        card = tk.Frame(dl_dialog, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.border_color)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        remote_ver = update_info.get("remote_version", "1.1.0")
        lbl_dl_title = tk.Label(card, text=f"Downloading ArrowFlow v{remote_ver}", font=("Segoe UI", 11, "bold"), bg=self.card_bg, fg=self.fg_color)
        lbl_dl_title.pack(anchor="w", padx=16, pady=(16, 4))

        lbl_dl_status = tk.Label(card, text="Connecting to server...", font=("Segoe UI", 8), bg=self.card_bg, fg=self.sec_fg)
        lbl_dl_status.pack(anchor="w", padx=16, pady=(0, 10))

        dl_progress = ttk.Progressbar(card, orient="horizontal", mode="determinate", style="Custom.Horizontal.TProgressbar")
        dl_progress.pack(fill="x", padx=16, pady=(0, 8))

        lbl_dl_pct = tk.Label(card, text="0%", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.accent_blue)
        lbl_dl_pct.pack(anchor="e", padx=16, pady=(0, 10))

        cancel_event = threading.Event()

        def on_cancel():
            cancel_event.set()
            dl_dialog.destroy()

        btn_cancel = tk.Button(
            card,
            text="Cancel Download",
            font=("Segoe UI", 8),
            bg=self.card_sec_bg,
            fg=self.sec_fg,
            bd=0,
            cursor="hand2",
            padx=12,
            pady=4,
            relief="flat",
            command=on_cancel
        )
        btn_cancel.pack(anchor="center")

        def download_worker():
            temp_dest = os.path.join(tempfile.gettempdir(), f"ArrowFlow_v{remote_ver}_update.exe")
            
            def progress_callback(downloaded, total):
                if total > 0:
                    pct = int((downloaded / total) * 100)
                    dl_mb = downloaded / (1024 * 1024)
                    tot_mb = total / (1024 * 1024)
                    status_str = f"Downloading: {dl_mb:.1f} MB / {tot_mb:.1f} MB"
                else:
                    pct = 0
                    dl_mb = downloaded / (1024 * 1024)
                    status_str = f"Downloading: {dl_mb:.1f} MB"

                def update_progress_ui():
                    if dl_dialog.winfo_exists():
                        dl_progress.config(value=pct, maximum=100)
                        lbl_dl_pct.config(text=f"{pct}%")
                        lbl_dl_status.config(text=status_str)

                if self.root.winfo_exists():
                    self.root.after(0, update_progress_ui)

            try:
                success = download_file_with_progress(
                    update_info.get("download_url", ""),
                    temp_dest,
                    progress_callback=progress_callback,
                    cancel_event=cancel_event
                )
                
                if not success or cancel_event.is_set():
                    if os.path.exists(temp_dest):
                        try: os.unlink(temp_dest)
                        except Exception: pass
                    return

                # SHA-256 Verification Step
                expected_sha256 = update_info.get("sha256", "").strip().lower()
                
                if expected_sha256:
                    def update_verifying_ui():
                        if dl_dialog.winfo_exists():
                            lbl_dl_status.config(text="Verifying SHA-256 checksum integrity...")
                    self.root.after(0, update_verifying_ui)
                    
                    calculated_sha256 = calculate_sha256(temp_dest)
                    
                    if calculated_sha256 != expected_sha256:
                        # Checksum verification failed - delete payload & abort
                        if os.path.exists(temp_dest):
                            try: os.unlink(temp_dest)
                            except Exception: pass
                        
                        def handle_sha_failure():
                            if dl_dialog.winfo_exists():
                                dl_dialog.destroy()
                            messagebox.showerror(
                                "Security Error",
                                f"SHA-256 Checksum Verification Failed!\n\n"
                                f"Expected:   {expected_sha256}\n"
                                f"Calculated: {calculated_sha256}\n\n"
                                "The downloaded file was discarded to protect your system."
                            )
                        self.root.after(0, handle_sha_failure)
                        return

                # Download & checksum verification succeeded - proceed to replacement!
                def handle_installation():
                    if dl_dialog.winfo_exists():
                        dl_dialog.destroy()
                    launch_updater_and_exit(
                        temp_dest,
                        controller=self.controller,
                        esc_listener=self.esc_listener
                    )

                self.root.after(0, handle_installation)

            except Exception as ex:
                if os.path.exists(temp_dest):
                    try: os.unlink(temp_dest)
                    except Exception: pass
                
                def handle_dl_error():
                    if dl_dialog.winfo_exists():
                        dl_dialog.destroy()
                    messagebox.showerror(
                        "Update Failed",
                        f"Failed to download ArrowFlow update:\n{str(ex)}\n\n"
                        "Your current version of ArrowFlow remains untouched."
                    )
                self.root.after(0, handle_dl_error)

        t = threading.Thread(target=download_worker, daemon=True)
        t.start()

    def on_closing(self):
        self.esc_listener.stop()
        self.controller.stop()
        self.root.destroy()
