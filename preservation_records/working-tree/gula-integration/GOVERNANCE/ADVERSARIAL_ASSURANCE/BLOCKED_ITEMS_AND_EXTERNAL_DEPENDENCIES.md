# Blocked Items and External Dependencies

**Artifact class:** Assurance record (honest disclosure, no status award)
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Audited HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Sibling repository:** `gula-platform` — READ-ONLY, pinned `f478676b6fc375338648dde46fbf076c015a3f91`
**Source:** consolidated from `FINDINGS_REGISTER.json` (81 Team A findings) and the nine local remediations in `REMEDIATION_REGISTER.json`.

**Phase 1 update (2026-11-19):** five CRITICAL/HIGH findings previously listed here as fully `BLOCKED` — `AUD-SEC-001`, `AUD-SEC-002`, `AUD-SEC-003`, `AUD-API-002`, `AUD-ARCH-003` — have since been remediated at **engineering scope** and independently verified. `AUD-SEC-003` and a residual in `AUD-API-002` were successfully falsified on the first pass, corrected, and survived fresh-context re-verification with no new defect found. All five are now `INDEPENDENTLY VERIFIED` at engineering scope. `AUD-API-002` and `AUD-ARCH-003` remain owner-gated for any production claim. No `PRODUCTION READY` status is awarded here.

This document records what CANNOT be closed by engineering work in this worktree. Nothing here is awarded `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`. Status words follow the mandated vocabulary: `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`.

---

## 1. Immutable owner-gated decisions (BLOCKED — do not change)

These decisions are protected records. They were left byte-identical and were NOT re-decided by any Team A auditor or by this integration cycle. No authority has supplied a superseding decision.

| Decision | Status | Note |
|---|---|---|
| HOLD (global release decision) | BLOCKED | Preserved. No release/production status may be asserted. |
| MPI REJECT | BLOCKED | Preserved. MPI resume requires a named authority decision. |
| MP-001 | BLOCKED | Preserved. |
| ODR-001 … ODR-004 | BLOCKED | Preserved. |
| D-020 / D-021 | BLOCKED | Preserved. |
| ADR-A … ADR-J | BLOCKED | Preserved. ADR-A 284-table gap remains open. |
| AUD-02 / AUD-07 / AUD-16 | BLOCKED | Preserved. |

**Protected MD5s verified unchanged:**

| Document | MD5 |
|---|---|
| `FINAL_DECISION.md` | `effdfeaf10234678d83b2668c4489552` |
| `MPI_FINAL_INDEPENDENT_AUDIT.md` | `1a02c01563c93b07a7cdb92c0462bf36` |
| `MPI_INDEPENDENT_AUDIT_FINDINGS.md` | `ea3969d09aaf7b0b28a065838b44a594` |

---

## 2. Owner-gated technical decisions still open (BLOCKED)

These require a named authority; engineering must not decide them unilaterally. Each entry cites the finding ID from `FINDINGS_REGISTER.json`.

| Finding | Severity | Owner gate | Status |
|---|---|---|---|
| `AUD-CLIN-001` | CRITICAL | Clinical owner must define recipient, escalation and acknowledgement policy. Durable outbox + honest status are IMPLEMENTED/TESTED; actual clinician delivery is BLOCKED. | BLOCKED (delivery); IMPLEMENTED (alert emission) |
| `AUD-CLIN-002` | HIGH | Clinical/data owner must define authoritative demographic-specific reference ranges and fail-closed behavior for missing ranges. | BLOCKED |
| `AUD-CLIN-004` | HIGH | Clinical formulary/data owner must define rule source, version and tenant-scope policy. | BLOCKED |
| `AUD-MPI-001` | HIGH | Identity/data owner decision on NID provenance and verification authority policy. Fail-closed gate is IMPLEMENTED/TESTED; authority policy is BLOCKED. | BLOCKED (policy); IMPLEMENTED (gate) |
| `AUD-ARCH-003` | HIGH | Identity/security owner ratification required for any **production claim** — designating the single canonical authorization authority changes the Shared Core registry. Engineering fix IMPLEMENTED/TESTED (health_core engine re-scoped SYNTHETIC ONLY; canonical authority named in code; 7-test differential equivalence corpus; ADR recorded) and `INDEPENDENTLY VERIFIED` at engineering scope. | INDEPENDENTLY VERIFIED (engineering); owner ratification PENDING; production claim BLOCKED |
| `AUD-DB-001` | HIGH | Owner decision on database-enforced row-level security (currently application-only tenant isolation). | BLOCKED |
| `AUD-DB-003` | HIGH | Breaking change — claims global idempotency uniqueness and NOT NULL constraints were dropped/downgraded. | BLOCKED |
| `AUD-DB-004` | HIGH | Owner decision — ORM FK to `national_encounters`, which no migration defines across 107 versions; static root cause of the ADR-A 284-table gap. | BLOCKED |
| `AUD-API-002` | HIGH | Breaking change — owner ratification required for any **production claim** on the OAuth2 token-type contract. Engineering fix IMPLEMENTED/TESTED (OAuth2 tokens mint canonical `type='access'` with user claims; `account_kind` persisted via nullable migration `20261118_0001`; domain-less tokens fail closed at mint; 10-test falsification suite) and `INDEPENDENTLY VERIFIED` at engineering scope after re-verification. | INDEPENDENTLY VERIFIED (engineering); owner ratification PENDING; production claim BLOCKED |
| `AUD-ARCH-002`, `AUD-SUP-003` | HIGH | Commit/branch policy + protected governance records require the repository/Program Director owner; the audited tree is not reproducible from HEAD. | BLOCKED |
| `AUD-SEC-001`, `AUD-SEC-002`, `AUD-SEC-003` | CRITICAL | Identity/security architecture defects. **Superseded engineering outcome:** all three safely remediated locally (14/18/13 adversarial tests) and `INDEPENDENTLY VERIFIED` at engineering scope — (001) NIAM control planes require an active elevated governance role, deny-by-default; (002) signed `account_kind` claim with strict collision-safe resolution; (003) staged privileged login with scoped `mfa_pending` token and single-use blacklisting, so password-only login cannot mint full tokens (falsified once, corrected, re-verified). Residual: caller-supplied `*_by` attribution fields in some NIAM routes remain (001); legacy tokens rely on signed `lab_id` derivation (002). No owner gate on the engineering fix; no runtime/operational DB validation. | INDEPENDENTLY VERIFIED (engineering); no production claim |
| `AUD-PERF-001`, `AUD-PERF-002` | HIGH | Performance/SLO claims contradict source defaults; owner must approve honest SLO instrumentation and certification-claim correction. | BLOCKED |
| `AUD-OFF-001`, `AUD-OFF-002`, `AUD-OFF-003`, `AUD-FE-001` | HIGH | Offline-first policy owner — conflict resolution defaults, durable-queue wiring and client-side data store are product/architecture decisions. | BLOCKED |
| `AUD-SUP-002`, `AUD-SUP-004`, `AUD-SUP-006`, `AUD-SUP-007` | HIGH | Supply-chain owner — image pinning, SBOM regeneration, hash-pinned tooling. | BLOCKED |

---

## 3. External dependencies (BLOCKED — no reachable authority/data in this environment)

| Dependency | Finding(s) | Status | Why blocked |
|---|---|---|---|
| Licensed SNOMED CT release dataset | Terminology findings | BLOCKED | Proprietary license; external data not present. No substitution with synthetic or unofficial content is authorized. |
| Official LOINC release dataset | Terminology findings | BLOCKED | Licensed/official release required; not available locally. |
| Official ICD and UCUM pinning | Terminology/interop findings | BLOCKED | Requires authoritative release artifacts and owner-approved version pinning. |
| Full conformance testing | Interop findings | BLOCKED | Requires external test harnesses and authoritative specifications. |
| Real-device E2E (analyzers, lab instruments) | Device-gateway findings | BLOCKED | No hardware; synthetic-only mandate. |
| External FHIR interoperability | Interop findings | BLOCKED | No external endpoint; no government integration permitted. WS-E guard preserved; T6 FHIR HTTP package remains NON-activated. |
| iOS Xcode build | Mobile findings | BLOCKED | macOS/Xcode toolchain unavailable on this Linux host. |
| Durable external audit anchor | Assurance findings | BLOCKED | No external notary/signature authority available; no external publication authorized. |
| Operational PostgreSQL access | NR-011, `AUD-DB-004`, migration verification | BLOCKED | No reachable DB; only SQLite test fixtures. Operational DB access is explicitly out of scope. |
| Production deployment | Global | BLOCKED | No deploy, no PR, no push, no merge authorized. |
| External government integration | Global | BLOCKED | Explicitly prohibited by mandate. |

---

## 4. Unmeasured / not-implemented capabilities (BLOCKED / NOT IMPLEMENTED)

| Item | Finding | Status | Detail |
|---|---|---|---|
| RPO / RTO measurement | `AUD-INF-002` | NOT IMPLEMENTED | No measured values. |
| Restore / PITR drill | `AUD-INF-002` | BLOCKED | No rehearsal on a reachable DB; existing report is untrusted/unverified. `scripts/validate-restore.sh` can return PASS with exit 0 even when `pg_restore` fails (`AUD-INF-001`). |
| Auto-rollback / canary error budget | `AUD-INF-003` | NOT IMPLEMENTED | Rollback is manual-only despite the name; canary has no error-budget gate. |
| Tenant isolation at DB layer | `AUD-DB-001` | NOT IMPLEMENTED | Application-only. |
| Client-side offline data store | `AUD-OFF-003`, `AUD-FE-001` | NOT IMPLEMENTED | No IndexedDB / `navigator.onLine` in `frontend-v3/src`. |
| Real clinician notification delivery | `AUD-CLIN-001` | BLOCKED | Outbox row is durable; no configured delivery worker or recipient. |
| Reproducible audited tree from HEAD | `AUD-ARCH-002`, `AUD-SUP-003` | BLOCKED | Large uncommitted surface; commit policy requires owner approval. |

---

## 5. Residual risk from applied remediations

| Remediation | Residual | Status |
|---|---|---|
| `REM-SUP-001` | Both `pip` and `uv` dependabot ecosystems now target `/backend/`, which may produce duplicate PRs. CI job has not executed on GitHub. | MONITOR (not a blocker) |
| `REM-CLIN-001` | No runtime HTTP/DB integration exercised; delivery policy absent. | BLOCKED (delivery) |
| `REM-MPI-001` | No operational DB validation; authority policy absent. | BLOCKED (policy) |
| `REM-FK-001` | No operational PostgreSQL migration verification. Broad regression on the **final corrected tree**: `4913 passed, 27 skipped, 0 failed, EXIT=0` (see `TEST_EVIDENCE_INDEX.md` §10). | PENDING (operational DB only) |
| `REM-SEC-001` | Caller-supplied `*_by` attribution fields remain in some NIAM control-plane routes — authorization is enforced, but an already-authorized actor could spoof attribution. Independently verified at engineering scope; residual unchanged. | MONITOR |
| `REM-SEC-002` | Legacy tokens without `account_kind` derive domain from signed `lab_id`; collision-safe but requires re-login for an explicit domain. Independently verified at engineering scope. | MONITOR |
| `REM-SEC-003` | Real second-factor delivery to an authenticator/WebAuthn device not exercised; no runtime validation; cross-worker JTI single-use depends on Redis (in-memory fallback otherwise). Independently verified at engineering scope. | MONITOR |
| `REM-API-002` | owner_gated — production claim needs owner ratification of the OAuth2 token contract; legacy `oauth2_access` tokens and NULL-domain tokens intentionally rejected (fail closed, a deliberate behavior change for legacy records). No operational DB validation. Independently verified at engineering scope. | BLOCKED (production claim) |
| `REM-ARCH-003` | owner_gated — production claim needs identity/security owner ratification; differential corpus cannot prove full semantic equivalence for all inputs. Independently verified at engineering scope. | BLOCKED (production claim) |

---

## 6. Assurance boundary statement

- No item in this document has been awarded `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`.
- Independent verification, if recorded, is engineering-only (static review + targeted synthetic tests) and is captured in `INDEPENDENT_VERIFICATION_TEAM_C.md`.
- No external human, clinical, regulatory or government validation was performed.
- All owner-gated decisions listed in §1–§2 remain unchanged and require a named authority with a documented superseding decision before any status change.
- `production_ready_items == 0` across the entire assurance set.
