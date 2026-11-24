# GULA National Identity Architecture Study — Implementation Roadmap (12 Phases)

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`. This roadmap does not change them.

---

## 0. How to read this roadmap

- This is a **recommendation only**. No phase may begin without explicit owner approval and a separate implementation change control; this study creates none.
- **No dates are invented.** Sequencing is by dependency; duration/resourcing are `TO BE DETERMINED` after owner approval.
- Every phase states: dependencies, deliverables, acceptance criteria, security gate, legal gate, test requirements, rollback, and required owner approval.
- Data rule throughout: synthetic or legally authorized de-identified data only; no operational DB, no real citizen data, no assumed government API.
- Honesty rule throughout: contract-envelope tests are not E2E evidence; no service is labeled E2E/RUNTIME/PRODUCTION verified until Phase 12.
- `FINAL_DECISION.md` stays HOLD until the final owner decision in Phase 12.

---

## Phase 1 — Owner decisions & legal basis (governance gate)
- **Depends on:** none.
- **Deliverables:** written owner decisions on authority boundaries (civil registry, NHID issuer, patient-identity authority, guardian/consent authority); legal opinions on statutes named in the brief (currently `UNVERIFIABLE`); approved D-IDENTITY interpretation; external-integration policy.
- **Acceptance:** every open question in `RISKS_AND_OPEN_QUESTIONS.md` §2 assigned owner + decision or explicit deferral; statutory bases documented; legal review signed off.
- **Security gate:** threat model accepted (`SECURITY_AND_PRIVACY_THREAT_MODEL.md`); data-minimization principles approved.
- **Legal gate:** `LEGAL_REVIEW_REQUIRED` items resolved; Law No. 3/2016 / 21/2024 applicability verified or recorded unverifiable.
- **Tests:** none (governance phase).
- **Rollback:** n/a (decisions are reversible via new decision records).
- **Owner approval:** all `NEEDS_OWNER_DECISION` and `LEGAL_REVIEW_REQUIRED` items.

## Phase 2 — Data ownership & migration integrity
- **Depends on:** Phase 1.
- **Deliverables:** resolve or formally archive F-085 bases (`DocIntelBase` 21, `InsBase` 30 classes); preserve NR-011 `env.py` delta `+49/-0`; eliminate duplicate `national_facilities` ownership (F-014); remove raw NID from `documents_json` (`identity_persistence_service.py:65-72`).
- **Acceptance:** migration chain green; no raw NID at rest in identity stores; no destructive/breaking migration; byte-stability of generated artifacts.
- **Security gate:** no raw NID in any store/log; archival of dormant plaintext-NID engine (`identity_engine/`).
- **Legal gate:** retention/residency rules applied to archived data.
- **Tests:** data-level — no raw NID scan; migration chain regression; F-085 resolution verified.
- **Rollback:** single-revert reversible migrations; archive-first (ADR-028-style), delete only after verification.
- **Owner approval:** archival of bases/engines; any migration touching identity tables.

## Phase 3 — Identity spine (NID, NHID, type vocabulary)
- **Depends on:** Phase 2.
- **Deliverables:** one digit-normalized NID HMAC contract across all callers; single NHID service/namespace/checksum/lifecycle (never reused), distinct temporary namespace; canonical IdentityType vocabulary with NIAM↔national aliases.
- **Acceptance:** hash parity across `identity.py`, `register.py`, `id_scan.py`; NHID uniqueness/never-reused; temp-number overwrite defect fixed (`identity_service.py:15-32` vs `citizen_service.py:74-78`).
- **Security gate:** NID HMAC-only; no NID in URLs/logs; key management approved.
- **Legal gate:** lawful basis for NID collection/matching confirmed (Phase 1).
- **Tests:** unit (hash parity, NHID format, alias map, twin independence); integration (registration→resolve→NHID).
- **Rollback:** migration-based reconciliation of existing hashes; feature-flag rollout.
- **Owner approval:** NHID namespace/issuer; IdentityType authority.

## Phase 4 — Registration spine (self + assisted)
- **Depends on:** Phase 3.
- **Deliverables:** one registration flow over MPI/NIAM; assisted path where staff never hold citizen credentials; zero mandatory per-login external cost; provisional identity support ready; verification codes channel-ownership only.
- **Acceptance:** self and assisted enrollments produce one identity spine; no paid SMS/email OTP dependency; no raw NID persisted.
- **Security gate:** staff cannot set citizen credentials; rate limits; no protected data in URLs.
- **Legal gate:** enrollment consent/data set approved.
- **Tests:** integration (self/assisted enrollment, channel-ownership codes); security (no credential handover, no NID exposure).
- **Rollback:** feature flags; registration path switch-back.
- **Owner approval:** canonical registration path; zero-cost policy confirmation.

## Phase 5 — Authentication safety
- **Depends on:** Phase 4.
- **Deliverables:** fix WebAuthn RP_ID/origin + challenge type (`webauthn.py:22-24,50,61,86,99`); fix `bump_perm_version` signature (`password_reset.py:91`); real device revocation terminating sessions/token blacklist (`device_service.py:79-85`); define enforceable risk policy or remove unused scoring.
- **Acceptance:** passkey flow correct across Android, iOS, Windows, Linux, browsers, low-cost devices; revocation effective; no mandatory external per-login cost.
- **Security gate:** security review of all auth changes; no regression in session security.
- **Legal gate:** none identified beyond Phase 1 policy.
- **Tests:** unit + integration regressions per defect; platform coverage matrix.
- **Rollback:** feature flags; credential re-enrollment path preserved.
- **Owner approval:** supported authenticator/platform matrix.

## Phase 6 — MPI consolidation & correctness
- **Depends on:** Phase 3.
- **Deliverables:** MPI as national patient authority (post-owner-decision); atomic claim repointing on merge; auditable unmerge/split; one configurable matcher (retire 3 scorers); consent/lab-ABAC preserved.
- **Acceptance:** no orphaned claims after merge; unmerge restores linkage with notification; calibrated thresholds (Phase 1 data gate); twins never merged.
- **Security gate:** admin-only merge, hash-chain audit, no auth→access escalation.
- **Legal gate:** merge authority and lawful basis approved.
- **Tests:** integration regressions for `resolver.py:367-369`; unmerge/split; twin non-merge; calibration dataset.
- **Rollback:** merge reversal via unmerge; matcher version pinning.
- **Owner approval:** MPI authority; auto-merge safeguards; matcher consolidation.

## Phase 7 — Provisional identity & reconciliation
- **Depends on:** Phases 3, 6.
- **Deliverables:** provisional healthcare identity for undocumented/unknown patients (no auto-delete, immediate care); reconciliation to MPI on verification; decision on mounting `/national/*` (only with real workflows).
- **Acceptance:** provisional→verified reconciliation audited; no care blocked; national workflows produce real evidence before any mount.
- **Security gate:** provisional ≠ verified; no offline device finalizes verification/merge.
- **Legal gate:** emergency-care duty and provisional status definition approved.
- **Tests:** integration (provisional→verified, child/guardian links); security (no offline finalization).
- **Rollback:** reconciliation reversal; router remains unmounted until gates pass.
- **Owner approval:** mount decision for `/national/*`; provisional policy.

## Phase 8 — Guardian, child & vital lifecycle
- **Depends on:** Phases 1, 7.
- **Deliverables:** one guardianship entity (time-bounded, multiple guardians, history); child NHID independent; age-18 transition job with reversal; birth/death healthcare evidence distinct from civil registration; medical records never deleted; fix lifecycle route↔service mismatch (`routes.py:460-469` vs `services.py:494-504`).
- **Acceptance:** every transition authorized, evidenced, audited, reversible; death ≠ `is_active=False`; no workflow `SUCCEEDED` without artifact; OTP stub removed or implemented.
- **Security gate:** two-person approval for final death/merge/guardian change; offline restrictions.
- **Legal gate:** age-of-majority, exceptions, death/civil registration law (`LEGAL_REVIEW_REQUIRED`).
- **Tests:** unit (state transitions, boundaries); integration (birth/death separation, reversal, guardian transition).
- **Rollback:** transition reversal events; job controlled-window and idempotent.
- **Owner approval:** lifecycle state definitions; age threshold; transition authorities.

## Phase 9 — OCR hardening & calibration (no new engine activation)
- **Depends on:** Phase 1 (authorized data), Phase 4.
- **Deliverables:** `/id-scan` per-field confidence + image-quality gates; Arabic/Iraqi calibration on authorized de-identified/synthetic data; declared/pinned OCR dependencies; remove dummy-byte benchmarks; explicit decision on `document_intelligence/` (rehabilitate or archive — no activation under blockers).
- **Acceptance:** confidence/quality thresholds evidence-based; OCR stays L0 with `needs_confirmation`; no authenticity claim; doc-int remains inactive unless all its blockers cleared.
- **Security gate:** security review for any doc-int activation; no raw image/NID retention; no silence on missing OCR libs.
- **Legal gate:** data-sharing/calibration data authorization.
- **Tests:** calibration measurements; unit (Arabic fields, date boundary, quality rejection); security (L0 cap, no authenticity claim).
- **Rollback:** feature flags; engine version pinning; doc-int stays dormant if gates fail.
- **Owner approval:** OCR engine choice; doc-int disposition; calibration data access.

## Phase 10 — Verification & external integration (legal-gated)
- **Depends on:** Phases 1, 9.
- **Deliverables:** preserve `VerificationPolicy` OCR/NFC = L0; gate/remove stub `confidence:1.0` connectors (`connector_service.py:85-123`); define external verification contracts **without assuming availability**; fail-closed verification with attribution/audit.
- **Acceptance:** no stub emits verified confidence; no external call without signed agreement; digital-signature verification real or explicitly absent.
- **Security gate:** fail-closed; least privilege; full audit.
- **Legal gate:** any government/civil-registry/NFC integration requires legal agreement and owner approval (`BLOCKED_BY_EXTERNAL_DEPENDENCY`).
- **Tests:** unit (assurance map, production guard); integration (verification fails closed when verifier unavailable).
- **Rollback:** verifier disable switch; feature flags.
- **Owner approval:** any external integration; verification assurance policy.

## Phase 11 — API contracts & test-honesty alignment
- **Depends on:** Phases 2–10 (as applicable).
- **Deliverables:** remove NID from query strings (`routes/identity.py:67`); versioned, structured-error, idempotent contracts; per-operation scopes; distinct contract-envelope vs E2E test labeling; regression tests for every verified defect.
- **Acceptance:** OpenAPI stability checks pass; no protected identifiers in URLs; every high-risk defect has a catch test; completion report language still honest.
- **Security gate:** per-operation authorization; no data in URLs/logs.
- **Legal gate:** contract change records where lawful basis changes.
- **Tests:** contract schema validation; security tests; regression suite; brain/baseline updates in the platform repo as separately authorized.
- **Rollback:** versioned contract rollback; feature flags.
- **Owner approval:** canonical public identity contract; scope model.

## Phase 12 — Runtime E2E, DR measurement & release decision
- **Depends on:** Phases 1–11 complete.
- **Deliverables:** synthetic-data runtime E2E journeys with real app boot + DB + Redis; RPO/RTO measurement; DR round trip; updated completion baseline; final owner decision on `FINAL_DECISION.md`.
- **Acceptance:** E2E/RUNTIME journeys pass with evidence; RPO/RTO measured (currently `UNMEASURED`); no E2E claim from contract-envelope tests; final safety check green.
- **Security gate:** full security regression; threat-model goals verified.
- **Legal gate:** all `LEGAL_REVIEW_REQUIRED` items closed.
- **Tests:** runtime E2E (distinct from contract tests); DR drill; performance; DR documentation.
- **Rollback:** staged rollout with rollback plan; `FINAL_DECISION.md` can stay HOLD if gates fail.
- **Owner approval:** **only the owner may change HOLD** — this study never does.

---

## 1. Phase dependency summary

```
Phase 1 (decisions/legal)
   ├─ Phase 2 (data/migrations) ── Phase 3 (identity spine) ─┬─ Phase 4 (registration) ── Phase 5 (auth)
   │                                                        ├─ Phase 6 (MPI) ── Phase 7 (provisional)
   │                                                        └─ Phase 7 ── Phase 8 (guardian/vital)
   ├─ Phase 9 (OCR, data-gated) ── Phase 10 (verification, legal-gated)
   └─ Phases 2–10 ── Phase 11 (contracts/tests) ── Phase 12 (E2E/DR/release decision)
```

**Critical path:** Phase 1 → 2 → 3 → 6 → 7 → 8 → 11 → 12. OCR (9) and verification (10) are parallelizable after Phase 1 but remain legally/data gated.

---

## 2. Cross-references

`MASTER_ARCHITECTURE.md` · `ARCHITECTURAL_DECISIONS.md` · `RISKS_AND_OPEN_QUESTIONS.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · all workstream documents · read-only baselines `GOVERNANCE/FINAL_DECISION.md`, `GOVERNANCE/GECS/GECS_CHECKPOINT.md`, `GOVERNANCE/NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md`, `GOVERNANCE/DATABASE_OWNERSHIP_MATRIX.md`.
