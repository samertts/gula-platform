# GULA Stable v1.0.0 — Current State

**Program state:** Phase 0 IN PROGRESS  
**Working branch:** `recovery/stable-v1`  
**Base/main SHA at setup:** `46158e905fd97f57ca21c61bb5574d03aed90293`  
**Production readiness:** NOT CERTIFIED; upstream commit explicitly records `production_ready=false`.

## Verified during setup
- Repository `samertts/gula-platform` is private and available through the connected GitHub integration.
- Default branch is `main`.
- Working branch `recovery/stable-v1` was created from the recorded main SHA.
- `docs/START_HERE.md` identifies `backend/app/` as canonical backend and `frontend-v3/` as primary web app; `services/` is future decomposition.
- Latest inspected commit reports 101 unique Alembic revision IDs and one head after its migration-graph repair.
- Latest inspected commit leaves NR-003 OPEN/P0 and says existing-database upgrade is unverified.

## Known blockers requiring fresh baseline verification
- NR-003 pharmacy primary-key type divergence.
- NR-006 dual ORM ownership of `national_facilities`.
- NR-007 entity-agnostic clinical state machine.
- Existing-database migration/upgrade path not proven.
- Full CI, security, privacy, tenant isolation, offline recovery, and capacity status not independently established in this setup.

## Not yet done
- No application code changed.
- No tests executed locally or in CI during this setup.
- No database migration executed.
- No deployment or release action taken.
- No Phase 1 remediation authorized.

## Next action
Complete Phase 0 inventory and reproducible test baseline on Ubuntu and Windows, then submit the baseline for human review.