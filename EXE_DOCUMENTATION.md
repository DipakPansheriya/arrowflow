# ArrowFlow Executable Documentation (Python)

A concise quick-start and technical documentation guide for building, running, and managing **`ArrowFlow.exe`** (built with Python & PyInstaller).

---

## 📌 1. Project Overview

**ArrowFlow** is a cross-platform desktop automation utility written in Python (Tkinter) and compiled into a standalone Windows executable (`ArrowFlow.exe`).

- **Version**: `1.0.0`
- **Default Credentials**: Username/Email: `admin` or `admin@arrowflow.com` | Password: `arrowflow`
- **Primary Tech Stack**: Python 3.11+, Tkinter, PyInstaller, `pyotp`, `pynput`, `pywin32`

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

## 🛠️ 3. Building Executables (`ArrowFlow.exe` & `ArrowFlowUpdater.exe`)

### Option A: Using the Automatic Build Script (Recommended)
Double-click [`build.bat`](file:///c:/Users/Admin/Desktop/arrowflow/build.bat) or run from terminal:
```cmd
build.bat
```

### Option B: Using PyInstaller Spec Files
```cmd
pyinstaller ArrowFlow.spec
pyinstaller ArrowFlowUpdater.spec
```

> 📦 **Output Executables**:
> - Main App: `dist/ArrowFlow.exe`
> - Auto-Updater: `dist/ArrowFlowUpdater.exe`

---

## 🔑 4. Core Features & Controls

| Feature | Key / Action | Description |
| :--- | :--- | :--- |
| **Authenticator 2FA** | TOTP / OTP Code | 2-Step Login (`Username/Password` → `Authenticator OTP`) |
| **Global Toggle** | `ESC` Key | Toggles automation ON / OFF globally from any app |
| **Stealth Mode** | `ALT + SPACE` | Hides/shows the application window & taskbar button |
| **Targeting** | Dropdown Menu | Select specific active Visual Studio Code window |
| **Auto Updater** | Background / Standalone | Automatic background update check with SHA-256 verification |

---

## 📁 5. Architecture & File Structure

| File | Purpose |
| :--- | :--- |
| [`main.py`](file:///c:/Users/Admin/Desktop/arrowflow/main.py) | Main entry point for Python interpreter & EXE bootloader. |
| [`gui.py`](file:///c:/Users/Admin/Desktop/arrowflow/gui.py) | Modern dark-themed Tkinter GUI, TOTP 2FA UI, update dialogs. |
| [`auth/`](file:///c:/Users/Admin/Desktop/arrowflow/auth/) | Authenticator 2FA, TOTP manager, and Super Admin enrollment services. |
| [`automation_engine.py`](file:///c:/Users/Admin/Desktop/arrowflow/automation_engine.py) | Background thread for random arrow key and mouse click simulation. |
| [`window_helper.py`](file:///c:/Users/Admin/Desktop/arrowflow/window_helper.py) | Detects active VS Code windows and sends targeted inputs. |
| [`global_listener.py`](file:///c:/Users/Admin/Desktop/arrowflow/global_listener.py) | `pynput` global key hooks for `ESC` and `ALT + SPACE`. |
| [`version.py`](file:///c:/Users/Admin/Desktop/arrowflow/version.py) | System version info (`1.0.0`) and semantic version parser. |
| [`update_checker.py`](file:///c:/Users/Admin/Desktop/arrowflow/update_checker.py) | Checks remote update manifest URL for newer releases. |
| [`updater.py`](file:///c:/Users/Admin/Desktop/arrowflow/updater.py) | Launches background updater executable during updates. |
| [`updater_main.py`](file:///c:/Users/Admin/Desktop/arrowflow/updater_main.py) | Standalone process for `ArrowFlowUpdater.exe`. |
| [`ArrowFlow.spec`](file:///c:/Users/Admin/Desktop/arrowflow/ArrowFlow.spec) | PyInstaller build spec for `ArrowFlow.exe`. |
| [`ArrowFlowUpdater.spec`](file:///c:/Users/Admin/Desktop/arrowflow/ArrowFlowUpdater.spec) | PyInstaller build spec for `ArrowFlowUpdater.exe`. |
| [`build.bat`](file:///c:/Users/Admin/Desktop/arrowflow/build.bat) | One-click Windows build batch script. |

