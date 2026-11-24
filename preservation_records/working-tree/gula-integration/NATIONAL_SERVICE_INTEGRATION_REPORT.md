# National Service Integration Report

**Repository:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date / environment:** 2026-11-19.
**Status vocabulary:** `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`. No `PRODUCTION READY` awarded.

## 1. Status — `NOT IMPLEMENTED` for integration verification

No new service implementation, wiring, or runtime integration was performed this session. The
authoritative read-only assessment is `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` (18 target
services; 4 effectively complete, 9 real but partial, 3 signals-only; dominant defect = missing
migrations). That document's verdicts were not re-run or changed here.

## 2. Services relevant to this execution

| Service | Status this session | Evidence |
|---|---|---|
| Identity / authentication | `TESTED` (scoped) | Phase 1/2 closeouts; step-up 37 tests (`IDENTITY_TRUST_REPORT.md`) |
| NIAM step-up endpoint | `INTEGRATED` (engineering scope) | app boots; OpenAPI exposes `POST /niam/auth/step-up/verify`; not wired into B4 |
| Adaptive-auth / MFA control plane (B4) | `BLOCKED` | source untouched; owner approval pending |
| Search, Workflow, PDF, Domain Platform, Professional Registry, Communication, Telegram, Insurance, Care Continuum, Offline Sync, FHIR, Analyzer Gateway, Event Bus | `NOT IMPLEMENTED` (integration verification this session) | inventory only; no runtime/integration claim |

## 3. Explicit non-claims

- A file, directory, or endpoint is **not** evidence that a service works; no such claim is made.
- No government API, external identity provider, broker, or analyzer integration is claimed.
- The frontend was not rebuilt or re-tested this session; see `GOVERNANCE/FRONTEND_INTEGRATION_REPORT.md`
  for the pre-existing contract-drift findings (101 unresolved calls, 28 verb mismatches).

**Final decision:** service integration verification `NOT IMPLEMENTED` in this execution; no
production claim, no commit/deploy, no protected-file change. Git SHA: `2206654dc713ea2de8c564a3207dfe05fde23549`.
