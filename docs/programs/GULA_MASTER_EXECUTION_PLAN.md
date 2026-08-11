# GULA — Master Execution Plan

**Document class:** AUTHORITATIVE sequencing plan (target-state delivery waves)
**Date:** 2026-08-11
**Basis:** Verified current state (GULA_CURRENT_REPOSITORY_STATE.md), gap matrix
(GULA_MASTER_GAP_MATRIX.md), target architecture (GULA_TARGET_ARCHITECTURE.md),
and the successor program (PROGRAM_NEXT_PHASE_PLAN.md / ADR-037).

**Governance gate:** This plan is the authoritative successor to the certified
PROGRAM-REPO-01. **Wave B of the successor program is NOT authorized** until the
Program Director approves. Waves below inherit that gating; every wave stops for
explicit approval before the next begins (PROGRAM-MIGRATION-001 §7).

---

## 1. Guiding Rules

1. Behavior preservation first; every migration reversible (`git revert`).
2. Backend remains the authoritative source of truth; verify OpenAPI + consumers.
3. P0 security/compliance fixes precede all store-facing work.
4. Never trust frontend authorization; server re-validates everywhere.
5. Arabic-first, RTL, national-platform compatibility throughout.
6. No vendor lock-in; self-hosted/local-first preference.

---

## 2. Delivery Waves (dependency-ordered)

### Wave 0 — Recovery & Governance (state captured)
- Complete this audit document set (7 docs) + change control + final report.
- Freeze the verified baseline (S1–S9, C1–C4, risks R-01..R-12).
- **Exit:** current state certified, priorities locked.

### Wave 1 — Security & Compliance P0 (must precede store/production release)
| Task | Ref | Priority |
|---|---|---|
| Auth on `/api/ai/operations` + `/api/ai/providers`; stop Ollama probing; minimize provider inventory leak | S1 | P0 |
| Web Privacy Policy + Terms of Service pages (+ consent page) | F-07/L-01 | P0 |
| Insurance IDOR scoping (`GET /insurance/{id}`) | S2/I-13 | P1 |
| Fix `docker-compose.full.yml` missing `security_opt` | S5/N-02 | P2 |
| K8s ingress control-plane authn (oauth2-proxy/basic-auth) | S6/N-03 | P2 |
| Fix broken CI workflows S7/N-12, S8/N-13, S9/N-14 | — | P1 |
| Pin actions in `ai-governance-enforcement.yml` (SHA) | C4/N-15 | P2 |
| Fix `GET /oauth2/revoke` authn | S3 | P2 |
| **Exit:** no HIGH security findings; legal pages live; CI workflows valid; regression suite green.**

### Wave 2 — Architecture Reconciliation
- Wire or retire `interoperability/` framework (zero importers). — B-06/P1
- Reconcile root experimental app + Dockerfile ambiguity. — D-4/P2
- Regenerate architecture master docs (MASTER_ARCHITECTURE, SHARED_CORE_REGISTRY, DOMAIN docs) after any movement.
- **Exit:** architecture gate PASS (25 ack / 0 new); OpenAPI unchanged where behavior-preserving.

### Wave 3 — Identity / Account / Organization / Authorization (authorized successor Wave B+)
- ABAC route enforcement (Wave B branch `wave-b/B1-abac-route-enforcement`).
- MFA hardening (enrollment audit trail). — I-03/P1
- ABAC conditions coverage expansion. — I-06/P1
- License-gated privilege renewal flow. — I-08/P1
- Organization graph traversal hardening. — I-10/P1
- Frontend authorization alignment (presentation-only, hint role). — F-06/P1
- Purpose-of-Use + consent primitives (build on `legal/`, currently stub). — I-14/B-12/P2
- **Exit:** authorization certified end-to-end (server authoritative); consent primitives usable.

### Wave 4 — App Shell + Workspaces
- Web shell with workspace switcher (all domains via workspaces — no fragmented apps).
- Android workspace model parity.
- iOS (if D-1 = rebuild) workspace parity.
- Desktop (if D-2 = fix) parity.
- **Exit:** one app per platform, workspaces functional across all surfaces.

### Waves 5–9 — Clinical Domains + Engines (in dependency order)
- EHR/clinical, Laboratory/LIS, Radiology/RIS/PACS/DICOM, Pharmacy, Hospital,
  Emergency/EMS, Blood Bank, Public Health, MPI, Research.
- Per-domain: data model → service → routes → tests → e2e → a11y → i18n.
- **Exit per wave:** domain certified (Domain Platform 9-check), full tests green.

### Wave 10 — Integration Hub
- Wire `interoperability/` connectors through the canonical integration surface.
- FHIR terminology service expansion; LOINC/CLSI mapping; analyzer connectors.
- **Exit:** every advertised integration standard is importable and tested.

### Wave 11 — Offline / DR
- Unified DB-backed offline sync engine (vector clocks + idempotency + reconciliation)
  replacing the in-memory mix. — B-09/P1
- iOS (if enabled) offline via Core Data + BGTask.
- Web offline via IndexedDB.
- Quarterly DR drill + RTO target (<4 h) documented.
- **Exit:** every offline surface encrypted, durable, reconcilable; DR drill green.

### Wave 12 — National Control Plane
- Ministry → Directorate → Hospital → Lab analytics surfaces.
- National dashboard/reporting (role-gated, audit-anchored).
- **Legally gated:** no national data flow before Iraq legal sign-off (L-04).

### Wave 13 — AI (hardening + expansion)
- Authenticated admin surface (S1 done in Wave 1).
- Approval workflow + evaluation harness expansions.
- Clinical CDS alerts hardening; RAG experiments gated as EXPERIMENTAL.
- **Exit:** AI classified SAFE/REQUIRES-HARDENING/EXPERIMENTAL; never silently clinical.

### Wave 14 — Entitlements
- Centralized subscription/entitlement (SUBSCRIPTION ≠ AUTHORIZATION). — L-03/P2
- Store metadata real values (fastlane placeholders) — D-6/P1.

### Wave 15 — Security / Scale Certification
- Full OWASP API Top 10 review; pentest; SBOM current; rate-limit budgets.
- Scale simulation (100 → 1M) with partitioning/pgbouncer.
- **Exit:** security certification + scale certification.

### Waves 16–17 — Pilot + Production Expansion
- Governorate pilot → national rollout per governance approval.

---

## 3. Dependency Map (abbreviated)

```
Wave 0 ──► Wave 1 (P0 security/legal) ──► Wave 2 (reconciliation)
              │                              │
              └──────────┬───────────────────┘
                         ▼
                 Wave 3 (identity/authz) ──► Wave 4 (shell+workspaces)
                                              │
              ┌───────────────┬───────────────┼───────────────┐
              ▼               ▼               ▼               ▼
        Wave 5 (EHR)    Wave 6 (Lab)    Wave 7 (Rad)    Wave 8 (Pharma)…
              └──────┬──────┴───────┬────────┴─────┐
                     ▼              ▼              ▼
              Wave 10 (Integrations)  Wave 11 (Offline/DR)  Wave 12 (National)
                     └──────────────┬──────────────┘
                                    ▼
                       Wave 13 (AI) ──► Wave 14 (Entitlements)
                                    ▼
                       Wave 15 (Security/Scale cert)
                                    ▼
                      Waves 16–17 (Pilot → Production)
```

## 4. Change Control (interface to GULA_CHANGE_CONTROL.md)

- Every wave entry: PD approval → one or more atomic, revertible commits →
  verification cycle → wave report → STOP.
- No wave may overlap another; no silent scope creep.
- Concurrent-session branches remain protected throughout.

## 5. Estimated Effort (planning only, not a commitment)

| Wave | Scope | Est. effort |
|---|---|---|
| 0 | State + audit docs (this set) | ~1 day |
| 1 | P0 security/legal/CI | 3–5 days |
| 2 | Reconciliation | 2–3 days |
| 3 | Identity/authz/consent | 2–3 weeks |
| 4 | Shell + workspaces | 1–2 weeks |
| 5–9 | Clinical domains | 2–4 weeks each |
| 10–15 | Integration/offline/national/AI/entitlements/cert | 6–10 weeks |
| 16–17 | Pilot → production | rollout-gated |

---

*Sequencing is advisory until the Program Director approves each wave gate.
Companion: `GULA_MASTER_GAP_MATRIX.md`, `GULA_TARGET_ARCHITECTURE.md`,
`GULA_RISK_REGISTER.md`, `GULA_DEPENDENCY_GRAPH.md`, `GULA_CHANGE_CONTROL.md`.*
