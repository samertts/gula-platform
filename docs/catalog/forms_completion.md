# Forms Completion Report — PROGRAM-03 v2.0

All production forms validated against backend request schemas (field names, required flags, value constraints).

| Form | Fields | Validation | Backend Schema Source |
|---|---|---|---|
| Order create | patient, status, tests[test_name,value,unit,normal_range_low,high] | required test rows; patient required | `orders.py` routes |
| Patient create | full_name, national_id, family_id, dob, gender, phone | NID pattern; dob | `patients.py` routes |
| Patient update | same minus national_id/family_id | — | `patients.py` routes |
| Sample register | barcode(optional), order_id, sample_type, notes | sample_type from SAMPLE_TYPES | `samples.py` routes |
| Sample transition | status, rejection_reason (required on reject) | STATUS_TRANSITIONS map | `samples.py` routes |
| QC entry | test_code, level, expected, measured, sd, unit, instrument, lot, notes | sd required in high level? backend `qc_service` | `quality_control.py` routes |
| Change password | current_password, new_password | min 8 chars, match confirm | `mobile.py` / `auth/change-password` |
| NID lookup | national_id | digits | `identity.py` routes |
| MFA code | 6-digit code | digits only, max 6 | `mfa-verify` (backend) |

## Rules

- Arabic-first labels; RTL layout inherited from root layout.
- All submit buttons show `loading` state; forms disable double-submit.
- All errors render inline with `getErrorMessage`.
