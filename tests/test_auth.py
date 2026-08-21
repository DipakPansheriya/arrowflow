"""
Unit Tests for ArrowFlow 2FA Module
Tests TOTP generation, validation, QR generation, Firebase Client parsing, and AuthService lifecycle.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import pyotp
from auth.totp_manager import TOTPManager
from auth.firebase_client import FirebaseClient
from auth.auth_service import AuthService

class TestTOTPManager(unittest.TestCase):
    def test_generate_secret(self):
        secret = TOTPManager.generate_secret(16)
        self.assertEqual(len(secret), 16)
        # Verify valid base32
        totp = pyotp.TOTP(secret)
        code = totp.now()
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    def test_verify_valid_otp(self):
        secret = TOTPManager.generate_secret(16)
        code = TOTPManager.get_current_otp(secret)
        self.assertTrue(TOTPManager.verify_otp(secret, code))

    def test_verify_invalid_otp(self):
        secret = TOTPManager.generate_secret(16)
        self.assertFalse(TOTPManager.verify_otp(secret, "000000" if TOTPManager.get_current_otp(secret) != "000000" else "111111"))
        self.assertFalse(TOTPManager.verify_otp(secret, "abc"))
        self.assertFalse(TOTPManager.verify_otp(secret, ""))

    def test_provisioning_uri(self):
        secret = "JBSWY3DPEHPK3PXP"
        uri = TOTPManager.get_provisioning_uri(secret, user="admin", issuer="ArrowFlow")
        self.assertTrue(uri.startswith("otpauth://totp/ArrowFlow:admin?"))
        self.assertIn("secret=JBSWY3DPEHPK3PXP", uri)
        self.assertIn("issuer=ArrowFlow", uri)

    def test_format_secret_display(self):
        secret = "JBSWY3DPEHPK3PXP"
        formatted = TOTPManager.format_secret_display(secret)
        self.assertEqual(formatted, "JBSW Y3DP EHPK 3PXP")

    def test_qr_image_generation(self):
        secret = TOTPManager.generate_secret(16)
        pil_img = TOTPManager.generate_qr_image(secret)
        self.assertIsNotNone(pil_img)
        self.assertGreater(pil_img.width, 50)
        self.assertGreater(pil_img.height, 50)

class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.mock_firebase = MagicMock(spec=FirebaseClient)
        self.auth = AuthService(firebase_client=self.mock_firebase)
        self.test_cache_path = os.path.join(tempfile.gettempdir(), "test_auth_sec.cache")
        if os.path.exists(self.test_cache_path):
            os.remove(self.test_cache_path)
        self.auth._local_cache_path = self.test_cache_path

    def tearDown(self):
        if hasattr(self, "test_cache_path") and os.path.exists(self.test_cache_path):
            try:
                os.remove(self.test_cache_path)
            except Exception:
                pass

    def test_password_verification(self):
        self.assertTrue(self.auth.verify_password("deep@2026"))
        self.assertTrue(self.auth.verify_password("Deep@2026"))
        self.assertFalse(self.auth.verify_password("Demo@123"))
        self.assertFalse(self.auth.verify_password("wrong_password"))
        self.assertFalse(self.auth.verify_password(""))

    def test_initialize_when_secret_exists_in_firebase(self):
        existing_secret = "JBSWY3DPEHPK3PXP"
        self.mock_firebase.get_authenticator_config.return_value = {
            "secret_key": existing_secret,
            "status": "active"
        }

        result = self.auth.initialize_authenticator_state()
        self.assertFalse(result["is_new"])
        self.assertEqual(result["secret_key"], existing_secret)
        self.assertEqual(self.auth.active_secret_key, existing_secret)
        self.mock_firebase.save_authenticator_config.assert_not_called()

    def test_initialize_when_no_secret_in_firebase(self):
        self.mock_firebase.get_authenticator_config.return_value = None
        self.mock_firebase.save_authenticator_config.return_value = True

        result = self.auth.initialize_authenticator_state()
        self.assertTrue(result["is_new"])
        self.assertEqual(len(result["secret_key"]), 16)
        self.assertEqual(self.auth.active_secret_key, result["secret_key"])
        self.mock_firebase.save_authenticator_config.assert_called_once()

    def test_verify_otp_flow(self):
        secret = TOTPManager.generate_secret(16)
        self.auth.active_secret_key = secret
        valid_otp = TOTPManager.get_current_otp(secret)
        
        self.assertTrue(self.auth.verify_otp_code(valid_otp))
        self.assertTrue(self.auth.is_authenticated)

if __name__ == "__main__":
    unittest.main()
