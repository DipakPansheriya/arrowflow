# ArrowFlow Production-Ready Windows Auto-Updater Documentation

ArrowFlow includes a production-grade automatic update system that allows installed versions (e.g. `v1.0.0`) to automatically detect, download, verify, and update to newer releases (e.g. `v1.1.0`) without requiring manual uninstalls or website downloads.

---

## 🏗️ Update System Architecture

```
[ ArrowFlow.exe Startup ]
            ↓
(Background Thread Checks Update Manifest via HTTPS)
            ↓
  (Is Remote Version > Current Version?)
     ├── NO ──> [ Continue Normal Operation ]
     └── YES ──> [ Show Update Prompt Dialog ]
                        ↓
                 (User Clicks "Update Now")
                        ↓
                 [ Download New Executable to %TEMP%\ArrowFlowUpdate\ ]
                        ↓
                 [ Verify SHA-256 Checksum ]
                     ├── Checksum Mismatch ──> [ Discard File & Show Error ]
                     └── Checksum Verified ──> [ Launch ArrowFlowUpdater.exe ]
                                                    ↓
                                             [ ArrowFlow.exe Exits ]
                                                    ↓
                                      [ Updater Waits for Process Exit ]
                                                    ↓
                                      [ Backup ArrowFlow.exe to .bak ]
                                                    ↓
                                      [ Overwrite ArrowFlow.exe with New Binary ]
                                                    ↓
                                      [ Delete Temp Files & Relaunch ArrowFlow.exe ]
```

---

## 📡 Remote Update Manifest Format

The remote manifest is hosted over HTTPS (default: `https://arrowflow.web.app/downloads/latest.json`).

```json
{
  "version": "1.1.0",
  "download_url": "https://arrowflow.web.app/downloads/ArrowFlow-1.1.0.exe",
  "sha256": "4b684568853b06bb6d589d9796e6d1912a77918a221f7c8d9e2b109e6c4627d3",
  "mandatory": false,
  "release_notes": "Added Authenticator-App OTP 2FA and Production Auto-Updater."
}
```

### Manifest Fields
- `version` *(string, required)*: Semantic version of the latest release (e.g., `"1.1.0"`).
- `download_url` *(string, required)*: Direct HTTPS download link for `ArrowFlow.exe`.
- `sha256` *(string, required)*: Lowercase 64-character SHA-256 hash of the release binary.
- `mandatory` *(boolean)*: Set `true` if update is required.
- `release_notes` *(string)*: Markdown/text changelog displayed in update prompt.

---

## 🛡️ Security & Data Integrity Safeguards

1. **HTTPS Enforcement**: Manifest queries and binary downloads use encrypted HTTPS requests.
2. **SHA-256 Checksum Verification**: Downloaded executables are verified against the manifest SHA-256 hash before launch. Malformed or tampered downloads are automatically discarded.
3. **Data Preservation**: User authentication state and settings stored in `%APPDATA%\ArrowFlow\auth_config.json` are untouched by the updater.
4. **Rollback Capability**: The updater creates a temporary `.bak` backup copy of `ArrowFlow.exe`. If binary replacement fails, the backup is automatically restored.
5. **No Update Loops**: Semantic version comparison (`parse_version()`) prevents reinstalling identical or older versions.

---

## 📦 Building both Executables

Run [`build.bat`](file:///c:/Users/Admin/Desktop/arrowflow/build.bat) from terminal or double-click to compile both binaries:

```cmd
build.bat
```

### Generated Executables
- `dist/ArrowFlow.exe`: Main application executable.
- `dist/ArrowFlowUpdater.exe`: Standalone auto-updater executable.

---

## 🚀 Release Workflow for Developers

When publishing a new release (e.g., `v1.1.0`):

1. **Update Central Version**:
   Update `CURRENT_VERSION = "1.1.0"` in [version.py](file:///c:/Users/Admin/Desktop/arrowflow/version.py).
2. **Build Executables**:
   Execute `build.bat` to produce `dist/ArrowFlow.exe` and `dist/ArrowFlowUpdater.exe`.
3. **Calculate SHA-256 Hash**:
   Run PowerShell to compute SHA-256:
   ```powershell
   Get-FileHash -Algorithm SHA256 .\dist\ArrowFlow.exe
   ```
4. **Upload Assets**:
   Upload `ArrowFlow.exe` to hosting server / GitHub releases.
5. **Update Manifest**:
   Update `latest.json` on `https://arrowflow.web.app/downloads/latest.json` with the new version number, download URL, and SHA-256 hash.
