# ArrowFlow Executable Documentation (Python)

A concise quick-start and technical documentation guide for building, running, and managing **`ArrowFlow.exe`** (built with Python & PyInstaller).

---

## 📌 1. Project Overview

**ArrowFlow** is a cross-platform desktop automation utility written in Python (Tkinter) and compiled into a standalone Windows executable (`ArrowFlow.exe`).

- **Version**: `1.0.0`
- **Default Lock Password**: ``
- **Primary Tech Stack**: Python 3.11+, Tkinter, PyInstaller, `pynput`, `pywin32`

---

## 🚀 2. Quick Start: Running from Python Source

### Prerequisites
Make sure Python 3.11 or higher is installed and added to your system `PATH`.

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Launch Application
```bash
python main.py
```

---

## 🛠️ 3. Building `ArrowFlow.exe`

### Option A: Using the Automatic Build Script (Recommended)
Double-click [`build.bat`](file:///c:/Users/Admin/Desktop/arrowflow/build.bat) or run from terminal:
```cmd
build.bat
```

### Option B: Using PyInstaller Spec File
```cmd
pyinstaller ArrowFlow.spec
```

### Option C: Direct PyInstaller Command
```cmd
pyinstaller --noconfirm --onefile --windowed --name "ArrowFlow" --icon "arrowflow.ico" --add-data "arrowflow.ico;." --collect-all pynput main.py
```

> 📦 **Output File Location**: `dist/ArrowFlow.exe`

---

## 🔑 4. Core Features & Controls

| Feature | Key / Action | Description |
| :--- | :--- | :--- |
| **Password Authentication** | Password Input | Unlocks the main control panel (Default: ``) |
| **Global Toggle** | `ESC` Key | Toggles automation ON / OFF globally from any app |
| **Stealth Mode** | `ALT + SPACE` | Hides/shows the application window & taskbar button |
| **Targeting** | Dropdown Menu | Select specific active Visual Studio Code window |
| **Auto Updater** | Background / Manual | Checks remote JSON manifest for new versions |

---

## 📁 5. Architecture & File Structure

| File | Purpose |
| :--- | :--- |
| [`main.py`](file:///c:/Users/Admin/Desktop/arrowflow/main.py) | Main entry point for Python interpreter & EXE bootloader. |
| [`gui.py`](file:///c:/Users/Admin/Desktop/arrowflow/gui.py) | Modern dark-themed Tkinter GUI, password lock screen, and stats UI. |
| [`automation_engine.py`](file:///c:/Users/Admin/Desktop/arrowflow/automation_engine.py) | Background thread for random arrow key and mouse click simulation. |
| [`window_helper.py`](file:///c:/Users/Admin/Desktop/arrowflow/window_helper.py) | Detects active VS Code windows and sends targeted inputs. |
| [`global_listener.py`](file:///c:/Users/Admin/Desktop/arrowflow/global_listener.py) | `pynput` global key hooks for `ESC` and `ALT + SPACE`. |
| [`version.py`](file:///c:/Users/Admin/Desktop/arrowflow/version.py) | System version info (`1.0.0`) and update configuration handler. |
| [`update_checker.py`](file:///c:/Users/Admin/Desktop/arrowflow/update_checker.py) | Checks remote update manifest URL for newer releases. |
| [`updater.py`](file:///c:/Users/Admin/Desktop/arrowflow/updater.py) | Downloads and replaces executable during version updates. |
| [`ArrowFlow.spec`](file:///c:/Users/Admin/Desktop/arrowflow/ArrowFlow.spec) | PyInstaller build specification file. |
| [`build.bat`](file:///c:/Users/Admin/Desktop/arrowflow/build.bat) | One-click Windows build batch script. |
