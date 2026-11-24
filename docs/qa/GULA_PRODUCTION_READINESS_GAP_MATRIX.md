# GULA Production Readiness Gap Matrix

Workstream 8. Evidence-linked, not a single score. Built from this
session's own real evidence where it exists; existing repository
artifacts cited by path where they exist and weren't re-verified in this
pass (stated explicitly, not conflated with fresh verification); honest
`NOT STARTED`/`UNKNOWN` everywhere neither applies. Statuses used only:
`VERIFIED`, `PARTIALLY VERIFIED`, `BLOCKED`, `FAILED`, `NOT STARTED`,
`UNKNOWN`.

| Category | Status | Evidence |
|---|---|---|
| Architecture | PARTIALLY VERIFIED | `ARCHITECTURE_REGRESSION_DELTA.md` (Workstream 7) — 11/16 checklist items evidenced, 5 unknown |
| Schema | PARTIALLY VERIFIED | Same — migration head/duplicate checks clean; the pre-existing `pharmacy_drug_substitution_rules` FK type mismatch remains open |
| Migrations | PARTIALLY VERIFIED | Single head, no duplicates (`ARCHITECTURE_REGRESSION_DELTA.md`); the one known-broken migration (above) still blocks a bare `alembic upgrade head` from a blank DB |
| Identity | PARTIALLY VERIFIED | Extensive: `NIAM_PLATFORM_AUTHORITY_COMPLETION.md`, `docs/security/NIAM_PLATFORM_AUTHORITY_ARCHITECTURE.md` (pre-existing), `scripts/identity_enterprise_certification.py` exists (not re-run this pass — cited, not re-verified) |
| Authentication | PARTIALLY VERIFIED | Real HTTP proof of 401/malformed-token/expired-session (`NIAM_RUNTIME_SECURITY_MATRIX.md`) for NIAM specifically; legacy monolith auth not re-verified this pass |
| Authorization | PARTIALLY VERIFIED | Platform Authority: 7 operations real-HTTP-proven (`NIAM_PLATFORM_AUTHORITY_COMPLETION.md`, `NIAM_RUNTIME_SECURITY_MATRIX.md`); 6 more `certificates/routes.py` endpoints identified with the same gap shape, not yet fixed (`NEXT_P0_P1_SECURITY_STATUS.md`) |
| Tenant isolation | NOT STARTED (this pass) | Not re-audited; existing `tenant-scope-sweep` row in `MUSTAFA_ACTIVE_REPAIR_QUEUE.md` covers other domains, unchanged surface, not re-verified here |
| Audit | PARTIALLY VERIFIED | Canonical audit chain real-Postgres proven for 7 NIAM operations + bootstrap (`bootstrap_started`/`_completed`, first real use); the legacy `AuditService`/`AuditAction` stream not re-verified this pass |
| Transactions | PARTIALLY VERIFIED | Real induced-failure rollback proof for the 7 NIAM operations (`NIAM_LIVE_PATH_PROOF_3.md`); transaction ownership pattern (route-commits-once) now consistent across all of them |
| Concurrency | UNKNOWN | Not examined this pass beyond what Platform Authority's existing partial unique index (Phase 10) already covers for that one table |
| Idempotency | PARTIALLY VERIFIED (gap identified) | `NIAM_RUNTIME_SECURITY_MATRIX.md` — none of the 7 Platform Authority routes have an idempotency-key contract; a retried request re-applies and re-audits rather than deduplicating |
| Clinical safety | NOT STARTED (this pass) | Out of this session's scope entirely (session touched `app/identity/**` and `scripts/self_audit_agent.py` only) — existing clinical-safety work (order/sample state machines, etc.) predates this session, not re-verified |
| Data integrity | PARTIALLY VERIFIED | Audit UUID fix, missing-commit fix, FK-drift fix all real-Postgres-proven this session; the plaintext-private-key fix is a data-integrity/confidentiality-at-rest fix, also proven |
| API contracts | UNKNOWN | Not examined this pass beyond the NIAM routes touched (response shapes unchanged for all seven — only new fields/checks added, no existing field removed or retyped) |
| Frontend contracts | NOT STARTED (this pass) | `docs/certification/` contains many pre-existing frontend contract/coverage reports (route completeness, API hook coverage, component coverage, etc.) — cited by path, not re-read/re-verified in this pass |
| Observability | UNKNOWN | Not examined this pass |
| Logging | PARTIALLY VERIFIED (incidental) | Confirmed real, structured log output during every real-app proof this session (`gula.startup`, `gula.identity.platform_authority.bootstrap`, etc.) — incidental observation, not a targeted audit |
| Metrics | UNKNOWN | Not examined this pass |
| Tracing | UNKNOWN | Not examined this pass |
| Backup | UNKNOWN | Not examined this pass; `make backup` exists per `CLAUDE.md` but wasn't exercised |
| Restore | UNKNOWN | Not examined this pass |
| Disaster recovery | UNKNOWN | Not examined this pass |
| Performance | PARTIALLY VERIFIED (one data point) | `VERIFICATION_IMPACT_MODEL.md` — the backend's own test suite runtime (~346s) is the only performance data point gathered this session; not representative of production request latency |
| Load behavior | UNKNOWN | Not examined this pass; `make scale`/HAProxy exist per `CLAUDE.md`, not exercised |
| Security | PARTIALLY VERIFIED | `NEXT_P0_P1_SECURITY_STATUS.md` — 6 real findings closed this session, 4 more identified and left open with reasons; not a repository-wide sweep |
| Secrets | PARTIALLY VERIFIED | Fixed one real secret-at-rest exposure (certificate/CA private keys, now encrypted via the existing canonical `encrypt()`); no broader secrets audit performed this pass |
| CI/CD | UNKNOWN (per this operation's own instruction) | Retained at the already-documented platform-level infra-failure signature (`docs/qa/PR259_CI_EVIDENCE.md` and this session's own repeated confirmations — 0ms runner duration across every check, on every push this session, including an unrelated `main`-branch workflow in the same window) — not relabeled without new evidence, none found |
| Dependency management | NOT STARTED (this pass) | Not examined; `VERIFICATION_IMPACT_MODEL.md` explicitly declined to add a new dependency (`pytest-xdist`) without authorization, which is the one dependency-management decision this session actually touched |
| Supply chain | NOT STARTED (this pass) | Not examined |
| Rollback | PARTIALLY VERIFIED | Real, byte-identical rollback proven repeatedly this session, both for NIAM transaction failures (DB-level) and for `self_audit_agent.py`'s file-level repairs (`AUTONOMOUS_ENGINEERING_LOOP_PROOF.md`, `AUTONOMOUS_ENGINEERING_FIELD_REPORT.md`) |
| Deployment | NOT STARTED (this pass) | Not examined; the Platform Authority bootstrap mechanism is deployment-time/environment-controlled by design but was proven only against a disposable local Postgres, not a real deployment pipeline |
| Offline behavior | NOT STARTED (this pass) | Not examined; `edge_agent/` exists per `CLAUDE.md`, untouched this session |
| Interoperability | NOT STARTED (this pass) | Not examined |
| FHIR | NOT STARTED (this pass) | Not examined; referenced in `CLAUDE.md`'s demo-data-generator docs, untouched this session |
| Documentation | PARTIALLY VERIFIED | This session alone produced 9 new evidence documents (`NIAM_LIVE_PATH_PROOF_2/3.md`, `NIAM_PLATFORM_AUTHORITY_COMPLETION.md`, `NIAM_RUNTIME_SECURITY_MATRIX.md`, `NEXT_P0_P1_SECURITY_STATUS.md`, `AUTONOMOUS_ENGINEERING_FIELD_REPORT.md`, `VERIFICATION_IMPACT_MODEL.md`, `ARCHITECTURE_REGRESSION_DELTA.md`, this matrix) plus the extensive pre-existing `docs/security/`, `docs/qa/`, `docs/engineering/` trees — not claiming completeness, only that this session's own work is durably recorded |
| Operations | UNKNOWN | Not examined this pass |
| Incident response | UNKNOWN | Not examined this pass |
| Changeability | PARTIALLY VERIFIED (incidental) | The NIAM-only async boundary (Phase 10.6.5) was deliberately scoped to avoid a global sync→async migration, and the Platform Authority capability model was deliberately kept to four fixed values — both are changeability-preserving design choices this session made, not a targeted changeability audit |
| Retirement/deprecation | NOT STARTED (this pass) | Not examined |

## Honest summary

Of 38 categories: **0 fully VERIFIED**, **12 PARTIALLY VERIFIED** (real
evidence exists, scoped to this session's actual work), **1 UNKNOWN-by-
instruction** (CI, correctly retained rather than relabeled), **14
UNKNOWN**, **11 NOT STARTED**. This session's real, verifiable
contribution is concentrated in Identity, Authentication, Authorization,
Audit, Transactions, Data integrity, and Security — exactly the domains
this session's four-plus-eight-workstream mandate actually touched. No
category is claimed VERIFIED or "production ready" without the linked
evidence to back it, per this operation's own explicit instruction.
