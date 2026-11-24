# GULA National Identity Architecture Study — Iraqi Legal & Institutional Assessment

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not legal advice, not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.
**Workstream:** K (Iraqi Legal and Institutional Assessment), inputs from A, B, G, H, I, J, L.

---

## 0. Scope, method and limits — READ FIRST

This document surveys **what the repository already documents** about the Iraqi legal and institutional environment and maps it to the identity architecture. It is **not** a legal opinion.

**Critical limits:**
- No statute, regulation or government source was independently verified on the web or through official gazettes in this study (read-only, documentation-only mandate).
- The two specific statutes named in the program brief — **Iraqi National Identity Card Law No. 3 of 2016** and **Birth and Death Registration Law No. 21 of 2024** — have **no verifying source in the repository**. They are recorded as `UNVERIFIABLE` claims requiring qualified Iraqi legal counsel. **No legal conclusion about their content, scope, or obligations is made here.**
- The label `DOCUMENTED_CLAIM` means "a repository document says this"; it does **not** mean "verified law."
- No government API, NFC interface, data-sharing agreement or legal access to civil registries is assumed to exist.
- Cost figures that appear in existing repository documents are **not reproduced as estimates** here; any cost modelling is in `CAPACITY_AND_COST_MODEL.md` and is explicitly labeled as assumption-based.

Label set: `VERIFIED_IN_SOURCE` (a repository document states it — not verified law), `UNVERIFIABLE` (not confirmable from repository evidence), `LEGAL_REVIEW_REQUIRED`, `BLOCKED_BY_EXTERNAL_DEPENDENCY`, `RECOMMENDED`, `NEEDS_OWNER_DECISION`.

---

## 1. Institutional context documented in the repository

### 1.1 Health system — `VERIFIED_IN_SOURCE` (documented claims with named sources)

`docs/IRAQ_HEALTH_SYSTEM_RESEARCH_NOTES.md` records, with primary-source links, the following **documented** context (each is a claim from a named source, not independently verified in this study):

| Topic | Documented claim | Named source in the document |
|---|---|---|
| System shape | Historically central public system under strain, gradually decentralizing; public/private mix | WHO EMRO, Health system strengthening (Iraq) |
| Infrastructure | 2,765 primary-care centres, 281 general hospitals; 8.4 physicians / 19.4 nurses per 10,000 (older indicators, used with caution) | WHO EMRO |
| Population / spend | Population 45,074,049 in 2023; current health expenditure 5.25% of GDP in 2021 | WHO Data Iraq; World Bank |
| Insurance | Health insurance body describes national provider network, electronic insurance card, appointments, EMR, e-payments, privacy protection; beneficiary coverage figures cited for 2023/2024 in the Arabic study | Iraq Health Insurance Authority (HIA) site; `docs/IRAQ_HEALTH_SYSTEM_DIGITAL_TRANSFORMATION_STUDY_AR.md` |
| Facility monitoring | HeRAMS assessed 5,205 facilities across all governorates and the Kurdistan Region; work began on DHIS2 | UN Iraq / WHO, 7 June 2023 |
| Private sector | Private sector significant; many laws predate 2003 and have not kept pace with decentralization; dual practice and weak financing/accountability noted | WHO UHC Partnership / MoH Iraq; US ITA; RAND (Kurdistan regional study) |
| Death registration quality | WHO Data notes cause-of-death data are estimates and **completeness of death registration and cause-of-death quality are low** — comparisons must be used cautiously | WHO Data Iraq |

**Implication for this study (inference):** low civil death-registration completeness strengthens the case for separating healthcare notification/confirmation from civil registration (D-IDENTITY-06, `BIRTH_AND_DEATH_LIFECYCLE.md`) and for not treating a missing civil record as proof that no event occurred. The document itself states its findings are preliminary and require review against official sources (`IRAQ_HEALTH_SYSTEM_RESEARCH_NOTES.md:71`).

### 1.2 Public trust and digital records — `VERIFIED_IN_SOURCE` (documented claim)

`docs/IRAQ_HEALTH_SYSTEM_DIGITAL_TRANSFORMATION_STUDY_AR.md` cites Alkailani et al., "Iraqi Population Trusts in Electronic Healthcare Records: A Cross-sectional Study, 2024" (`:187`). The existence of this citation is verified; its findings were **not** read or summarized in this study. **Inference:** public trust is a relevant adoption factor but must be studied with the actual source before any claim is made. `LEGAL_REVIEW_REQUIRED` before using trust data to justify consent or disclosure design.

### 1.3 Medico-legal governance model — `VERIFIED_IN_SOURCE` (design document, not law)

`docs/sovereign/phase24-legal-governance/04-medico-legal-analysis.md` documents a governance model already assumed by the platform:

| Concept | Documented position |
|---|---|
| Reconstructive power | Audit chain + AI evidence packets + patient-card history can reconstruct who ordered/collected/performed/released/alerted and what human accepted/rejected |
| Liability boundaries | Clinician responsible for clinical decisions; lab for sample/handling/result release; operator for platform state; AI advisory with human in loop; adapter peers per contract. The platform does **not** take positions on apportionment, indemnification or insurance |
| Evidence preservation | Legal hold on active matters; retention purges skip held subjects; deletion/redaction suspended; heightened access logging; hold lifecycle audited |
| Evidence disclosure | Sealed, signed, time-bounded, integrity-verified export only for court/regulator order; no ad-hoc disclosure |
| Cross-jurisdiction | Data sovereignty governs whether/how data leaves jurisdiction; counsel orchestrates, platform executes per policy |
| Forensic snapshot | Signed "moment in time" unit: patient + consent state, canonical-id history, clinical record, AI invocations, adapter calls, operator actions, chain hashes |
| Clinical-safety linkage | Every clinical-safety incident referenced in committee log + audit subset + reconciliation events + AI evidence packets |
| Limitations | Reconstruction only as accurate as captured audit; off-system care cannot be reconstructed; generative-AI replay may be approximate |

**Inference:** this model is a **useful design basis** for identity auditability (`SECURITY_AND_PRIVACY_THREAT_MODEL.md`), but it is a repository design document, not a statement of Iraqi law.

---

## 2. Statutes named in the program brief — `UNVERIFIABLE`

| Statute named in brief | Repository evidence | Status | Required action |
|---|---|---|---|
| Iraqi National Identity Card Law No. 3 of 2016 | No source found in repository; no verified text, authority, obligations or NFC/interface provisions | `UNVERIFIABLE` | Qualified Iraqi legal counsel to obtain the official text, confirm current force, and determine obligations for collection, storage, matching and integration |
| Birth and Death Registration Law No. 21 of 2024 | No source found in repository | `UNVERIFIABLE` | Legal counsel to verify existence, number, date, current force, competent authority, registration procedures and correction processes |
| Applicable health-sector laws | `reports/LEGAL_MASTER_PLAN.md:214` lists Iraq → "National Health Data Law, SNDHS" as primary compliance requirement (an unattributed doc claim) | `UNVERIFIABLE` | Identify exact statute(s), competent authority and data-sharing rules |
| Medical confidentiality | No verified statute in repository; medico-legal design doc (§1.3) assumes confidentiality duties | `UNVERIFIABLE` | Legal counsel to identify confidentiality obligations and permitted disclosures |
| Personal data / privacy | No verified Iraqi data-protection statute in repository | `UNVERIFIABLE` | Legal counsel to determine applicable law, lawful basis, data-subject rights, cross-border rules and breach-notification duties |
| Child protection / guardianship | `docs/niam/GUARDIAN_ACCOUNTS.md`, `docs/niam/CITIZEN_LIFECYCLE.md` describe model roles; no legal citation verified | `UNVERIFIABLE` | Legal counsel to define who may be a guardian, authority levels, custody-dispute handling, and age-of-majority exceptions |
| Civil registration / correction | No verified source | `UNVERIFIABLE` | Legal counsel to identify authority, evidence standards and correction/reversal procedure |
| Official documents / electronic transactions / digital evidence | No verified source | `UNVERIFIABLE` | Legal counsel to determine admissibility of OCR extracts, electronic signatures and audit records |

**Explicit conclusion:** because the governing texts are unverified, this study **cannot** state which data collection is lawful, what consent is required, what retention periods apply, or whether government-system integration is permitted. Every such item is `LEGAL_REVIEW_REQUIRED`.

---

## 3. Repository-documented compliance gaps (not legal conclusions)

`reports/LEGAL_MASTER_PLAN.md` records the following **documented** readiness gaps. These are engineering/compliance observations from an existing report, carried forward honestly; they are not independent legal findings and are not re-verified here.

| Area | Documented gap (`LEGAL_MASTER_PLAN.md`) | Study interpretation |
|---|---|---|
| GDPR readiness (`:185-195`) | No DPA template; no DPO; breach-notification process missing; consent table missing GDPR fields; right-to-deletion incomplete; no export/portability endpoint; no PIA | `RECOMMENDED` engineering controls; applicability of GDPR to Iraq must be determined by counsel (`LEGAL_REVIEW_REQUIRED`) |
| HIPAA considerations (`:197-206`) | Encryption at rest "National ID only, not all PHI"; RBAC exists but no automatic timeouts/session recording; audit hash chain present; emergency "break glass" exists in governance but no procedure | Aligns with findings in `AUTHENTICATION_AND_RECOVERY_DESIGN.md` (session/timeout gaps) and `SECURITY_AND_PRIVACY_THREAT_MODEL.md` |
| Country-specific (`:210-220`) | Iraq → "National Health Data Law, SNDHS" | Unattributed doc claim — `UNVERIFIABLE` |
| Privacy posture (governance) | `GOVERNANCE/UNIFICATION_BLOCKERS.md:28` — privacy/consent/audit posture **PARTIAL — NOT CERTIFIED** | Carried into `RISKS_AND_OPEN_QUESTIONS.md` |

---

## 4. Authority and data-sharing matrix (target — to be validated by counsel)

The architecture must identify, for each identity capability, the competent authority and legal basis **before** any integration or final-status decision. The table below is a **design checklist**, not an assertion of law.

| Capability | Candidate authority (to verify) | Legal basis needed (to verify) | Data-sharing requirement (to verify) | Status |
|---|---|---|---|---|
| Civil identity number issuance / verification | Civil registry / national identity authority | Statutory authority to collect and match | Formal agreement + verified interface; **not assumed** | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| NHID assignment | National health authority | Statutory mandate for a health identifier | Internal governance; link to civil registry only if lawful | `NEEDS_OWNER_DECISION` + `LEGAL_REVIEW_REQUIRED` |
| Birth notification / confirmation | Delivering healthcare facility | Healthcare reporting duty | Facility attestation artifact | `LEGAL_REVIEW_REQUIRED` |
| Birth civil registration | Civil registry authority | Statutory registration procedure | Official certificate/record | `LEGAL_REVIEW_REQUIRED` / `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| Death notification / confirmation | Authorized clinician / facility | Healthcare reporting duty | Clinical confirmation artifact | `LEGAL_REVIEW_REQUIRED` |
| Death civil registration | Civil registry authority | Statutory registration procedure | Official death certificate | `LEGAL_REVIEW_REQUIRED` / `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| Guardian authority | Courts / family-law authority | Legal guardianship order or statutory parental authority | Verified evidence reference | `LEGAL_REVIEW_REQUIRED` |
| Child data access | Guardian + child (age-based) | Guardian authority + child-protection rules + privacy law | Purpose + consent where required | `LEGAL_REVIEW_REQUIRED` |
| Patient-record access by institution | Healthcare institution | Treatment/legal basis + purpose + relationship | RBAC/ABAC + audit + consent | `LEGAL_REVIEW_REQUIRED` |
| Document verification via chip/NFC | Document-issuing authority | Statutory verification authority | Interface + cryptographic keys; **not assumed available** | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| Cross-border data transfer | Relevant authorities | Data-sovereignty / transfer rules | Counsel-orchestrated, platform executes per policy (§1.3) | `LEGAL_REVIEW_REQUIRED` |

---

## 5. Legal gates for the implementation roadmap

Each roadmap phase (`IMPLEMENTATION_ROADMAP.md`) requires a legal gate before progression. There are no invented dates.

| Phase theme | Required legal gate |
|---|---|
| Identity architecture foundation | Confirm lawful basis for person identity, civil-number matching and NHID; confirm data-ownership authority (ADR-B/D/E pending) |
| NHID and MPI | Confirm matching/HMAC legality, retention, dispute and merge/unmerge authority |
| Citizen registration | Confirm required/optional fields, proofing rules, assisted-registration authority, child/registration consent |
| Authentication and recovery | Confirm recovery proofing authority; confirm no mandatory paid external factor; accessibility duties |
| OCR / document intelligence | Confirm lawful document capture, minimization, retention, and that OCR output is advisory only (not proof) |
| Document verification | Confirm NFC/government-interface authority; confirm face-matching/biometrics legality and non-exclusive use |
| Guardian and child | Confirm guardian definitions, custody rules, age-of-majority/exceptions, adolescent-confidentiality rules |
| Birth and death | Confirm notification vs civil-registration authorities, correction and reversal procedure, death-status obligations |
| Healthcare integration | Confirm purpose-based access, legal basis, data-sharing agreements, consent mapping |
| Security and privacy hardening | Confirm breach notification, DPIA/PIA, retention/deletion restrictions, encryption/key requirements |
| Pilot | Confirm pilot legal basis, cohort consent/notice, data residency, audit/disclosure procedure |
| National rollout | Confirm national statutory mandate, authority approvals, ongoing compliance and disclosure process |

---

## 6. Decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages / risks | Legal | Security | Ops / cost | Dependencies | Failure scenario | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LAW-01 | Treat all statutes named in the brief as unverified until counsel confirms | No verifying source in repository | Assume statutes as stated | Avoids unsupported legal conclusions | Delays legal design sign-off | Core | None | Low | Qualified Iraqi legal counsel | Wrong legal basis baked into design | Reversible | §2 | `LEGAL_REVIEW_REQUIRED` |
| LAW-02 | Separate healthcare notification/confirmation from civil registration | D-IDENTITY-06 | Single status flag | Matches owner decision; robust to low registration completeness | State-machine complexity | **Requires legal authority per state** | Positive | Moderate | Workstream I; counsel | Unverified event treated as final | Reversible | §1.1, §4 | `LEGAL_REVIEW_REQUIRED` |
| LAW-03 | No government API/NFC access assumed | No verified interface/agreement | Assume availability | Honest, no fabricated integration | Optional step-up unavailable | Data-sharing agreement required | Positive | Lower | Verified interface + agreement | Unauthorized integration attempt | Reversible | §0, §4 | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| LAW-04 | Legal hold + signed forensic snapshot as evidence basis | Medico-legal defensibility | Ad-hoc exports | Aligns with documented governance model | Implementation effort | **Admissibility to be confirmed** | Positive | Moderate | §1.3 model; counsel | Inadmissible or tampered evidence | Reversible | §1.3 | `LEGAL_REVIEW_REQUIRED` |
| LAW-05 | Close documented compliance gaps (DPA, DPO, PIA, breach, consent fields, encryption of all PHI, timeouts) | Documented readiness gaps | Defer | Reduces legal/security exposure | Effort; GDPR applicability unconfirmed | Confirm applicable regimes | Positive | Moderate–high | `LEGAL_MASTER_PLAN.md` findings | Breach/audit failure | Reversible | §3 | `RECOMMENDED` |
| LAW-06 | Obtain qualified Iraqi counsel determination before any data-sharing integration | No verified legal basis for sharing | Proceed on assumption | Legally defensible | External dependency | Core | Positive | Counsel cost | Counsel engagement | Unlawful disclosure | Reversible | §2, §4 | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |

---

## 7. Open questions for legal counsel

1. Are Law No. 3 of 2016 and Law No. 21 of 2024 in force as of the study date, and what exact obligations do they impose?
2. What is the lawful basis for collecting and HMAC-matching the Iraqi National Identity Card number, and who may access it?
3. Which authority assigns NHID, and is a national health-identifier mandate enacted?
4. What are the registration authorities, evidence standards and correction/reversal procedures for birth and death?
5. Who may be a legal guardian, what authority does each guardian type hold, and what are the age-of-majority exceptions?
6. Which privacy/data-protection and medical-confidentiality laws apply, and what are breach-notification and retention rules?
7. Are OCR extracts, electronic signatures and hash-chained audit records admissible as digital evidence?
8. Under what conditions, if any, may GULA integrate with civil-registry or document-verification systems, and with what agreements?
9. What data-residency / cross-border transfer rules apply (`LEGAL_MASTER_PLAN.md:214` "SNDHS" claim)?

---

## 8. Cross-references

`MASTER_ARCHITECTURE.md` · `NATIONAL_IDENTITY_MODEL.md` · `GUARDIAN_AND_CHILD_IDENTITY_DESIGN.md` · `BIRTH_AND_DEATH_LIFECYCLE.md` · `DOCUMENT_VERIFICATION_DESIGN.md` · `SECURITY_AND_PRIVACY_THREAT_MODEL.md` · `RISKS_AND_OPEN_QUESTIONS.md` · `IMPLEMENTATION_ROADMAP.md` (legal gates per phase) · `EXECUTIVE_SUMMARY_AR.md` (Iraqi legal dependencies).
