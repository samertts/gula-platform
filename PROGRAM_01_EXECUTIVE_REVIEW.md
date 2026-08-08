# PROGRAM-01 EXECUTIVE REVIEW — Pre-Wave-5 Go/No-Go

> **Prepared by:** Autonomous Chief Software Architect / Program Director review request
> **Stage:** PROGRAM-01 Wave 4 certification — before Wave 5 (orders 20–22) and Wave 6 (orders 23–24)
> **Scope:** Analysis only — no code changes, no migrations, no new ADRs in this review
> **Inputs:** `TECHNICAL_DEBT_REGISTER.md` (new), `.ai/core/architecture/constitution_baseline.json`,
> `ARCHITECTURAL_MIGRATION_CLASSIFICATION.md`, `ARCHITECTURE_CONSTITUTION.md`,
> `COMMIT_3_6_VERIFICATION_REPORT.md`, `PROGRAM-01_DASHBOARD.md`, `MASTER_REMAINING_WORK.md`

---

## 1. Executive Summary

Program-01 has migrated the Shared Core debt from **51 → 27 acknowledged findings** with
**0 new findings since the deterministic baseline was established**. Four waves have
landed: false-positive removal, dead-code archiving, canonical provider promotion, and
canonical provider completion — culminating in Commit 3.6 (ADR-036) which retired the
**broken `national/workflow_runtime`** (0-byte `service.py` → HTTP 500 surface, now fully
archived, canonical `backend/app/workflows` remains the single engine).

**Verification state (Commit 3.6 final):**
- Backend: **5080 passed / 0 failed** (658.54 s)
- Frontend: vitest **122 passed**, `tsc` 0, `eslint` 0
- Lint: ruff **378** (< 379 baseline)
- Boot: **118 routes**; OpenAPI **2006 methods / 1677 paths** — zero `/national/workflows/*`
- Architecture gate: **PASS** — 27/27 acknowledged, 0 new; Domain 11/11; Country PASS; Policy PASS
- Git: working tree CLEAN; commits `6aadb55c` `83c4601b` `a03794e5` authored (ahead of origin 3, not pushed)

**Recommendation: GO for Wave 5 (conditional).** Wave 5 consists of only **2 actionable
archives** (#1 doc-intel `EncryptionService`, #2 ecosystem `EncryptionEngine` module surgery)
plus **authorization Retain registration** (#21+#30, ADR-034). Wave 6 is documentation +
register (ADR-030/034) with **zero production movement**. All remaining 25 findings are
Retain/Strategic-Exception — they are legitimate domain-owned or kernel-backbone code, not
Shared Core violations. Gate stays deterministic: any NEW finding fails.

---

## 2. Findings Audit — Every Remaining Finding Classified (A–E)

Classification key — **A** Complete-in-Program-01, **B** Program-02 (defer), **C** Strategic
exception, **D** Retain-as-domain-owned (document, don't migrate), **E** False positive /
de-facto canonical facade.

| Class | Meaning | Count | Findings |
|---|---|---|---|
| **A** | Actionable in Program-01 (only the 2 encryption module surgeries) | 2 | #1, #2 |
| **B** | Defer to Program-02 (code churn, no behavior gain) | 0 | — |
| **C** | Strategic exception (kernel backbone, canonical is strict subset) | 1 | #18 (+ #11/#32/#33 folded, see D) |
| **D** | Retain as domain-owned (register + document) | 22 | #4, #8, #10, #12, #13, #14, #15, #16, #19, #21, #23, #29, #30, #31, #34, #37, #40, #41, #45, #11, #32, #33 |
| **E** | False positive / canonical facade | 2 | #26, #48 |
| | **Total** | **27** | |

### 2.1 Class A — Actionable (Wave 5, 2 findings)

| # | Finding | Why now | Risk |
|---|---|---|---|
| 1 | `document_intelligence/security.py` `EncryptionService` / Fernet | Dormant-orchestrator path; module surgery to canonical `shared/security` / `backend/app/security`; no live consumer churn | L |
| 2 | `national/ecosystem/transformation/engine.py` Fernet usage | Live (ecosystem router wired, `routes.py` instantiates `TransformationEngine`); carve-out to canonical encryption, behavior-preserving | L |

Both are `Fernet(` signal matches — the remaining encryption duplication. Order 20 (#2, live)
and order 21 (#1, dormant) as scheduled in the Wave 5 roadmap.

### 2.2 Class C — Strategic Exception (Wave 6, 1 finding)

| # | Finding | Evidence |
|---|---|---|
| 18 | `kernel/event_bus/bus.py` `EventBus` (809 L: store/outbox/DLQ/replay) | LIVE kernel backbone (15 importers). Canonical `shared/events` is a 41-L sync strict subset. Migration = rewrite with **no behavior gain**, H risk. ADR-030 registers the exception. |

### 2.3 Class D — Retain as Domain-Owned (Wave 6, 22 findings)

- **Interfaces / ABCs (8, zero-impl, L risk):** #4, #8, #12, #14, #15, #31, #34, #45 (doc-intel
  + national doc-platform + task-engine interfaces).
- **Real impls where canonical is a stub or different scheme (6):** #13, #16 (canonical
  `capabilities/document_management` routes are stubs; live repos cannot be re-pointed), #19
  (national-id vs NIAM), #23 (in-memory inbox vs delivery), #37 (re-exported public FHIR API),
  #41 (doc-verify token, not image QR).
- **Legacy live path with strategic NIAM destination (3):** #21, #30 (`services/authorization_service.py`
  — lab-UI scoped, DB-backed; ADR-034 registers, no forced migration), #10 (decision-log schema
  canonical lacks).
- **Component-governance / kernel runtime (4):** #29 (`control_plane` policy enforcer, not user
  access control), #11, #32, #33 (kernel DI/scheduler — LIVE bootloader infra, ADR-030 kernel-domain register).
- **Data-format coupling (1):** #40 (`generate_barcode`, live LIMS column default; re-point changes barcode values = data impact).

### 2.4 Class E — False Positive / Facade (register only, 2 findings)

| # | Finding | Evidence |
|---|---|---|
| 26 | `platform/notifications.py` `NotificationService` | Is the canonical facade — delegates to `app.notifications`, zero duplication |
| 48 | `kernel/runtime_sdk.py` `publish_event` | Facade over kernel bus, not a reimplementation |

---

## 3. Technical-Debt Register Reference

See **`TECHNICAL_DEBT_REGISTER.md`** (new) for the full per-finding register with
runtime-reachability evidence (LIVE vs DORMANT), risk, ADR, and wave assignment, plus
**12 non-finding program-level debt items** (deployment, CI/CD release pipeline, DR restore
untested, ENCRYPTION_KEY rotation unexercised, frontend `/metrics`, 71 N999, mypy timeout,
62 backref, 67 untranslated pages, zero-drift doc churn, PG container network pinning).

---

## 4. Readiness Scorecard (8 Dimensions)

| Dimension | Score | Rationale |
|---|---|---|
| Architecture | 0.82 | 27→0-actionable after W5+W6; 11/11 domain isolation; canonical providers authoritative; gate deterministic |
| Security | 0.85 | SQLi fixed, 0 audit advisories (react-router 8), encryption #1/#2 carve-out is the last Fernet duplication |
| Testing | 0.84 | 5080 backend + 122 frontend pass; 0 failures; regression per bug/feature policy enforced |
| Performance | 0.80 | 0 bottlenecks; p95 ≤35 ms; 18/18 budget tests; boot ~24 s once-per-worker |
| Reliability | 0.78 | Retry/circuit/outbox self-heal covered; DR restore (TD-04) and rotation (TD-05) unexercised |
| Observability | 0.75 | Prometheus + OTLP + health/ready/deep; frontend `/metrics` WARN (TD-03) |
| Deployment | 0.70 | Non-root images, K8s 43 manifests, compose hardened; no release pipeline (TD-02), compose-v2 gap (TD-01) |
| Governance | 0.90 | Baseline-gated CI, ADR chain, brain fresh, wave cert process operational |

**Overall readiness: 0.805** — production-trainable; Wave 5/6 closes the last actionable
Shared Core debt with near-zero residual risk.

---

## 5. Roadmap Reorder (effort × risk × dependency × benefit)

Current order is already near-optimal. No reorder required; rationale documented:

1. **Order 20 (#2, live Fernet carve-out)** → **Order 21 (#1, dormant Fernet)** — do the live
   one first (higher value, real reachability), then the dormant one (lowest risk clean-up).
   Both L risk, no ADR (no new canonical surface, no API change).
2. **Order 22 (#21+#30 Retain, ADR-034)** — no code movement; must follow #20/#21 so the ADR-034
   register lists the *final* 25-finding state (post-encryption).
3. **Wave 6 — orders 23–24 (#18 SE + #11/#32/#33 kernel register ADR-030; then 21-finding
   domain register ADR-034)** — documentation-only, gate-recognition; concludes the program with
   27 → 0 actionable.

No dependency conflict: nothing in W5 depends on W6; W6's registers must be written after W5
to reflect the post-carve-out baseline (25 retained).

---

## 6. Go/No-Go Recommendation

**GO — with conditions.**

- **Approve** Wave 4 certification sign-off (Commit 3.6 evidence is final: 5080 pass, gate PASS, tree clean).
- **Approve** Wave 5 (orders 20–22): two behavior-preserving encryption module surgeries
  (#2 then #1) + authorization Retain registration (ADR-034). L risk each, single-revert reversible (ADR-028).
- **Defer** Wave 6 (orders 23–24) to the immediately following approval — zero production
  movement, but the ADR-030/034 registers are the program's closing artifacts.
- **Program-02** is not required for Shared Core closure; remaining debt is the documented
  non-finding register (TD-01…12) owned by the permanent engineering loop.

**Conditions before each Wave-5 commit:** full suite + ruff + tsc + eslint + architecture gate
PASS; OpenAPI byte-identical; Migration Impact Report per commit (ADR-028); STOP and await
explicit Program Director approval after each commit (constitution §1.7).

---

## 7. Stopping Condition (per constitution)

This review is **analysis only**. No production code, migrations, or ADRs were changed.
Awaiting explicit Program Director approval for: (a) Wave 4 certification sign-off,
(b) Wave 5 execution (orders 20–22), (c) Wave 6 (orders 23–24), and (d) PROGRAM-02 charter.
