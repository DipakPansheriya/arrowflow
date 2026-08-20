"""
ArrowFlow Standalone Updater Entrypoint (ArrowFlowUpdater.exe)
Executes process monitoring, binary replacement with rollback protection,
and automatic relaunch of updated ArrowFlow application.
"""

import os
import sys
import time
import shutil
import argparse
import subprocess

def is_process_running(pid: int) -> bool:
    """Check if process with given PID is still active on Windows/macOS."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x00100000
            process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if process:
                kernel32.CloseHandle(process)
                # Double check with tasklist for accuracy
                cmd = f'tasklist /FI "PID eq {pid}"'
                output = subprocess.check_output(cmd, shell=True).decode("utf-8", errors="ignore")
                return str(pid) in output
            return False
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

def wait_for_process_exit(pid: int, timeout_sec: int = 15) -> bool:
    """Wait for process PID to exit cleanly before file replacement."""
    start_time = time.time()
    while time.time() - start_time < timeout_sec:
        if not is_process_running(pid):
            time.sleep(0.5) # Give OS half a second to release file handles
            return True
        time.sleep(0.5)
    return not is_process_running(pid)

def main():
    parser = argparse.ArgumentParser(description="ArrowFlow Standalone Auto-Updater")
    parser.add_argument("--pid", type=int, default=0, help="PID of main ArrowFlow process to wait for")
    parser.add_argument("--new-exe", type=str, required=True, help="Path to verified new executable")
    parser.add_argument("--target-exe", type=str, required=True, help="Path to target executable to replace")
    
    args = parser.parse_args()

    new_exe = os.path.abspath(args.new_exe)
    target_exe = os.path.abspath(args.target_exe)
    target_dir = os.path.dirname(target_exe)
    exe_name = os.path.basename(target_exe)
    backup_exe = os.path.join(target_dir, f"{exe_name}.bak")

    # 1. Wait for parent process PID to terminate
    if args.pid > 0:
        wait_for_process_exit(args.pid, timeout_sec=15)

    if not os.path.exists(new_exe):
        sys.exit(1)

    # 2. Create backup of current executable
    if os.path.exists(target_exe):
        try:
            shutil.copy2(target_exe, backup_exe)
        except Exception:
            pass

    # 3. Replace target executable with new executable
    replacement_success = False
    try:
        shutil.copy2(new_exe, target_exe)
        replacement_success = os.path.exists(target_exe)
    except Exception:
        replacement_success = False

    # 4. Handle replacement failure & rollback
    if not replacement_success:
        if os.path.exists(backup_exe):
            try:
                shutil.copy2(backup_exe, target_exe)
            except Exception:
                pass
        sys.exit(1)

    # 5. Cleanup backup and temporary download
    if os.path.exists(backup_exe):
        try:
            os.remove(backup_exe)
        except Exception:
            pass

    if os.path.exists(new_exe):
        try:
            os.remove(new_exe)
        except Exception:
            pass

    # 6. Relaunch updated ArrowFlow application
    try:
        if sys.platform == "win32":
            subprocess.Popen([target_exe], creationflags=subprocess.DETACHED_PROCESS)
        else:
            subprocess.Popen(["open", target_exe])
    except Exception:
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
