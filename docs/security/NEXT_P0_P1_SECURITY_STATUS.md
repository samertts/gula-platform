# Next P0/P1 Security Status

Workstream 4, extended by the follow-on "P0/P1 SECURITY CLOSURE +
CERTIFICATE AUTHORITY HARDENING" operation's Phase 9. Starts from the
existing registry (`docs/engineering/MUSTAFA_ACTIVE_REPAIR_QUEUE.md`,
~40 rows, extensively fixed/verified across prior phases) rather than
re-discovering from zero, per this workstream's own instruction. Adds
only what changed or was newly found this session. Does not re-fix
anything already marked FIXED there unless this session's change surface
could plausibly affect it (it did not — this session touched only
`app/identity/**` and `scripts/self_audit_agent.py`, disjoint from the
queue's prior work across `radiology/`, `blood_bank/`, `pilot_platform/`,
etc.).

## Closed this session (evidenced, real Postgres + HTTP where applicable)

| ID | Severity | Finding | Fix | Evidence |
|---|---|---|---|---|
| niam-audit-uuid | P1 (data integrity) | `CanonicalAuditService.record()` never set `IdentityAuditEntry.uuid` (NOT NULL, no default) — every real canonical audit write crashed against a real DB | `uuid=str(uuid.uuid4())`, matching every sibling call site | `NIAM_LIVE_PATH_PROOF_3.md` |
| niam-no-commit | P1 (data integrity) | No code in the NIAM write path (`get_db()` included) ever called `.commit()` — nothing persisted, ever, through this dependency | Route-level `await db.commit()`, matching the existing `app/routes/admin.py` canonical pattern | `NIAM_LIVE_PATH_PROOF_3.md` |
| niam-trust-fk-drift | P1 (schema/ORM drift) | `TrustFramework.authority_id` referenced a nonexistent `niam_identity_authorities` table | Corrected to `niam_gov_authorities`, matching the already-correct, already-deployed migration exactly — no migration needed | `NIAM_LIVE_PATH_PROOF_3.md` |
| niam-authority-gaps | P0 (authorization bypass) | `register_provider`, `activate_framework`, `issue_certificate`, `revoke_certificate`, `create_authority` were authenticated but had zero authorization — any NIAM account of any role could perform them | Platform capability check + audit + commit added to all five (same pattern as the two already-fixed Phase 6 findings) | `NIAM_PLATFORM_AUTHORITY_COMPLETION.md` |
| niam-session-no-expiry | P1 (authentication integrity) | `get_current_niam_actor`/`_sync` never checked `UserSession.expires_at` — an expired session (still `is_active=True`) remained valid indefinitely | `expires_at > now()` added to both queries | `NIAM_RUNTIME_SECURITY_MATRIX.md` |
| niam-cert-plaintext-private-key | **P0** (credential exposure at rest) | `issue_certificate`/`register_ca` stored a real RSA private key (PKCS8, `NoEncryption()`) verbatim in `private_key_encrypted` | Reused the existing canonical `app.security.encryption.encrypt()` (Fernet/`ENCRYPTION_KEY`) | commit `77ae130e`, regression test proving the stored value isn't a raw PEM block |
| niam-cert-router-gap | **P0** (authorization bypass) | `rotate_certificate`, `register_ca`, `generate_crl`, `generate_api_key`, `revoke_api_key`, `rotate_api_key` were authenticated but had zero platform-capability check, no audit, no commit, and used the broken sync `Depends(get_db)` dependency | Same pattern as the five Workstream 1 fixes: capability check + `CanonicalAuditService` event + route-level commit + `get_niam_db`; added a shared FK-existence validator (`_require_existing_reference`) for a mass-assignment gap found incidentally | `CERTIFICATE_AUTHORIZATION_RUNTIME_COMPLETION.md` — full 401/403/422/200 matrix, fresh-session persistence, audit, and an induced-failure rollback proof |
| niam-trust-no-state-machine | **P1** (data integrity) | `TrustFramework.activate_framework` unconditionally set `active` regardless of prior status — a `superseded` framework could be silently reactivated | Terminal-state guard (`_TERMINAL_STATUSES`), idempotent re-activation, and a real `SELECT ... FOR UPDATE` row lock for concurrency (no schema change — no optimistic-lock column exists to add without a migration) | `TRUSTFRAMEWORK_STATE_MACHINE_STATUS.md` — real HTTP proof of valid/idempotent/denied transitions plus a genuine 2-second row-lock blocking proof |
| niam-trust-create-framework-gap | P1 (authorization) | `create_framework` (the entry point into the TrustFramework state machine) had zero platform-capability check and used the broken sync `Depends(get_db)` | In-scope because it's the TrustFramework state machine's own entry transition, which this pass was asked to secure | Same fix pattern, `TRUSTFRAMEWORK_STATE_MACHINE_STATUS.md` |

## Closed this session — reclassified from OPEN to VERIFIED/NOT_APPLICABLE

`niam-no-idempotency-key`'s three genuinely-safe operations
(`revoke_certificate`/`revoke_api_key` via their existing `is_active`
precondition, `activate_framework`/`supersede_framework` via this
session's own idempotent-no-op fix) are now proven safe without any new
mechanism. The remaining four operations
(`generate_api_key`/`issue_certificate`/`rotate_certificate`/
`rotate_api_key`) are precisely reclassified `REQUIRES_IDEMPOTENCY` and
correctly left **BLOCKED** (needs a migration + human approval) rather
than declared fixed — see `IDEMPOTENCY_CONTRACT_AND_GAP_REPORT.md` for
the full classification and reasoning.

## Open — discovered this session, not fixed, documented rather than hidden

| ID | Severity | Finding | Why not fixed this pass | Recommended next action |
|---|---|---|---|---|
| niam-cert-issuer-ca-fk-drift | **P1** (schema/ORM drift, newly discovered) | `DigitalCertificate.issuer_ca_id`'s FK constraint targets `niam_cert_certificates.id` (itself) instead of `niam_cert_authorities.id` (the actual CA table) — confirmed via a real `ForeignKeyViolation` when a genuine CA id was passed as `issuer_ca_id` to `issue_certificate` | A live-table FK-target correction is a schema change (`ALTER TABLE ... DROP/ADD CONSTRAINT`), which this operation's own rules place in "Requires human approval" (`CLAUDE.md`) — not something to migrate unilaterally | A new migration correcting the FK target, reviewed and approved before applying to any real database |
| niam-broad-sync-db-mismatch | **P1** (correctness, newly discovered, large surface) | Quantified via `grep -c "Depends(get_db)"`: `governance` (24), `federation` (15), `lifecycle` (42), `workflows` (8), `notifications` (11), `adaptive_auth` (16), `admin` (12), `compliance` (8), and the remaining ~20 non-`TrustFramework` endpoints in `trust` (26 total, 3 fixed this pass) — 162+ occurrences of the identical broken sync/async engine mismatch already proven and fixed for `certificates` and `TrustFramework` | Fixing 162+ occurrences across 8 route modules is a "generic repository rewrite," explicitly out of this operation's bounded scope (it named the certificate cluster and the TrustFramework state machine specifically) | A dedicated future workstream applying the exact same proven pattern (capability check + audit + `get_niam_db` + commit) module by module, prioritized by which routes are actually reachable/used |
| niam-identitybase-metadata-gap | P3 (test infrastructure) | `IdentityBase` is not part of `tests/conftest.py`'s merged-metadata SQLite fixture (`_all_metas`), and `niam_assignments` itself has cross-`Base` FK dependencies (`clinical_organization_resource_id`→`organizations`, `clinical_facility_resource_id`→`facilities`) that block creating `IdentityBase`'s tables in isolation even outside that fixture | A real architectural/test-infra decision (merge metadata? which owns the cross-reference?), not a quick fix | Workstream 7 (architecture regression sweep) — flagged there too |
| niam-idempotency-gap-4-ops | P2 (reliability, reclassified from P3) | `generate_api_key`/`issue_certificate`/`rotate_certificate`/`rotate_api_key` retried after a successful-but-unacknowledged commit can duplicate real effects (orphaned API key; double-rotation invalidating a client's just-issued credential) | Needs a new `idempotency_key_hash`/`request_fingerprint` column pair (reusing `CitizenRelationshipWorkflow`'s existing, correct pattern) — a schema change, "Requires human approval" | `IDEMPOTENCY_CONTRACT_AND_GAP_REPORT.md` |

## GATE 2 — repository-wide claim discipline

**Not claiming zero P0/P1 repository-wide.** This pass's evidence is
scoped to `app/identity/**` (this session's actual change surface) plus
whatever the existing `MUSTAFA_ACTIVE_REPAIR_QUEUE.md` already covered
across other domains (radiology, blood bank, pilot platform, adaptive
auth, etc. — extensively fixed/verified there, not re-audited here since
nothing in this session touched those files). A genuinely repository-wide
"zero P0/P1" claim would require re-walking every domain listed in that
queue plus everything never yet audited (payments, billing beyond the one
finding above, edge platform, pharmacy, hospital, EMS, etc.) — **NOT
STARTED** in this pass; UNKNOWN, not asserted as clean. The newly
quantified `niam-broad-sync-db-mismatch` finding is itself evidence that
even the audited `app/identity/**` surface was not fully swept before
this pass — closing the certificate cluster and TrustFramework does not
mean the rest of NIAM is clean.

## Status

**PARTIALLY VERIFIED** — nine real P0/P1 findings now closed with
evidence across this session and its follow-on operation (six from the
original pass, three more this pass: the certificate/CA/API-key cluster,
the TrustFramework state machine, and `create_framework`'s own
authorization gap); four more discovered and honestly left open with
reasons and recommended next actions (one schema-drift FK fix, one large
same-shape sweep, one test-infrastructure gap, one idempotency
mechanism), none silently dropped or fabricated as fixed.
