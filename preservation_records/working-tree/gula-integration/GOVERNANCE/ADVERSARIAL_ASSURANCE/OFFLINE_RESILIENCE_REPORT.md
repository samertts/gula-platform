# Team A5 — Adversarial Offline Resilience Audit

**Audit ID:** A5
**Scope:** `gula-integration` working tree at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549` (dirty tree; audited as observed).
**Method:** READ-ONLY static adversarial review. No operational DB, no network, no crash/replay run, no synthetic-event execution performed by this audit.
**Overall verdict on audited work:** **BLOCKED** for production offline resilience. The offline/durable surface is explicitly synthetic and in-process; the frontend has no offline data capability. No `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` status is awarded.

## 0. Prior disclosures honoured (not re-reported)

`GOVERNANCE/NATIONAL_INTEGRATION/10_RELIABILITY_OFFLINE_SURVEY.md:3-21` already and honestly records: in-memory `TESTED`, durable external anchor `BLOCKED`, crash durability `NOT IMPLEMENTED`, RPO/RTO `NOT IMPLEMENTED`. `13_INTEGRATION_TEST_AND_VERIFICATION.md:108` already classifies T3 durable queue as "Synthetic in-process queue; no runtime wiring."

This audit does **not** re-raise those known disclosures as new findings. It raises findings for risks that are **not** disclosed or are **contradicted** by the disclosures — most importantly, an actual default conflict policy that silently loses updates while the disclosure claims "no lost updates."

## 1. Headline finding

The reliability survey asserts (`10_RELIABILITY_OFFLINE_SURVEY.md:13`) that conflict handling is "honest `CONFLICT_QUARANTINE` — no lost updates." The **live offline sync service defaults detected conflicts to `LAST_WRITE_WINS`** (`offline_sync_service.py:307`). A genuinely honest quarantine implementation exists (`offline_sync_service.py:200-246`) but is not the default path returned by `_detect_conflict`. For clinical data this is a silent-overwrite hazard, and the assurance documentation is inaccurate in the safety-critical direction.

## 2. Findings

### AUD-OFF-001 — Default conflict resolution is LAST_WRITE_WINS, contradicting the "no lost updates" safety claim (HIGH — clinical safety)

- **Evidence**
  - `backend/app/services/offline_sync_service.py:293-308` — `_detect_conflict` returns `ConflictRecord(..., resolution=ConflictResolution.LAST_WRITE_WINS)` for every causally-unrelated concurrent operation on the same entity.
  - `backend/app/services/offline_sync_service.py:25` — `CONFLICT_QUARANTINE` is defined as a distinct enum member.
  - `backend/app/services/offline_sync_service.py:200-246` — an honest `CONFLICT_QUARANTINE` branch with `_resolution_status = "CONFLICT_QUARANTINED"` exists at line 238, but is reached only when that resolution is explicitly selected.
  - `GOVERNANCE/NATIONAL_INTEGRATION/10_RELIABILITY_OFFLINE_SURVEY.md:13` — "Offline conflict strategy is **honest `CONFLICT_QUARANTINE`** — no CRDT claim; no lost updates; idempotent."
  - `backend/app/health_core/integration/conflicts.py:94-95` — replay ordering key is `(occurred_at, event_id)`; `conflicts.py:23` defines `KEEP_LAST_WITH_AUDIT`, a second newest-wins strategy.
- **Reproduction / falsification:** Construct two `SyncOperation`s for the same `entity_type`/`entity_id` with causally-unrelated vector clocks, call `OfflineSyncEngine._detect_conflict(incoming)`, and observe `resolution == ConflictResolution.LAST_WRITE_WINS`. Falsify by demonstrating that the runtime sync flow always overrides this result with `CONFLICT_QUARANTINE` before applying, or by a test proving no overwrite occurs. No such override was found.
- **Root cause:** A safe strategy was implemented but the default in the conflict detector was left at last-write-wins; documentation describes the safe branch as if it were the default.
- **Impact:** Concurrent offline edits can silently overwrite one another; the assurance record asserts the opposite. Clinical result/order data loss is possible. Behaviour was not executed by this audit — the risk is established statically; runtime impact is `NOT MEASURED`.
- **Severity:** HIGH · **Likelihood:** HIGH (deterministic default) · **Status:** `DISCOVERED` · **owner_gated:** YES (conflict policy is a clinical-safety/owner decision — do not change without approval).
- **Recommended remediation:** With owner approval, change the default to `CONFLICT_QUARANTINE`, correct the survey sentence to describe the actual default, and add a regression test asserting that two concurrent same-entity operations are quarantined with an audit record and neither is discarded. Keep `KEEP_LAST_WITH_AUDIT` only where explicitly opted in.
- **Alternatives:** (a) Fail closed on any unresolved conflict and require human adjudication; (b) implement CRDT for specific non-clinical fields only, explicitly excluding results/orders.

### AUD-OFF-002 — "Durable" queue is synthetic and non-wired; replay reconstructs events with empty payloads (HIGH)

- **Evidence**
  - `backend/app/health_core/reliability/durable_queue.py:1-18` — self-described "design harness for synthetic `SYN-` events"; "the 'log' is a byte buffer in this process ... There is no filesystem, database, broker, network, keyed signature or external monotonic anchor. This is NOT production-grade durability and makes NO durability claim."
  - `backend/app/health_core/reliability/durable_queue.py:1042-1052` — crash-recovery replay creates `QueueEvent(..., payload={}, payload_digest=...)`; the raw payload is never in the log.
  - `GOVERNANCE/NATIONAL_INTEGRATION/13_INTEGRATION_TEST_AND_VERIFICATION.md:108` — T3 status `TESTED` with boundary "Synthetic in-process queue; no runtime wiring."
  - Search: no runtime import of `durable_queue` outside the `health_core` package and its tests.
- **Reproduction / falsification:** Read the cited module docstring and replay constructor; run an import search. Falsify by showing a production service wiring the queue into real event delivery and an external anchor whose payload survives a process restart.
- **Root cause:** The module is a correctness harness for queue *semantics*, not a persistence implementation; its name over-states its capability.
- **Impact:** There is no offline/on-device durable event delivery at runtime. Even in-synthetic crash recovery loses payload content (`payload={}`), so redelivery cannot reconstruct the original operation. Durability is `NOT IMPLEMENTED` / `BLOCKED` as already disclosed.
- **Severity:** HIGH · **Likelihood:** HIGH (code fact; non-wiring confirmed) · **Status:** `DISCOVERED` · **owner_gated:** YES (external anchor is owner-gated/`BLOCKED`).
- **Recommended remediation:** After owner authorisation, implement a keyed, tenant-scoped durable external anchor and persist encrypted payloads (or a retrievable payload reference) so replay is lossless; wire the queue into the real delivery path; add a true process-restart test. Until then, rename/document the module to avoid "durable" being read as a production claim.
- **Alternatives:** (a) Adopt an existing self-hosted durable broker per the platform's Free/Open-Source/No-Vendor-Lock-In policy; (b) use the existing outbox table pattern if it can be made crash-safe.

### AUD-OFF-003 — No client-side offline data capability; "offline-first" is not implemented in the browser (HIGH)

- **Evidence**
  - `frontend-v3/src/main.tsx:6-17` — only PWA service-worker registration; no offline data store or sync manager initialised.
  - `frontend-v3/vite.config.ts:45-71` — Workbox caches static build globs, images, and fonts only; no API/data runtime caching.
  - Repository-wide search of `frontend-v3/src` for `indexedDB`, `idb`, `Dexie`, `localforage`, `navigator.onLine`, and background sync: **zero matches**.
  - `frontend-v3/vite.config.ts:60-69` — the only API-adjacent runtime cache is for Google fonts, not application data.
- **Reproduction / falsification:** Run the search above and inspect the Workbox config. Falsify by identifying a client-side store and an offline queue that survives a page reload and re-syncs when connectivity returns.
- **Root cause:** Offline-first was implemented as backend-in-process harnesses plus a static-asset PWA shell; no browser persistence layer exists.
- **Impact:** The application shell may load offline, but no patient, order, or result data is available offline, and no offline action can be queued on the device. Client offline capability is `NOT IMPLEMENTED`.
- **Severity:** HIGH · **Likelihood:** HIGH (code fact) · **Status:** `DISCOVERED` · **owner_gated:** YES (offline-first is a project constitution invariant; any readiness claim about it is an owner decision).
- **Recommended remediation:** With owner approval, implement an encrypted client-side outbox (e.g. IndexedDB) with idempotency keys, explicit quarantine conflicts, connectivity-aware UI, and a replay path bound to the server's honest conflict strategy. Add a browser-level test simulating offline → online.
- **Alternatives:** (a) Declare the web client online-only and scope offline-first to a dedicated native/edge client; (b) ship a read-only offline cache for reference data only, explicitly excluding clinical writes.

### AUD-OFF-004 — Operation signature is a homebrew digest that omits timestamp and vector clock; forgeable with the default empty secret (HIGH)

- **Evidence**
  - `backend/app/services/offline_sync_service.py:328-336` — `_sign_operation` computes `sha256(f"{op_id}:{json.dumps(data)}:{device_id}:{secret}")`; `_verify_signature` recomputes the same string. This is a hand-rolled MAC construction, not an HMAC/keyed MAC.
  - `backend/app/services/offline_sync_service.py:81-84` — `device_secret: str = ""` — the default is an empty secret, making the digest computable by any caller.
  - `backend/app/services/offline_sync_service.py:97-116` — `timestamp = time.time()` (client-supplied) and `vector_clock` are **not** included in the signed material.
- **Reproduction / falsification:** Instantiate `OfflineSyncEngine()` with no secret; compute the digest of an arbitrary operation from public fields; it verifies. Alter `op.timestamp` or `op.vector_clock` and observe `_verify_signature` still returns true. Falsify by showing a proper HMAC over all integrity-sensitive fields with a provisioned per-device key.
- **Root cause:** Ad-hoc digest used as authenticity control; key management and field coverage were not designed.
- **Impact:** With an empty or leaked secret, operation data can be forged; timestamps/vector clocks can be tampered with without detection, undermining causality and conflict detection. Integrity is `NOT MEASURED` in deployment because no key provisioning evidence was found.
- **Severity:** HIGH · **Likelihood:** MEDIUM (depends on deployed secret provisioning) · **Status:** `DISCOVERED` · **owner_gated:** NO (cryptographic correction is internal; key provisioning policy has a separate owner dependency).
- **Recommended remediation:** Replace with `hmac.new(key, canonical_bytes, sha256)` over `op_id`, `entity_id`, `operation`, `data`, `device_id`, `timestamp`, and `vector_clock`; require a non-empty per-device key and fail closed if absent; use constant-time comparison (`compare_digest`).
- **Alternatives:** (a) Use a standard signed envelope (JWS with a per-device key); (b) rely on transport mTLS plus server-assigned timestamps and drop the custom signature entirely.

### AUD-OFF-005 — Encrypted sync store silently falls back to plaintext when no key is configured (MEDIUM)

- **Evidence:** `backend/app/services/offline_sync_service.py:339-342` (`EncryptedSyncStore.__init__` stores `_key = encryption_key`), `371-377` (`_encrypt` returns `data` unchanged when `_key` is falsy), `379-385` (`_decrypt` likewise).
- **Reproduction / falsification:** Instantiate `EncryptedSyncStore()` with no key, put bytes, and observe the stored value is the original plaintext. Falsify by showing an always-present validated key or a fail-closed constructor.
- **Root cause:** Optional-encryption design where absence of a key degrades silently instead of failing.
- **Impact:** A component described as an "encrypted store" may hold sensitive sync payloads in plaintext; a later keyed deployment cannot decrypt earlier plaintext entries. Actual exposure is `NOT MEASURED`.
- **Severity:** MEDIUM · **Likelihood:** MEDIUM · **Status:** `DISCOVERED` · **owner_gated:** NO.
- **Recommended remediation:** Require an encryption key at construction (raise if missing/weak), use authenticated encryption (e.g. AES-GCM) with versioned key IDs, and add a test asserting no plaintext bytes are ever stored.
- **Alternatives:** (a) Explicitly rename to `MaybeEncryptedStore` and gate every call on a capability check; (b) store only a server-side reference, never payload bytes on the device.

### AUD-OFF-006 — Edge agent state file written non-atomically (MEDIUM)

- **Evidence**
  - `edge_agent/gula_edge_agent/state.py:65-70` — `_write` calls `self.state_file.write_bytes(blob)` directly; no temp-file + `os.replace` + `fsync`.
  - `edge_agent/gula_edge_agent/state.py:58-62` — `_read` raises `StateError("corrupt state file: ...")` on decrypt/parse failure.
  - `edge_agent/gula_edge_agent/agent.py:191-199` — the agent polls a heartbeat that can issue kill/quarantine commands; no offline task queue was found in the edge agent runtime.
- **Reproduction / falsification:** Inspect `_write` for atomic-rename semantics and `fsync`. Falsify by showing a temporary-file + atomic-replace + directory fsync implementation and a simulated power-loss test.
- **Root cause:** In-place overwrite of the single state file.
- **Impact:** A crash or power loss during write can leave a truncated ciphertext; the next read fails closed and the edge agent cannot resume its state. Crash-consistency is `NOT IMPLEMENTED`.
- **Severity:** MEDIUM · **Likelihood:** MEDIUM · **Status:** `DISCOVERED` · **owner_gated:** NO.
- **Recommended remediation:** Write to a temp file in the same directory, `fsync` it, `os.replace` atomically, then `fsync` the directory; keep a last-known-good backup and add a simulated-interruption test.
- **Alternatives:** (a) Use an embedded transactional store (e.g. SQLite) for agent state; (b) treat state as disposable and re-fetch from the control plane on corruption.

## 3. Coverage and limitations

| Area inspected | Result |
|---|---|
| Durable queue semantics/wiring | AUD-OFF-002 |
| Offline outbox/replay internals | Prior disclosure honoured; not re-reported |
| Conflict strategy consistency | AUD-OFF-001 |
| Offline sync engine integrity/encryption | AUD-OFF-004, AUD-OFF-005 |
| Edge agent state durability | AUD-OFF-006 |
| Browser/client offline capability | AUD-OFF-003 |
| Crash durability / RPO / RTO | **NOT MEASURED / `NOT IMPLEMENTED`** (already disclosed) |
| Production readiness | **BLOCKED** — no `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` awarded |

No synthetic events were executed, no crash/replay was simulated, and no external anchor was contacted. Findings are established statically from the cited source and governance documents. The pre-existing `NR-011` FK test under `tests/identity` was not re-reported.
