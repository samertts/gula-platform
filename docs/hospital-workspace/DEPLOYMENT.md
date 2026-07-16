# NHDW Deployment Guide

**National Hospital Desktop Workspace — Deployment and Installation Guide**
**Version:** 1.0.0
**Last Updated:** 2026-07-16

---

## 1. Prerequisites

### 1.1 Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Dual-core 2.0 GHz | Quad-core 3.0 GHz |
| RAM | 4 GB | 8 GB |
| Storage | 500 MB free | 2 GB free |
| Display | 1366×768 | 1920×1080 |
| Network | Internet for initial setup | Broadband (4 Mbps+) |
| Optional | Barcode scanner | RFID reader |

### 1.2 Software Requirements

| Software | Version | Notes |
|----------|---------|-------|
| Windows | 10 (64-bit) or 11 | Windows 10 Pro/Enterprise recommended |
| Python | 3.11 or 3.12 | 3.10 is NOT supported |
| PowerShell | 5.1+ | For automated installation |
| GULA Backend | 2.1.0+ | Running and accessible from the hospital network |

### 1.3 Network Requirements

- Access to the GULA backend API server (HTTPS)
- Port 443 (HTTPS) outbound to backend server
- Port 8000 (HTTP) if connecting to local/development server
- Internal DNS resolution for the backend hostname, or static IP configuration
- No inbound ports required (NHDW initiates all connections)

---

## 2. Installation

### 2.1 Standard Installation (Windows Executable)

1. **Download the installer** from the GULA platform releases page or provided distribution media.

2. **Run the installer** (`NHDW-Setup-{version}.exe`):
   - Double-click the installer
   - Accept the license agreement
   - Choose installation directory (default: `C:\Program Files\NHDW`)
   - Select components:
     - [x] NHDW Desktop Application (required)
     - [x] Create Desktop Shortcut
     - [x] Create Start Menu Shortcut
     - [ ] Enable Auto-Update (recommended)
   - Click Install

3. **Launch NHDW** from the desktop shortcut or Start Menu.

### 2.2 Python Installation (Development/Power Users)

```powershell
# 1. Verify Python installation
python --version
# Must be Python 3.11 or 3.12

# 2. Clone or extract the NHDW package
cd C:\NHDW

# 3. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run NHDW
python run.py
```

### 2.3 Silent Installation (Enterprise Deployment)

```powershell
# For mass deployment via GPO or SCCM
NHDW-Setup-{version}.exe /S /D=C:\Program Files\NHDW

# With specific config preloaded
NHDW-Setup-{version}.exe /S /CONFIG="\\server\share\nhdw-config.json"
```

---

## 3. Configuration

### 3.1 Environment Configuration (.env)

Create a `.env` file in the NHDW installation directory:

```ini
# NHDW Configuration
NHDW_API_BASE_URL=https://gula-backend.hospital.gov.iq
NHDW_LANGUAGE=ar
NHDW_THEME=dark
NHDW_OFFLINE_MODE=false
NHDW_AUTO_SYNC_INTERVAL=60
NHDW_AUTO_REFRESH_INTERVAL=30
NHDW_SESSION_TIMEOUT_MINUTES=480
NHDW_NOTIFICATIONS_ENABLED=true
NHDW_MINIMIZE_TO_TRAY=true
NHDW_CHECK_UPDATES=true
```

### 3.2 Application Settings

Settings are stored in `%APPDATA%\NHDW\config.json` and can be modified:

- **From the UI**: Settings → Preferences
- **Manually**: Edit `%APPDATA%\NHDW\config.json`
- **Via command line**: `python run.py --server https://gula-backend.hospital.gov.iq --theme light --language en`

### 3.3 Command-Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--theme` | Theme: `dark` or `light` | `--theme light` |
| `--language` | Language: `ar` or `en` | `--language en` |
| `--server` | API base URL | `--server https://gula-backend.hospital.gov.iq` |
| `--offline` | Start in offline mode | `--offline` |

### 3.4 Feature Flags

Feature flags control which modules are available. Configure in `%APPDATA%\NHDW\config.json`:

```json
{
  "feature_flags": {
    "admissions": true,
    "discharges": true,
    "transfers": true,
    "queue_management": true,
    "clinical_tasks": true,
    "ward_rounds": true,
    "vital_signs": true,
    "care_plans": true,
    "messaging": true,
    "critical_alerts": true,
    "bed_management": true,
    "equipment_tracking": true,
    "or_schedule": true,
    "reports": true,
    "analytics": true,
    "export_pdf": true,
    "export_excel": true,
    "patient_registration": true,
    "patient_search": true
  }
}
```

---

## 4. Running NHDW

### 4.1 Normal Startup

- Double-click the desktop shortcut or Start Menu entry
- The splash screen displays while NHDW initialises
- If a valid session exists (previous login), the main window opens directly
- If no session exists, the login dialog is displayed

### 4.2 Command-Line Startup

```powershell
# With virtual environment
cd C:\NHDW
.\venv\Scripts\Activate.ps1
python run.py

# With custom configuration
python run.py --server https://gula-backend.hospital.gov.iq --theme dark --offline

# With debug logging
set NHDW_LOG_LEVEL=DEBUG
python run.py
```

### 4.3 First-Time Login

1. Enter the **Server URL** (e.g., `https://gula-backend.hospital.gov.iq`)
2. Enter your **Username** and **Password** (provided by your hospital IT administrator)
3. Click **Login**
4. The session is saved for subsequent launches (tokens are persisted securely)

---

## 5. Building Windows Installer (PyInstaller)

### 5.1 Prerequisites

```powershell
pip install pyinstaller
```

### 5.2 Build Command

```powershell
# Build NHDW executable
pyinstaller --onefile --windowed --name NHDW `
    --icon=resources/nhdw.ico `
    --add-data "resources;resources" `
    --hidden-import PySide6.QtCore `
    --hidden-import PySide6.QtGui `
    --hidden-import PySide6.QtWidgets `
    --hidden-import cryptography `
    --hidden-import sqlalchemy `
    main.py
```

### 5.3 Build With Inno Setup (Installer)

1. Build the executable with PyInstaller (above)
2. Create `installer.iss` with Inno Setup script
3. Compile with Inno Setup Compiler

```iss
; Sample Inno Setup script (installer.iss)
[Setup]
AppName=NHDW
AppVersion=1.0.0
DefaultDirName={autopf}\NHDW
DefaultGroupName=NHDW
OutputDir=.\dist
OutputBaseFilename=NHDW-Setup-1.0.0

[Files]
Source: "dist\NHDW.exe"; DestDir: "{app}"
Source: "resources\*"; DestDir: "{app}\resources"

[Icons]
Name: "{commondesktop}\NHDW"; Filename: "{app}\NHDW.exe"
Name: "{commonprograms}\NHDW"; Filename: "{app}\NHDW.exe"
```

### 5.4 Build Output

- `dist/NHDW.exe` — Standalone executable (~80 MB)
- `dist/NHDW-Setup-{version}.exe` — Windows installer (~50 MB)

---

## 6. Desktop Shortcuts

### 6.1 Manual Shortcut Creation

```powershell
# Create desktop shortcut via PowerShell
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("$Home\Desktop\NHDW.lnk")
$Shortcut.TargetPath = "C:\Program Files\NHDW\NHDW.exe"
$Shortcut.WorkingDirectory = "C:\Program Files\NHDW"
$Shortcut.Description = "National Hospital Desktop Workspace"
$Shortcut.IconLocation = "C:\Program Files\NHDW\resources\nhdw.ico"
$Shortcut.Save()
```

### 6.2 Start Menu Shortcut

The installer creates shortcuts in:
- `%ProgramData%\Microsoft\Windows\Start Menu\Programs\NHDW\`
- `%UserProfile%\Desktop\NHDW.lnk`

---

## 7. Auto-Update Configuration

### 7.1 Update Server Configuration

The update mechanism uses a simple JSON manifest hosted on a web server:

```json
{
  "version": "1.1.0",
  "release_date": "2026-08-01",
  "download_url": "https://updates.gula-platform.iq/nhdw/NHDW-Setup-1.1.0.exe",
  "checksum": "sha256:abcdef1234567890...",
  "changelog": [
    "Added new KPI dashboard reports",
    "Improved sync performance",
    "Bug fixes in bed management view"
  ],
  "mandatory": false
}
```

### 7.2 Update Check Interval

- Default: Every 24 hours
- Configurable via `NHDW_CHECK_UPDATES` and `NHDW_UPDATE_INTERVAL_HOURS`
- Users can also check manually: **Help → Check for Updates**

### 7.3 Update Process

1. NHDW checks the update manifest URL
2. If a newer version is found and `mandatory` is false, user is prompted
3. If `mandatory` is true or user accepts, the installer is downloaded
4. NHDW closes, installer runs, and NHDW restarts

---

## 8. Offline Setup

### 8.1 First-Time Sync (Online Required)

1. Connect to the internet
2. Launch NHDW and login
3. NHDW performs an initial full sync to populate the local SQLite database
4. Once complete, NHDW can operate offline

### 8.2 Offline Configuration

```json
{
  "offline_mode": true,
  "auto_sync_interval": 60
}
```

- In offline mode, all operations work on the local SQLite database
- Changes are queued in the `sync_log` table
- When connectivity is restored, changes are pushed automatically

### 8.3 Offline Database Location

The local SQLite database is stored at:
- Windows: `%APPDATA%\NHDW\nhdw.db`
- Linux: `~/.config/NHDW/nhdw.db`
- macOS: `~/Library/Application Support/NHDW/nhdw.db`

### 8.4 Backup Offline Database

```powershell
# Copy the offline database for backup
copy "%APPDATA%\NHDW\nhdw.db" "D:\Backups\nhdw-backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%.db"
```

---

## 9. Integration with Backend API

### 9.1 API Endpoints Used

NHDW communicates with the backend via these endpoint groups:

| Endpoint Group | Usage |
|----------------|-------|
| `/auth/*` | Authentication, token refresh |
| `/nhdw/*` | NHDW-specific operations (ADT, tasks, alerts, sync) |
| `/hospital/*` | Read hospital data (departments, beds, rooms) |
| `/patients/*` | Patient search, detail |
| `/users/*` | Staff directory |

### 9.2 API Client Configuration

The `ApiClient` is configured with:

| Parameter | Configuration Source | Default |
|-----------|---------------------|---------|
| Base URL | `config.api_base_url` / `--server` | `http://localhost:8000` |
| Timeout | Hard-coded | 30 seconds |
| Retry | Hard-coded | 3 attempts, exponential backoff |
| Token refresh | Automatic on 401 | Refresh token endpoint |

### 9.3 Authentication Flow

```
1. Login: POST /auth/login → { access_token, refresh_token }
2. API calls: Authorization: Bearer {access_token}
3. On 401: POST /auth/refresh → { access_token }
4. On refresh failure: Show login dialog
```

### 9.4 Troubleshooting Backend Connectivity

1. **Check API URL**: Ensure `api_base_url` is correct
2. **Test connectivity**: `curl https://gula-backend.hospital.gov.iq/health`
3. **Check credentials**: Verify username/password
4. **Check firewall**: Ensure port 443 outbound is allowed
5. **Check SSL**: Ensure the server certificate is trusted on the hospital machine

---

## 10. Troubleshooting

### 10.1 Installation Issues

| Issue | Solution |
|-------|----------|
| "Python not found" | Install Python 3.11+ from python.org |
| "PySide6 installation failed" | Install Visual C++ Redistributable (2015-2022) |
| "Permission denied" | Run installer as Administrator |
| "Antivirus blocking" | Add NHDW folder to antivirus exceptions |

### 10.2 Runtime Issues

| Issue | Solution |
|-------|----------|
| Application won't start | Delete `%APPDATA%\NHDW\instance.lock` (stale lock file) |
| Login fails | Check API URL, verify credentials, check network |
| Sync stuck | Restart NHDW, check `sync_log` for failed entries |
| UI in wrong language | Settings → Language → Arabic or English → Restart |
| Theme not applying | Settings → Theme → Restart |
| Database corrupted | Delete `nhdw.db` (will re-sync on next online launch) |

### 10.3 Log Files

Logs are written to:
- `%APPDATA%\NHDW\logs\nhdw.log`
- Debug logs: `set NHDW_LOG_LEVEL=DEBUG`

### 10.4 Support

- **Documentation**: See `docs/hospital-workspace/` in the GULA repository
- **Issue tracker**: https://github.com/samertts/gula-platform/issues
- **Email support**: hospital-support@gula-platform.iq
- **Phone**: +964 123 456 7890 (Sunday–Thursday, 8:00–16:00 Baghdad time)
