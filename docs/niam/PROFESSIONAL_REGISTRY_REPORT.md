# GULA Professional Registry — Report

> Generated: 2026-08-05T22:30:00+00:00
> Program: PROGRAM-STABLE-003
> Module: `backend/app/identity/professional_registry/`

---

## Verdict

**CERTIFIED — VERIFICATION-GATED PRIVILEGES**

## Mandate

"Professional permissions are granted only after verification by the responsible
authority. Clinical privileges are NEVER activated automatically."

## Design

`niam_professional_registry` records a person's professional registration issued
by an authority (e.g. Ministry of Health). Privileges activate **only** via the
single `verify()` path:

```
register()          → status=pending, verified=False, privileges_activated_at=None
verify()            → status=verified, verified=True, privileges_activated_at=now (authority-only)
suspend()           → privileges_activated_at=None (immediate loss of privileges)
revoke()            → verified=False, privileges_activated_at=None
is_privileged()     → True only when verified + current + not suspended/revoked
```

`is_privileged()` is the single enforcement point the authorization layer must
consult before granting operational/clinical permissions.

## Professions (12 categories)

doctor, dentist, pharmacist, laboratory_scientist, nurse, radiographer,
physiotherapist, veterinarian, researcher, student, retired_professional,
foreign_professional.

## Verified Behaviors (Tests)

| Scenario | Result |
|---|---|
| Register → pending, no privileges | ✅ |
| Unknown profession rejected | ✅ |
| Verify → privileges activated + license verified | ✅ |
| Suspend → privileges immediately revoked | ✅ |
| Revoke → verification cleared | ✅ |
| `is_privileged` True (verified + current) | ✅ |
| `is_privileged` False (pending) | ✅ |
| `is_privileged` False (expired) | ✅ |
| Re-verify a revoked entry | ❌ rejected |
| List entries for a person | ✅ |

## API Surface (7 endpoints)

`/niam/professional-registry/` — register, get, person list, verify, suspend,
revoke, privileges-check.

## Verified Facts

- **Tests:** 12 professional-registry tests pass.
- **Database:** table created in `20260805_0002` with FK to `niam_identity_authorities`.
- **Lint:** ruff clean.

## Open Items

- Authorize `verify()` so only the issuing authority's service account may call it
  (currently takes `verified_by` as a parameter).
- Wire `is_privileged()` into clinical authorization decisions.
