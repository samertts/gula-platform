# GULA — Risk Register

**Document class:** AUTHORITATIVE risk register (verified evidence-based)
**Date:** 2026-08-11
**Basis:** GULA_CURRENT_REPOSITORY_STATE.md §6/§8, GULA_MASTER_GAP_MATRIX.md.

**Scoring:** Likelihood (L) 1–5, Impact (I) 1–5, Score = L × I.
Rating: CRITICAL (≥20) · HIGH (12–19) · MEDIUM (6–11) · LOW (≤5).

---

## 1. Verified Technical Risks (from current-state findings)

| ID | Risk | L | I | Score | Rating | Owner | Mitigation | Wave |
|---|---|---|---|---|---|---|---|---|
| R-01 | iOS app unbuildable (empty Xcode project, no Core Data model) despite store metadata + CI referencing it | 4 | 5 | 20 | **CRITICAL** | Mobile | D-1: rebuild or formal defer; fix/gate `mobile-ios.yml` | W1 |
| R-02 | AI admin endpoints unauthenticated (S1) — provider inventory + Ollama probe leak | 3 | 5 | 15 | HIGH | Security | Auth dependency + stop probing; minimize leak | W1 |
| R-03 | No web Privacy Policy / Terms pages before store production linkage (F-07/L-01) | 4 | 4 | 16 | HIGH | Product | Build legal pages pre-release | W1 |
| R-04 | Desktop drift DB layer broken (`database.g.dart` placeholder) — advertised but non-compiling offline path (M-06) | 4 | 4 | 16 | HIGH | Desktop | D-2: regenerate drift code or archive | W1 |
| R-05 | Three divergent API base domains across clients (M-08) | 4 | 3 | 12 | HIGH | Platform | Unify to one canonical domain | W1 |
| R-06 | Broken CI workflows (S7 duplicate push, S8 lighthouse config, S9 iOS workspace) | 4 | 3 | 12 | HIGH | DevOps | Fix all three; add workflow parse gate | W1 |
| R-07 | Frontend authorization client-side only (S4) — UI self-grant risk if ever trusted | 2 | 5 | 10 | MEDIUM | Authz | Keep server authoritative; document; hint-only UI | W1 |
| R-08 | Offline sync not unified / not DB-persisted except nhdw (B-09) | 3 | 3 | 9 | MEDIUM | Platform | Unified DB-backed engine | W11 |
| R-09 | `interoperability/` framework advertised but zero importers (B-06) | 3 | 3 | 9 | MEDIUM | Interop | Wire or retire; update docs | W2 |
| R-10 | Insurance IDOR candidate (S2) | 2 | 4 | 8 | MEDIUM | Authz | Ownership scoping + tests | W1 |
| R-11 | `legal/` consent module is an 11-line stub with no DB (B-12) — cannot support Purpose-of-Use | 3 | 3 | 9 | MEDIUM | Consent | Build consent primitives | W3 |
| R-12 | Compose full missing `security_opt` (S5) + K8s ingress no control-plane authn (S6) | 3 | 2 | 6 | MEDIUM | DevOps | Harden both | W1 |
| R-13 | OAuth2 revoke unauthenticated (S3) | 2 | 2 | 4 | LOW | Security | Add client/session auth | W1 |
| R-14 | Root experimental app (server/client) ambiguity via root Dockerfile (D-4) | 2 | 2 | 4 | LOW | Platform | Document or archive | W2 |

## 2. Process / Governance Risks

| ID | Risk | L | I | Score | Rating | Mitigation |
|---|---|---|---|---|---|---|
| R-G1 | Wave B of successor program unapproved; scope creep into Wave B territory | 3 | 4 | 12 | HIGH | Gate every wave on PD approval; change control |
| R-G2 | Concurrent sessions working in parallel (branches fetched: manus admin, security-hardening-demo, wave0-audit-hardening) | 3 | 3 | 9 | MEDIUM | Never modify their work; preserve branches; report ownership conflicts |
| R-G3 | National data flow before Iraq legal sign-off (L-04) | 2 | 5 | 10 | MEDIUM | Hard legal gate before any national sharing |
| R-G4 | Store metadata/fastlane placeholders deployed to production stores | 3 | 3 | 9 | MEDIUM | Real values gated on store launch (D-6) |
| R-G5 | v1.0.0 tag / GitHub release premature (ADR-037 §8) | 2 | 4 | 8 | MEDIUM | Keep release deferred; use pre-release semantics |

## 3. Residual / Accepted Risks

- **R-07 (frontend authz)** is accepted as MEDIUM with a documented boundary:
  server-side dependencies are the enforcement point; the frontend `RoleGuard`
  is a UX affordance only. Must never be promoted to an authority.
- **E-402 (167) / N801 (141) / N999 (71) ruff baseline (379)** — accepted
  (documented in validate baseline), not in scope for remediation without approval.
- **62 `backref=` in dormant bounded contexts** — accepted, dormant.

## 4. Risk Trend

- Risk count by rating: CRITICAL 1 (R-01) · HIGH 5 (R-02..R-06) · MEDIUM 7
  (R-07..R-12) + 2 governance (R-G1, R-G3) · LOW 2 (R-13, R-14) + 2 governance
  (R-G4, R-G5).
- P0/Wave-1 remediation removes 1 CRITICAL + 4 HIGH (R-01, R-02, R-03, R-06)
  and reduces R-05/R-04 to tracked items.
- **No new risks introduced by this audit** (read-only; no production change).

---

*Register will be updated as waves execute. Escalation: any risk crossing into
CRITICAL triggers immediate Program Director review. Companion:
`GULA_MASTER_EXECUTION_PLAN.md`, `GULA_CHANGE_CONTROL.md`.*
