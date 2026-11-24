# Phase 2 Candidate Plan — Privacy / Security Remediation

**Artifact class:** Planning record — **NO implementation started, NO status awarded**
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Audited HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date:** 2026-11-19

## Gating (mandatory)

Per the program mandate, Phase 2 implementation may begin **only after** all five Phase 1 fixes
are either independently verified by fresh-context Team C **or** precisely blocked with
owner/external dependencies documented. This document is prepared in advance of that gate and
authorizes no code change. Team C Phase 1 report:
`INDEPENDENT_VERIFICATION_TEAM_C_PHASE1.md` and its re-verification addendum
`INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md` (both COMPLETE — all five Phase 1 fixes
`INDEPENDENTLY VERIFIED` at engineering scope, no new defect found). Owner ratification for the
two owner-gated items (AUD-API-002, AUD-ARCH-003) is still required for any production claim.

## Selection method

`FINDINGS_REGISTER.json` was filtered to findings that are **not owner-gated**, **not already
remediated**, and of **HIGH or above severity**. Result: **13 HIGH** findings (listed below);
the remaining 18 non-owner-gated findings are MEDIUM/LOW and are deferred to later tranches.

Each candidate was checked against its original auditor evidence (file + line anchors) to confirm
the defect is a concrete, locally fixable engineering issue rather than a policy/product decision.

## Tier A — engineering-fixable, proceed first after the gate

These have a narrow blast radius, a specific evidence anchor, and a natural adversarial test.
Order is by security/privacy impact.

| # | Finding | Evidence anchor | Proposed remediation (to confirm against source at execution time) | Adversarial falsification to add |
|---|---|---|---|---|
| A1 | `AUD-SEC-007` | `identity/api/workspaces.py:65-89` — async actor query omits `Account.is_locked.is_(False)` present in sync query `:54` | Add the missing lock filter to the async actor resolver; factor a single predicate so sync/async cannot drift | Locked account rejected by async path; locked-but-otherwise-valid actor cannot reach a workspace route |
| A2 | `AUD-API-001` | Active `GET /integration/standards` deterministically raises `AttributeError` (HTTP 500) | Locate the wrong attribute access, correct it, add a happy-path route test | Endpoint returns 200 with a well-formed body; no 500 on the documented path |
| A3 | `AUD-PRV-001` | `services/patient_service.py:324-345` — national-ID duplicate branch queries `Patient.national_id_hash` with **no lab filter** and returns `patient_to_dict(existing)` (full PHI) | Scope the national-ID duplicate lookup to the caller's facility and return only a non-identifying duplicate indicator, not another facility's PHI | Cross-facility national-ID match does not leak name/phone/DOB/health_id; same-facility behavior preserved |
| A4 | `AUD-SEC-004` | `routes/login.py:257-267` logout reads token only from cookies, while `security/dependencies.py:27-35` accepts Bearer first | Revoke the presented token regardless of transport (Bearer or cookie); keep cookie clearing | Bearer logout blacklists the token and a subsequent request with it is rejected; cookie flow still works |
| A5 | `AUD-PRV-003` | `routes/patients.py:39,199` — client `force_create` passed straight into `create_patient`, skipping duplicate detection | Gate `force_create` behind an explicit server-side authorization check (elevated role / reviewed break-glass), never a bare client flag | Unauthorized `force_create=true` cannot bypass duplicate detection; authorized override still works |
| A6 | `AUD-CLIN-003` | Auto-validation critical flags not persisted by the route → critical-result workflow skips the result | Persist the computed critical flag on the result before the workflow reads it | Critical result reaches the critical workflow and alert path; non-critical unaffected |

## Tier B — real but larger blast radius / partial owner input; assess at execution

| # | Finding | Why not Tier A |
|---|---|---|
| B1 | `AUD-SEC-005` — patient PHI routes authenticated but no per-action authorization/consent | Requires mapping every patient route to a permission action; interacts with the Tier-A consent/break-glass work below. Coordinate with `AUD-PRV-002` rather than patch piecemeal. |
| B2 | `AUD-PRV-002` — consent unwired; break-glass is a client-supplied `X-Emergency-Access` header | Removing a client-controlled break-glass header changes an emergency-access workflow. Implementation can fail closed and log, but the *policy* for who may break glass needs owner confirmation before any production claim. |
| B3 | `AUD-PRV-005` — minor/guardian linkage optional and unenforced | Enforcing linkage may break existing minor records; needs a data-policy decision on backfill/fail-closed. |
| B4 | `AUD-SEC-006` — adaptive-auth/MFA/session control plane mounted authentication-only | Broad surface; must be reconciled with Phase 1 `AUD-SEC-003` staged-login and `AUD-SEC-001` control-plane guard to avoid two competing mechanisms. |
| B5 | `AUD-SEC-008` — synthetic Health Core deny-by-default facade not wired into runtime routes | Wiring a second authorization engine into runtime routes conflicts with Phase 1 `AUD-ARCH-003` (single canonical authority). Must be designed as delegation to the canonical authority, not a second engine. **Do not implement before owner ratification of AUD-ARCH-003.** |
| B6 | `AUD-OFF-004` — homebrew operation signature omits timestamp/vector clock; forgeable | Changing the signature format is a wire-format breaking change across offline clients. |
| B7 | `AUD-ARCH-001` — architecture compliance engine fails 7.1/100; L1–L5 all FAIL | Architecture-score remediation is large and partly policy-gated; treat as a separate workstream, not a quick security fix. |

## Deferred (MEDIUM/LOW, non-owner-gated)

`AUD-ARCH-007`, `AUD-DB-002`, `AUD-DB-005`, `AUD-FE-002`, `AUD-FE-003`, `AUD-OFF-005`,
`AUD-OFF-006`, `AUD-PERF-003`, `AUD-PERF-004`, `AUD-PERF-005`, `AUD-PERF-006`, `AUD-PRV-004`,
`AUD-API-007`, `AUD-ARCH-008`, `AUD-ARCH-009`, `AUD-DB-006`, `AUD-FE-004`, `AUD-PERF-007`
— 18 total. `AUD-PRV-004` (raw PII in tamper-evident audit log)
is the highest-priority of these and should lead the following tranche.

## Execution protocol for each selected finding

Identical to Phase 1, and mandatory:

1. Re-read the original auditor evidence from `FINDINGS_A*.json` / `FINDINGS_REGISTER.json`.
2. Reproduce safely (synthetic data only; no operational DB, network, or government integration).
3. Establish root cause; map affected APIs/services/clients/data domains.
4. Implement the strongest justified behavior-preserving fix — **never weaken auth/authz to integrate**.
5. Add adversarial regression tests (falsification-first), plus a backward-compatibility neighbor suite.
6. Verify: targeted tests + Ruff + authoritative gates (`phase_b_gate.py`, `national_integration_verify.py`).
7. Request fresh-context Team C verification before awarding `INDEPENDENTLY VERIFIED`.
8. Update `FINDINGS_REGISTER.json`, `REMEDIATION_REGISTER.json`, `TEST_EVIDENCE_INDEX.md`,
   `status_registry.json`. Keep finding-level `status = DISCOVERED` and `production_ready == 0`.

## Invariants to preserve throughout

- 20 staged `R100` renames under `archive/legacy/workflow_runtime/` untouched; staged count stays 20.
- Protected MD5s (`FINAL_DECISION.md`, MPI audit files) byte-identical.
- Sibling repo `gula-platform` read-only at `f478676b6fc375338648dde46fbf076c015a3f91`.
- No commit, push, PR, merge, deploy, or external integration.
- No `PRODUCTION READY` self-award; owner-gated items remain owner-gated.
