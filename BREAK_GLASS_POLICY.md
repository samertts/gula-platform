# GULA Platform — Emergency Access & Break Glass Policy

**Version:** 1.0.0

---

## 1. Introduction

Emergency Access (Break Glass) allows authorized healthcare professionals to access resources they would not normally have permission to access, when a genuine clinical emergency requires it.

## 2. When Break Glass Is Permitted

| Trigger | Example | Time Sensitivity |
|---------|---------|-----------------|
| Patient critical condition | Cardiac arrest | Immediate |
| Missing primary physician | Specialist unavailable | < 30 min |
| System failure | Authorization service down | Immediate |
| Natural disaster | Hospital evacuation | Immediate |
| Epidemic outbreak | Surge triage | < 1 hour |
| Time-sensitive decision | Stroke window | < 15 min |
| Equipment failure | Lab analyzer down | < 1 hour |

## 3. Break Glass Process

```
Patient in critical condition
  → User identifies need for elevated access
  → User activates Break Glass (button/API)
  → System prompts: reason category + free-text justification
  → User submits:
      - Emergency category
      - Justification (min 20 characters)
      - Patient ID (optional but recommended)
  → System evaluates:
      1. Is user eligible? (clinical role required)
      2. Is emergency mode valid?
      3. Is this a known trigger?
  → If approved:
      - Grant temporary elevated permissions
      - Open audit session
      - Notify: supervisor, compliance officer, security team
  → If denied (rare):
      - Log the attempt
      - Notify security team
```

### 3.1 Activation Methods

| Method | Description | Response Time |
|--------|-------------|---------------|
| UI Button | Click "Emergency Access" in sidebar | 2 seconds |
| Keyboard Shortcut | Ctrl+Shift+E (Cmd+Shift+E on Mac) | Instant |
| API | POST /authz/break-glass | 200ms |
| NFC/Tap | Physical break-glass NFC tag | 1 second |

## 4. What Break Glass Grants

| Capability | Duration | Audit |
|-----------|----------|-------|
| Read all patient data for current facility | 4 hours | Full |
| Write critical results | 4 hours | Full |
| Access patient records outside facility | 4 hours | Full + notification |
| Access sensitive diagnoses (HIV, cancer, etc.) | 4 hours | Full + notification |
| Override normal workflow restrictions | 4 hours | Full |
| Cross-tenant data access | 4 hours | Full + notification |

### 4.1 What Break Glass Does NOT Grant

- Financial operations (billing, refunds)
- User management (create, delete, role changes)
- System configuration changes
- Audit log modification (impossible by design)
- Permission to export large datasets
- Permission to delete records

## 5. Time Limits

| Context | Default Duration | Maximum Extension | Requires |
|---------|-----------------|-------------------|----------|
| Clinical emergency | 4 hours | 24 hours | Supervisor approval |
| System failure | 2 hours | 8 hours | System admin approval |
| Natural disaster | 24 hours | 72 hours | Emergency director |
| Epidemic outbreak | 7 days | 30 days | Ministry approval |

## 6. Notifications

When break glass is activated:
- **Immediate notification** to user's direct supervisor
- **Immediate notification** to facility compliance officer
- **Summary sent** to security team within 5 minutes
- **Daily digest** to CISO of all break-glass events
- **Weekly report** to hospital administration

### Notification Channels

| Recipient | Channel | Priority |
|-----------|---------|----------|
| Supervisor | Push notification | Critical |
| Compliance Officer | Email + SMS | High |
| Security Team | Email (digest) | Normal |

## 7. Audit Requirements

Every break-glass action is recorded with:

| Field | Always Recorded |
|-------|----------------|
| User ID | ✅ |
| User Role | ✅ |
| Timestamp | ✅ (microsecond precision) |
| Emergency Category | ✅ |
| Justification | ✅ |
| Resources Accessed | ✅ |
| Actions Performed | ✅ |
| Duration | ✅ |
| IP Address | ✅ |
| Device ID | ✅ |
| Notifications Sent | ✅ |

## 8. Post-Event Review

### 8.1 Immediate Review (Within 24 hours)

- User must confirm the emergency
- Supervisor must acknowledge
- Justification may be challenged

### 8.2 Formal Review (Within 7 days)

```
User submits written justification
  → Compliance officer reviews
  → If approved: archive with audit
  → If rejected:
      → Root cause analysis
      → Potential disciplinary action
      → Remediation plan
```

### 8.3 Trend Analysis (Quarterly)

- All break-glass events reviewed
- Pattern analysis
- System improvements
- Policy updates

## 9. Abuse Prevention

| Control | Description |
|---------|-------------|
| Rate limiting | Max 5 break-glass activations per user per day |
| Cooling period | 30 minutes between activations |
| Duplicate detection | Same patient/resource within 1 hour |
| Pattern analysis | ML-based anomaly detection |
| Supervisor approval | Required for extension beyond 4 hours |
| Mandatory justification | Minimum 20 characters, meaningful |
| Concurrent limit | Max 10 active break-glass sessions per facility |

## 10. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/authz/break-glass/activate` | Activate break-glass |
| POST | `/authz/break-glass/deactivate` | Deactivate break-glass |
| GET | `/authz/break-glass/status` | Check break-glass status |
| GET | `/authz/break-glass/history` | View break-glass history |
| GET | `/authz/break-glass/active` | List active break-glass sessions |
| GET | `/authz/break-glass/review/:id` | Get break-glass event for review |
| POST | `/authz/break-glass/review/:id/approve` | Approve break-glass event |
| POST | `/authz/break-glass/review/:id/reject` | Reject break-glass event |
