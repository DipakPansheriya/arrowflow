import json
import hashlib
import threading
import urllib.request
import urllib.error
import ssl
import os
import sys
from version import CURRENT_VERSION, get_update_manifest_url, is_newer_version

def fetch_update_manifest(manifest_url: str = None, timeout: int = 6) -> dict:
    """
    Fetch and parse the JSON update manifest over HTTPS or local file path.
    Returns parsed dictionary or raises an exception on failure.
    """
    url = manifest_url or get_update_manifest_url()
    
    # Handle local file path or file:// URL for testing & local release channels
    if os.path.exists(url) or url.startswith("file://"):
        local_path = url.replace("file:///", "").replace("file://", "")
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)

    os_name = "macOS" if sys.platform == "darwin" else "Windows"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"ArrowFlow/{CURRENT_VERSION} ({os_name} UpdateChecker)"}
    )
    
    # Create unverified context fallback if local SSL certificates are missing/outdated
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
        if response.status == 200:
            content = response.read().decode("utf-8")
            data = json.loads(content)
            return data
        else:
            raise RuntimeError(f"HTTP error status: {response.status}")

def check_for_updates_async(callback, manifest_url: str = None):
    """
    Asynchronously checks for updates in a background daemon thread.
    Invokes callback(result_dict, error_message) on completion.
    """
    def worker():
        try:
            manifest = fetch_update_manifest(manifest_url)
            remote_ver = manifest.get("version", "")
            download_url = manifest.get("download_url", "")
            sha256_hash = manifest.get("sha256", "")
            release_notes = manifest.get("release_notes", "")
            
            update_available = is_newer_version(CURRENT_VERSION, remote_ver)
            
            result = {
                "update_available": update_available,
                "current_version": CURRENT_VERSION,
                "remote_version": remote_ver,
                "download_url": download_url,
                "sha256": sha256_hash,
                "release_notes": release_notes,
                "manifest_raw": manifest
            }
            callback(result, None)
        except Exception as e:
            callback(None, str(e))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

def calculate_sha256(filepath: str) -> str:
    """
    Compute SHA-256 hash of a file in 64KB chunks.
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest().lower()

def download_file_with_progress(download_url: str, dest_path: str, progress_callback=None, cancel_event=None) -> bool:
    """
    Downloads file from download_url to dest_path over HTTPS or local file system.
    Reports progress via progress_callback(downloaded_bytes, total_bytes).
    Returns True if downloaded successfully, False if cancelled or failed.
    """
    if os.path.exists(download_url) or download_url.startswith("file://"):
        local_src = download_url.replace("file:///", "").replace("file://", "")
        if not os.path.exists(local_src):
            raise FileNotFoundError(f"Update binary not found at: {local_src}")
        
        total_size = os.path.getsize(local_src)
        downloaded = 0
        chunk_size = 32768

        with open(local_src, "rb") as src, open(dest_path, "wb") as dst:
            while True:
                if cancel_event and cancel_event.is_set():
                    return False
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)
        return True

    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": f"ArrowFlow/{CURRENT_VERSION} (Windows Downloader)"}
    )
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 32768
        
        with open(dest_path, "wb") as out_file:
            while True:
                if cancel_event and cancel_event.is_set():
                    return False
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)
    return True
