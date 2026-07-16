# NHDW Operations Guide

**National Hospital Desktop Workspace — Operations and Administration**
**Version:** 1.0.0
**Last Updated:** 2026-07-16

---

## 1. Daily Operations Checklist

### 1.1 Start of Day

- [ ] Verify NHDW is running on all hospital workstations
- [ ] Check connection status indicator (should show green/connected)
- [ ] Verify last sync time is within the last hour
- [ ] Check for any critical alerts or unread messages
- [ ] Review pending sync items (Settings → Sync Status)
- [ ] Verify bed board accuracy against physical ward status
- [ ] Confirm staff are logged in with correct roles

### 1.2 Throughout the Day

- [ ] Monitor queue waiting times for ED and clinics
- [ ] Track clinical task completion rates
- [ ] Verify admissions/discharges/transfers are being recorded
- [ ] Check department occupancy and bed availability
- [ ] Review any system alerts or error notifications

### 1.3 End of Day

- [ ] Complete all pending admissions and discharges
- [ ] Ensure all clinical tasks are updated to correct status
- [ ] Verify sync queue is empty (all changes pushed to server)
- [ ] Review daily KPI summary
- [ ] Log off NHDW sessions

---

## 2. Monitoring

### 2.1 Connection Status

The status bar displays the current connection state:

| Indicator | Meaning | Action Required |
|-----------|---------|-----------------|
| Green dot | Connected to server | None |
| Yellow dot | Connected, syncing | None |
| Red dot | Offline/disconnected | Check network, verify server status |
| Grey dot | Connecting | Wait for connection attempt |

### 2.2 Sync Status

Access via **Settings → Sync Status** or by hovering over the sync indicator:

| Field | Description |
|-------|-------------|
| Last Sync | Timestamp of last successful synchronisation |
| Pending Changes | Number of local changes waiting to be pushed |
| Is Syncing | Whether a sync operation is currently in progress |
| Online | Connection status to the backend API |

**Healthy state**: Last sync within 5 minutes, pending changes = 0, online = true.

### 2.3 Error Logs

Access logs at `%APPDATA%\NHDW\logs\nhdw.log`:

```powershell
# View recent errors
Get-Content "$env:APPDATA\NHDW\logs\nhdw.log" -Tail 100 | Select-String "ERROR"

# Monitor log in real-time
Get-Content "$env:APPDATA\NHDW\logs\nhdw.log" -Tail 10 -Wait
```

### 2.4 System Health Checks

**Quick health check**:
1. Open NHDW and verify login
2. Navigate to Dashboard — KPI cards should display data
3. Search for a patient — results should return within 3 seconds
4. Check sync status — should show online with 0 pending changes

**Backend health check** (from the hospital machine):
```powershell
# Check backend API is reachable
curl https://gula-backend.hospital.gov.iq/health

# Expected response:
# {"status": "healthy", "database": "connected", "redis": "connected"}
```

---

## 3. Backup and Restore

### 3.1 Local Database Backup

The offline SQLite database (`%APPDATA%\NHDW\nhdw.db`) contains cached data and pending sync changes.

**Automatic backup**: NHDW creates a daily backup at `%APPDATA%\NHDW\backups\nhdw_daily.db`.

**Manual backup**:
```powershell
# Create timestamped backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "$env:APPDATA\NHDW\nhdw.db" "$env:APPDATA\NHDW\backups\nhdw_$timestamp.db"
```

### 3.2 Configuration Backup

```powershell
# Backup config
Copy-Item "$env:APPDATA\NHDW\config.json" "$env:APPDATA\NHDW\backups\config_$timestamp.json"
```

### 3.3 Session Backup

```powershell
# Backup session (contains authentication tokens)
Copy-Item "$env:APPDATA\NHDW\session.json" "$env:APPDATA\NHDW\backups\session_$timestamp.json"
```

### 3.4 Restore Procedure

1. Close NHDW
2. Delete the corrupted database: `Remove-Item "$env:APPDATA\NHDW\nhdw.db"`
3. Restore from backup: `Copy-Item "$env:APPDATA\NHDW\backups\nhdw_20260701_120000.db" "$env:APPDATA\NHDW\nhdw.db"`
4. Launch NHDW — it will sync with the backend to reconcile any missing data
5. If the session is invalid, log in again

**Full reset** (if restore fails):
```powershell
# Reset NHDW to factory state
Remove-Item "$env:APPDATA\NHDW\nhdw.db"
Remove-Item "$env:APPDATA\NHDW\session.json"
Remove-Item "$env:APPDATA\NHDW\instance.lock"
```
Launch NHDW and log in again. The local database will be repopulated via full sync.

### 3.5 Backup Schedule

| Backup Type | Frequency | Retention | Location |
|-------------|-----------|-----------|----------|
| Local DB | Daily (auto) | 7 days | `%APPDATA%\NHDW\backups\` |
| Config | On change | 30 days | `%APPDATA%\NHDW\backups\` |
| Full machine | Weekly (IT) | 30 days | Hospital network share |

---

## 4. User Management

### 4.1 User Roles

NHDW uses the existing GULA RBAC system:

| Role | Permissions |
|------|-------------|
| **Hospital Admin** | Full access — all modules, user management, config |
| **Department Head** | Department scope — bed management, tasks, reports |
| **Nurse** | Clinical tasks, vitals, patient view, messaging |
| **Doctor** | Patient view, order management, clinical tasks |
| **Admissions Clerk** | ADT workflow, patient registration, queue |
| **Viewer** | Read-only — dashboards, reports, patient info |

### 4.2 Adding Users

Users are managed through the GULA backend admin panel. NHDW authenticates against the same user database.

1. **Web admin**: Go to the GULA admin interface → Users → Add User
2. **API**: `POST /api/users` with `{ username, password, role, department_id }`
3. User can then log in to NHDW with their credentials

### 4.3 Password Management

- Password changes happen through the GULA backend
- NHDW session is invalidated on password change (user must re-login)
- Session timeout: 480 minutes (configurable via `NHDW_SESSION_TIMEOUT_MINUTES`)

### 4.4 Role Assignment

Role changes are reflected in NHDW on the next API call (or after re-login). UI elements are shown/hidden based on permissions.

---

## 5. Performance Tuning

### 5.1 Sync Interval

Adjust the sync interval to balance data freshness with network load:

| Setting | Interval | Use Case |
|---------|----------|----------|
| Real-time | 15 seconds | Critical care, busy ED |
| Normal | 60 seconds | Standard ward (default) |
| Battery saving | 300 seconds | Laptop on battery |
| Manual only | Off | Metered/expensive connection |

Configure in `%APPDATA%\NHDW\config.json`:
```json
{
  "auto_sync_interval": 60,
  "auto_refresh_interval": 30
}
```

### 5.2 Cache Settings

```json
{
  "cache_enabled": true
}
```
- Disable cache on low-storage machines
- Cache stores patient search results and department data
- Size limit: ~100 MB (auto-managed)

### 5.3 Large Hospital Performance

For hospitals with 500+ beds:

1. **Increase sync interval** — Set to 120-300 seconds
2. **Disable trend charts** for departments with >50 beds
3. **Use delta sync** — Avoid full sync on reconnect
4. **Limit patient search** — Search by MRN or phone (not broad name search)

### 5.4 SQLite Performance

The local SQLite database is optimised for:
- WAL mode (Write-Ahead Logging) for concurrent reads and writes
- Indexes on commonly queried columns: `mrn`, `patient_id`, `status`, `assignee`
- `deleted = 0` soft-delete filter for efficient queries
- Use of JSON column for flexible extra data fields

---

## 6. Troubleshooting Common Issues

### 6.1 Login Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| "Invalid credentials" | Wrong username/password | Reset password via admin panel |
| "Cannot connect to server" | Server unreachable | Check server URL, network, firewall |
| "Session expired" | Token expired | Re-login |
| "Connection refused" | Server down | Verify backend is running (`make health`) |
| "SSL certificate error" | Untrusted certificate | Install CA certificate on hospital machine |

### 6.2 Sync Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Pending changes never sync | No network | Check internet connection |
| Sync fails with 401 | Token expired after session restore | Re-login to refresh tokens |
| "Network error" in sync log | Intermittent connectivity | Wait for retry, check network stability |
| Conflict warning | Concurrent offline edit | Last-writer-wins applied automatically |
| High pending changes count | Extended offline period | Verify after sync completes; if persistent, restart NHDW |

### 6.3 Data Display Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Dashboard shows "No data" | Initial sync not complete | Wait for first full sync, or trigger manual sync |
| Patient not found | Not synced locally | Use online mode for search, or wait for full sync |
| Department list empty | Permissions issue | Verify user has department access |
| Arabic text garbled | Encoding issue | Restart NHDW, verify system locale is set to Arabic |
| Charts not rendering | Missing cached data | Refresh dashboard view |

### 6.4 Application Crashes

| Symptom | Cause | Solution |
|---------|-------|----------|
| Crash on startup | Corrupted session | Delete `session.json`, restart |
| Crash on sync | Database corruption | Delete `nhdw.db`, re-sync |
| Crash on certain view | UI state corruption | Reset layout: delete `config.json` dock_positions |
| Out of memory | Too many cached patients | Clear cache: Settings → Clear Local Data |
| Freeze on search | Large result set | Narrow search criteria (use MRN or exact phone) |

### 6.5 Recovery Procedures

**Procedure 1: Quick Recovery**
```powershell
# Stop NHDW
# Clear cache and session
Remove-Item "$env:APPDATA\NHDW\session.json"
Remove-Item "$env:APPDATA\NHDW\instance.lock"
# Restart NHDW
```

**Procedure 2: Full Reset**
```powershell
# Stop NHDW
# Backup existing data
New-Item -ItemType Directory -Force "$env:APPDATA\NHDW\backups\emergency"
Copy-Item "$env:APPDATA\NHDW\*" "$env:APPDATA\NHDW\backups\emergency\" -Recurse
# NHDW will recreate these on next launch
Remove-Item "$env:APPDATA\NHDW\nhdw.db"
Remove-Item "$env:APPDATA\NHDW\session.json"
Remove-Item "$env:APPDATA\NHDW\config.json"
Remove-Item "$env:APPDATA\NHDW\instance.lock"
# Restart NHDW — it will prompt for initial login and config
```

**Procedure 3: Network Diagnostics**
```powershell
# Test DNS resolution
Resolve-DnsName gula-backend.hospital.gov.iq

# Test reachability
Test-NetConnection gula-backend.hospital.gov.iq -Port 443

# Test API endpoint
Invoke-WebRequest -Uri "https://gula-backend.hospital.gov.iq/health"

# Check proxy settings
Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
```

---

## 7. Support Contacts

### 7.1 Level 1: Hospital IT Support

First point of contact for NHDW issues:

| Contact | Role | Availability |
|---------|------|-------------|
| Hospital IT Desk | Local IT support | Hospital working hours |
| Department Super User | Trained NHDW power user | Department hours |

**Responsibilities**:
- Basic troubleshooting (login, network, config)
- User account management
- Application reinstallation
- Backup and restore

### 7.2 Level 2: NHDW Support Team

For issues that Level 1 cannot resolve:

| Channel | Contact | Response Time |
|---------|---------|---------------|
| Email | nhdw-support@gula-platform.iq | 4 business hours |
| Phone | +964 123 456 7890 | 8:00–16:00 Baghdad time, Sun–Thu |
| Portal | https://support.gula-platform.iq | 2 business hours |

**When contacting Level 2, provide**:
- NHDW version (Help → About)
- Windows version
- Backend API URL
- Error message and screenshot
- Steps to reproduce
- Log file: `%APPDATA%\NHDW\logs\nhdw.log`

### 7.3 Level 3: Development Team

For bugs, feature requests, and technical escalations:

| Channel | Contact |
|---------|---------|
| GitHub Issues | https://github.com/samertts/gula-platform/issues |
| Documentation | https://github.com/samertts/gula-platform/docs/hospital-workspace/ |
| Internal | Engineering team, #nhdw channel (internal Slack/Teams) |

### 7.4 Escalation Matrix

| Severity | Definition | Response | Escalation |
|----------|------------|----------|------------|
| **Critical** | NHDW completely unavailable, affecting patient care | 1 hour | L1 → L2 immediate, L2 → L3 within 2 hours |
| **High** | Major feature unavailable, workaround exists | 4 hours | L1 → L2, L3 within 24 hours |
| **Medium** | Non-critical feature issue | 24 hours | L2 within 48 hours |
| **Low** | Cosmetic, minor improvement | 5 business days | Standard process |

---

## 8. Version Management

### 8.1 Current Version

Check current version:
- Help → About → Version: `1.0.0`
- Config file: `%APPDATA%\NHDW\config.json` → not directly stored

### 8.2 Update Channels

| Channel | Update Frequency | Risk |
|---------|-----------------|------|
| Stable | Monthly | Low — production-tested |
| Beta | Weekly | Medium — may have minor issues |
| Nightly | Daily | High — for testing/QA only |

### 8.3 Rollback Procedure

1. Uninstall current version via **Control Panel → Programs → Uninstall**
2. Install previous version from the releases archive
3. Preserve `%APPDATA%\NHDW\config.json` (should be kept during uninstall)
4. Restart NHDW

---

## 9. Security Checklist

- [ ] All NHDW installations use HTTPS connections to the backend
- [ ] User passwords follow GULA password policy (minimum 8 characters, complexity)
- [ ] Sessions expire after 480 minutes of inactivity
- [ ] Local SQLite database is stored in user's AppData folder (not shared)
- [ ] Only authorised hospital staff have NHDW access
- [ ] NHDW is not installed on public/shared computers without user-specific login
- [ ] Windows updates are applied regularly on all hospital machines
- [ ] Antivirus software is active on all NHDW workstations
- [ ] Backend API uses valid TLS certificates
- [ ] Audit logging captures all NHDW mutations on the backend
