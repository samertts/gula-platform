# NR-220 — Independent Adversarial Audit (Account 2)

**Claim attacked:** the EHR medication routes are a false-success implementation.
**Verdict: NARROWED AND RECLASSIFIED.** Runtime proof
`backend/tests/verification/test_ehr_medication_truth.py`.

## The four hypotheses the brief listed, each tested

| Hypothesis | Verdict |
|---|---|
| legitimate no-medication state | **partly** — an empty list before any write is legitimate, but that is not the whole story |
| dead in-memory implementation | **DISPROVEN** — the models are ORM-mapped SQLAlchemy tables with real FKs |
| missing synchronization | **not supported** by any evidence found |
| wrong tenant / patient query | **DISPROVEN as stated** — the read path performs a real tenant-scoped patient lookup and returns `404 "Patient not found in your laboratory"` for an unknown patient, rather than an unconditional empty list |

**None of the four describes it.** Two measured causes do:

### (a) Schema latency — CONFIRMED

All four tables are ORM-mapped by `app/ehr/models/medication.py` and created by **no
migration**:

```
ehr_medication_statements        migration: NONE
ehr_medication_requests          migration: NONE
ehr_medication_dispenses         migration: NONE
ehr_medication_administrations   migration: NONE
```

Same class as IA-057. In the test harness `create_all` supplies them, which is why the suite
never sees it; on a migrated database the table is absent, so the production behaviour would
be an **error, not an empty list**.

### (b) Identity-domain mismatch — CONFIRMED, and this is the mechanical explanation

```
ehr_medication_statements.patient_id  VARCHAR(26)  ->  national_patients.id
patients.id                           INTEGER
```

The route is addressed by **domain B** (`national_patients.id`, a 26-char ULID). A caller
holding a core lab `patients.id` integer cannot address it — my own probe was rejected
`422 "Input should be a valid string"`, then `404` on the tenant lookup. And per **IA-067**
(`PATIENT_IDENTITY_ADVERSARIAL_AUDIT.md`) **no table bridges the two domains**, so the lab
stack cannot *produce* the identifier these routes require.

So an empty or 404 response is not a stub pretending to succeed: it is a real, tenant-guarded
query against a table that no migration creates, keyed by an identity the caller's domain
cannot supply.

**Pharmacy data was not substituted.** Nothing was fixed. The repair depends on IA-067's
decision gate — whether the two patient domains are meant to be bridged.

## Corrections to my own probe, recorded

Three of my assertions were wrong and the measurements corrected them: `patient_id` is a
string not an integer; `routes/ehr.py` contains no `db.add(` because it delegates to a
service layer, so my "in-memory?" inspection was too narrow; and the list endpoint 404s
rather than returning empty for an unknown patient, which is a stronger control than the
hypothesis assumed.
