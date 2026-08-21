"""
Authentication Service for ArrowFlow
Coordinates password verification, Firebase 2FA secret synchronization,
and OTP validation lifecycle.
"""

import os
import json
import base64
import hashlib
from typing import Optional, Dict, Any, Tuple
from auth.firebase_client import FirebaseClient
from auth.totp_manager import TOTPManager

class AuthService:
    # SHA-256 Hash for Admin Password: "deep@2026"
    ALLOWED_PASSWORD_HASHES = {
        "be261ef578ec540a9ce3f82c8427e75d155a34d7d49171d9d79834d5269001a3",  # deep@2026
        "16d7b5441cd65b3092ed27778f745f923689228012408b8af981f44de1958dec",  # Deep@2026
    }

    def __init__(self, firebase_client: Optional[FirebaseClient] = None):
        self.firebase = firebase_client or FirebaseClient()
        self.active_secret_key: Optional[str] = None
        self.is_new_registration: bool = False
        self.is_authenticated: bool = False
        self._local_cache_path = self._get_cache_path()

    def _get_cache_path(self) -> str:
        """Get local cache file path for resilient offline fallback."""
        app_data = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or os.path.expanduser("~")
        arrow_dir = os.path.join(app_data, "ArrowFlow")
        os.makedirs(arrow_dir, exist_ok=True)
        return os.path.join(arrow_dir, "sec_token.cache")

    def _save_local_cache(self, secret_key: str):
        """Save obfuscated local copy for persistent reuse and offline continuity."""
        try:
            payload = {
                "key": secret_key,
                "chk": hashlib.sha256(secret_key.encode("utf-8")).hexdigest()
            }
            raw = json.dumps(payload).encode("utf-8")
            b64 = base64.b64encode(raw).decode("utf-8")
            with open(self._local_cache_path, "w", encoding="utf-8") as f:
                f.write(b64)
        except Exception:
            pass

    def _load_local_cache(self) -> Optional[str]:
        """Read fallback secret key from local cache."""
        try:
            if os.path.exists(self._local_cache_path):
                with open(self._local_cache_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                raw = base64.b64decode(content.encode("utf-8")).decode("utf-8")
                data = json.loads(raw)
                key = data.get("key")
                chk = data.get("chk")
                if key and hashlib.sha256(key.encode("utf-8")).hexdigest() == chk:
                    return key
        except Exception:
            pass
        return None

    def verify_password(self, entered_password: str) -> bool:
        """Validate entered password against configured SHA-256 hashes."""
        if not entered_password:
            return False
        entered_hash = hashlib.sha256(entered_password.encode("utf-8")).hexdigest()
        return entered_hash in self.ALLOWED_PASSWORD_HASHES

    def initialize_authenticator_state(self) -> Dict[str, Any]:
        """
        Check Firebase and local storage for an existing authenticator secret key.
        - If key exists in Firebase: loads existing key, returns is_new=False.
        - If key exists in local cache: ensures Firebase is synchronized, returns is_new=False.
        - If NO key exists anywhere (first-time EXE creation/launch): generates 16-char key ONCE,
          persists to Firebase & local storage, and returns is_new=True.
        - Guarantees the key is generated ONLY ONCE and reused on all subsequent runs.
        """
        cached_secret = self._load_local_cache()

        try:
            remote_config = self.firebase.get_authenticator_config()
            
            if remote_config and remote_config.get("secret_key"):
                # 1. Key exists in Firebase -> ALWAYS reuse existing key
                self.active_secret_key = remote_config["secret_key"]
                self.is_new_registration = False
                self._save_local_cache(self.active_secret_key)
                return {
                    "is_new": False,
                    "secret_key": self.active_secret_key,
                    "config": remote_config,
                    "source": "firebase"
                }

            if cached_secret:
                # 2. Local key exists but remote was empty -> sync existing local key to Firebase
                self.active_secret_key = cached_secret
                self.is_new_registration = False
                try:
                    self.firebase.save_authenticator_config(
                        secret_key=cached_secret,
                        metadata={"restored_from_cache": True}
                    )
                except Exception:
                    pass
                return {
                    "is_new": False,
                    "secret_key": cached_secret,
                    "config": {"secret_key": cached_secret, "status": "active"},
                    "source": "cache_synced"
                }

            # 3. No key anywhere -> First-time setup: Generate key ONCE and store in Firebase & local cache
            new_secret = TOTPManager.generate_secret(length=16)
            self.firebase.save_authenticator_config(
                secret_key=new_secret,
                metadata={"initial_setup": True}
            )
            self.active_secret_key = new_secret
            self.is_new_registration = True
            self._save_local_cache(self.active_secret_key)
            return {
                "is_new": True,
                "secret_key": new_secret,
                "config": {"secret_key": new_secret, "status": "active"},
                "source": "firebase_new"
            }

        except Exception as e:
            # Network failure / offline handling
            if cached_secret:
                self.active_secret_key = cached_secret
                self.is_new_registration = False
                return {
                    "is_new": False,
                    "secret_key": cached_secret,
                    "config": {"secret_key": cached_secret, "offline": True},
                    "source": "offline_cache",
                    "warning": f"Operating in offline mode ({str(e)})"
                }
            raise RuntimeError(f"Authentication system could not connect to Firebase: {str(e)}")

    def verify_otp_code(self, otp_code: str) -> bool:
        """
        Validate entered OTP code against the active secret key.
        """
        if not self.active_secret_key:
            raise RuntimeError("Authenticator state not initialized.")

        valid = TOTPManager.verify_otp(self.active_secret_key, otp_code, valid_window=1)
        if valid:
            self.is_authenticated = True
        return valid

    def get_active_secret(self) -> Optional[str]:
        """Get the active secret key."""
        return self.active_secret_key
