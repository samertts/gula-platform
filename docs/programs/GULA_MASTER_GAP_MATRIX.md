# GULA — Master Gap Matrix

**Document class:** AUTHORITATIVE planning artifact (gap analysis)
**Date:** 2026-08-11
**Method:** Evidence-based classification of the actual repository state
(verified at HEAD `f735a7a1`). Each row states the **verified current state**,
the **target classification**, and the **recommended action** with priority.

**Classification legend**
- CURRENT: CERTIFIED / STABLE / PARTIAL / BROKEN / INSECURE / LEGACY / DUPLICATE / EXPERIMENTAL / MISSING
- TARGET: REQUIRED / OPTIONAL / FUTURE
- ACTION: KEEP / FIX / HARDEN / REFACTOR / REPLACE / ARCHIVE / BUILD / DEFER
- Priority: P0 (immediate) / P1 (high) / P2 (medium) / P3 (low)

---

## A. Identity, Account, Authorization

| # | Capability | Current | Target | Action | Priority | Domain | Validation |
|---|---|---|---|---|---|---|---|
| I-01 | Identity types (11 canonical) | CERTIFIED | REQUIRED | KEEP | P2 | Identity | unit tests |
| I-02 | Password auth (bcrypt) + JWT | CERTIFIED | REQUIRED | KEEP | P2 | Identity | tests |
| I-03 | MFA (TOTP + WebAuthn) | CERTIFIED | REQUIRED | HARDEN (review enrollment audit) | P1 | Identity | tests + pentest |
| I-04 | OAuth2/OIDC + SAML | STABLE | REQUIRED | HARDEN | P1 | Identity | tests |
| I-05 | RBAC role→permission | CERTIFIED | REQUIRED | KEEP | P2 | Authz | tests |
| I-06 | ABAC policy engine | STABLE | REQUIRED | HARDEN (conditions coverage) | P1 | Authz | tests |
| I-07 | Workspace platform (8 tables, one active) | CERTIFIED | REQUIRED | KEEP | P2 | Workspace | tests |
| I-08 | Professional license-gated privilege | STABLE | REQUIRED | HARDEN (renewal flow) | P1 | Authz | tests |
| I-09 | Frontend authorization | INSECURE (client-side only, S4) | REQUIRED | HARDEN (keep server authoritative; add UI hints only) | P1 | Frontend | e2e |
| I-10 | Account→Organization→Facility hierarchy | STABLE | REQUIRED | HARDEN (graph traversal) | P1 | Identity | tests |
| I-11 | Citizen registry | STABLE | REQUIRED | HARDEN | P2 | Citizen | tests |
| I-12 | Unauthenticated AI admin endpoints (`/operations`,`/providers`) | **INSECURE** | REQUIRED | **FIX (auth + minimize leak)** | **P0** | Security | tests + audit |
| I-13 | `GET /insurance/{id}` IDOR candidate | PARTIAL | REQUIRED | FIX (ownership scoping) | P1 | Insurance | tests |
| I-14 | Purpose-of-Use access / consent | MISSING (legal module is 11-line stub) | REQUIRED (Wave D) | BUILD | P2 | Consent | tests |

---

## B. Frontend (Web)

| # | Capability | Current | Target | Action | Priority | Validation |
|---|---|---|---|---|---|---|
| F-01 | React 19 shell, routing, lazy loading | CERTIFIED | REQUIRED | KEEP | P2 | e2e |
| F-02 | Auth + MFA UI | STABLE | REQUIRED | KEEP | P2 | tests |
| F-03 | i18n ar/en + RTL (530 keys) | CERTIFIED | REQUIRED | KEEP | P2 | tests |
| F-04 | PWA + service worker | STABLE | REQUIRED | HARDEN (offline UX) | P2 | e2e |
| F-05 | 45+ page areas | STABLE | REQUIRED | KEEP | P2 | e2e |
| F-06 | Client-side RBAC only (S4) | INSECURE | REQUIRED | FIX (never authority; align with server) | P1 | e2e |
| F-07 | Legal pages (privacy/terms/consent) | **MISSING** | REQUIRED (pre-production) | **BUILD** | **P0** | e2e + review |
| F-08 | Accessibility (WCAG) | PARTIAL | REQUIRED | HARDEN | P2 | a11y audit |
| F-09 | Component duplication | PARTIAL | REQUIRED | REFACTOR (consolidate) | P2 | code review |
| F-10 | Offline IndexedDB store | PARTIAL (SW only; no IndexedDB usage) | REQUIRED | BUILD | P2 | e2e |
| F-11 | Test coverage (16 vitest + 8 e2e) | STABLE | REQUIRED | EXPAND | P2 | CI |

---

## C. Backend / Data / Interoperability

| # | Capability | Current | Target | Action | Priority | Validation |
|---|---|---|---|---|---|---|
| B-01 | 1,643-path route surface, 82 routers | STABLE | REQUIRED | KEEP (govern growth) | P2 | architecture gate |
| B-02 | FHIR R4 server + mappers | CERTIFIED | REQUIRED | KEEP | P2 | tests |
| B-03 | HL7 v2 receive + gateway | STABLE | REQUIRED | HARDEN (ACK semantics, validation) | P2 | tests |
| B-04 | DICOM/PACS storage | STABLE | REQUIRED | HARDEN (auth on retrieval) | P1 | tests |
| B-05 | LIS (LIMS) module | STABLE | REQUIRED | KEEP | P2 | tests |
| B-06 | `interoperability/` framework (zero importers) | **DUPLICATE/UNUSED** | REQUIRED | REFACTOR → wire or retire | P1 | architecture gate |
| B-07 | Event bus (outbox/inbox/DLQ/replay) | CERTIFIED | REQUIRED | KEEP | P2 | kernel tests |
| B-08 | Immutable audit (hash-chain + anchors) | CERTIFIED | REQUIRED | KEEP | P2 | chain tests |
| B-09 | Offline sync | PARTIAL (in-memory except nhdw) | REQUIRED | **REFACTOR → unified DB-backed engine** | P1 | tests |
| B-10 | 57-migration chain | CERTIFIED | REQUIRED | KEEP | P2 | migration gate |
| B-11 | Health ID / MPI | STABLE | REQUIRED | HARDEN | P2 | tests |
| B-12 | `legal/` consent stub | **BROKEN** (no DB) | REQUIRED | BUILD | P2 | tests |
| B-13 | `optimization/` + 7 empty dirs | EMPTY | FUTURE | ARCHIVE or BUILD | P3 | — |

---

## D. Mobile

| # | Capability | Current | Target | Action | Priority | Validation |
|---|---|---|---|---|---|---|
| M-01 | Android single app `io.gula.android` | CERTIFIED (buildable) | REQUIRED | KEEP | P2 | CI + tests |
| M-02 | Android offline Room + encrypted prefs | STABLE | REQUIRED | HARDEN | P2 | tests |
| M-03 | Android signing / Play CI | STABLE | REQUIRED | HARDEN (secret hygiene) | P1 | CI |
| M-04 | **iOS application** | **BROKEN** (empty `.xcodeproj`) | REQUIRED | **FIX (regenerate Xcode project)** | **P0** | CI build |
| M-05 | iOS Core Data model | **BROKEN** (missing) | REQUIRED | FIX | **P0** | CI |
| M-06 | Desktop (Flutter) drift DB layer | **BROKEN** (`database.g.dart` placeholder) | OPTIONAL | FIX or ARCHIVE | P1 | CI build |
| M-07 | Desktop lab device discovery | STUB (returns empty) | OPTIONAL | BUILD or DEFER | P2 | tests |
| M-08 | Unified API base domain | **BROKEN** (3 divergent domains) | REQUIRED | FIX (one canonical domain) | P1 | CI |
| M-09 | Store metadata (Play/App Store) | STABLE | REQUIRED | KEEP | P2 | review |

---

## E. Infrastructure / Deployment / Security / Ops

| # | Capability | Current | Target | Action | Priority | Validation |
|---|---|---|---|---|---|---|
| N-01 | Docker Compose production | STABLE | REQUIRED | KEEP | P2 | compose validation |
| N-02 | `docker-compose.full.yml` (48 svc) missing `security_opt` (S5) | INSECURE | OPTIONAL | HARDEN | P2 | config scan |
| N-03 | K8s ingress no control-plane authn (S6) | PARTIAL | FUTURE | HARDEN (oauth2-proxy) | P2 | config |
| N-04 | `services/*` microservice stubs | EXPERIMENTAL | FUTURE | DEFER (not production) | P3 | — |
| N-05 | Helm chart (36 templates) | STABLE | FUTURE | KEEP | P3 | helm lint |
| N-06 | terraform/ | PARTIAL | FUTURE | BUILD | P3 | — |
| N-07 | Deploy pipeline (SSH + health + rollback) | CERTIFIED | REQUIRED | KEEP | P2 | CI |
| N-08 | Blue-green / canary / auto-rollback | STABLE | REQUIRED | KEEP | P2 | CI |
| N-09 | Secrets hygiene | CERTIFIED | REQUIRED | KEEP | P2 | gitleaks + detect-secrets |
| N-10 | Observability (health/ready/deep, metrics, OTLP, JSON logs) | CERTIFIED | REQUIRED | KEEP | P2 | tests |
| N-11 | DR (PG16 drill, RPO≈1min) | CERTIFIED | REQUIRED | KEEP (regular drills) | P1 | DR report |
| N-12 | `build-images.yml` duplicate `push:` (S7) | BROKEN | REQUIRED | FIX | P1 | workflow parse |
| N-13 | `frontend-pwa.yml` missing lighthouse config (S8) | BROKEN | REQUIRED | FIX | P1 | workflow |
| N-14 | `mobile-ios.yml` references missing workspace (S9) | BROKEN | REQUIRED | FIX | P1 | workflow |
| N-15 | `ai-governance-enforcement.yml` unpinned actions (C4) | INSECURE | REQUIRED | HARDEN (SHA pin) | P2 | workflow |

---

## F. AI / Clinical Safety

| # | Capability | Current | Target | Action | Priority | Validation |
|---|---|---|---|---|---|---|
| A-01 | AI provider router (8 providers, local Ollama) | STABLE | REQUIRED | HARDEN | P1 | tests |
| A-02 | AI evaluation harness + clinical suite | STABLE | REQUIRED | KEEP | P2 | tests |
| A-03 | AI approval workflow (suggest→approve→execute) | STABLE | REQUIRED | HARDEN (audit) | P1 | tests |
| A-04 | AI stub-by-default (no keys → no output) | STABLE (safe default) | REQUIRED | KEEP | P2 | boot tests |
| A-05 | Clinical safety (wrong patient/sample/result) | PARTIAL | REQUIRED | HARDEN (verification points) | P1 | clinical tests |
| A-06 | Human-verification mandatory points | PARTIAL | REQUIRED | HARDEN | P1 | policy + tests |

---

## G. Legal / Governance / Commercial

| # | Capability | Current | Target | Action | Priority | Validation |
|---|---|---|---|---|---|---|
| L-01 | Web Privacy Policy / Terms | **MISSING** | REQUIRED (pre-release) | **BUILD** | **P0** | review |
| L-02 | Store terms/privacy metadata | STABLE | REQUIRED | KEEP | P2 | review |
| L-03 | Subscription/entitlement (FREE FOREVER basic) | MISSING | REQUIRED (Wave 14) | BUILD (centralized, SUBSCRIPTION ≠ AUTHORIZATION) | P2 | tests |
| L-04 | Iraq legal sign-off for national data flow | MISSING | REQUIRED gate | DEFER (gated) | P1 | governance |

---

## Priority Summary (actionable ordering)

### P0 — immediate (before any further release/store work)
1. **S1** — auth on `GET /api/ai/operations` + `/api/ai/providers`; remove Ollama probing / provider inventory leak.
2. **F-07 / L-01** — web Privacy Policy + Terms of Service pages.
3. **M-04 / M-05** — regenerate iOS Xcode project + Core Data model (or formally defer iOS).
4. **B-12** — consent/legal module is a stub; cannot support Purpose-of-Use.

### P1 — high (Wave B and adjacent)
5. **B-06** — wire or retire the `interoperability/` framework.
6. **B-09** — unified DB-backed offline sync engine.
7. **M-08** — unify API base domains to one canonical domain.
8. **N-12/N-13/N-14** — fix broken CI workflows.
9. **I-13** — insurance IDOR scoping.
10. **I-03/I-06/I-08** — MFA/ABAC/license hardening.
11. **F-06** — frontend authorization alignment.
12. **M-06** — desktop drift DB layer decision (fix or archive).
13. **L-04** — confirm Iraq legal gate before any national data flow.

### P2/P3 — medium/low (later waves)
14. Remaining HARDEN/REFACTOR/BUILD rows (RTL a11y, offline IndexedDB, entitlement, terraform, etc.).

---

*Every classification above is derived from verified repository evidence
(see `GULA_CURRENT_REPOSITORY_STATE.md` §6 and §9). Where a capability is
marked BROKEN or INSECURE, the exact evidence file:line is cited in the
current-state document.*
