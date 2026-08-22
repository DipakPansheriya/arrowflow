"""
ArrowFlow Standalone Updater & Bootstrapper Executable.
Handles out-of-process executable replacement, process termination waiting, integrity verification, safe rollback, and application restarting.
"""

import os
import sys
import time
import argparse
import shutil
import subprocess
import logging
import hashlib
from typing import Optional


def setup_updater_logging() -> logging.Logger:
    """
    Configures file and console logging for the updater application.
    """
    logger = logging.getLogger("ArrowFlowUpdater")
    logger.setLevel(logging.DEBUG)

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        log_dir = os.path.join(local_app_data, "ArrowFlow", "logs")
    else:
        log_dir = os.path.join(os.path.expanduser("~"), ".arrowflow", "logs")

    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "updater.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
        logger.addHandler(file_handler)
    except Exception:
        pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("[UPDATER] %(message)s"))
    logger.addHandler(console_handler)

    return logger


def is_process_running(pid: int) -> bool:
    """
    Checks if a process with given PID is still active on Windows.
    """
    if pid <= 0:
        return False

    if sys.platform == "win32":
        try:
            import ctypes
            PROCESS_QUERY_INFORMATION = 0x0400
            SYNCHRONIZE = 0x00100000
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | SYNCHRONIZE, False, pid)
            if not handle:
                return False
            exit_code = ctypes.c_ulong()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                STILL_ACTIVE = 259
                is_active = (exit_code.value == STILL_ACTIVE)
                kernel32.CloseHandle(handle)
                return is_active
            kernel32.CloseHandle(handle)
            return False
        except Exception:
            # Fallback using tasklist command
            try:
                cmd = f"tasklist /FI \"PID eq {pid}\" /FO CSV"
                out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
                return str(pid) in out
            except Exception:
                return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def wait_for_process_exit(pid: int, timeout_sec: float = 30.0, logger: Optional[logging.Logger] = None) -> bool:
    """
    Waits up to timeout_sec for target process PID to terminate.
    """
    if pid <= 0:
        return True

    if logger:
        logger.info(f"Waiting for target process PID {pid} to terminate (timeout {timeout_sec}s)...")

    start_time = time.time()
    while time.time() - start_time < timeout_sec:
        if not is_process_running(pid):
            if logger:
                logger.info(f"Target process PID {pid} has terminated.")
            time.sleep(0.5)  # Brief grace period for OS file lock release
            return True
        time.sleep(0.5)

    if logger:
        logger.warning(f"Target process PID {pid} did not exit within {timeout_sec}s timeout.")
    return False


def calculate_file_sha256(file_path: str) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest().lower()


def run_updater(target_exe: str, staged_exe: str, pid: int, target_version: str) -> int:
    logger = setup_updater_logging()
    logger.info("========================================================")
    logger.info(f"ArrowFlow Updater starting - Version: {target_version}")
    logger.info(f"Target Executable: {target_exe}")
    logger.info(f"Staged Executable: {staged_exe}")
    logger.info(f"Target Process PID: {pid}")
    logger.info("========================================================")

    # Step 1: Validate input parameters
    if not target_exe or not staged_exe:
        logger.error("Missing required arguments --target or --stage.")
        return 1

    target_exe = os.path.abspath(target_exe)
    staged_exe = os.path.abspath(staged_exe)

    if not os.path.exists(staged_exe):
        logger.error(f"Staged executable not found at: {staged_exe}")
        return 1

    staged_hash = calculate_file_sha256(staged_exe)
    logger.info(f"Staged payload SHA-256: {staged_hash}")

    # Step 2: Wait for running application process to terminate
    if pid > 0:
        exited = wait_for_process_exit(pid, timeout_sec=25.0, logger=logger)
        if not exited:
            logger.warning("Attempting force terminate of target process...")
            try:
                if sys.platform == "win32":
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"Failed to terminate PID {pid}: {e}")

    # Step 3: Create backup of active application binary
    backup_exe = target_exe + ".bak"
    if os.path.exists(target_exe):
        try:
            if os.path.exists(backup_exe):
                os.remove(backup_exe)
            shutil.copy2(target_exe, backup_exe)
            logger.info(f"Created backup binary at: {backup_exe}")
        except Exception as e:
            logger.error(f"Failed to create backup binary: {e}")
            # Non-fatal if target_exe was missing (first install)

    # Step 4: Perform replacement (Copy staged EXE -> Target EXE)
    success = False
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Copying staged payload to target (Attempt {attempt}/{max_retries})...")
            shutil.copy2(staged_exe, target_exe)
            success = True
            break
        except Exception as e:
            logger.warning(f"File copy attempt {attempt} failed: {e}")
            time.sleep(1.0)

    # Step 5: Verify installation integrity
    if success and os.path.exists(target_exe):
        installed_hash = calculate_file_sha256(target_exe)
        if installed_hash == staged_hash:
            logger.info("Installation verified successfully! SHA-256 checksum matches.")
            # Remove staging file and backup
            try:
                os.remove(staged_exe)
            except Exception:
                pass
            try:
                os.remove(backup_exe)
            except Exception:
                pass

            # Step 6: Launch new application
            logger.info(f"Launching updated ArrowFlow executable: {target_exe}")
            try:
                subprocess.Popen([target_exe], close_fds=True)
            except Exception as e:
                logger.error(f"Failed to launch updated binary: {e}")
            return 0
        else:
            logger.error(f"SHA-256 mismatch after copy! Staged: {staged_hash}, Installed: {installed_hash}")
            success = False

    # Step 7: Rollback if installation failed
    logger.error("Installation failed! Executing automatic rollback...")
    if os.path.exists(backup_exe):
        try:
            if os.path.exists(target_exe):
                os.remove(target_exe)
            shutil.copy2(backup_exe, target_exe)
            logger.info("Rollback successful! Restored original application binary.")
            # Launch restored application
            try:
                subprocess.Popen([target_exe], close_fds=True)
            except Exception as e:
                logger.error(f"Failed to restart original binary: {e}")
        except Exception as e:
            logger.critical(f"Rollback failed! Critical error restoring backup: {e}")
            return 1
    else:
        logger.error("No backup binary available to perform rollback.")
        return 1

    return 1


def main():
    parser = argparse.ArgumentParser(description="ArrowFlow Standalone Updater & Bootstrapper")
    parser.add_argument("--target", required=True, help="Path to main target ArrowFlow.exe")
    parser.add_argument("--stage", required=True, help="Path to downloaded staged ArrowFlow.exe")
    parser.add_argument("--pid", type=int, default=0, help="PID of running ArrowFlow.exe process to wait for")
    parser.add_argument("--version", default="latest", help="Target version string")

    args = parser.parse_args()
    ret_code = run_updater(args.target, args.stage, args.pid, args.version)
    sys.exit(ret_code)


if __name__ == "__main__":
    main()
