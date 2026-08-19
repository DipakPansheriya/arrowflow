#!/bin/bash
# =========================================================================
# ArrowFlow macOS Build & Packaging Script
# Compiles ArrowFlow.app standalone application and creates ArrowFlow.dmg
# =========================================================================

set -e

echo "========================================================"
echo "         ArrowFlow macOS Build System"
echo "========================================================"

# Step 1: Install macOS Requirements
echo "[1/4] Installing Python requirements for macOS..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Step 2: Clean previous build artifacts
echo "[2/4] Cleaning previous build folders..."
rm -rf build dist ArrowFlow_macOS.app ArrowFlow.dmg

# Step 3: Run PyInstaller macOS spec
echo "[3/4] Compiling ArrowFlow.app standalone executable..."
python -m PyInstaller --noconfirm ArrowFlow_macOS.spec

# Step 4: Package ArrowFlow.dmg
echo "[4/4] Packaging ArrowFlow.dmg distribution image..."
if [ -d "dist/ArrowFlow.app" ]; then
    cd dist
    hdiutil create -volname "ArrowFlow" -srcfolder "ArrowFlow.app" -ov -format UDZO "ArrowFlow.dmg"
    cd ..
    echo "========================================================"
    echo "BUILD SUCCESSFUL!"
    echo "Executable Bundle: dist/ArrowFlow.app"
    echo "Disk Image Asset:  dist/ArrowFlow.dmg"
    echo "========================================================"
else
    echo "ERROR: dist/ArrowFlow.app was not found."
    exit 1
fi
