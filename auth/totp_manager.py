"""
TOTP (Time-based One-Time Password) Manager for ArrowFlow
Implements RFC 6238 TOTP generation, validation, URI creation, and QR code rendering.
"""

import base64
import os
import pyotp
import qrcode
from PIL import Image, ImageTk
from typing import Optional, Tuple

class TOTPManager:
    DEFAULT_ISSUER = "ArrowFlow"
    DEFAULT_USER = "admin"
    SECRET_LENGTH = 16  # Standard Base32 16-character secret

    @classmethod
    def generate_secret(cls, length: int = 16) -> str:
        """
        Generate a secure Base32 secret key (16 or 32 characters) compatible with
        Google Authenticator and Microsoft Authenticator.
        """
        # 16-char Base32 = 10 bytes; 32-char Base32 = 20 bytes
        num_bytes = 10 if length == 16 else 20
        raw = os.urandom(num_bytes)
        secret = base64.b32encode(raw).decode("ascii").rstrip("=")
        return secret[:length]

    @classmethod
    def get_provisioning_uri(
        cls, 
        secret: str, 
        user: str = DEFAULT_USER, 
        issuer: str = DEFAULT_ISSUER
    ) -> str:
        """
        Create a standard otpauth:// provisioning URI for QR code scanning.
        """
        totp = pyotp.TOTP(secret, interval=30, digits=6)
        return totp.provisioning_uri(name=user, issuer_name=issuer)

    @classmethod
    def generate_qr_image(
        cls, 
        secret: str, 
        user: str = DEFAULT_USER, 
        issuer: str = DEFAULT_ISSUER,
        box_size: int = 4,
        border: int = 2
    ) -> Image.Image:
        """
        Generate a scannable PIL Image QR code for the TOTP secret.
        """
        uri = cls.get_provisioning_uri(secret, user=user, issuer=issuer)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#090C15", back_color="#FFFFFF").convert("RGB")
        return img

    @classmethod
    def generate_tk_qr_image(
        cls,
        secret: str,
        user: str = DEFAULT_USER,
        issuer: str = DEFAULT_ISSUER,
        target_size: Tuple[int, int] = (160, 160)
    ) -> ImageTk.PhotoImage:
        """
        Generate a Tkinter-compatible PhotoImage QR code resized for GUI cards.
        """
        pil_img = cls.generate_qr_image(secret, user=user, issuer=issuer)
        pil_img = pil_img.resize(target_size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(pil_img)

    @classmethod
    def verify_otp(cls, secret: str, otp_code: str, valid_window: int = 1) -> bool:
        """
        Verify a 6-digit OTP code against the secret key.
        Args:
            secret: Base32 secret key.
            otp_code: The 6-digit code entered by the user.
            valid_window: Number of 30-second steps to check before and after (default 1 = ±30s).
        Returns:
            True if valid, False otherwise.
        """
        if not secret or not otp_code:
            return False

        # Clean code
        clean_code = str(otp_code).strip().replace(" ", "").replace("-", "")
        if not clean_code.isdigit() or len(clean_code) != 6:
            return False

        try:
            totp = pyotp.TOTP(secret, interval=30, digits=6)
            return bool(totp.verify(clean_code, valid_window=valid_window))
        except Exception:
            return False

    @classmethod
    def get_current_otp(cls, secret: str) -> str:
        """
        Generate the current 6-digit OTP code (useful for diagnostics and automated testing).
        """
        totp = pyotp.TOTP(secret, interval=30, digits=6)
        return totp.now()

    @classmethod
    def format_secret_display(cls, secret: str) -> str:
        """
        Format a 16-character Base32 secret in grouped format for manual entry.
        Example: ABCD EFGH IJKL MNOP
        """
        clean = secret.strip().replace(" ", "").upper()
        chunks = [clean[i:i+4] for i in range(0, len(clean), 4)]
        return " ".join(chunks)
