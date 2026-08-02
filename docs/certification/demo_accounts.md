# Demo Accounts — PROGRAM-05

*Generated 2026-08-02 · idempotent provisioning via `POST /admin/users` (platform API, no direct DB writes)*

Demo users are created **only when missing** (never overwritten). Pattern: `demo.{role}@demo.local`.

> Shared demo password: `Demo@2026!Pass` — for local/CI use only; production deploys must rotate.

| Role | Level | Email | State |
|---|---|---|---|
| `master_admin` | 100 | `demo.master_admin@demo.local` | exists |
| `ministry_admin` | 90 | `demo.ministry_admin@demo.local` | exists |
| `organization_admin` | 85 | `demo.organization_admin@demo.local` | exists |
| `directorate_admin` | 80 | `demo.directorate_admin@demo.local` | exists |
| `province_admin` | 80 | `demo.province_admin@demo.local` | exists |
| `auditor` | 70 | `demo.auditor@demo.local` | exists |
| `security_officer` | 70 | `demo.security_officer@demo.local` | exists |
| `hospital_admin` | 60 | `demo.hospital_admin@demo.local` | exists |
| `phc_admin` | 55 | `demo.phc_admin@demo.local` | exists |
| `lab_manager` | 50 | `demo.lab_manager@demo.local` | exists |
| `admin` | 50 | `demo.admin@demo.local` | exists |
| `lab_admin` | 50 | `demo.lab_admin@demo.local` | exists |
| `lab_supervisor` | 45 | `demo.lab_supervisor@demo.local` | exists |
| `quality_manager` | 45 | `demo.quality_manager@demo.local` | exists |
| `pathologist` | 40 | `demo.pathologist@demo.local` | exists |
| `doctor` | 35 | `demo.doctor@demo.local` | exists |
| `technician` | 30 | `demo.technician@demo.local` | exists |
| `nurse` | 25 | `demo.nurse@demo.local` | exists |
| `receptionist` | 20 | `demo.receptionist@demo.local` | exists |
| `cashier` | 20 | `demo.cashier@demo.local` | exists |
| `staff` | 20 | `demo.staff@demo.local` | exists |
| `lab_staff` | 20 | `demo.lab_staff@demo.local` | exists |
| `api_client` | 5 | `demo.api_client@demo.local` | exists |
| `patient` | 10 | `demo.patient@demo.local` | exists |
| `citizen` | 10 | `demo.citizen@demo.local` | exists |

## Notes
- Roles with MFA (`auditor`, `security_officer`, `pathologist`) require MFA challenge on login;
  the role-experience harness handles `mfa_pending` → `POST /mfa-verify`.
- `citizen` is a shared-model role (0 permissions) — provided for completeness of the 25-role universe;
  frontend gates it to login/profile only.
- `api_client` (`is_delegatable=false`) is the machine role; demo account documents its read-only scope.