"""
Integrity and security verification utilities for ArrowFlow update system.
Includes SHA-256 hash checksum calculation and Windows Authenticode code signature checks.
"""

import os
import hashlib
import subprocess
import sys
from typing import Tuple


def calculate_sha256(file_path: str, chunk_size: int = 65536) -> str:
    """
    Calculates and returns the lower-case hex SHA-256 checksum of a file.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found for hash calculation: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest().lower()


def verify_sha256(file_path: str, expected_sha256: str) -> bool:
    """
    Verifies if the file's SHA-256 matches expected_sha256 (case-insensitive).
    """
    if not expected_sha256:
        return False
    actual_hash = calculate_sha256(file_path)
    return actual_hash == str(expected_sha256).strip().lower()


def verify_authenticode_signature(file_path: str) -> Tuple[bool, str]:
    """
    Verifies the Windows Authenticode digital signature of an executable.
    Returns (True, "Valid signature") if signed by a trusted certificate.
    Returns (False, "Reason") if unsigned or untrusted.
    """
    if not os.path.isfile(file_path):
        return False, "File does not exist"

    if sys.platform != "win32":
        return True, "Non-Windows platform - signature check skipped"

    ps_command = f"(Get-AuthenticodeSignature -FilePath '{file_path}').Status.ToString()"
    try:
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_command]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=10).strip()
        if output == "Valid":
            return True, "Valid Authenticode signature"
        elif output == "NotSigned":
            return False, "Unsigned binary"
        elif output == "UnknownError" or output == "HashMismatch":
            return False, f"Invalid signature status: {output}"
        else:
            return False, f"Signature status: {output}"
    except Exception as e:
        return False, f"Signature verification error: {str(e)}"
