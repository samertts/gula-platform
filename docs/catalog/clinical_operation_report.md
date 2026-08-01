# Clinical Operation Report — PROGRAM-03 v2.0

**Certification:** Clinical data-entry and approval workflows are fully operational end-to-end.

## End-to-End Clinical Loop

```
Order  →  Sample  →  Analyzer/QC  →  Result  →  Verify  →  Public Release
 (create/validate/cancel)  (register/status)  (QC entry)  (category/filter)  (verify)  (/r/:token + PDF)
```

## Loop Verification

1. **Order intake** — clinician creates order from patient + test profile; validates or cancels; clinical intelligence available per order. `OrdersPage`
2. **Sample logistics** — laboratory registers sample against the order; transitions through collected→received→processing→analyzed (or rejected with reason). `SamplesPage`
3. **Quality assurance** — QC supervisor enters Westgard control data; 30-day summary (total/passed/warning/pass-rate). `QCPage`
4. **Result management** — results listed with abnormal/category filters; verified results are authoritative; audit trail via backend. `ResultsPage`
5. **Patient release** — patient retrieves own results via public token link with PDF download, no login required. `PublicResultPage`

## Security & Clinical Safety

- Privileged MFA challenge enforced at login (ASVS 2.4); brute-force bounded by single-use session + rate limit.
- Audit log entries: `login_mfa_challenge_issued`, `login_failed_mfa_code`, `login_denied_mfa_required`, plus existing `login`/`logout`.
- Westgard multi-rule engine (incl. 2-2s ordering fix from earlier program) remains the QC gate.
- Data isolation: queries scoped by lab_id via auth dependencies (tenant isolation retained).

## Roles

All 14 roles mapped; privileged roles (master/ministry/province admin) receive the strictest authentication path. Citizen flow uses `/citizen/*` API group (unchanged).
