import os
import sys
import tempfile
import subprocess

def is_frozen() -> bool:
    """Check if application is running as a compiled PyInstaller executable."""
    return getattr(sys, 'frozen', False)

def get_current_exe_path() -> str:
    """Return the absolute path of the currently running executable or main script."""
    if is_frozen():
        return os.path.abspath(sys.executable)
    else:
        return os.path.abspath(sys.argv[0])

def launch_updater_and_exit(new_exe_path: str, controller=None, esc_listener=None):
    """
    Safely stops active automation and global listeners, creates a detached background updater batch script,
    and terminates current process so Windows file locks on current executable are released.
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
    exe_name = os.path.basename(current_exe)
    backup_exe = os.path.join(target_dir, f"{exe_name}.bak")

    # Create temporary updater script path
    temp_dir = tempfile.gettempdir()
    updater_bat = os.path.join(temp_dir, "arrowflow_updater.bat")

    # Construct robust Windows batch script content
    # Handles PID exit wait, backup creation, EXE replacement, permission error fallback, cleanup, and restart.
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
    powershell -Command "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms]::MessageBox::Show('ArrowFlow could not complete the update because Windows permissions prevented the update.', 'ArrowFlow Update Error', 'OK', 'Error')" >nul 2>&1
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

    # Launch batch script in detached background mode (no visible CMD window)
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW

    subprocess.Popen(["cmd.exe", "/c", updater_bat], creationflags=creationflags, close_fds=True)

    # Clean exit current process
    sys.exit(0)
