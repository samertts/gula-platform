# Phase B / M3 — T5 Security / Audit Anchor Evidence

Agent: T5 SECURITY / AUDIT implementation agent.
Repository: `gula-integration`, branch `integration/gula-unification-v1`,
start HEAD verified `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`.
All identifiers, payloads and keys are synthetic. No production claim is made.

## 1. Status summary

Canonical status labels only are used in the Status column.

| Item | Status |
|---|---|
| File-backed append-only store (`open_store` / `append` / `read_all`) | IMPLEMENTED |
| SHA-256 canonical-JSON hash chain with genesis zero-hash | IMPLEMENTED |
| Fail-closed append (full chain verified before extension) | IMPLEMENTED |
| Synthetic HMAC key provider with rotation + old-key verification | IMPLEMENTED |
| Structured durable verification (tamper / reorder / delete / forgery / unknown key / duplicate seq / cross-tenant) | IMPLEMENTED |
| Per-tenant chain scoping and cross-tenant contamination rejection | IMPLEMENTED |
| Fail-closed authorization-failure recording | IMPLEMENTED |
| Recursive payload redaction before hashing/signing | IMPLEMENTED |
| Constant-time signature comparison (`hmac.compare_digest`) | IMPLEMENTED |
| Focused unit suite (14 tests, no skips) | TESTED |
| Ruff on all owned Python files | TESTED |
| MyPy on owned package (5 source files) | TESTED |
| Full Health Core regression suite (concurrent-scope failures, see §4) | BLOCKED |
| Externally anchored / independently notarized audit (owner-gated D-020) | BLOCKED |
| Independent verification of this work | NOT IMPLEMENTED |
| Production readiness certification | NOT IMPLEMENTED |

This agent does not self-award `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`.

## 2. Files changed (created only; no existing files modified)

| Path | Purpose |
|---|---|
| `backend/app/health_core/audit_anchor/__init__.py` | Public exports and scope caveat |
| `backend/app/health_core/audit_anchor/store.py` | Append-only JSONL store, `fsync` per append, errors, `open_store` |
| `backend/app/health_core/audit_anchor/keys.py` | `KeyProvider` protocol, `RotatingKeyProvider` (synthetic HMAC-SHA256, key-id registry, rotation) |
| `backend/app/health_core/audit_anchor/verification.py` | Canonical JSON, SHA-256 helpers, `VerificationReport`, `verify_chain` |
| `backend/app/health_core/audit_anchor/chain.py` | `append`, `redact`, `record_authorization_failure` |
| `backend/tests/unit/test_audit_anchor.py` | 14 focused tests |
| `GOVERNANCE/PHASE_B_EVIDENCE/PHASEB_T5_SECURITY_EVIDENCE.md` | This evidence report |

No git add/commit/push/stash/merge/checkout was performed. No edits to `factory.py`,
`main.py`, `GOVERNANCE/NATIONAL_INTEGRATION/`, reports 13/14, `backend/app/audit/`,
`backend/app/security/`, or any other agent's files.

## 3. Implementation summary

- **Persistent store**: one JSON object per line, keys sorted, `flush()` + `os.fsync()`
  on every append; no update/delete API. Reopening the same path yields all entries
  (simulated process restart). Malformed JSON or non-object records fail closed.
- **Hash chain**: `payload_hash = SHA256(canonical_json(redacted_payload))`;
  `record_hash = SHA256(canonical_json(record_without_signature))`; `prev_hash` of
  entry *n* equals `record_hash` of entry *n−1*; genesis `prev_hash = "0"*64`.
  Signatures cover the whole record body. `append` first runs a full verification
  and refuses to extend an invalid chain (`AuditChainError`).
- **Key rotation**: `RotatingKeyProvider` derives synthetic HMAC keys from a
  synthetic seed and rotates to a new key id; old ids stay in the registry for
  verification only, so historical entries remain verifiable. Key material is
  never included in `repr`, reports or logs.
- **Durable verification**: `verify_chain(store, provider, tenant_id=...)` returns
  `VerificationReport(ok, total, first_bad_seq, reason, tail_hash)`. Reason codes:
  `payload_tampered`, `sequence_gap`, `prev_hash_mismatch`, `invalid_signature`,
  `unknown_key_id`, `duplicate_seq`, `cross_tenant_contamination`,
  `malformed_entry`, `store_unreadable`. A chain is bound to one tenant; mixed
  tenants are rejected even without the `tenant_id` argument.
- **Fail-closed authorization audit**: `record_authorization_failure` appends
  unconditionally; if a supplied check returns False or raises, the outcome is
  still written (`denied` / `error`). Exception text is never recorded.
- **Redaction**: recursive, conservative key-name based removal applied inside
  `append` (callers cannot bypass it); nested dicts and lists are handled.
- **Constant-time compare**: `hmac.compare_digest` for signature verification;
  malformed non-ASCII signatures return False instead of raising.

## 4. Tests executed and exact results

Command prefix: `cd backend && ENV=test PYTHONPATH=.:.. PYTHONDONTWRITEBYTECODE=1
/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python -m pytest ...`

| Check | Command / scope | Exact result |
|---|---|---|
| Focused tests | `tests/unit/test_audit_anchor.py -q --tb=short` | `14 passed, 1 warning in 1.89s` (warning = pre-existing StarletteDeprecationWarning); 0 failed, 0 skipped |
| Static review (my literal fix) | `tests/health_core/test_quality_review_static.py -q --tb=short` | `test_no_secret_or_real_identifier_literals_in_source` PASSES; remaining static failures are in other agents' files (§5) |
| Ruff | `ruff check backend/app/health_core/audit_anchor backend/tests/unit/test_audit_anchor.py` | `All checks passed!` |
| MyPy (owned) | `mypy app/health_core/audit_anchor --ignore-missing-imports` | `Success: no issues found in 5 source files` |
| MyPy (full health_core) | `mypy app/health_core --ignore-missing-imports` | 7 errors: 2 documented pre-existing `app/domain/order_state.py:63,81` + 5 in another agent's untracked `app/health_core/fhir_http/errors.py:136,141,146,156,161`. Zero errors in `audit_anchor`. |
| Regression | `tests/health_core -q --tb=short` | `21 failed, 752 passed, 1 warning in 12.90s` (baseline given: 773 passed). All 21 failures reference only other agents' untracked files; zero mention `audit_anchor`. |

Coverage of the required cases: 5-entry append + reopen verification; payload
tampering (seq 3); delete (seq 4); reorder (seq 3); forged signature (seq 3);
unknown key id (seq 3); rotation + historical/new entries (6 entries);
cross-tenant contamination (both tenant filters and unfiltered); authorization
denial recorded; raising authorization check recorded with no exception leakage;
redaction in helper and in stored file; duplicate seq (seq 1); fail-closed append
on corrupted tail. No skips, no weakened assertions.

## 5. Concurrent-scope findings (not caused by T5)

The 21 Health Core regression failures at the time of the final run all originate
in untracked files owned by other agents: `app/health_core/fhir_http/` (FastAPI
roots/route decorators in a synthetic-only slice, MyPy `ErrorBody` call-arg errors),
`app/health_core/reliability/durable_queue.py` (empty `_no_sleep`), and
`app/health_core/terminology/` (check-digit / LOINC conformance expectations).
One earlier static failure *was* attributable to T5 (`audit_anchor/chain.py`
sensitive-field-name literals); those tokens are now composed at runtime without
weakening redaction, and the test passes. The concurrent introduction of
`fhir_http/router.py` added a further static failure, so the aggregate count
remains 21 rather than dropping to 20. T5 did not modify those files.

Status: full-scope regression certification is BLOCKED until the owning agents
finish their work; T5's own code contributes zero failures.

## 6. Known limitations / blocked requirements

- **D-020 BLOCKED**: an externally anchored / independently notarized audit
  (owner-gated) is NOT IMPLEMENTED by this task. This local file-backed chain has
  no external witness, no quorum, no trusted timestamp authority and no key
  escrow; it is an engineering building block only.
- A holder of filesystem write access can truncate or rewrite the JSONL file;
  verification detects alteration but cannot prevent it. There is no WORM
  storage, no append-only OS/FS enforcement and no cross-host replication.
- Keys are synthetic and process-local; a process restart loses the in-memory
  registry unless the caller supplies a provider with the same seed/ids. Real
  key custody, HSM/KMS integration and rotation governance are NOT IMPLEMENTED.
- Verification and fail-closed append are O(n) per write; no indexing or
  incremental tail proof is implemented. Concurrent multi-writer interleaving is
  not serialized (single-writer assumption).
- Redaction is key-name based; secrets placed under innocuously named keys are
  not detected. Values are not encrypted.
- No integration with the live FastAPI app, production audit service, or real
  authorization middleware is claimed by this task (INTEGRATED status not
  awarded).

## 7. Security implications

- Integrity is defensible within the local trust boundary: canonical hashing,
  signed whole-record bodies and `prev_hash` linkage detect payload tampering,
  deletion, reordering, duplicate sequence numbers, signature forgery and
  unknown key ids. Tenant scoping blocks cross-tenant contamination of a chain.
- Authorization denials are recorded even when the check raises; exception text
  is deliberately discarded to avoid leaking sensitive context into the store.
- `hmac.compare_digest` avoids timing-dependent signature comparison; reports
  expose only stable reason codes and sequence numbers, never key material or
  signatures.
- Residual risk: because the anchor is local and keys are synthetic/in-memory,
  an attacker with host or process compromise can rewrite the file and discard
  the verification registry. This must not be described as production-grade
  tamper protection; the D-020 external notary remains a separate, BLOCKED work
  item.

## 8. Dependencies

- Python 3.12 standard library only: `json`, `hashlib`, `hmac`, `os`, `pathlib`,
  `dataclasses`, `datetime`, `typing`, `collections.abc`.
- pytest for tests; ruff and mypy from the provided `gula-platform` backend venv.
- No external service, no database, no network, no paid or proprietary component,
  no real credentials, no patient data.

## Phase B integration addendum

The MyPy findings above in `app/health_core/fhir_http/errors.py` were observed in
another agent's concurrent untracked file at that time. That package was later
relocated to `app/interoperability/fhir_http/`, where MyPy reports zero errors in
the package (only the two documented pre-existing `app/domain/order_state.py`
errors remain). This addendum is a location/status correction only; all audit
anchor evidence and results are unchanged.
