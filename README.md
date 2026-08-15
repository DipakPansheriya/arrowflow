# ArrowFlow ⭐ (Cross-Platform Windows & macOS)

A lightweight, background-compatible desktop utility designed for generating randomized Arrow-Key (`Up`, `Down`, `Left`, `Right`) and Mouse input actions targeted at active Visual Studio Code projects, featuring dynamic per-minute random target generation, password security, decoupled event scheduling, and real-time live statistics.

---

## 🌟 Key Features

- **💻 Cross-Platform Support**: Native binaries for **Windows** (`ArrowFlow.exe`) and **macOS** (`ArrowFlow.app` / `ArrowFlow.dmg`).
- **🎨 Modern Developer Dark Theme**: Premium UI palette (`#181825` background, `#121625` cards, `#00D2FF` blue accent, `#00E5A3` success green).
- **🎯 Specific VS Code Target Selection**: Select a target VS Code window from the dropdown list.
- **🛡️ Focus Safety & Decoupled Events**: Independently schedules keyboard arrow press events and mouse clicks with collision separation ($\ge 0.10\text{s}$).
- **🔐 Password Lock Screen**: Protects application startup with secure SHA-256 authentication (`Deep@2026`).
- **🎲 Custom Range (Min to Max)**: Generates a new random target between your specified Minimum and Maximum presses at the start of every 60-second window.
- **⚡ Global ESC Toggle**: Pressing `ESC` anywhere on Windows or macOS toggles automation ON/OFF instantly.
- **🪟 Taskbar & Window Toggle**: Pressing `ALT + SPACE` toggles window and taskbar button visibility.
- **📦 Portable Release Packages**: Standalone executable on Windows (`dist/ArrowFlow.exe`) and DMG disk image on macOS (`dist/ArrowFlow.dmg`).

---

## 🔒 Security & Password Lock

The application launches into a secure Password Lock Screen before revealing the main controls:

- **Default Password**: `Deep@2026`
- **Security Standard**: Verified via SHA-256 hashing to prevent plaintext exposure.

---

## 🍏 macOS Permissions Guide

macOS requires specific user privacy permissions for global keyboard hooks (`ESC` key) and window targeting:

1. **Accessibility Permission**:
   - Open **System Settings** > **Privacy & Security** > **Accessibility**.
   - Enable the toggle for **ArrowFlow.app** (or terminal app when running from source).
2. **Input Monitoring Permission** *(if prompted)*:
   - Open **System Settings** > **Privacy & Security** > **Input Monitoring**.
   - Enable **ArrowFlow.app**.

---

## 🚀 How to Build & Package

### Windows Build (`ArrowFlow.exe`)
Double-click `build.bat` or run in CMD / PowerShell:
```cmd
build.bat
```
*Output generated at:* `dist/ArrowFlow.exe`

### macOS Build (`ArrowFlow.app` & `ArrowFlow.dmg`)
Run the macOS build shell script:
```bash
chmod +x build_macos.sh
./build_macos.sh
```
*Output generated at:*
- App Bundle: `dist/ArrowFlow.app`
- Disk Image: `dist/ArrowFlow.dmg`

---

## 🌐 Angular Landing Page Deployment

The landing page automatically detects the user's OS (`Windows` vs `macOS`) and serves the appropriate direct download asset:

- **Configuration File**: [`website/src/app/config/app-config.ts`](file:///c:/Users/Admin/Desktop/Automation/website/src/app/config/app-config.ts)
  ```typescript
  export const APP_CONFIG = {
    windowsDownloadUrl: 'https://github.com/USERNAME/REPO/releases/download/v1.0.0/ArrowFlow.exe',
    macosDownloadUrl: 'https://github.com/USERNAME/REPO/releases/download/v1.0.0/ArrowFlow.dmg'
  };
  ```

### Build Landing Page Production Bundle
```bash
cd website
npm run build
```
*Output location:* `website/dist/website`
