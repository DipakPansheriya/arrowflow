"""
ArrowFlow TOTP Authentication Module
=====================================
Handles TOTP (Time-based One-Time Password) generation, verification,
and Firebase Firestore persistence of the authenticator secret key.

Uses the Firestore REST API with Firebase Web SDK credentials (no service
account / file download required — just the API key and project ID).

Dependencies: pyotp, qrcode[pil], requests
"""

import pyotp
import qrcode
import requests
from datetime import datetime, timezone


# ── Firebase Web SDK config (from Firebase Console) ─────────────────────────
FIREBASE_API_KEY  = "AIzaSyAmhc0w2nJkKIx01oIKW3OrEnrh3AmGtCI"
FIREBASE_PROJECT  = "arrowflow-f6b65"

# Firestore document path for TOTP config
FIRESTORE_COLLECTION = "arrowflow_config"
FIRESTORE_DOCUMENT   = "totp_auth"

# Firestore REST API base URL
_FIRESTORE_BASE = (
    f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT}"
    f"/databases/(default)/documents"
)


# ── Internal helper ───────────────────────────────────────────────────────────

def _doc_url():
    """Return the full REST URL for the totp_auth document."""
    return f"{_FIRESTORE_BASE}/{FIRESTORE_COLLECTION}/{FIRESTORE_DOCUMENT}?key={FIREBASE_API_KEY}"


def _parse_string_field(doc_data, field_name):
    """Extract a stringValue from a Firestore REST document field."""
    fields = doc_data.get("fields", {})
    field = fields.get(field_name, {})
    return field.get("stringValue")


# ── Public API ────────────────────────────────────────────────────────────────

def init_firebase():
    """
    Validate connectivity to Firestore via a lightweight HTTP probe.

    This is a no-op for the REST API approach (no SDK to initialise),
    but kept for API compatibility with the GUI caller.

    Raises:
        ConnectionError: If Firestore is unreachable.
    """
    # Lightweight connectivity check — HEAD request to the Firestore root
    test_url = (
        f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT}"
        f"/databases/(default)?key={FIREBASE_API_KEY}"
    )
    try:
        resp = requests.get(test_url, timeout=10)
        if resp.status_code not in (200, 403, 404):
            raise ConnectionError(
                f"Firestore returned unexpected status {resp.status_code}:\n{resp.text}"
            )
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Cannot reach Firebase Firestore.\n"
            "Please check your internet connection."
        )
    except requests.exceptions.Timeout:
        raise ConnectionError(
            "Firebase Firestore connection timed out.\n"
            "Please check your internet connection."
        )


def get_totp_secret_from_firebase():
    """
    Check Firestore for an existing TOTP secret key.

    Returns:
        str | None: The base32 secret if it exists, otherwise None.

    Raises:
        ConnectionError: On network failure.
        RuntimeError: On unexpected Firestore API errors.
    """
    try:
        resp = requests.get(_doc_url(), timeout=10)
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Network error reading from Firebase:\n{e}")

    if resp.status_code == 404:
        return None   # Document does not exist yet

    if resp.status_code != 200:
        raise RuntimeError(
            f"Firestore GET failed (status {resp.status_code}):\n{resp.text}"
        )

    return _parse_string_field(resp.json(), "secret_key")


def generate_and_store_totp_secret():
    """
    Generate a new TOTP secret and persist it in Firestore.

    Call only after confirming no key exists via get_totp_secret_from_firebase().

    Returns:
        str: The newly generated 16-character base32 TOTP secret.

    Raises:
        ConnectionError: On network failure.
        RuntimeError: On Firestore write failure.
    """
    secret = pyotp.random_base32()   # e.g. "JBSWY3DPEHPK3PXP"

    payload = {
        "fields": {
            "secret_key": {"stringValue": secret},
            "created_at": {"stringValue": datetime.now(timezone.utc).isoformat()},
        }
    }

    # PATCH creates-or-replaces the document
    patch_url = (
        f"{_FIRESTORE_BASE}/{FIRESTORE_COLLECTION}/{FIRESTORE_DOCUMENT}"
        f"?key={FIREBASE_API_KEY}"
    )
    try:
        resp = requests.patch(patch_url, json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Network error writing to Firebase:\n{e}")

    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Firestore PATCH failed (status {resp.status_code}):\n{resp.text}"
        )

    return secret


def verify_totp(secret, otp_code):
    """
    Verify a 6-digit TOTP code against the secret key.

    Args:
        secret (str): The base32 TOTP secret.
        otp_code (str): The 6-digit code entered by the user.

    Returns:
        bool: True if valid (allows ±30 s clock drift), False otherwise.
    """
    if not otp_code or not otp_code.strip():
        return False

    totp = pyotp.TOTP(secret)
    return totp.verify(otp_code.strip(), valid_window=1)


def get_totp_provisioning_uri(secret):
    """
    Build an otpauth:// URI for scanning into an authenticator app.

    Args:
        secret (str): The base32 TOTP secret.

    Returns:
        str: The provisioning URI.
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name="Admin", issuer_name="ArrowFlow")


def generate_qr_code_image(secret):
    """
    Generate a QR code PIL Image for the TOTP provisioning URI.

    Args:
        secret (str): The base32 TOTP secret.

    Returns:
        PIL.Image.Image: QR code image styled to ArrowFlow theme.
    """
    uri = get_totp_provisioning_uri(secret)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#00D2FF", back_color="#121625")
    return img.get_image()
