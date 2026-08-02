# Backend ↔ Frontend Parity Certification — PROGRAM-06

Automated via `scripts/p6_parity_check.py` against the **live backend route table**
(ground truth) and `frontend-v3/src/api/endpoints.ts` (frontend contract).

## Result

- Frontend API calls: **145** (141 unique paths)
- Live backend routes: **1987**
- Route parity: **145/145** calls matched (141 unique paths)
- Drift (frontend path with no backend route): **0**

## Drift

_None — every frontend API path resolves to a live backend route._

## Permission parity (frontend ROLE_PERMISSIONS ↔ shared model)

- Roles in shared model: 25 · Roles in frontend: 25
- Level mismatches: **0**
_None — levels identical._

## Permission-array parity (frontend ROLE_PERMISSIONS ↔ shared model)

- Roles compared: **25** (shared 25 · FE 25)
- Permission set differences: **0**
_None — permission sets identical for every role._

## Method coverage (frontend)

| Method | Calls matched |
|---|---|
| DELETE | 2 |
| GET | 124 |
| POST | 18 |
| PUT | 1 |
