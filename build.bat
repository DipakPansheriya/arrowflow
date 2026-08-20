@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo Building ArrowFlow.exe and ArrowFlowUpdater.exe
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
echo Compiling ArrowFlow.exe...
"!PY_CMD!" -m PyInstaller --noconfirm ArrowFlow.spec

echo.
echo Compiling ArrowFlowUpdater.exe...
"!PY_CMD!" -m PyInstaller --noconfirm ArrowFlowUpdater.spec

if exist "dist\ArrowFlow.exe" if exist "dist\ArrowFlowUpdater.exe" (
    echo.
    echo ========================================================
    echo BUILD SUCCESSFUL!
    echo Main App:   dist\ArrowFlow.exe
    echo Updater:    dist\ArrowFlowUpdater.exe
    echo ========================================================
    goto end
)

echo.
echo ========================================================
echo BUILD FAILED! Check console output above for details.
echo ========================================================

:end
pause
