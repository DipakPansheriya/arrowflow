"""
Central source of truth for ArrowFlow application version and update configuration.
"""

import os

CURRENT_VERSION = "1.0.0"

# Default HTTPS URL for the update manifest.
UPDATE_MANIFEST_URL = "https://raw.githubusercontent.com/arrowflow/arrowflow-desktop/main/latest.json"

def get_update_manifest_url() -> str:
    """
    Resolves the update manifest URL.
    Order of precedence:
    1. ARROWFLOW_UPDATE_URL environment variable if set.
    2. 'update_url.txt' file located in the same directory as the executable.
    3. Default UPDATE_MANIFEST_URL.
    """
    env_url = os.environ.get("ARROWFLOW_UPDATE_URL")
    if env_url and env_url.strip():
        return env_url.strip()

    try:
        import sys
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        
        url_file = os.path.join(exe_dir, "update_url.txt")
        if os.path.exists(url_file):
            with open(url_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
    except Exception:
        pass

    return UPDATE_MANIFEST_URL

def parse_version(v_str: str):
    """
    Parse a version string like '1.0.0', 'v1.2.3', or '1.10.0' into a comparable tuple of ints.
    Non-digit suffixes are safely ignored or handled.
    """
    if not v_str:
        return (0, 0, 0)
    
    # Strip leading 'v' or spaces if present
    v_clean = str(v_str).strip().lstrip('v').lstrip('V')
    
    parts = []
    for part in v_clean.split('.'):
        # Extract numeric prefix from each part (e.g. '0-beta' -> 0)
        num_str = ""
        for char in part:
            if char.isdigit():
                num_str += char
            else:
                break
        parts.append(int(num_str) if num_str else 0)
    
    return tuple(parts)

def is_newer_version(current_ver: str, remote_ver: str) -> bool:
    """
    Returns True if remote_ver is strictly greater than current_ver using semantic comparison.
    Example:
      1.1.0 > 1.0.0 -> True
      1.10.0 > 1.9.0 -> True
      1.0.0 > 1.0.0 -> False
    """
    try:
        return parse_version(remote_ver) > parse_version(current_ver)
    except Exception:
        return False
