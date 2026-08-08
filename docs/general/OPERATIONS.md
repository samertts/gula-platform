# GULA Platform — Operations Runbook

## Before Any Government Presentation

```bash
# 1. Run restore test (takes ~2 min, generates live evidence)
./scripts/restore-test.sh

# 2. Open compliance page → verify all green
# Navigate to: https://your-domain/#compliance
```

---

## Weekly Checklist

| Task | Command | Expected |
|------|---------|----------|
| Restore test | `./scripts/restore-test.sh` | PASS, < 120s |
| Audit integrity | `GET /api/compliance/audit-integrity` | `"status": "intact"` |
| Anchor HMAC | check `hmac_failures: 0` in response | 0 failures |
| NTP drift | `GET /api/compliance/time-sync` | `drift_warning: false` |
| Failed logins | compliance UI → Security Details | < 10 in 24h |

---

## Key Rotation (Every 90 Days)

```bash
# 1. Generate new key
NEW_KEY=$(openssl rand -hex 32)

# 2. Update /etc/gula-secrets.env
NID_HMAC_KEY_PREV=<current_key>   # keep for 30 days
NID_HMAC_KEY=<new_key>
ANCHOR_KEY_VERSION=2              # increment

# 3. Restart app
docker compose restart api

# 4. After 30 days: clear NID_HMAC_KEY_PREV
```

---

## What to Say to the Audit Committee

> "النظام لا يطلب الثقة — بل يُثبتها"

1. **Tamper detection**: Any modification to any record is detected immediately via cryptographic hash chain
2. **External proof**: Audit checkpoints exist outside the database — rebuilding the DB cannot erase the evidence
3. **Tested recovery**: Disaster recovery was tested on [date], restore time: [N] seconds — here is the signed report
4. **Time integrity**: Server clock is NTP-synchronized with drift monitoring (threshold: 2s)

**Do NOT say**: "We use HMAC and SHA-256..."
**DO say**: "Any tampering is detected and shown here in real time"

---

## Production Setup (One Time)

```bash
# Secure secrets file
sudo bash scripts/setup-secrets.sh

# Verify permissions
ls -la /etc/gula-secrets.env
# Should show: -rw------- root root
```

---

## Compliance Page — What Each Section Shows

| Section | Source | What It Proves |
|---------|--------|---------------|
| Audit Chain | `/compliance/audit-integrity` | No record was modified |
| External Anchor | `audit_anchors/` dir | DB cannot be silently rebuilt |
| Restore Test | `last_restore_test.json` | Recovery actually works |
| NTP Status | `timedatectl` | Timestamps are trustworthy |
| Compliance Checklist | Backend config | Standards implementation status |
