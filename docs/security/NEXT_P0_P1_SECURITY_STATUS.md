# Next P0/P1 Security Status

Workstream 4. Starts from the existing registry
(`docs/engineering/MUSTAFA_ACTIVE_REPAIR_QUEUE.md`, ~40 rows, extensively
fixed/verified across prior phases) rather than re-discovering from zero,
per this workstream's own instruction. Adds only what changed or was
newly found this session. Does not re-fix anything already marked FIXED
there unless this session's change surface could plausibly affect it (it
did not — this session touched only `app/identity/**` and
`scripts/self_audit_agent.py`, disjoint from the queue's prior work
across `radiology/`, `blood_bank/`, `pilot_platform/`, etc.).

## Closed this session (evidenced, real Postgres + HTTP where applicable)

| ID | Severity | Finding | Fix | Evidence |
|---|---|---|---|---|
| niam-audit-uuid | P1 (data integrity) | `CanonicalAuditService.record()` never set `IdentityAuditEntry.uuid` (NOT NULL, no default) — every real canonical audit write crashed against a real DB | `uuid=str(uuid.uuid4())`, matching every sibling call site | `NIAM_LIVE_PATH_PROOF_3.md` |
| niam-no-commit | P1 (data integrity) | No code in the NIAM write path (`get_db()` included) ever called `.commit()` — nothing persisted, ever, through this dependency | Route-level `await db.commit()`, matching the existing `app/routes/admin.py` canonical pattern | `NIAM_LIVE_PATH_PROOF_3.md` |
| niam-trust-fk-drift | P1 (schema/ORM drift) | `TrustFramework.authority_id` referenced a nonexistent `niam_identity_authorities` table | Corrected to `niam_gov_authorities`, matching the already-correct, already-deployed migration exactly — no migration needed | `NIAM_LIVE_PATH_PROOF_3.md` |
| niam-authority-gaps | P0 (authorization bypass) | `register_provider`, `activate_framework`, `issue_certificate`, `revoke_certificate`, `create_authority` were authenticated but had zero authorization — any NIAM account of any role could perform them | Platform capability check + audit + commit added to all five (same pattern as the two already-fixed Phase 6 findings) | `NIAM_PLATFORM_AUTHORITY_COMPLETION.md` |
| niam-session-no-expiry | P1 (authentication integrity) | `get_current_niam_actor`/`_sync` never checked `UserSession.expires_at` — an expired session (still `is_active=True`) remained valid indefinitely | `expires_at > now()` added to both queries | `NIAM_RUNTIME_SECURITY_MATRIX.md` |
| niam-cert-plaintext-private-key | **P0** (credential exposure at rest) | `issue_certificate`/`register_ca` stored a real RSA private key (PKCS8, `NoEncryption()`) verbatim in `private_key_encrypted` | Reused the existing canonical `app.security.encryption.encrypt()` (Fernet/`ENCRYPTION_KEY`) | commit `77ae130e`, regression test proving the stored value isn't a raw PEM block |

## Open — discovered this session, not fixed, documented rather than hidden

| ID | Severity | Finding | Why not fixed this pass | Recommended next action |
|---|---|---|---|---|
| niam-cert-router-gap | **P1** (authorization) | `certificates/routes.py` has six more mutating endpoints beyond the two fixed (`rotate_certificate`, `register_ca`, `generate_crl`, `generate_api_key`, `revoke_api_key`, `rotate_api_key`) — same "authenticated, zero platform-capability check" shape as the six Workstream 1 closed, but not in that workstream's explicitly named six operations | Out of Workstream 1's bounded scope (it named six specific operations); fixing six more well is comparable effort to Workstream 1 itself | Repeat Workstream 1's exact pattern (capability check + audit + commit) on these six, likely `platform.certificates.manage` for all of them |
| niam-trust-no-state-machine | P2 (data integrity, not yet proven exploitable) | `TrustFramework` has no transition guard — `activate_framework` unconditionally sets `active` regardless of prior status (e.g. a `superseded` framework) | Needs a domain decision on the intended state graph (mirrors `imaging-slice-order-transition-graph`'s precedent of not inventing one without evidence) | Domain owner specifies the intended graph, then reuse `domain/order_state.py`/`domain/sample_state.py`'s existing pattern |
| niam-identitybase-metadata-gap | P3 (test infrastructure) | `IdentityBase` is not part of `tests/conftest.py`'s merged-metadata SQLite fixture (`_all_metas`), and `niam_assignments` itself has cross-`Base` FK dependencies (`clinical_organization_resource_id`→`organizations`, `clinical_facility_resource_id`→`facilities`) that block creating `IdentityBase`'s tables in isolation even outside that fixture | A real architectural/test-infra decision (merge metadata? which owns the cross-reference?), not a quick fix | Workstream 7 (architecture regression sweep) — flagged there too |
| niam-no-idempotency-key | P3 (reliability) | None of the seven Platform-Authority-bearing routes have an idempotency-key contract (unlike `ClinicalCommandGuard`'s existing pattern) — a retried request re-applies and re-audits | New contract (headers + dedup storage), not a bug fix | Only if retried-request duplication is judged to matter for these specific operations |

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
STARTED** in this pass; UNKNOWN, not asserted as clean.

## Status

**PARTIALLY VERIFIED** — six real P0/P1 findings closed with evidence
this session; four more discovered and honestly left open with reasons
and recommended next actions, none silently dropped.
