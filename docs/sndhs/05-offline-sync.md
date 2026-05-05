# 05 — Offline-First Sovereign Operation & Sync Engine

## 5.1 Goals

- Each Regional Sovereign Node (RSN) operates **fully autonomously for
  ≥ 72 h** with zero national connectivity. Patient registration,
  encounter management, referrals (intra-region), orders, results,
  triage, MCOM, audit, and reporting MUST continue.
- Reconnection MUST converge to a single, legally defensible canonical
  history. No data loss. No silent overwrite. No double-write.
- Cross-region operations during partition are degraded but safe:
  proposals are accepted locally, and the canonical owning RSN
  reconciles on heal.

## 5.2 RSN node design

Each RSN is a complete vertical:

- 3-node PostgreSQL (Patroni, sync replica + 1 async).
- 3-node NATS JetStream (RAFT clustering, regional only).
- 3-node Redis Sentinel.
- App fleet (3-N replicas) of every Critical and Clinical Plane service.
- Local audit ledger with WORM mirror to an air-gapped local archive.
- Local time authority agent (stratum-2) backed by GPS (multi-constellation)
  + Rb oscillator + chrony. Falls back to monotonic-only when both GPS
  and uplink are lost (`time_quality = LOCAL_FALLBACK`).
- Local Policy Mirror — last signed bundle from policy authority,
  sufficient for 72 h. Beyond 72 h with no refresh, the RSN escalates
  to safe-mode policy (the "freeze bundle").
- Local AI Mirror — frozen weights of any *promoted* AI advisory at
  partition start; no new shadow runs on promoted models during
  partition (audit logs continue locally and ship after heal).

## 5.3 Sync protocol

### 5.3.1 Layers

```
┌──────────────────────────────────┐
│ application: events + proposals  │
├──────────────────────────────────┤
│ session: signed envelope, vector │
│   clocks, replay tokens          │
├──────────────────────────────────┤
│ transport: gRPC over QUIC, mTLS  │
│   with multipath (cellular +     │
│   sat + microwave failover)      │
└──────────────────────────────────┘
```

### 5.3.2 Replica clocks

- Each RSN maintains:
  - `local_seq[stream_kind, stream_id]` — monotonic per stream.
  - `vector_clock[rsn]` — high-watermark of events seen from each peer.
  - `wall_skew_ns` — observed offset to time authority (NaN if drifted).
- Every event carries `(source_rsn, local_seq, vector_clock_snapshot)`.

### 5.3.3 Push / pull cycle

1. **Heartbeat** every 5 s while online: each RSN sends its
   `vector_clock` digest to peers + NFT.
2. **Pull**: peer replies with events the requester has not seen,
   chunked, signed, ≤ 4 MiB per chunk, in `(source_rsn, local_seq)`
   order.
3. **Push**: when an RSN owns an entity referenced by a remote
   proposal, it pushes ownership-bound events (e.g., approvals,
   acceptances).
4. **Ack**: receiver applies, persists, then acks the high-watermark.
5. **Replay window**: 7 days kept locally; older events fetched from
   NFT cold archive on demand.

### 5.3.4 Bandwidth tiers

| Tier | Available bandwidth | Behaviour |
|------|---------------------|-----------|
| Green | ≥ 50 Mbps | Full sync, near-real-time |
| Yellow | 1–50 Mbps | Priority sync only (P0/P1 streams), batch P2/P3 hourly |
| Red | < 1 Mbps | P0 only (dispatch, MCOM, deaths), everything else queued |
| Black | 0 | Full offline; queue locally; safe-mode policy |

The bandwidth tier is observed and the sync scheduler reorders
replication accordingly.

## 5.4 Conflict resolution policy

| Entity class | Resolution | Rationale |
|--------------|-----------|-----------|
| Allergies, problem list, immunisations, family history | OR-set CRDT, tombstones with TTL | Strictly additive in clinical practice; merging preserves all observations |
| Vitals, lab results | append-only with `idempotency_key` dedup; ordering by `measured_at_ns` | Observations are facts; never overwrite |
| Encounter / Referral state | event-log replay through deterministic FSM resolver | Owner's timeline wins; non-owning proposals validated against the resulting state |
| Identity demographics | three-way merge with field-level priority + manual queue on conflict | Govt-issued ID > scanned doc > self-reported |
| MPI merges | only on owning RSN of the surviving record; cross-region merge requires NFT custody handoff | One source of truth per merge |
| Custody handoff | two-phase commit | Avoid lost-update during transfer |
| Orders / medications | last-writer-wins **on idempotency key**, not on payload; conflicting non-idempotent orders → manual reconciliation | Prevents duplicate dispense |
| Documents/attachments | content-addressed (BLAKE3); duplicates dedup; metadata last-writer-wins | Files are immutable bytes |

### Determinism

The FSM resolver is deterministic given the same canonical event log;
two RSNs that converge on the same event-log prefix will compute the
same state. This property is model-checked in `Sync.tla`.

### Manual queue

Any unresolved conflict creates a `manual-merge` record with:

- both timelines, full provenance,
- a diff visualization for the medical-records officer,
- two-person rule for severity ≥ S2,
- target SLA: P0 (≤ 30 min), P1 (≤ 4 h), P2 (≤ 7 d).

## 5.5 Priority sync

Streams are tagged with priority class:

- `crit.dispatch.*` — P0 — sync on heartbeat
- `enc.critical.*`, `referral.p0.*`, `mcom.*`, `death.*` — P0
- `enc.routine.*`, `referral.p1.*` — P1
- `result.*`, `vitals.*` — P1 (P0 if encounter is critical)
- `audit.*` — P0 (legal requirement)
- `analytics.*`, `pubhealth.*` — P3

Under bandwidth scarcity the sync scheduler drains higher priority
streams first; per-stream backlog metrics are exported.

## 5.6 Partition detection & safe-mode

Partition signals (any two trigger safe-mode):

1. Loss of NFT heartbeat for > 60 s.
2. Loss of time-authority signed token validation for > 60 s.
3. Policy mirror older than 72 h.
4. Quorum loss within the RSN cluster.

Safe-mode actions:

- Switch to **freeze policy bundle** — most conservative settings (e.g.,
  block any cross-region MPI write, block AI promotion changes,
  disable analytics export).
- Mark `time_quality = LOCAL_FALLBACK` on writes; downstream consumers
  flag these as "needs revalidation on heal".
- Force MCOM at least at level 2 (advisory).
- Disable AI advisories visible to humans (flip circuit even if
  promoted).
- Persist a `partition_started` event locally; when heal occurs, emit
  `partition_resolved` with duration and counts.

## 5.7 Reconciliation on heal

Order of operations:

1. **Time anchor**: re-anchor wall clock to time authority; recompute
   `wall_skew_ns`. Locally written events keep their `monotonic_ns`;
   their `wall_utc` is annotated `provisional` until confirmed.
2. **Audit chain merge**: reconcile audit hash chains (each RSN keeps
   a local chain; the national chain interleaves and references each
   regional head). The cryptographic linkage is verified end-to-end;
   any break is a P0 incident.
3. **Stream catch-up**: pull missed events from peers in
   `(source_rsn, local_seq)` order. Apply with at-least-once dedup.
4. **Proposal upload**: push locally generated proposals to the owner
   RSNs. Owners apply or reject; rejections feed `manual-merge`.
5. **State validation**: run `consistency-check` over a 1% sample of
   entities; mismatches escalated.
6. **Policy refresh**: pull latest policy bundle and verify signature.
   Switch from freeze bundle back to live bundle.
7. **AI restoration**: only after validation pass — re-enable promoted
   AI advisories; re-run shadow on a fresh batch.

## 5.8 Two-phase custody handoff

Cross-RSN transfer of ownership (patient transfer between regions):

```
RSN-A (current owner)            RSN-B (destination)
   │                                       │
   │  prepare_transfer(entity, vector)     │
   │ ──────────────────────────────────►   │
   │                                       │  validate, accept locally as 'pending-take'
   │                                       │  emit 'transfer.prepared'
   │  ack(transfer_id)                     │
   │ ◄──────────────────────────────────   │
   │                                       │
   │  commit_transfer(transfer_id)         │
   │ ──────────────────────────────────►   │
   │  emit 'transfer.committed'            │
   │  local 'owning_rsn = RSN-B'           │  apply 'owning_rsn = RSN-B'
```

Timeouts: prepare → commit must complete in 30 s under green/yellow,
30 min under red. Beyond timeout, RSN-A reverts (`transfer.aborted`),
RSN-B drops the pending-take. During the window, both RSNs treat the
entity as **read-only**.

## 5.9 Observability of sync

- `sync_lag_seconds{stream, peer, priority}` per stream/peer.
- `sync_backlog_events{stream, priority}`.
- `partition_active{rsn}` (0/1).
- `safe_mode_active{rsn}` (0/1).
- `manual_merge_open{severity}` count.
- `vector_clock_skew{peer}`.

Alerting:

- P0 stream lag > 5 s → page.
- Audit chain break → P0, immediate.
- Manual merge severity S0 unattended > 30 min → page Ministry duty.

## 5.10 Bench targets

| Metric | Target |
|--------|--------|
| Local writes during partition | ≥ baseline TPS |
| Sync catch-up rate (post-heal, green) | ≥ 50 k events/min/peer |
| Cold-start (RSN bootstrap from peer) | full RSN ≤ 4 h |
| Custody handoff (green) | P99 < 5 s |
| Manual-merge rate | < 1 / 10 000 sync ops in steady state |
