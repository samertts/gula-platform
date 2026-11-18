# Decision Packages Requiring External Authority

**Document:** 05 · **Program:** National Integration · **Date:** 2026-11-18
**Status:** `IMPLEMENTED` as packages; **all decisions `BLOCKED` — no approval is invented.**

---

> These packages are **prepared, not granted**. Each identifies the authority required, the evidence already available, the options, and the reversible technical path. No owner signature is fabricated and no owner-gated status is changed.

## §1 — Iraq legal / regulatory / government interface authority

- **Decision needed:** legal basis for national identity linkage, NID handling, guardian/child identity, birth/death evidence, data retention and cross-ministry exchange.
- **Evidence:** `GOVERNANCE/IDENTITY_ARCHITECTURE_STUDY/IRAQI_LEGAL_AND_INSTITUTIONAL_ASSESSMENT.md`, `BIRTH_AND_DEATH_LIFECYCLE.md`, `CITIZEN_REGISTRATION_DESIGN.md`.
- **Authority:** Iraqi MoH / civil-registry / legal counsel. **Status:** `BLOCKED`.
- **Technical work permitted now:** none beyond synthetic models and this package.

## §2 — MP-001 (DB uniqueness for canonical links)

- **Decision needed:** owner-authorized migration adding `UNIQUE(patient_id)` / `UNIQUE(citizen_id)` on canonical link tables.
- **Evidence:** MPI audit AUD-02 partially remediated at app layer; app-layer `require_link_actor` + `require_own_lab` + advisory locks verified; 6/6 200 on 2-conn pool; 10/10 idempotent NID registration.
- **Options:** (a) add constraints after duplicate audit on a disposable clone; (b) keep app-layer-only with documented residual. Recommendation: (a), reversible via down-migration, **never** on an operational DB.
- **Authority:** Identity + Database owner. **Status:** `BLOCKED`.

## §3 — ODR-001…004 / D-MPI-5 (identity resolution and fork policy)

- **ODR-002 / D-MPI-5:** whether a corrected NID/name/DOB may be re-resolved through `/mpi/resolve`; closes AUD-07 (MEDIUM). Authority: Identity owner. `BLOCKED`.
- **ODR-003 / D-MPI-3/4:** response policy when a canonical fork is detected; closes AUD-16 (INFO). Authority: Identity + Clinical owner. `BLOCKED`.
- **ODR-001 / ODR-004:** supporting ordering/ownership decisions referenced by the MPI remediation backlog. Authority: Identity owner. `BLOCKED`.

## §4 — D-020 security certification and D-021 clinical certification

- **Evidence:** final decision §4/§7 — security review report + remediation diff; 69 public endpoints classified (R-01…R-11 residuals open); clinical routes remain unmounted.
- **Authority:** Security lead (D-020), Clinical lead + legal (D-021). **Status:** `BLOCKED`.
- **Program promise:** prepare diff indexes and test evidence; never self-certify.

## §5 — ADR-A … ADR-J

| ADR | Decision | Authority | Status |
|---|---|---|---|
| A | 426-table migration strategy (after NR-011) | Program Director / Architect | `BLOCKED` |
| B | Ownership of `facilities`/`organizations`/`national_facilities` | Database owner | `BLOCKED` |
| C | `care_continuum` cross-cutting host vs decomposition | Architect | `BLOCKED` |
| D | Audit actor / scoped service principals | Security lead + owner | `BLOCKED` |
| E | (per `ADR_DECISION_REQUEST.md`) | Architect | `BLOCKED` |
| F | (per source) | Architect | `BLOCKED` |
| G | Insurance/claims ordering | Architect + owner | `BLOCKED` |
| H | (per source) | Architect | `BLOCKED` |
| I | Insurance dependency | Architect + owner | `BLOCKED` |
| J | (per source) | Architect | `BLOCKED` |

Original ADR request md5 and `PENDING` statuses are unchanged. This package does not select an option on the owner's behalf.

## §6 — HOLD lifting

- **Exit criteria still unmet in the original record:** 5 (`MIG-EXISTING`), 7 (human security sign-off), 8 (frontend drift acceptance), 9 (four unwired service extractions / contract diff).
- **Authority:** Program Director. **Status:** `BLOCKED`. This program does **not** request or simulate lifting.

## §7 — Licensed data and absent platforms

| Item | Reason | Status |
|---|---|---|
| SNOMED CT (official release) | Licensed dataset unavailable; no invented license | `BLOCKED` |
| LOINC check-digit verification offline | Authoritative release unavailable | `NOT IMPLEMENTED` |
| iOS application | Xcode project absent from checkout | `NOT IMPLEMENTED` |
| Real client platform adapters | No owner authorization / platform SDKs | `BLOCKED` |
| Production deployment / external publication | No deployment authorization | `BLOCKED` |

---

_No approval above is claimed, implied or simulated. Packages are ready for the named authorities._
