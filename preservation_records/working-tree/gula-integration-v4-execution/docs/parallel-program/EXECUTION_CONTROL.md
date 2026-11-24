# EXECUTION CONTROL — PROGRAM-GULA-EXECUTION-AUTHORIZATION-002

**Program:** GULA Stable v1.0.0 — Full Isolated Remediation, Verification, Hardening & Stabilization
**Authority:** Project Owner — Explicit Execution Authorization (2026-11-19)
**Mode:** Autonomous engineering execution within the authorized isolated clone
**Priority:** Patient Safety > Data Integrity > Security > Reliability > Interoperability > Performance > UX

---

## 1. Authorization reconciliation

| ID | Decision | Status |
|---|---|---|
| U-01 | Release 3 files for replication | APPROVED |
| U-02 | Isolation Option D (clone + named-file replication) | APPROVED |
| U-03 | Severity reassessment (A02-001→P1, A06-001→P1) | APPROVED; historical classifications preserved in audit history |
| U-04 | Certification halt until A06-001 + A06-002 verified | APPROVED; HALT ACTIVE |
| U-05 | Execute 36 designed tests + static/security/integration/simulation | APPROVED |
| U-06 | emergency-recovery containment + deploy.sh correction in clone | APPROVED; original script never executed |
| U-07 | Ownership assignments (SEC/CLIN/DB-API/ARCH/CI/QA/UX) | OWNER ASSIGNMENT — unassigned roles recorded as UNASSIGNED — HUMAN APPROVAL REQUIRED |
| U-08 | Open architecture ADRs where necessary | APPROVED |

---

## 2. Original repository preservation manifest (capture #1 — before replication)

| Field | Value |
|---|---|
| Path | `/home/samertts/workspace/projects/gula-integration` |
| HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` |
| Branch | `integration/gula-unification-v1` |
| Upstream | `origin/main` |
| Non-report porcelain paths | 389 (protected user work) |
| Worktree entries | 6 (5 active + 1 prunable) |
| Stashes | 2 |

### Authorized files — original hashes and metadata (MUST remain unchanged)

| Original path | Git status | SHA-256 | mtime |
|---|---|---|---|
| `backend/app/services/offline_sync_service.py` | ` M` | `e19e7ca5731920439d927e381a165c616f68d75b13910aae0601fd00eb82dc98` | 2026-11-17 19:19:09 +0300 |
| `backend/tests/test_offline_sync.py` | ` M` | `224fe6bd7e6719e80d8e26caec315d8f4892afdafbecf2bfe67925b36ba5154e` | 2026-11-17 19:19:24 +0300 |
| `backend/tests/test_offline_conflict_synthetic.py` | `??` | `a5bdb7546c8136f09fe5e8afabf06b47da5aae78cde28eccf7849dacc92068fc` | 2026-11-17 19:19:50 +0300 |

**Originals are never moved, deleted, staged, committed, or modified.**

---

## 3. Isolated clone manifest

| Field | Value |
|---|---|
| Path | `/tmp/opencode/gula-isolation-eval` |
| Base HEAD (verified) | `2206654dc713ea2de8c564a3207dfe05fde23549` |
| Base state | clean (0 porcelain paths) |
| Execution branch | `execution/gula-stabilization-v1` |
| Python | 3.10.12 |
| pytest | 9.1.1 |
| cryptography | 49.0.0 |
| `node_modules` | absent (frontend gates require install) |

### Replicated file manifest (SHA-256 recorded after replication)

| Clone path | Source | Replicated SHA-256 | Match |
|---|---|---|---|
| `backend/app/services/offline_sync_service.py` | original ` M` | pending | pending |
| `backend/tests/test_offline_sync.py` | original ` M` | pending | pending |
| `backend/tests/test_offline_conflict_synthetic.py` | original `??` | pending | pending |

---

## 4. Ownership assignments (U-07)

| Role | Assignment | Scope |
|---|---|---|
| SEC | **UNASSIGNED — HUMAN APPROVAL REQUIRED** | Security & identity changes; security fixes implemented conservatively by orchestrator but not formally approved |
| CLIN | **UNASSIGNED — HUMAN APPROVAL REQUIRED** | Clinical policy decisions (thresholds, recipients, QC acceptance) — no clinical values invented |
| DB-API | **UNASSIGNED — HUMAN APPROVAL REQUIRED** | Schema/migration/contract changes — static validation only, no production DB |
| ARCH | **UNASSIGNED — HUMAN APPROVAL REQUIRED** | ADRs drafted with evidence; decisions not finalized |
| CI | **UNASSIGNED — HUMAN APPROVAL REQUIRED** | CI workflow changes in clone only |
| QA | **UNASSIGNED — HUMAN APPROVAL REQUIRED** | Independent verification — orchestrator performs execution, not independent sign-off |
| UX | **UNASSIGNED — HUMAN APPROVAL REQUIRED** | frontend-v3 design/a11y decisions |

> Per instruction, no approvals or identities are invented. All seven roles are
> recorded as UNASSIGNED — HUMAN APPROVAL REQUIRED. Technical work proceeds where it
> does not require inventing clinical values or security policy; such items are
> reported as blockers and never signed off.

---

## 5. Execution boundaries

**AUTHORIZED:** all source changes in the clone, local commits/branches, test execution, dev dependency install, synthetic test DBs, CI/docs changes in clone, P0–P3 remediation, repeated fix-test-review cycles.

**NOT AUTHORIZED:** destructive operations on original, deletion of user work, production deployment/DB, real patient data, publication of unverified clinical behavior, external push/merge to protected branches, secret exposure.

---

## 6. Progress ledger

| Step | Status | Evidence |
|---|---|---|
| 1. Reconcile five planning docs | COMPLETE | Read |
| 2. Verify original + clone state | COMPLETE | §2, §3 |
| 3. Preservation manifest + hashes | COMPLETE | §2 |
| 4. Replicate 3 files into clone | PENDING | — |
| 5. Run 36 designed tests, capture baseline | PENDING | — |
| 6. Fix CONFLICT_QUARANTINE R1–R6 | PENDING | — |
| 7. Six P0 tracks | PENDING | — |
| 8. P1/P2/P3 batches | PENDING | — |
| 9. Integration/security/clinical/offline/FHIR/reliability verification | PENDING | — |
| 10. Release readiness report | PENDING | — |

---

## 7. Certification gate

**HALT ACTIVE** — clinical synchronization certification remains halted until A06-001 and A06-002 pass required verification and acceptance criteria (U-04).
