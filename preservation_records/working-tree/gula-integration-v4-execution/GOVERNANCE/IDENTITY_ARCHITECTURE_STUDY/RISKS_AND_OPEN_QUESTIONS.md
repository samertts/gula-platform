# GULA National Identity Architecture Study — Risks & Open Questions

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. All findings are static, read-only observations; runtime impact is `UNVERIFIABLE` (no tests run, no DB contacted). Risk severity is a qualitative study judgment, not a measured metric. No legal conclusion, OCR benchmark, cost figure or external-service availability is asserted.

---

## 1. Consolidated risk register

| ID | Risk | Severity | Evidence / status | Mitigation direction | Classification |
|---|---|---|---|---|---|
| R-01 | Wrongful identity merge/attribution from inconsistent NID hashing and orphaned claims | High | Raw vs digit-normalized HMAC (`register.py:341-343` vs `identity.py:222`); claims not repointed (`resolver.py:367-369`) | One hash contract; claim repointing + unmerge; regression tests | `SECURITY_REVIEW_REQUIRED` |
| R-02 | Raw NID exposure at rest / in logs / in URLs | High | Raw NID in `documents_json` (`identity_persistence_service.py:65-72`); NID query string (`routes/identity.py:67`) | HMAC-only, no NID in URLs/logs; security tests | `SECURITY_REVIEW_REQUIRED` |
| R-03 | Defective authentication (WebAuthn, password reset, device revocation) | High | `shared/auth/webauthn.py:22-24,50,61,86,99`; `password_reset.py:91` vs `session.py:40-47`; `device_service.py:79-85` | Fix + regression tests before trust; zero external cost preserved | `SECURITY_REVIEW_REQUIRED` |
| R-04 | False sense of verification from OCR/document capabilities | High | Stub `confidence:1.0` connectors (`connector_service.py:85-123`); OCR no authenticity check; doc-int encryption/audit stubs | Keep OCR L0; gate stubs; real-or-absent verification | `SECURITY_REVIEW_REQUIRED` |
| R-05 | Document-intelligence platform non-functional / misleading | High | Orchestrator never initialized (`wiring.py:1039-1042`); dummy benchmarks (`providers/base.py:51-72`); unregistered `DocIntelBase` (F-085) | Do not activate; rehabilitate with real services and tests | `SECURITY_REVIEW_REQUIRED` |
| R-06 | Identity fragmentation — multiple authorities, formats, matchers, guardian stores | High | 5+ NHID formats; 3 matchers; 4 guardian stores; competing person registries | Owner decision on authorities; consolidate behind one spine | `NEEDS_OWNER_DECISION` |
| R-07 | Dormant national router activated without real workflows | Medium–High | Router unmounted (`national/api/routes/__init__.py:20-36`); workflows mark `SUCCEEDED` without work | Owner decision before mounting; evidence per step | `NEEDS_OWNER_DECISION` |
| R-08 | Child/guardian and age-transition legal non-compliance | High | Age transition `NOT_IMPLEMENTED`; guardian fragmentation; majority threshold undefined | Legal decision + auditable transition job | `LEGAL_REVIEW_REQUIRED` |
| R-09 | Birth/death evidence conflation leading to wrongful record deletion/state | High | Death may be `is_active=False`; healthcare vs civil evidence not separated; workflow stubs | Distinct vital states; never delete medical records | `OWNER_APPROVED` (D-IDENTITY-06) + `LEGAL_REVIEW_REQUIRED` |
| R-10 | Completion-baseline overstatement (contract-envelope ≠ E2E) | Medium–High | 0 E2E/RUNTIME/PRODUCTION verified, RPO/RTO UNMEASURED (completion report) | Runtime E2E + RPO/RTO measurement before release claim | `NEEDS_OWNER_DECISION` |
| R-11 | F-085 / NR-011 migration debt | Medium | 2 bases / 51 classes unregistered; first-wins merge; `env.py` delta `+49/-0` | Resolve or formally archive bases; preserve delta | `RECOMMENDED` |
| R-12 | Unauthorized external integration / data-sharing | High | Stub government gateway and civil connectors; no legal agreement in repo | No assumed API; legal + owner approval before any integration | `BLOCKED_BY_EXTERNAL_DEPENDENCY` / `LEGAL_REVIEW_REQUIRED` |
| R-13 | Data-protection / statutory non-compliance | High | Iraqi statutes in brief lack verifying source in repo → `UNVERIFIABLE` | Legal review of every collection/matching/retention basis | `LEGAL_REVIEW_REQUIRED` |
| R-14 | Dormant plaintext-NID JSON engine exposure | Medium | `services/identity_engine/citizen_registry.py:4-18` plaintext NID | Formal archival; do not activate | `SECURITY_REVIEW_REQUIRED` |
| R-15 | OCR calibration on unavailable/unsuitable data | Medium | No benchmarks; no authorized Iraqi sample data in repo | Authorized de-identified/synthetic data; thresholds from evidence | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| R-16 | Test coverage gaps on high-risk fixes | Medium | Verified defects lack catch tests (doc-int startup, lifecycle wiring, hash parity, claim repointing) | Regression tests per defect before change | `RECOMMENDED` |
| R-17 | National document signature/QR verification ineffective | High | Signing/verification hash different timestamps (`document_platform/service.py:263` vs `:322`); QR fallback checks existence only, no hash/expiry/signature (`:415-425`) | Repair signing input; validate hash/expiry/signature; security tests | `SECURITY_REVIEW_REQUIRED` |
| R-18 | No image quality / tamper / near-duplicate gates; Arabic-Indic numerals not normalized | Medium–High | `document_intelligence/wiring.py:125-232,454-465`; no tamper detector; exact-SHA-256-only dedup (`repository.py:208-217`); display-only digit conversion (`citizen_platform/accessibility.py:122-127`) | Add quality + tamper + near-duplicate gates and Arabic text normalization | `RECOMMENDED` |

---

## 2. Open questions by workstream

**Identity / NHID (B):**
1. Which registry is authoritative for civil person identity?
2. Who owns NHID issuance; what is the national namespace/checksum? (`LEGAL_REVIEW_REQUIRED`.)
3. How are existing per-surface NID hashes reconciled to one contract?

**Lifecycle (B/I):**
4. What are the lawful status definitions and transition authorities?
5. Is majority exactly 18, and what exceptions apply (unused `EMANCIPATED_AGE = 16`)?
6. Which downstream systems consume death/correction status?

**MPI (C):**
7. Which store is authoritative for patient identity?
8. Which merge cases are safe for deterministic auto-merge, and who approves? (`NEEDS_OWNER_DECISION` / `LEGAL_REVIEW_REQUIRED`.)
9. Can authorized de-identified data be obtained for threshold calibration? (`BLOCKED_BY_EXTERNAL_DEPENDENCY`.)
10. Who is notified on unmerge/split, and with what SLA?

**Registration (D):**
11. Which registration path is canonical (self `register.py` / NIAM lifecycle / national)?
12. What is the lawful enrollment data set and consent basis? (`LEGAL_REVIEW_REQUIRED`.)
13. How are provisional records reconciled, and by whom?

**Authentication (E):**
14. Are WebAuthn/reset/revocation defects confirmed at runtime? (Requires executed test.)
15. Which local credential methods satisfy D-IDENTITY-09 across Android, iOS, Windows, Linux, browsers and low-cost devices?

**OCR & verification (F/G):**
16. Which OCR engine(s) are acceptable for Arabic/Iraqi documents and self-hosting?
17. Is there legally authorized access to representative de-identified Iraqi document images? (`BLOCKED_BY_EXTERNAL_DEPENDENCY`.)
18. Should `document_intelligence/` be rehabilitated, archived or left dormant? (`SECURITY_REVIEW_REQUIRED`.)
19. Is any official government verification interface legally available? (`BLOCKED_BY_EXTERNAL_DEPENDENCY`.)

**Legal / institutional (K):**
20. Do the statutes named in the brief (Law No. 3/2016, Law No. 21/2024) apply, and what do they require? (`UNVERIFIABLE` — no verifying source in repo; `LEGAL_REVIEW_REQUIRED`.)
21. What are the retention, data-residency and cross-border rules for identity/PHI? (`LEGAL_REVIEW_REQUIRED`.)

**API / data / testing (L/M/P):**
22. Which API surface is the canonical public identity contract, and who approves removing NID from query strings?
23. Should `/national/*` ever be mounted, and under what governance?
24. What runtime E2E and RPO/RTO evidence is required before any release-status change? (`NEEDS_OWNER_DECISION`.)

---

## 3. Decisions requiring owner approval (summary)

- **Authority choices:** civil identity registry, NHID issuer, patient-identity authority, guardian authority, consent authority (R-06, R-08).
- **Activation choices:** mounting `/national/*`, rehabilitating/archiving `document_intelligence/` and dormant engines (R-05, R-07, R-14).
- **Release posture:** runtime E2E + RPO/RTO evidence, and any change to `FINAL_DECISION.md` from HOLD (R-10) — explicitly **not** exercised by this study.
- **External integration:** any government ID verification, civil-registry connector, NFC/data-sharing agreement (R-12, R-19) — `BLOCKED_BY_EXTERNAL_DEPENDENCY` / `LEGAL_REVIEW_REQUIRED`.

---

## 4. Cross-references

All documents in `GOVERNANCE/IDENTITY_ARCHITECTURE_STUDY/`, especially `SECURITY_AND_PRIVACY_THREAT_MODEL.md`, `IRAQI_LEGAL_AND_INSTITUTIONAL_ASSESSMENT.md`, `ARCHITECTURAL_DECISIONS.md`, `IMPLEMENTATION_ROADMAP.md`. Read-only baselines: `GOVERNANCE/FINAL_DECISION.md`, `GOVERNANCE/GECS/GECS_CHECKPOINT.md`, `GOVERNANCE/NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md`, `GOVERNANCE/DATABASE_OWNERSHIP_MATRIX.md`.
