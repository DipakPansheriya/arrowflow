import os
import sys
import tempfile
import subprocess

def is_frozen() -> bool:
    """Check if application is running as a compiled PyInstaller executable."""
    return getattr(sys, 'frozen', False)

def get_current_exe_path() -> str:
    """Return the absolute path of the currently running executable or target binary."""
    if is_frozen():
        return os.path.abspath(sys.executable)
    else:
        # Development / script mode: Target ArrowFlow.exe in workspace or dist
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        dist_exe = os.path.join(script_dir, "dist", "ArrowFlow.exe")
        if os.path.exists(dist_exe):
            return dist_exe
        root_exe = os.path.join(script_dir, "ArrowFlow.exe")
        if os.path.exists(root_exe):
            return root_exe
        return os.path.join(script_dir, "ArrowFlow.exe")


def launch_updater_and_exit(new_exe_path: str, controller=None, esc_listener=None):
    """
    Safely stops active automation and global listeners, launches the standalone ArrowFlowUpdater executable
    (or background script fallback), and terminates the current process so file locks are released.
    """
    # 1. Safely stop active keyboard/mouse automation and listeners
    if controller and hasattr(controller, 'stop'):
        try:
            controller.stop()
        except Exception:
            pass

    if esc_listener and hasattr(esc_listener, 'stop'):
        try:
            esc_listener.stop()
        except Exception:
            pass

    current_exe = get_current_exe_path()
    current_pid = os.getpid()
    target_dir = os.path.dirname(current_exe)

    # Check for standalone ArrowFlowUpdater executable
    updater_exe = os.path.join(target_dir, "ArrowFlowUpdater.exe")
    updater_script = os.path.join(target_dir, "updater_main.py")

    if sys.platform == "win32":
        if os.path.exists(updater_exe):
            cmd = [updater_exe, "--pid", str(current_pid), "--new-exe", new_exe_path, "--target-exe", current_exe]
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
            subprocess.Popen(cmd, creationflags=creationflags, close_fds=True)
            sys.exit(0)
        elif os.path.exists(updater_script) and not is_frozen():
            cmd = [sys.executable, updater_script, "--pid", str(current_pid), "--new-exe", new_exe_path, "--target-exe", current_exe]
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
            subprocess.Popen(cmd, creationflags=creationflags, close_fds=True)
            sys.exit(0)
        else:
            # Legacy batch script fallback
            exe_name = os.path.basename(current_exe)
            backup_exe = os.path.join(target_dir, f"{exe_name}.bak")
            temp_dir = tempfile.gettempdir()
            updater_bat = os.path.join(temp_dir, "arrowflow_updater.bat")

            bat_content = f"""@echo off
set "PID={current_pid}"
set "NEW_EXE={new_exe_path}"
set "TARGET_EXE={current_exe}"
set "BACKUP_EXE={backup_exe}"

:wait_loop
tasklist /FI "PID eq %PID%" 2>NUL | find /I "%PID%" >NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak >nul
    goto wait_loop
)

timeout /t 1 /nobreak >nul

rem Create backup of existing executable
copy /y "%TARGET_EXE%" "%BACKUP_EXE%" >nul 2>&1

rem Overwrite target executable with downloaded new version
copy /y "%NEW_EXE%" "%TARGET_EXE%" >nul 2>&1
if errorlevel 1 (
    rem Replacement failed due to permissions or lock - restore backup
    if exist "%BACKUP_EXE%" copy /y "%BACKUP_EXE%" "%TARGET_EXE%" >nul 2>&1
    if exist "%NEW_EXE%" del /f /q "%NEW_EXE%" >nul 2>&1
    if exist "%BACKUP_EXE%" del /f /q "%BACKUP_EXE%" >nul 2>&1
    del "%~f0" & exit /b 1
)

rem Cleanup backup and downloaded temp files
if exist "%BACKUP_EXE%" del /f /q "%BACKUP_EXE%" >nul 2>&1
if exist "%NEW_EXE%" del /f /q "%NEW_EXE%" >nul 2>&1

rem Relaunch updated ArrowFlow executable
start "" "%TARGET_EXE%"

rem Self delete updater script
del "%~f0"
"""
            with open(updater_bat, "w", encoding="utf-8") as f:
                f.write(bat_content)

            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
            subprocess.Popen(["cmd.exe", "/c", updater_bat], creationflags=creationflags, close_fds=True)
            sys.exit(0)

    elif sys.platform == "darwin":
        temp_dir = tempfile.gettempdir()
        updater_sh = os.path.join(temp_dir, "arrowflow_updater.sh")

        sh_content = f"""#!/bin/bash
PID={current_pid}
NEW_FILE="{new_exe_path}"
TARGET_FILE="{current_exe}"

while kill -0 $PID 2>/dev/null; do
    sleep 0.5
done

sleep 0.5

if [ -f "$NEW_FILE" ]; then
    cp -f "$NEW_FILE" "$TARGET_FILE" 2>/dev/null || cp -R -f "$NEW_FILE" "$TARGET_FILE" 2>/dev/null
    rm -rf "$NEW_FILE"
fi

open "$TARGET_FILE"
rm -f "$0"
"""
        with open(updater_sh, "w", encoding="utf-8") as f:
            f.write(sh_content)

        os.chmod(updater_sh, 0o755)
        subprocess.Popen(["/bin/bash", updater_sh], close_fds=True)
        sys.exit(0)

    else:
        sys.exit(0)
