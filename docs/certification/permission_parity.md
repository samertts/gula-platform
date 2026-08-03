# Permission Parity Certification — PROGRAM-06 (detailed)

> Generated: 2026-08-02 · Companion to `role_parity.md`

## Permission vocabulary (16) — identical on both sides

```
patients:read    patients:write   patients:delete
orders:read      orders:write
results:read     results:write
staff:manage     lab:read         lab:manage
dashboard:read   audit:read
platform:manage_labs   platform:manage_users   platform:view_stats
system:admin
```

## Permission → route enforcement map (active modules)

| Permission | Enforcing routes (examples) | Frontend guard |
|---|---|---|
| `patients:read/write/delete` | `/patients` GET/POST, `PUT /patients/{id}` | PatientsPage RoleGuard + nav |
| `orders:read/write` | `/orders` GET/POST, `/{id}/validate`, `/{id}/cancel`, `/samples` (reception) | OrdersPage/SamplesPage |
| `results:read/write` | `/test-results` GET/POST, `/qc*`, `/lims/results*`, `/alerts*` | ResultsPage/QCPage/LimsPage |
| `staff:manage` | lab employee endpoints | LabsPage |
| `lab:read/manage` | `/labs*`, `/labs/me*`, `/edge*` | LabsPage/EdgePage |
| `dashboard:read` | `/dashboard`, `/stats*`, `/greeting` | DashboardPage/StatsPage |
| `audit:read` | `/admin/audit-logs`, `/compliance*` | AdminAuditPage/CompliancePage |
| `platform:manage_users` | `/admin/users*`, `/admin/doctors*`, `/admin/citizens*`, `/service-accounts*` | AdminUsersPage/IdentityPage |
| `platform:manage_labs` | `/admin/labs*`, `/admin/labs/pending`, `/admin/tiers/*` | AdminLabsPage |
| `platform:view_stats` | `/admin/stats` | AdminPages |
| `system:admin` | `/admin/*` (kill-switch, control-layer, stats), `/admin/log-level` | AdminControlPage |
| `results:verify` (derived) | `PUT /test-results/{id}/verify` via `require_verify_authority` | ResultsPage verify button |

## Drift scan result

- Frontend `ROLE_PERMISSIONS[role]` == backend `EXTENDED_ROLE_PERMISSIONS[role]` for **all 25 roles** — verified by automated comparison.
- No permission string exists on one side only.
- No role name exists on one side only.

## Verdict

**PERMISSION PARITY: 100% — zero permission drift (ASVS 4.x, OWASP API Top 10 compliance posture maintained).**
