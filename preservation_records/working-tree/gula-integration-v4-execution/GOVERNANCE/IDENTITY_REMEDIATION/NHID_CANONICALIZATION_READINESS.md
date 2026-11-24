# NHID Canonicalization Readiness Report

> **Tranche:** bounded, uncommitted session/MPI/NHID readiness work. **Release
> decision remains HOLD** (`GOVERNANCE/FINAL_DECISION.md`, md5 `effdfeaf…`).
> D-020/D-021 remain `PENDING_APPROVAL`. No runtime/E2E/clinical/production
> claim. Paths inside `gula-integration` @ `integration/gula-unification-v1`,
> HEAD `2827c1ff…`. This is a **source inventory + compatibility-test** tranche;
> **no identifier was changed, no data migrated, no canonical NHID implemented.**

## 1. Classification and status

| Item | Classification | Status |
|---|---|---|
| Complete identifier-format inventory | `OWNER_APPROVED` | `VERIFIED_IN_SOURCE` |
| Synthetic compatibility tests | `OWNER_APPROVED` | `TEST_VERIFIED` (23 tests) |
| Single canonical NHID model adoption | `NEEDS_OWNER_DECISION` + `LEGAL_REVIEW_REQUIRED` | `BLOCKED` / `NOT_IMPLEMENTED` |
| Breaking contract / migration / renumbering | `NEEDS_OWNER_DECISION` | `BLOCKED` (not performed) |
| PID→NHID linkage implementation | `NEEDS_OWNER_DECISION` | `BLOCKED` (no authoritative model) |

## 2. Identifier-format inventory (current source — authoritative)

| # | Format | Generator (file:line) | Validator / uniqueness | Consumers & notes |
|---|---|---|---|---|
| 1 | `HID-<8hex>-<2base32>` | `backend/app/services/identity_matching.py:94-102` (`generate_health_id`) | `verify_health_id` (:134-146) — only structural checksum validator found; in-memory `used_health_ids` | Main active HID; NID-derived (HMAC-SHA256, first 8 hex) + base32 checksum |
| 2 | `HID-<8hex>-<8hex>` | `shared/identity/service.py:42-57` (`IdentityService.generate_health_id`) | none; caller/repository uniqueness | **Competing** generator: trailer = SHA256 of raw NID; deterministic from NID; shape incompatible with #1 |
| 3 | `HID-YYYY-<8base32>` | `nhop-platform/app/services/health_id.py:16-32` | `parse_health_id` shape/year regex (:35-42); process-local `used_ids` | Third HID namespace; separate prefix structure |
| 4 | `HN-<12hex>` | `backend/app/governance/services/health_number_service.py:48-52` | repository `health_number_exists` + 20-attempt retry (:77-105); no checksum | Persisted issuance with lifecycle/audit (`ACTIVE`→`SUSPENDED`→`REACTIVATED`→`EXPIRED`) |
| 5 | `HN-<8>-<4>-<4>` (in-memory) | `backend/app/services/governance/identity_governance.py:131-134` | no checksum/uniqueness | `uuid4().hex[:16]` slices; in-memory governance objects; raw NID HMAC at :451-456 |
| 6 | `HN-<8>-<4>-<4>` (persisted) | `backend/app/governance/services/identity_persistence_service.py:282-285` | retry loop; canonicalizes digit-only NID (:269-280) | Persisted governance HN; raw NID redacted in documents (:66-75) |
| 7 | `HN-<8hex>` | `backend/app/services/reference/universal_identifier.py:87-93` | `validate()` is membership-only | Third HN namespace; FHIR identifier crosswalks |
| 8 | `IQ<year><seq:06d>` | `backend/app/national/services/citizen_service.py:22-29` | process-local `_sequence`; no checksum | **Actively overwrites** temporary `health_number` (:74-78); claimed "sole authority" in `national/ADR.md:10-15` and `docs/adr/ADR-012-identity-platform.md:52` — contradicted by all other generators |
| 9 | `NB- / FR- / VS- / EM-` temporary | `backend/app/national/services/identity_service.py:15-32,34-81` | process-local sequence; no checksum | Pre-permanent placeholders (newborn/foreigner/visitor/emergency/unknown); overwritten with no linkage; national router defined but **not mounted in `factory.py`** (dormant at runtime) |
| 10 | `NH-<uuid8>` | `backend/services/identity_engine/citizens_db.py:20-21` | none | Dormant prototype; variable named `nhid` — concept only, not implemented canonical service |
| 11 | `DEMO-####` | test/demo fixtures (e.g. `nhop-platform/tests/conftest.py:46`) | n/a | Must never enter production namespace |

The study's format list (`NATIONAL_IDENTITY_MODEL.md:64-79`) understates this:
11 concrete formats/families exist, including base32 HID, 12-hex HN, `NH-`, `DEMO-`.

## 3. Divergent normalization & duplicate detection (source-verified)

- **Canonical NID contract (single):** `backend/app/services/identity.py:214-279`
  maps all Unicode decimal digits (Arabic-Indic `١٢٣`, Extended `۱۲۳`) to ASCII,
  strips separators, and HMACs the result; `nid_hash_candidates()` supports legacy
  records. Used by `routes/register.py:336-345` and `routes/id_scan.py:23,173-185`.
- **NID-derived identifier divergence:** `shared/identity/service.py:46-57`,
  `services/governance/identity_governance.py:451-456`,
  `services/identity_matching.py:87-91` (strips non-digits with `\\D` but does
  **not** map Unicode decimal digits — Arabic-Indic and Western forms derive
  **different** legacy HIDs), `governance/services/identity_persistence_service.py:269-280`.
- **Four different duplicate-detection engines/ thresholds:** MPI matcher
  (`services/mpi/matcher.py:32-46`, auto-merge ≥0.90 / review 0.70–0.90),
  identity matching (`services/identity_matching.py:151-157`, `MATCH_THRESHOLD=0.85`),
  MDM (`health_data/mdm/matching.py:31-131`, 1.0/0.7), governance merge
  (`services/governance/merge_engine.py:35-98`, ≥0.6). No shared gold standard:
  the same pair can be auto-merged, flagged, or rejected depending on path.
- **Account/NIAM/DB-id confusion:** NIAM `Person` carries both `national_id_hash`
  and a bare `health_id` (`identity/models/person.py:11-15`); the persons endpoint
  accepts caller-supplied `health_id` with no registry validation
  (`identity/api/persons.py:15-42`); lifecycle routes set arbitrary `health_id`
  (`identity/lifecycle/routes.py:388-396`, `services.py:415-418`); LIMS
  `patient.py:28` and `canonical_patient.py:32` use different uniqueness
  semantics for the same conceptual "health number".

## 4. Temporary identifier / PID linkage
- No explicit `PID→NHID` linkage, alias table, `replaces`/`supersedes` field, or
  `temporary_id → permanent_nhid` mapping exists. `PID` hits are overwhelmingly
  HL7 segment references (`contracts/hl7/protocol.json:98-100`, `lims/integration/hl7.py:18,85-88`).
- The `IQ…` path **overwrites** `NB/FR/VS/EM` temporary numbers
  (`citizen_service.py:74-78`) rather than linking them; a test
  (`national/tests/integration/test_identity_flow.py:11-30`) asserts only the
  returned local value's prefix, not that the persisted number is retained.
- Provenance preservation and PID linkage are explicit owner requirements; the
  current source cannot satisfy them without an authoritative identity model.

## 5. Synthetic compatibility tests (executed)
New `backend/tests/unit/test_nhid_readiness.py` — **23 tests, all passing**
(Python 3.12.13 isolated venv, `ENV=test PYTHONPATH=backend:.`), covering:
- Arabic-Indic / Extended-Arab-Indic / Western parity; leading/trailing
  whitespace; punctuation; empty and non-digit inputs; equivalent
  representations; canonical+legacy `nid_hash_candidates`; cross-representation
  duplicate detection;
- legacy `HID-` generate/verify round-trip; tampered-checksum rejection;
  malformed/empty rejection; collision resistance (500 synthetic ids);
- two characterization tests documenting (a) incompatible HID namespace shapes
  and (b) the known defect that the legacy HID generator does **not**
  canonicalize Arabic-Indic digits. These pin current behaviour and are
  explicitly labelled as risks — **not** desired end state, and not a fix.

No real patient data; no identifier changed; no test skipped or weakened.

## 6. Proposed single canonical NHID model (documentation only — NOT implemented)
- **Identifier:** `NHID-1-<CSPRNG payload>-<checksum>`; opaque random payload,
  **never derived from NID, name, DOB or any personal attribute**; one published
  checksum validator; never reused (tombstone on retirement).
- **NID role:** protected *matching attribute only* — canonicalize via
  `backend/app/services/identity.py:214-279`, store only salted HMAC; never
  embedded in or deterministically generating an NHID; no new NHID for a child
  merely because a national ID card is later issued.
- **Issuance/lifecycle:** one registry-owned issuer with uniqueness check + audit;
  `PROVISIONAL → ACTIVE → SUSPENDED → RETIRED/MERGED`.
- **Linkage:** explicit `Person ↔ HealthIdentifier(NHID + aliases) ↔ Account ↔
  MPIRecord`; temporary `NHTMP-…` linked to permanent NHID via an alias table;
  old IDs remain resolvable (PID→NHID provenance preserved).
- **Migration:** every existing format becomes a migration alias pointing to a
  newly issued NHID; alias lookup provides backward compatibility; no legacy
  format accepted as canonical after cutover. ADRs claiming "`IQ…` sole
  authority" must be revised. Architecture gate should fail any new
  `generate_health_id`/`_generate_health_number` outside the single issuer.

## 7. Required owner decisions / reviews
| Decision | Classification |
|---|---|
| Adopt single canonical NHID authority and retire competing generators | `NEEDS_OWNER_DECISION` |
| Issuer/namespace/checksum algorithm and governance ownership | `NEEDS_OWNER_DECISION` |
| Migration/alias strategy; no bulk renumbering without approval | `NEEDS_OWNER_DECISION` |
| Legal interpretation (NID usage, provisional identity, retention, consent) | `LEGAL_REVIEW_REQUIRED` |
| Revise ADR-012 / national ADR "IQ sole authority" claims | `NEEDS_OWNER_DECISION` |
| Fix legacy HID Arabic-Indic divergence / retire NID-derived HID | `NEEDS_OWNER_DECISION` |

## 8. Evidence limits / verification boundary
`VERIFIED_IN_SOURCE` for the inventory (broad greps were truncated at 250–400
matches; all identified generators/validators/key consumers/tests were read
individually; generated audit artifacts were not treated as authoritative).
`TEST_VERIFIED` for the synthetic compatibility suite only. No database access,
no DDL, no data migration, no dormant router/engine activation, no canonical NHID
implementation, and no claim of duplicate-identity resolution in production.
