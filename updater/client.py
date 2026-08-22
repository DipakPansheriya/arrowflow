"""
Update client module for ArrowFlow application.
Handles background update checking, secure downloading to staging directory, SHA-256 verification, and launching the updater process.
"""

import os
import sys
import tempfile
import threading
import subprocess
import requests
from typing import Optional, Tuple, Callable

from version import CURRENT_VERSION, is_newer_version
from .manifest import UpdateManifest
from .verifier import verify_sha256, verify_authenticode_signature

DEFAULT_MANIFEST_URL = "https://raw.githubusercontent.com/DipakPansheriya/arrowflow/main/latest.json"
FALLBACK_MANIFEST_URL = "https://github.com/DipakPansheriya/arrowflow/releases/latest/download/latest.json"


def get_updates_dir() -> str:
    """
    Returns directory path for storing staging files and update artifacts.
    On Windows: %LOCALAPPDATA%\\ArrowFlow\\updates
    Fallback: tempdir/ArrowFlow_updates
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base_dir = os.path.join(local_app_data, "ArrowFlow", "updates")
    else:
        base_dir = os.path.join(tempfile.gettempdir(), "ArrowFlow_updates")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def get_staging_dir() -> str:
    """
    Returns path to staging directory for downloaded binaries.
    """
    staging_dir = os.path.join(get_updates_dir(), "staging")
    os.makedirs(staging_dir, exist_ok=True)
    return staging_dir


class UpdateClient:
    def __init__(self, manifest_url: str = DEFAULT_MANIFEST_URL):
        self.manifest_url = manifest_url
        self.current_version = CURRENT_VERSION
        self.latest_manifest: Optional[UpdateManifest] = None

    def check_for_updates(self, timeout: int = 8) -> Tuple[bool, Optional[UpdateManifest], Optional[str]]:
        """
        Synchronously checks if an update is available.
        Returns (is_available, manifest, error_message).
        """
        urls_to_try = [self.manifest_url, FALLBACK_MANIFEST_URL]
        last_error = None

        for url in urls_to_try:
            try:
                response = requests.get(url, timeout=timeout, headers={"User-Agent": f"ArrowFlow/{self.current_version}"})
                if response.status_code == 200:
                    manifest = UpdateManifest.from_json(response.text)
                    self.latest_manifest = manifest
                    if is_newer_version(self.current_version, manifest.version):
                        return True, manifest, None
                    else:
                        return False, manifest, None
                else:
                    last_error = f"HTTP {response.status_code} fetching update manifest from {url}"
            except Exception as e:
                last_error = str(e)

        return False, None, last_error or "Failed to connect to update server."

    def check_for_updates_async(self, callback: Callable[[bool, Optional[UpdateManifest], Optional[str]], None]):
        """
        Runs check_for_updates in a background thread and invokes callback(is_avail, manifest, err).
        """
        def worker():
            is_avail, manifest, err = self.check_for_updates()
            callback(is_avail, manifest, err)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def download_update(
        self,
        manifest: UpdateManifest,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        cancel_event: Optional[threading.Event] = None
    ) -> str:
        """
        Downloads main app executable specified in manifest to staging directory.
        Verifies SHA-256 hash. Returns path to staged executable.
        Raises ValueError or Exception on failure or hash mismatch.
        """
        staging_dir = get_staging_dir()
        staged_exe_path = os.path.join(staging_dir, "ArrowFlow_staged.exe")

        # Clean up existing staged file if present
        if os.path.exists(staged_exe_path):
            try:
                os.remove(staged_exe_path)
            except Exception:
                pass

        response = requests.get(manifest.url, stream=True, timeout=30, headers={"User-Agent": f"ArrowFlow/{self.current_version}"})
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded_size = 0

        with open(staged_exe_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):
                if cancel_event and cancel_event.is_set():
                    f.close()
                    if os.path.exists(staged_exe_path):
                        os.remove(staged_exe_path)
                    raise InterruptedError("Download cancelled by user.")
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded_size, total_size)

        # Verify SHA-256 hash checksum
        if not verify_sha256(staged_exe_path, manifest.sha256):
            if os.path.exists(staged_exe_path):
                os.remove(staged_exe_path)
            raise ValueError(f"Integrity check failed: SHA-256 hash does not match manifest!")

        # Download updater binary if specified in manifest and missing locally
        if manifest.updater_url:
            staged_updater_path = os.path.join(staging_dir, "ArrowFlowUpdater.exe")
            try:
                u_resp = requests.get(manifest.updater_url, timeout=15)
                if u_resp.status_code == 200:
                    with open(staged_updater_path, "wb") as uf:
                        uf.write(u_resp.content)
                    if manifest.updater_sha256:
                        verify_sha256(staged_updater_path, manifest.updater_sha256)
            except Exception:
                # Non-fatal if local updater binary exists
                pass

        return staged_exe_path

    @staticmethod
    def find_updater_executable() -> Optional[str]:
        """
        Locates the standalone ArrowFlowUpdater.exe binary.
        Checks application directory, current working directory, and staging directory.
        """
        candidates = []
        if getattr(sys, "frozen", False):
            app_dir = os.path.dirname(sys.executable)
            candidates.append(os.path.join(app_dir, "ArrowFlowUpdater.exe"))

        candidates.append(os.path.join(os.getcwd(), "ArrowFlowUpdater.exe"))
        candidates.append(os.path.join(os.getcwd(), "dist", "ArrowFlowUpdater.exe"))
        candidates.append(os.path.join(get_staging_dir(), "ArrowFlowUpdater.exe"))

        for path in candidates:
            if os.path.isfile(path):
                return os.path.abspath(path)

        return None

    def launch_updater_and_exit(self, target_exe: str, staged_exe: str, version: str) -> bool:
        """
        Launches ArrowFlowUpdater.exe in a separate process and terminates current application.
        Returns False if updater executable cannot be found.
        """
        updater_exe = self.find_updater_executable()
        if not updater_exe:
            return False

        pid = os.getpid()
        cmd = [
            updater_exe,
            "--target", os.path.abspath(target_exe),
            "--stage", os.path.abspath(staged_exe),
            "--pid", str(pid),
            "--version", str(version)
        ]

        # Launch detached updater process
        if sys.platform == "win32":
            # DETACHED_PROCESS flag (0x00000008) or CREATE_NEW_CONSOLE (0x00000010)
            subprocess.Popen(cmd, creationflags=0x00000008, close_fds=True)
        else:
            subprocess.Popen(cmd, close_fds=True)

        sys.exit(0)
