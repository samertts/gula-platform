# GULA National Identity Architecture Study — Capacity & Cost Model

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.
**Workstream:** O (Performance, Capacity and Cost), inputs from A, C, E, F, G, J, N.

---

## 0. Honesty statement — READ FIRST

**No OCR benchmark, confidence threshold, throughput figure, latency figure, or operating cost is measured or asserted in this document.** No production-like snapshot, load test, or OCR benchmark was executed in this study. Where numbers appear, they are either:

- **DOCUMENTED_CONTEXT** — a figure already written in a repository document, attributed to its named source, and explicitly not independently verified; or
- **ASSUMPTION / VARIABLE** — a symbol in a sizing formula that must be populated from real measurements or vendor quotes before it can be used.

Cost is expressed as a **model structure** (formulas over unknown unit prices), not fabricated currency amounts. The national completion baseline records RPO/RTO as UNMEASURED and 0 services RUNTIME/PRODUCTION verified; this document does not improve that status.

---

## 1. Documented anchors (DOCUMENTED_CONTEXT — not verified in this study)

| Quantity | Value | Source in repository | Caveat |
|---|---|---|---|
| Iraq population | 45,074,049 in 2023 | `docs/IRAQ_HEALTH_SYSTEM_RESEARCH_NOTES.md:35` (WHO Data Iraq) | Historical; do not use as a current planning figure without refresh |
| Primary-care centres | 2,765 | `docs/IRAQ_HEALTH_SYSTEM_RESEARCH_NOTES.md:13` (WHO EMRO) | Older indicator; used with caution per the source |
| General hospitals | 281 | `docs/IRAQ_HEALTH_SYSTEM_RESEARCH_NOTES.md:13` (WHO EMRO) | Older indicator |
| Facilities assessed by HeRAMS | 5,205 across all governorates and the Kurdistan Region | `docs/IRAQ_HEALTH_SYSTEM_RESEARCH_NOTES.md:43` (UN Iraq / WHO, 7 June 2023) | Assessment coverage count, not a count of GULA-connected facilities |
| Health expenditure | 5.25% of GDP in 2021 | `docs/IRAQ_HEALTH_SYSTEM_RESEARCH_NOTES.md:35` | Context only; not a GULA budget |

**Program scale targets (design inputs, not measured):** "millions of citizens" and "tens of thousands of healthcare facilities" are the brief's planning envelopes. They are used as variables `N_citizens` and `F_facilities` below, not asserted as current facts.

---

## 2. Sizing model structure

### 2.1 Variables (all must be populated from measurement/procurement)

| Symbol | Meaning | How to obtain |
|---|---|---|
| `N_citizens` | Number of person identities / NHIDs | Authoritative registry count (currently not verified) |
| `F_facilities` | Connected facilities | Facility registry (ownership disputed — ADR-B pending) |
| `D_day` | Documents captured per day | Measured at pilot |
| `I_doc` | Mean compressed document image size | Measured from representative captures |
| `K_docs` | Retention multiplier / copies | Legal retention decision (Workstream K) |
| `L_ocr` | OCR jobs per document (classification + extraction + re-review) | Measured from workflow |
| `T_ocr` | Wall-clock time per OCR job on a chosen engine/hardware | **Benchmark required** (Workstream F) — no value assumed |
| `R_login_peak` | Peak authentication requests/sec | Measured at pilot |
| `R_mpi_peak` | Peak MPI match requests/sec | Measured at pilot |
| `E_audit_day` | Audit events/day | Derived from transaction mix; measured |
| `C_unit_*` | Unit prices (compute, storage, network, licensing, support) | Local procurement / vendor quotes — **no values assumed** |

### 2.2 Storage

| Store | Formula (structure) | Notes |
|---|---|---|
| Identity/NHID relational data | `N_citizens × bytes_per_identity_record × replication_factor` | Plus aliases, provenance, merge history (D-IDENTITY-02/07) |
| Document object store | `D_day × I_doc × K_docs × retention_days` | Encryption at rest; immutability/versioning; legal hold |
| OCR extraction + verification metadata | `D_day × L_ocr × bytes_per_result × retention` | Advisory results, not proof (D-IDENTITY-10) |
| Audit + forensic snapshots | `E_audit_day × bytes_per_event × retention + snapshot_volume` | Append-only, hash-chained; legal hold |
| Backups / DR | `total_persistent_data × backup_copies` | Encrypted, integrity-verified; RPO/RTO UNMEASURED |

**Note:** `DocIntelBase` (21 classes) is not registered in Alembic (`F-085`, `DATABASE_OWNERSHIP_AND_DATA_MODEL.md §2`), so document/OCR schema capacity cannot be reliably planned until that ownership is resolved. This is a `BLOCKED`-style planning dependency, not a sizing result.

### 2.3 Compute

| Workload | Model | Uncertainty |
|---|---|---|
| Authentication | `R_login_peak` against bcrypt/JWT/JTI-check cost; Redis HA for revocation store | bcrypt work factor and Redis topology to be measured; fail-closed 503 on store outage (`AUTHENTICATION_AND_RECOVERY_DESIGN.md §2.4`) |
| MPI matching | `R_mpi_peak` × candidate-generation + scoring cost; scales with `N_citizens` and index design | No benchmark exists; threshold calibration requires synthetic/de-identified Iraqi dataset (D-IDENTITY-07) |
| OCR | `D_day × L_ocr × T_ocr` → required worker-seconds/day → workers = `ceil(worker_seconds / (window_seconds × utilization))` | `T_ocr` **must be measured** per engine/hardware; GPU optional pending evaluation (Workstream F) |
| Audit hashing/verification | `E_audit_day` × HMAC/SHA cost | Low relative to OCR but must be included |

**GPU:** whether a GPU is required at all is an open question pending OCR evaluation (`OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md`). No GPU requirement is asserted here.

### 2.4 Network and database load

- Ingress: `D_day × I_doc` image upload traffic + form payloads; egress: cached identity views + verification results.
- Database: TPS from registration, MPI, audit writes and session/revocation checks; cross-base FK insert ordering (17 merged metadata) must be considered.
- Facility sync: `F_facilities × events_per_facility × sync_frequency` with idempotent outbox (`OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md`).
- No measurement of any of these exists in this study.

---

## 3. Deployment topology (design guidance — no premature microservices)

- **Modular monolith first:** existing `factory.py` registers 91 routers across many domains in one application; the study recommends scaling this deployment horizontally (multiple app instances) before introducing new services.
- **Separate OCR worker pool:** document/image processing is the natural scale-out boundary because it is CPU/GPU-bound and queue-driven; reuse an existing queue/outbox rather than introducing a new orchestration engine.
- **Shared security store (Redis):** HA deployment required because authentication fails closed on unavailability; size for `R_login_peak` + verification-code load.
- **Database:** single relational cluster with read replicas for MPI lookup/reporting; no sharding before evidence of need at `N_citizens` scale.
- **Object storage:** self-hosted S3-compatible (e.g. MinIO) for documents, consistent with the platform's self-hosted/open-source posture.
- **No vendor lock-in:** each component replaceable; prefer open-source; no paid SaaS assumed.

**Inference:** the current architecture already has many domain routers in one app; adding new microservices for identity would increase operational complexity without evidence of need.

---

## 4. Cost model structure (no figures invented)

| Cost line | Model | Notes |
|---|---|---|
| Compute (app tier) | `app_instances × instance_unit_cost × hours` | Unit cost from procurement |
| Compute (OCR workers) | `workers × (CPU/GPU unit cost) × hours` | `workers` from §2.3; GPU cost only if evaluation requires it |
| Storage | `total_bytes × storage_unit_cost × months` | Includes documents, audit, backups |
| Network | `ingress_bytes × egress_unit_cost + egress_bytes × egress_unit_cost` | Facility sync + citizen access |
| Database / Redis | `cluster_nodes × node_unit_cost` | HA for revocation store |
| Backup / DR | `backup_storage × unit_cost + DR_site_cost` | DR drill evidence from national completion report; RPO/RTO UNMEASURED |
| Identity verification / government interfaces | `0` until a lawful interface exists; then `per-query cost × volume` | **No API assumed** (Workstream G/K); do not budget a guessed fee |
| SMS/email OTP | **0 mandatory** (D-IDENTITY-09) | Any optional operator-funded gateway costed separately only if approved |
| Licensing | Prefer open-source (0 license fee); any paid OCR engine evaluated separately with justification | No paid dependency without documented exception |
| Support / operations | `staff_hours × loaded_rate` | Local staffing model |

**Owner-approved cost constraint:** D-IDENTITY-09 requires zero mandatory per-authentication external service cost. The model therefore contains **no per-login external line item**.

---

## 5. Scaling to national level — staged approach

1. **Pilot measurement:** populate all variables in §2 from a legally authorized pilot with synthetic/de-identified data.
2. **Benchmark OCR:** run the Workstream F evaluation on representative Iraqi document samples; obtain `T_ocr` per engine/hardware and field-level accuracy. No engine selected before this.
3. **Load-test authentication and MPI:** measure `R_login_peak`, `R_mpi_peak`, candidate-generation cost at increasing `N_citizens`.
4. **Capacity plan:** compute workers/instances from formulas; add headroom factor chosen by the owner (not invented here).
5. **Cost plan:** fill unit prices from procurement; produce a budget for owner approval.
6. **Rehearse DR:** measure RPO/RTO, currently UNMEASURED per completion baseline.

---

## 6. Test requirements (design-level; no tests run in this study)

| Level | Required coverage |
|---|---|
| Performance | Authentication throughput under `R_login_peak`; MPI latency at scale; audit write throughput; cache/session hit rates. |
| OCR benchmark | CER, WER, field exact match, document classification, national-number and date accuracy, human-review rate, FAR/FRR, CPU/RAM/GPU, latency, throughput — measured, not asserted. |
| Capacity | Storage growth projection from measured `D_day`/`I_doc`; backup/restore timing; RPO/RTO measurement. |
| Cost | Validate formulas with real unit prices; verify zero mandatory per-login external cost. |

Use synthetic or legally authorized de-identified data only. Do not claim E2E from contract-envelope tests.

---

## 7. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages / risks | Legal | Security | Ops / cost | Dependencies | Failure scenario | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CAP-01 | Modular monolith + horizontal app scaling before new microservices | Avoid premature microservice proliferation | Split into many services | Lower ops complexity | Monolith scaling limits at extreme scale | None identified | Neutral | Lower | Measurement at pilot | Scale ceiling reached | Reversible | §3 | `RECOMMENDED` |
| CAP-02 | Dedicated OCR worker pool driven by existing queue/outbox | CPU/GPU-bound workload | Inline OCR in request path | Isolated scaling, resumable jobs | Queue ops | Data-residency rules apply | Positive | Moderate | Workstream F benchmark; no new orchestration engine | Queue backlog | Reversible | §2.3, §3 | `RECOMMENDED` |
| CAP-03 | HA self-hosted Redis for revocation/verification store | Auth fails closed on unavailability | Single instance | Availability | Infra cost | None identified | Positive | Moderate | `AUTHENTICATION_AND_RECOVERY_DESIGN.md §2.4` | Auth outage | Reversible | §2.3 | `RECOMMENDED` |
| CAP-04 | No OCR engine selected before representative benchmark | No measured benchmarks exist | Pick a popular engine now | Evidence-based choice | Delayed selection | Document data handling | Positive | Benchmark cost | Synthetic/authorized Iraqi dataset | Wrong engine for Arabic docs | Reversible | §0, §5 | `RECOMMENDED` |
| CAP-05 | Budget model excludes mandatory per-login external cost | D-IDENTITY-09 | Paid SMS/email OTP | Cost/inclusion | Requires assisted paths | None identified | Positive | Zero per-login external | D-IDENTITY-09 | Vendor dependency | Reversible | §4 | `OWNER_APPROVED` (D-IDENTITY-09) |
| CAP-06 | Measure RPO/RTO before national rollout | Currently UNMEASURED | Assume targets | Evidence-based DR | DR drill cost | None identified | Positive | Moderate | National completion baseline | Unrecoverable outage | Reversible | §0, §5 | `RECOMMENDED` |

---

## 8. Open questions

1. What is the authoritative current citizen/facility count? (Only historical documented context exists.)
2. What are real document volumes and image sizes from a representative facility?
3. Which OCR engine and hardware meet Arabic/Iraqi-document accuracy and latency needs? (Benchmark required.)
4. What are the actual unit prices from local procurement?
5. What RPO/RTO targets are acceptable, and can the platform meet them? (Currently UNMEASURED.)
6. Who owns the budget and the legal authority for any future government verification interface?

---

## 9. Cross-references

`MASTER_ARCHITECTURE.md` · `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` (benchmark strategy) · `AUTHENTICATION_AND_RECOVERY_DESIGN.md` · `MASTER_PATIENT_INDEX_DESIGN.md` · `OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md` · `SECURITY_AND_PRIVACY_THREAT_MODEL.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · `RISKS_AND_OPEN_QUESTIONS.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 5, 9, 11, 12).
