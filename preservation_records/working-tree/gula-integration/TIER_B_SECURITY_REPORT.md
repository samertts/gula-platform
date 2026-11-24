# Tier B — Consent/Break-glass, Verified Guardian, Delegation (implementer evidence)

**Document:** `TIER_B_SECURITY_REPORT.md`
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Baseline HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Owner authority:** `GULA-MASTER-AUTH-2026-11-19` §5 (explicit Tier B implementation authorization)
**Date:** 2026-11-19
**Status vocabulary:** `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`.

This is **implementer-side** evidence. Every control below is `IMPLEMENTED / TESTED` only. `INDEPENDENTLY
VERIFIED` and `PRODUCTION READY` are **not** self-awarded; fresh-context Team C verification of the
security-critical controls (B2/B3/B5) is requested and its verdict will be recorded separately in
`GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md`. B1 is covered by the
canonical authorization regression set. This report makes **no** release, clinical, regulatory, legal,
or production claim.

---

## 1. Scope and exact owner model

| Control | Owner model enforced |
|---|---|
| **B1** — centralized PHI permission map | One centralized per-action PHI permission map; enforcement stays in the canonical `AuthorizationDecisionService` via `AuthorizationReason.phi_permission_conflict`. No second enforcement path. |
| **B2** — consent / break-glass (AUD-PRV-002) | Separate consent and break-glass, fail-closed. `X-Emergency-Access` is **intent-only**; a persisted, active, unexpired, non-deactivated `BreakGlassSession` owned by the actor, with an eligible clinical role and read-only patient-scoped access, is **required**. |
| **B3** — verified guardian/minor/NHID (AUD-PRV-005) | Age derived server-side from DOB (never client `is_minor`); near-majority (17 within 90 days of 18) requires fresh re-verification; **no canonical NHID minted** (canonical NHID remains `NEEDS_OWNER_DECISION / BLOCKED`) — only the canonical NID normalization/hash input contract; twins-never-merged; guardian relationships require an authorized verifier (no subject self-assertion); canonical `GuardianRulesService` action table; fail-closed. |
| **B5** — delegation into canonical authority (AUD-SEC-008) | Delegation only into the **single** canonical authority (`RolePermissionService.effective_permissions`); account-based IDs + canonical role IDs; verified non-empty permission subset; scope containment; time-bounded; revocable; depth-limited (max 3, policy **and** DB CHECK); fully audited. No second engine, no new role/permission. |

Across all controls: no new authorization engine, no new role or permission catalog entry, no
destructive migration, no client-supplied authority accepted as proof, deny by default.

---

## 2. Baseline preservation (rechecked this session)

| Invariant | Observed | Result |
|---|---|---|
| Integration HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` | unchanged |
| Branch | `integration/gula-unification-v1` | unchanged |
| Staged `R100` renames | 20 | preserved |
| Protected MD5 `GOVERNANCE/FINAL_DECISION.md` | `effdfeaf10234678d83b2668c4489552` | unchanged |
| Protected MD5 `MPI_FINAL_INDEPENDENT_AUDIT.md` | `1a02c01563c93b07a7cdb92c0462bf36` | unchanged |
| Protected MD5 `MPI_INDEPENDENT_AUDIT_FINDINGS.md` | `ea3969d09aaf7b0b28a065838b44a594` | unchanged |
| Sibling `gula-platform` HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` | untouched, clean (0 status entries) |
| `production_ready_items` | 0 | unchanged (see §6 reconciliation) |

No commit, push, PR, merge, deploy, history rewrite, `git add -A`, operational DB/Redis, real patient
data, protected-decision change, or external integration was performed. All data is disposable
synthetic SQLite.

---

## 3. Implemented behavior

### 3.1 B1 — `backend/app/identity/services/phi_permission_map.py`
Centralized per-action map; 13 dedicated tests. Enforcement remains solely in the canonical
`AuthorizationDecisionService` (`AuthorizationReason.phi_permission_conflict`).

### 3.2 B2 — `backend/app/security/break_glass_guard.py`
Rewired `backend/app/security/consent_dep.py`; hardened `backend/app/routes/authorization.py`
(activation + deactivation). Server-verifies the persisted `BreakGlassSession` (active, unexpired,
non-deactivated, actor-owned, eligible clinical role, read-only scope) and resolves the patient via
MPI `Citizen.canonical(strict=True)` + `IdentityClaim`. Naive SQLite datetimes normalized to
UTC-aware (`_asutc`). 26 tests in `backend/tests/test_consent.py`.

### 3.3 B3 — `backend/app/identity/services/verified_guardian_guard.py`
Additive `create_pending_guardian()` in canonical `citizen_relationship_service.py` (verifier role,
minor subject, NID digest only, twin-collision denial, audit) and an additive guardian gate in
canonical `AuthorizationDecisionService._relationship_allows` (verified relationship + scope +
canonical rule table). 41 tests in `backend/tests/unit/test_b3_verified_guardian.py`. Other
relationship types are unchanged.

### 3.4 B5 — `backend/app/identity/models/delegation.py`, `delegation_service.py`, migration `20261119_0002`
NIAM-native, account-based `niam_delegations` record consumed by the single canonical
`RolePermissionService.effective_permissions()`. `DelegationService` validates holding authority,
permission subset, scope containment, duration (1..720 h), depth (1..3), self-delegation, active
account/role, and reason; writes `delegation_granted/revoked/denied` audit via canonical
`AuditService`. Additive/reversible migration (upgrade creates the table only; downgrade drops only
that table) — single Alembic head `20261119_0002`, 110 migration files. 26 tests in
`backend/tests/unit/test_b5_delegation.py`.

---

## 4. Verification evidence (exact commands and results)

Pinned interpreter (Python 3.12.13):
`/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python`.
Environment prefix for every test command:
`cd /home/samertts/workspace/projects/gula-integration/backend && ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <pinned python> -m pytest … -q`.

| Check | Command target | Result |
|---|---|---|
| B5 focused | `tests/unit/test_b5_delegation.py` | **26 passed, 1 warning in 12.27s** |
| Combined Tier B + canonical | B4, B1, B2 (`test_consent.py`), B3, B5, phase7, phase8, synthetic scope, workflow, NHID readiness, step-up | **226 passed / 0 failed, EXIT=0** (74.73s) |
| Ruff | all B1/B2/B3/B5 changed scopes | `All checks passed!` |
| Migration chain | Alembic `ScriptDirectory` probe | single head `20261119_0002`, bases `20250322_0000`, 110 files, `down_revision=20261119_0001` |
| B5 migration live round-trip | disposable PG `gula_b5_migration_verify` (`172.18.0.2:5432`) | `alembic upgrade head` **EXIT=0** (head `20261119_0002`, 23-column `niam_delegations`, depth CHECK verified) → `alembic downgrade -1` **EXIT=0** (head `20261119_0001`, table count 0) → `alembic upgrade head` **EXIT=0** (table restored) → throwaway DB **dropped**. No operational DB/data touched |
| OpenAPI stability | `app.main.app.openapi()` | **1815 paths** (unchanged) |

The final Tier B tree full suite was rerun after all Tier B changes:
`/tmp/opencode/final_tree_full_suite_tierB.log` —
`ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <pinned py> -m pytest tests/ -q`
→ **5105 passed, 27 skipped, 203 warnings, EXIT=0 (12m03s)**, zero failures (supersedes the `4984`
step-up-tree run). After the B5 security fixes, the same command was rerun on the post-fix tree:
`/tmp/opencode/final_tree_full_suite_b5_fixed.log` →
**5117 passed, 27 skipped, 203 warnings, EXIT=0 (13m12s)**, zero failures (`5117 = 5105 + 12` new
regressions). The post-fix run is authoritative for final-tree claims. Both results are folded into
`MASTER_EXECUTION_STATUS.md` (§3/§5), `FINAL_ACCEPTANCE_REPORT.md` (criteria 3/4), and
`GOVERNANCE/EXECUTION_LEDGER.md` (rows T-B-05/T-B-10).

---

## 5. Residual risks / policy dependencies

- B3 canonical NHID remains `NEEDS_OWNER_DECISION / LEGAL_REVIEW_REQUIRED / BLOCKED`; no NHID is minted
  by this work. Iraqi legal specifics for guardian/consent remain documented policy dependencies; no
  legal or clinical approval is fabricated.
- B4 residual risks R-1…R-4 (global policy-mutation routes, role-assignment scope, pre-authorization
  denial audit, purpose/evidence binding) are recorded in `INDEPENDENT_VERIFICATION_TEAM_C_B4.md` and
  remain for a follow-up owner decision.
- Post-fix final-tree full-suite result is recorded above (`5117 passed / 0 failed`); the fresh-context
  Team C Tier B verdict is recorded in §8 below and the B5 re-verification is pending. This
  implementer report does not self-award any `INDEPENDENTLY VERIFIED` status.

---

## 6. `status_registry.json` raw-substring reconciliation

A naive substring scan of `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json` reports
`"PRODUCTION READY"` × 7 and `"production_ready"` × 4. A deterministic structural walk of the parsed
JSON proves these are **not** status assignments: exact string-value assignments of `"PRODUCTION READY"`
= **0**; the four `production_ready*` fields (`$.production_ready_items`,
`$.phase_b.production_ready_items`,
`$.adversarial_assurance.findings_register.production_ready`,
`$.adversarial_assurance.remediation_register.production_ready`) are all **0** (nonzero count fields =
0). The raw hits are the vocabulary definition, count-field names, negation strings, and the
`critical_path` line "production readiness (BLOCKED)". Invariant `production_ready_items == 0` holds.

---

## 7. Verdict summary

| Control | Implementer status | Independent (Team C) status |
|---|---|---|
| B1 | `IMPLEMENTED / TESTED` | `INDEPENDENTLY VERIFIED` (engineering scope, later verifier pass) |
| B2 | `IMPLEMENTED / TESTED` | `INDEPENDENTLY VERIFIED` (engineering scope) |
| B3 | `IMPLEMENTED / TESTED` | `INDEPENDENTLY VERIFIED` (engineering scope) |
| B5 | `IMPLEMENTED / TESTED` | `INDEPENDENTLY VERIFIED` (engineering scope) — all 3 prior findings remediated and re-verified (§8) |

No `INDEPENDENTLY VERIFIED` and no `PRODUCTION READY` awarded by this implementer report. Team C is
authoritative for independent verification.

---

## 8. Fresh-context Team C Tier B verdict (2026-11-19)

Authoritative report: `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md`
(timestamp `2026-11-19T09:38:19Z`). **Two fresh-context passes conflict; the later, more adversarial
and evidence-backed pass governs.** The earlier pass (14+22+16 probes) reported no bypass; the later
pass re-executed the implementer suite (**226 passed, EXIT=0**) and Ruff (clean), and reached:

| Control | Verdict | Real bypasses |
|---|---|---|
| B1 — centralized PHI permission map | `INDEPENDENTLY VERIFIED` (engineering scope) | 0 |
| B2 — consent / break-glass | `INDEPENDENTLY VERIFIED` (engineering scope) | 0 |
| B3 — verified guardian / minor / NHID | `INDEPENDENTLY VERIFIED` (engineering scope) | 0 |
| B5 — delegation into canonical authority | `BLOCKED` | **2 HIGH findings** |

**B5 findings (report §4):**
1. **Authority laundering (HIGH):** `delegation_service.py:185-218` checks requested permission keys
   only against the role catalog; an actor holding a narrow delegation (only `lab_result.read`) can
   re-delegate `lab_result.export` from the same role, which they do not hold. Reproduced with the
   real `DelegationService` and canonical `effective_permissions()` on disposable SQLite
   (`/tmp/opencode/tierC_probe_b5_escalation.py`). Remediation: check keys against the actor's
   **effective** holding, not just the role catalog.
2. **Integration gap (HIGH):** `POST /authz/delegations` (`routes/authorization.py:345-359`) uses the
   legacy `app.services.authorization_service.DelegationService`, writing the ungoverned `delegations`
   table; canonical `effective_permissions()` reads `niam_delegations`, which no app route writes.
3. **Transitive revocation (MEDIUM residual, report §6.4):** revoking the delegator's direct role
   assignment does not remove the delegate's authority at enforcement time.

Also recorded: B1 seeded-catalog gap (fail-closed false-deny), B2 category-pattern mismatch
(fail-closed), B3 near-majority adapter flag (fail-closed), B3 legacy audit sink, and an unverified
`citizen_ulid` owner-bypass provenance question. B4 residuals R-1…R-4 are unchanged.

`PRODUCTION READY` is not awarded. B5 stayed `BLOCKED` until fixed, regression-tested and
independently re-verified — which has now occurred (below).

**B5 re-verification (third fresh-context pass):** `GOVERNANCE/ADVERSARIAL_ASSURANCE/
INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md` (timestamp `2026-11-19T10:35:28Z`). Re-executed the
focused suite (**238 passed, EXIT=0**), Ruff on all changed scopes (clean), and independent
adversarial probes. Verdicts: finding 1 `INDEPENDENTLY VERIFIED` (exact prior escalation repro now
DENIED; mixed keys, depth-2 holders, scope widening and cross-catalog attempts all fail closed with
correct audit reasons), finding 2 `INDEPENDENTLY VERIFIED` (real-app OpenAPI mounts `/niam/delegations`;
HTTP POST wrote `niam_delegations` and changed `effective_permissions`, revoke removed authority;
all three legacy methods HTTP 410 with no writes; no route imports the legacy service), finding 3
`INDEPENDENTLY VERIFIED` (enforcement-time chain walk denies root/intermediate revoke, expiry,
role/permission deactivation, forged cycle and depth tamper; live depth-2 chain still grants).
**Overall B5 = `INDEPENDENTLY VERIFIED` (engineering scope), zero real API-reachable bypasses.**
One residual defense-in-depth gap is recorded in that report §6 novel probe 1: a directly forged
`niam_delegations` row can carry an unheld key because enforcement validates chain liveness and
catalog membership but not per-hop key attenuation. It requires out-of-band write access to the
canonical table (single production writer), so it is not an API-reachable bypass of the three
findings; recommended follow-up is to attest the parent key set in the chain walk and intersect at
enforcement. No `PRODUCTION READY` awarded.

---

## 9. B5 remediation implemented (2026-11-19) — `TESTED`, independently re-verified

All three Team C B5 findings from §8 have been fixed in the working tree:

| Finding | Fix | Regression |
|---|---|---|
| Authority laundering (HIGH) | `delegation_service.py::delegate_role` checks requested keys against the actor's effective holding (direct = full active catalog; delegated = that delegation's own subset); denies/audits `permission_exceeds_holding_authority` | `test_narrow_delegate_cannot_redelegate_unheld_permission` |
| Integration gap (HIGH) | New canonical `/niam/delegations` API (`app/identity/api/delegations.py`) on `AsyncSession` backed by the single B5 service; legacy `/authz/delegations` failed closed (HTTP 410) | `test_canonical_route_writes_governed_table_and_changes_effective_permissions` (HTTP e2e), `test_legacy_delegation_surface_fails_closed`, `test_canonical_route_registered_on_real_app` |
| Transitive revocation (MEDIUM) | `authorization_service_v2.py::_delegation_chain_valid` validates the full delegator chain at enforcement time | `test_revoking_delegator_direct_role_revokes_delegate_authority`, `test_multi_hop_chain_still_grants_while_live` |

All fixes in `backend/tests/unit/test_b5_security_regressions.py` (6 new tests). Focused Tier B +
canonical suite **238 passed, EXIT=0**; Ruff clean; OpenAPI `1815 → 1817` (+2 intentional canonical
routes, no existing contract changed). Post-fix final-tree full suite **5117 passed / 0 failed,
EXIT=0** (`/tmp/opencode/final_tree_full_suite_b5_fixed.log`, ledger row T-B-10). A third fresh-context Team C pass
(`INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md`) has since confirmed the fixes and awarded B5
`INDEPENDENTLY VERIFIED` (engineering scope) — no `INDEPENDENTLY VERIFIED` status was self-awarded by
this implementer report.
