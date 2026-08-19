@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo Building ArrowFlow.exe with PyInstaller
echo ========================================================

set "PY_CMD="

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
) else if exist "%PROGRAMFILES%\Python312\python.exe" (
    set "PY_CMD=%PROGRAMFILES%\Python312\python.exe"
) else (
    where python >nul 2>&1
    if !errorlevel!==0 (
        set "PY_CMD=python"
    ) else (
        set "PY_CMD=py"
    )
)

echo Using Python executable: !PY_CMD!
echo.

echo Installing requirements...
"!PY_CMD!" -m pip install -r requirements.txt

echo.
echo Compiling executable...
"!PY_CMD!" -m PyInstaller --noconfirm --onefile --windowed --name "ArrowFlow" --icon "arrowflow.ico" --add-data "arrowflow.ico;." --collect-all pynput main.py

if exist "dist\ArrowFlow.exe" (
    echo.
    echo ========================================================
    echo BUILD SUCCESSFUL!
    echo Executable created at: dist\ArrowFlow.exe
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo BUILD FAILED! Check console output above for details.
    echo ========================================================
)
pause
