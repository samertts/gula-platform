# Identity & MPI Remediation Report — P0 Tranche

> Records the identity-records and Master Patient Index fixes implemented in
> this tranche. Unit/integration evidence only; no patient-record-corruption
> claim, no production claim. Synthetic fixtures only.

## 1. Verdict

| Dimension | Status |
|---|---|
| Canonical national-ID handling | IMPLEMENTED — tests pass |
| MPI manual-merge integrity | IMPLEMENTED (`IdentityClaim` repoint scope only) — tests pass |
| MPI unmerge / cross-domain repointing | **BLOCKED** — historical data + schema/ownership decision |
| Patient-record-corruption claim | **NONE** — not evaluated on real records |
| Release decision | HOLD, unchanged |

## 2. National identity handling (P0-A)

### Behavior changes
1. **Script-independent NID hashing** — `backend/app/services/identity.py`
   canonicalizes Unicode digit scripts (Arabic-Indic `٠-٩`, Extended
   Arabic-Indic `۰-۹`, Western `0-9`) before HMAC. The same person's NID yields
   a single hash regardless of which digit script the source system used.
2. **No raw NID persisted** — the governance identity-persistence service
   writes hashes, not raw identifiers, into `documents_json` and its search
   structures. Alphanumeric references that are not digit-only national IDs
   retain their historical hash to avoid changing legacy behavior.
3. **Registration consistency** — `routes/register.py` uses the canonical hash
   for both storage and duplicate checks, closing a bypass where two scripts
   of the same NID could both be accepted.
4. **Secure lookup path** — `routes/identity.py` offers a POST body lookup so
   the NID is not placed in a URL/query string. The old GET lookup is marked
   deprecated and kept only to avoid breaking an existing contract; its
   removal needs owner approval.

### Why this is safe
- Canonicalization is a pure normalization on digit characters; it does not
  change the HMAC key, the hash algorithm, or the stored schema.
- The no-raw-NID change removes sensitive data from at-rest JSON without
  altering query semantics for digit-only identifiers.
- Duplicate checks now see equivalent hashes; no legitimate distinct person is
  rejected because their differences were in digit script (a name/family-hash
  separation test pins the opposite collision from being introduced).

### Regression coverage
`backend/tests/unit/test_national_id_canonicalization.py` — 17 tests:
Arabic-Indic / Extended-Arabic-Indic / Western equivalence, whitespace and
punctuation, invalid input, family-hash separation, legacy hash candidates, no
raw NID at rest, cross-script duplicate detection. Plus the full pre-existing
`backend/tests/test_persisted_identity_governance.py` (35 tests) green.

## 3. MPI manual-merge integrity (P0-E1)

### Defect
`mpi/resolver.py::merge_citizens` set `secondary.merged_into_id` and status but
did not repoint the secondary's `IdentityClaim` rows. Claims continued to point
at a merged-away citizen, so downstream reads could resolve a patient through a
retired identity. There was no self-merge/cycle rejection, no idempotency, and
no rollback guarantee if a later step failed.

### Implemented guarantees
- **All-or-nothing via nested SAVEPOINT** — claim repointing, secondary state
  change and audit append happen inside `db.begin_nested()`. Any exception
  rolls back only the merge, preserving unrelated caller work.
- **Input validation** — empty ULIDs, self-merge, blank reason, missing
  citizens, non-active primary, already-merged secondary and invalid merge
  sources are rejected.
- **Cycle detection** — inputs that already resolve to the same canonical
  identity are rejected (distinct from an idempotent retry).
- **Idempotency** — retrying an already-applied merge returns the original
  `MergeAudit` row instead of creating a duplicate.
- **Claim repointing with provenance** — every `IdentityClaim` of the secondary
  moves to the primary; `merged_from_citizen_ulid` and `merge_reason` are
  recorded in the claim's match features, preserving the original features.
- **Immutable audit** — a hash-chained `MergeAudit` entry records the decision,
  including the list of repointed claim IDs.
- **Post-merge consistency checks** — verify no claims still reference the
  secondary, secondary state is consistent, and the primary's canonical chain
  is intact, before committing the savepoint.

### Scope boundary
Only `IdentityClaim` repointing is in scope. **Unmerge/historical event
repointing is explicitly out of scope** (P0-E2, blocked). Cross-domain
dependent references (national patients, encounters, orders, samples, results,
documents, audit) were not repointed.

### Regression coverage
`backend/tests/test_mpi_merge_integrity.py` — 6 tests: claim repoint +
provenance, hash-chained audit, idempotent retry, self-merge rejection, cycle
rejection, reason required, and forced-audit-failure rollback. All pass.

## 4. Verification

- `backend/tests/test_mpi_merge_integrity.py`: 6 passed, EXIT 0.
- `backend/tests/test_persisted_identity_governance.py`: 35 passed, EXIT 0.
- Combined 109-test final run: EXIT 0.
- Full commands and counts in `ACCEPTANCE_EVIDENCE.md`.

## 5. Blocked / not done

- **P0-E2** unmerge/split and cross-domain dependent reference repointing:
  `BLOCKED_BY_EXTERNAL_DEPENDENCY` / `NEEDS_OWNER_DECISION`. Requires historical
  event data and an ownership/schema decision. Not silently claimed fixed.
- No real patient record was read, merged or validated. No migration was run.
- No claim that MPI is clinically safe or production ready.

## 6. Honest non-claims

0 PRODUCTION_VERIFIED · 0 RUNTIME_VERIFIED · 0 E2E_VERIFIED · no
patient-record-corruption evaluation · RPO/RTO UNMEASURED · D-021 clinical
certification pending · HOLD unchanged.
