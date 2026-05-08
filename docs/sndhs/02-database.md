# 02 — Database Design

## 2.1 Storage planes

| Plane | Engine | Purpose | Replication |
|-------|--------|---------|-------------|
| Operational (clinical) | PostgreSQL 16 | FHIR resources, MPI, FSM state | Patroni 3-node, sync replica + 1 async |
| Event log | PostgreSQL 16 (separate cluster) + NATS JetStream | Append-only domain events | Per-RSN local, async to NFT |
| Audit ledger | PostgreSQL 16 + WORM object store | Hash-chained audit | Sync replica + WORM archive |
| Search/index | OpenSearch | Patient lookup, free-text | Per-RSN, rebuildable |
| Cache | Redis 7 (sentinel) | Sessions, idempotency keys, dedup | Per-RSN |
| Time-series | Victoria Metrics / Mimir | Vitals, telemetry | Hot per-RSN, cold national |
| Object | Sovereign S3 (MinIO/R2) | DICOM, lab images, PDF reports | Erasure-coded per RSN, sync to NFT |
| Cold archive | WORM tape / object | Audit, immutable retention | National only |

PostgreSQL is the system of record for clinical data, audit, and event log.
Other engines are derived stores rebuildable from the event log.

## 2.2 Identifier strategy

- **`sndhs_id`** — ULID (26 chars, lexicographically sortable, monotonic per
  RSN). All tables use ULIDs as PKs unless they map directly to a FHIR
  identifier system.
- **`mpi_id`** — opaque ULID. National scope. The only ID that crosses
  systems.
- **`region_id`** — short code (`BG`, `BS`, `NJ`, …). Embedded in event
  topics and CRDT replica IDs.
- **`pseudonym_id`** — per-purpose pseudonym derived as
  `HMAC(secret_per_purpose, mpi_id || purpose_tag)`. Used for analytics so
  research data sets cannot be correlated across purposes.

External identifiers (national ID, passport, driver licence) are held only
inside MPI and are encrypted at rest with a column-level key.

## 2.3 Core schema (operational store)

All clinical tables include the following meta columns. Tables that omit
them are non-clinical and live outside the audit boundary.

```sql
CREATE TYPE time_quality AS ENUM ('TRUSTED','DRIFTED','UNVERIFIED','LOCAL_FALLBACK');

CREATE TABLE _clinical_meta_template ( -- documentary; do not create
  id                  CHAR(26) PRIMARY KEY,
  region_id           TEXT NOT NULL,
  owning_rsn          TEXT NOT NULL,
  policy_version_id   CHAR(26) NOT NULL REFERENCES policy_versions(id),
  decision_context_hash BYTEA NOT NULL,
  created_at_ns       BIGINT NOT NULL,
  created_at_utc      TIMESTAMPTZ NOT NULL,
  created_tz_offset   SMALLINT NOT NULL,
  time_authority_id   UUID NOT NULL,
  time_quality        time_quality NOT NULL,
  created_by_principal CHAR(26) NOT NULL,
  attestation_id      CHAR(26) NOT NULL,
  causation_id        CHAR(26),
  correlation_id      CHAR(26) NOT NULL,
  version             BIGINT NOT NULL DEFAULT 1, -- optimistic lock
  schema_version      INT NOT NULL,
  legal_hold          BOOLEAN NOT NULL DEFAULT FALSE,
  retention_class     TEXT NOT NULL,
  archived            BOOLEAN NOT NULL DEFAULT FALSE
);
```

### 2.3.1 MPI

```sql
CREATE TABLE mpi_record (
  id                CHAR(26) PRIMARY KEY,           -- mpi_id
  status            TEXT NOT NULL CHECK (status IN ('ACTIVE','MERGED','ARCHIVED','DECEASED')),
  merged_into       CHAR(26),
  region_origin     TEXT NOT NULL,
  -- demographics — encrypted column group
  given_name_enc    BYTEA NOT NULL,
  family_name_enc   BYTEA NOT NULL,
  dob_enc           BYTEA NOT NULL,
  sex_enc           BYTEA NOT NULL,
  -- searchable hashes (HMAC under per-attribute key)
  hmac_given        BYTEA NOT NULL,
  hmac_family       BYTEA NOT NULL,
  hmac_dob          BYTEA NOT NULL,
  hmac_phone        BYTEA,
  -- meta
  version           BIGINT NOT NULL DEFAULT 1,
  policy_version_id CHAR(26) NOT NULL,
  created_at_ns     BIGINT NOT NULL,
  updated_at_ns     BIGINT NOT NULL
);
CREATE UNIQUE INDEX idx_mpi_record_active_natid ON mpi_record(hmac_natid)
  WHERE status='ACTIVE';
CREATE INDEX idx_mpi_record_phone ON mpi_record(hmac_phone) WHERE hmac_phone IS NOT NULL;

CREATE TABLE mpi_external_id (
  id                CHAR(26) PRIMARY KEY,
  mpi_id            CHAR(26) NOT NULL REFERENCES mpi_record(id),
  system            TEXT NOT NULL,        -- e.g. 'urn:iraq:nid', 'urn:iraq:passport'
  value_enc         BYTEA NOT NULL,
  hmac_value        BYTEA NOT NULL,
  is_primary        BOOLEAN NOT NULL DEFAULT FALSE,
  status            TEXT NOT NULL DEFAULT 'ACTIVE',
  UNIQUE (system, hmac_value)
);

CREATE TABLE mpi_match_decision (
  id                CHAR(26) PRIMARY KEY,
  candidate_a       CHAR(26) NOT NULL,
  candidate_b       CHAR(26) NOT NULL,
  score             NUMERIC(5,4) NOT NULL,
  decision          TEXT NOT NULL CHECK (decision IN ('MATCH','POSSIBLE','NO_MATCH','MERGED','REJECTED')),
  decided_by        CHAR(26),                          -- null = automated
  policy_version_id CHAR(26) NOT NULL,
  decided_at_ns     BIGINT NOT NULL
);
```

### 2.3.2 Encounter / FSM

```sql
CREATE TABLE encounter (
  id                CHAR(26) PRIMARY KEY,
  mpi_id            CHAR(26) NOT NULL,
  facility_id       CHAR(26) NOT NULL,
  state             TEXT NOT NULL,                    -- see 04-state-machines.md
  acuity_class      TEXT,                             -- ESI 1-5 / MTS color
  opened_at_ns      BIGINT NOT NULL,
  closed_at_ns      BIGINT,
  is_critical       BOOLEAN NOT NULL DEFAULT FALSE,
  parent_encounter  CHAR(26),
  -- meta
  policy_version_id CHAR(26) NOT NULL,
  version           BIGINT NOT NULL DEFAULT 1,
  region_id         TEXT NOT NULL,
  owning_rsn        TEXT NOT NULL
);

CREATE TABLE encounter_transition (
  id                CHAR(26) PRIMARY KEY,
  encounter_id      CHAR(26) NOT NULL REFERENCES encounter(id),
  from_state        TEXT NOT NULL,
  to_state          TEXT NOT NULL,
  trigger           TEXT NOT NULL,
  actor_principal   CHAR(26) NOT NULL,
  reason_code       TEXT,
  policy_version_id CHAR(26) NOT NULL,
  decision_context_hash BYTEA NOT NULL,
  occurred_at_ns    BIGINT NOT NULL,
  -- model-checked invariant: (from_state,to_state) ∈ allowed_transitions(policy_version_id)
  CONSTRAINT chk_transition_allowed CHECK (true)  -- enforced by trigger; see below
);

CREATE INDEX idx_enc_state_open ON encounter(state) WHERE closed_at_ns IS NULL;
CREATE INDEX idx_enc_critical_open ON encounter(opened_at_ns) WHERE is_critical AND closed_at_ns IS NULL;
```

Transition validity is enforced by a trigger that consults
`policy_version.transition_table`:

```sql
CREATE OR REPLACE FUNCTION enforce_encounter_transition() RETURNS trigger AS $$
DECLARE
  ok BOOLEAN;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM policy_transition_rule r
    WHERE r.policy_version_id = NEW.policy_version_id
      AND r.entity = 'encounter'
      AND r.from_state = NEW.from_state
      AND r.to_state = NEW.to_state
  ) INTO ok;
  IF NOT ok THEN
    RAISE EXCEPTION 'illegal encounter transition % -> % under policy %',
      NEW.from_state, NEW.to_state, NEW.policy_version_id
      USING ERRCODE = 'P0001';
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
```

### 2.3.3 Referral (closed-loop)

```sql
CREATE TABLE referral (
  id                CHAR(26) PRIMARY KEY,
  mpi_id            CHAR(26) NOT NULL,
  from_facility     CHAR(26) NOT NULL,
  to_facility       CHAR(26) NOT NULL,
  specialty         TEXT NOT NULL,
  priority_class    TEXT NOT NULL CHECK (priority_class IN ('P0','P1','P2','P3')),
  state             TEXT NOT NULL,                    -- see 04-state-machines.md
  reason_code       TEXT NOT NULL,
  clinical_summary_blob CHAR(26),                     -- pointer to encrypted blob
  -- closed-loop fields
  acceptance_deadline_ns BIGINT NOT NULL,
  acceptance_at_ns  BIGINT,
  appointment_at_ns BIGINT,
  arrival_at_ns     BIGINT,
  outcome_at_ns     BIGINT,
  outcome_code      TEXT,
  feedback_to_origin BOOLEAN NOT NULL DEFAULT FALSE,
  -- meta + lifecycle
  policy_version_id CHAR(26) NOT NULL,
  version           BIGINT NOT NULL DEFAULT 1,
  region_id         TEXT NOT NULL,
  owning_rsn        TEXT NOT NULL,
  created_at_ns     BIGINT NOT NULL
);

CREATE INDEX idx_referral_open_p01 ON referral (priority_class, created_at_ns)
  WHERE state NOT IN ('CLOSED','CANCELLED','REJECTED');
```

### 2.3.4 Order / Result / Vitals

```sql
CREATE TABLE clinical_order (
  id                CHAR(26) PRIMARY KEY,
  encounter_id      CHAR(26) NOT NULL REFERENCES encounter(id),
  mpi_id            CHAR(26) NOT NULL,
  order_type        TEXT NOT NULL CHECK (order_type IN ('LAB','IMAGING','MEDICATION','PROCEDURE')),
  catalogue_code    TEXT NOT NULL,             -- LOINC / SNOMED / ATC
  state             TEXT NOT NULL,
  priority_class    TEXT NOT NULL,
  ordered_by        CHAR(26) NOT NULL,
  ordered_at_ns     BIGINT NOT NULL,
  policy_version_id CHAR(26) NOT NULL,
  version           BIGINT NOT NULL DEFAULT 1,
  idempotency_key   CHAR(26) NOT NULL,
  UNIQUE (idempotency_key)
);

CREATE TABLE clinical_result (
  id                CHAR(26) PRIMARY KEY,
  order_id          CHAR(26) REFERENCES clinical_order(id),
  encounter_id      CHAR(26) NOT NULL,
  mpi_id            CHAR(26) NOT NULL,
  result_type       TEXT NOT NULL,
  observation_code  TEXT NOT NULL,           -- LOINC
  value_quantity    NUMERIC,
  value_unit        TEXT,
  value_string      TEXT,
  abnormal_flag     TEXT,
  status            TEXT NOT NULL,
  recorded_at_ns    BIGINT NOT NULL,
  device_id         CHAR(26),
  policy_version_id CHAR(26) NOT NULL,
  version           BIGINT NOT NULL DEFAULT 1
);

CREATE TABLE vital_sign_obs (
  id                CHAR(26) PRIMARY KEY,
  encounter_id      CHAR(26) NOT NULL,
  mpi_id            CHAR(26) NOT NULL,
  loinc_code        TEXT NOT NULL,
  value             NUMERIC NOT NULL,
  unit              TEXT NOT NULL,
  measured_at_ns    BIGINT NOT NULL,
  source            TEXT NOT NULL,            -- 'monitor','manual','ambulance'
  device_id         CHAR(26),
  policy_version_id CHAR(26) NOT NULL
);
CREATE INDEX idx_vitals_enc_time ON vital_sign_obs(encounter_id, measured_at_ns DESC);
```

### 2.3.5 Decisions (stabilizer view)

```sql
CREATE TABLE decision (
  id                CHAR(26) PRIMARY KEY,
  decision_class    TEXT NOT NULL,
  subject_kind      TEXT NOT NULL,            -- 'encounter','region','patient'
  subject_id        CHAR(26) NOT NULL,
  current_value     TEXT NOT NULL,
  pending_value     TEXT,
  state             TEXT NOT NULL,            -- STABLE | EVALUATING | LOCKED | OSCILLATING | FROZEN
  evaluating_since_ns BIGINT,
  locked_until_ns   BIGINT,
  flips_in_window   INT NOT NULL DEFAULT 0,
  policy_version_id CHAR(26) NOT NULL,
  version           BIGINT NOT NULL DEFAULT 1,
  UNIQUE (decision_class, subject_kind, subject_id)
);

CREATE TABLE decision_history (
  id                CHAR(26) PRIMARY KEY,
  decision_id       CHAR(26) NOT NULL REFERENCES decision(id),
  from_value        TEXT,
  to_value          TEXT NOT NULL,
  signal_strength   NUMERIC,
  hysteresis_ok     BOOLEAN NOT NULL,
  human_override    CHAR(26),
  occurred_at_ns    BIGINT NOT NULL,
  policy_version_id CHAR(26) NOT NULL
);
```

## 2.4 FHIR mapping

- **MPI → FHIR `Patient`** (`mpi_record` + `mpi_external_id`).
- **Encounter → FHIR `Encounter`** (state mapped via lookup table; SNDHS
  states are richer — see `04-state-machines.md` §encounter mapping).
- **Referral → FHIR `ServiceRequest`** with `category=referral` plus a
  `Task` for closed-loop follow-up.
- **Order → FHIR `ServiceRequest` / `MedicationRequest`** (by type).
- **Result → FHIR `Observation` / `DiagnosticReport`**.
- **Vitals → FHIR `Observation` (vital-signs profile)**.
- **AllergyIntolerance, Condition, Procedure, Immunization, MedicationStatement**
  follow FHIR R5 directly with the meta envelope.

The FHIR view is **derived**, not stored. A read endpoint composes FHIR
JSON from the canonical tables on demand. A nightly `consistency-check`
diffs canonical → FHIR projection on a sample to detect mapping drift.

## 2.5 Event sourcing model

- **Domain event** (`domain_event` table, also published to NATS):

```sql
CREATE TABLE domain_event (
  id                CHAR(26) PRIMARY KEY,         -- ULID, monotonic
  stream_kind       TEXT NOT NULL,                 -- 'encounter','referral','order',...
  stream_id         CHAR(26) NOT NULL,
  sequence          BIGINT NOT NULL,               -- per stream
  event_type        TEXT NOT NULL,
  schema_version    INT NOT NULL,
  payload_json      JSONB NOT NULL,
  -- meta
  policy_version_id CHAR(26) NOT NULL,
  causation_id      CHAR(26),
  correlation_id    CHAR(26) NOT NULL,
  actor_principal   CHAR(26) NOT NULL,
  attestation_id    CHAR(26) NOT NULL,
  occurred_at_ns    BIGINT NOT NULL,
  recorded_at_ns    BIGINT NOT NULL,
  region_id         TEXT NOT NULL,
  source_rsn        TEXT NOT NULL,
  signature         BYTEA NOT NULL,                -- Ed25519 over canonical bytes
  UNIQUE (stream_kind, stream_id, sequence)
);
CREATE INDEX idx_event_recorded ON domain_event(recorded_at_ns);
CREATE INDEX idx_event_corr ON domain_event(correlation_id);
```

- **Outbox + projection**: writes use the transactional outbox pattern.
  Service `X` writes to `X.snapshot` and `domain_event` in one
  transaction; an outbox-poller publishes the event to NATS at-least-once;
  consumers idempotently update read models.
- **Snapshots**: each stream has a snapshot every `N=200` events; rebuild
  reads the latest snapshot + tail events.
- **Replay**: any read model is rebuildable by replaying `domain_event`
  filtered by `stream_kind`. Replays run against a shadow database first;
  a swap-over is a Ministry-approved release.

## 2.6 Versioning model

| Mechanism | Where | Purpose |
|-----------|-------|---------|
| Optimistic lock (`version` column) | every clinical row | concurrent edit safety |
| Per-stream `sequence` | event log | deterministic ordering |
| `schema_version` in payload | every event/contract | forward/back compatibility |
| `policy_version_id` | every clinical row + event | bind decision to rules |
| Branch `replica_clock` | offline RSNs | conflict reasoning (see §2.7) |

Schema migrations follow the same migration policy as `gula-platform`
(forward-only, idempotent guards, never edit a merged migration). All
new clinical columns must be NULL-able or have a server default.

## 2.7 Conflict resolution (offline / cross-RSN)

- Every clinical entity has exactly one **owning RSN** (`owning_rsn` column).
- Mutations on a non-owning RSN are stored as **proposals** (`*_proposal`
  tables). They never become canonical until reconciled with the owner.
- On reconnect, proposals are sent in a vector-clocked envelope. The owner
  applies a per-entity resolver:

  | Entity class | Resolver |
  |--------------|----------|
  | Allergies, problem list, immunisations | CRDT (OR-set) — additive merge, last-writer-wins on tombstones |
  | Encounter / Referral state | Event-log replay via deterministic FSM resolver; proposals that violate the FSM under the canonical timeline are rejected with `STATE_CONFLICT_REJECTED` |
  | Vitals, lab results | Append-only — duplicates dedup by `idempotency_key`; ordering by `measured_at_ns` |
  | Identity (MPI demographic edits) | Three-way merge with field-level priority (e.g., govt-issued ID wins over manual edit). Otherwise → manual queue |
  | Custody handoff (transfer to another RSN) | Two-phase commit: source emits `transfer.prepared`, destination ACKs; on ACK source emits `transfer.committed` and ownership flips. Without ACK, source remains owner. |

- Unresolvable conflicts open a `manual-merge` ticket with full diff and
  both timelines; the medical-records officer merges, with a two-person
  rule for high-severity classes.

## 2.8 Partitioning & retention

- `domain_event`, `audit_entry`, `vital_sign_obs`, `clinical_result` use
  `LIST` partitioning by `region_id`, then `RANGE` by `occurred_at_ns`
  monthly. Retention enforced by `pg_partman` with the `retention_class`
  field deciding archive vs purge (`11-governance.md`).
- Hot window kept on local NVMe; warm window on slower SSD; cold archive
  on WORM (audit) or pruned (per retention class).

## 2.9 Constraints, triggers, and integrity

- **No raw `now()`**: a `BEFORE INSERT/UPDATE` trigger rejects rows where
  `created_at_ns` was not supplied via signed time (the SDK injects it;
  direct DB clients fail).
- **Tenant guard** (regional view): row-level security ensures a user
  with `attr_region=BG` cannot read rows where `region_id != 'BG'`
  unless they hold the `cross-region-read` permission.
- **Audit hash chain**: see `06-security.md` §audit chain. Trigger on
  `audit_entry` computes `prev_hash || canonical(this)` → BLAKE3 → store.
- **No physical deletes** of clinical rows. Tombstoning by `archived=true`
  + retention class. Deletion is performed by the data-lifecycle service
  only, with a signed deletion order.
- **Foreign keys**: cross-domain FKs are forbidden; references between
  domains carry the ID but no DB-level FK (so domain replicas stay
  independent for offline). Integrity is enforced by event handlers and a
  nightly `referential-integrity-audit`.

## 2.10 Indexing & access patterns

Every clinical lookup must hit an index. The query review checklist is
part of the migration gate. Forbidden patterns: `LIKE '%x%'` on patient
attributes, `ILIKE` on demographics, `OFFSET` paging on tables > 1 M
rows (use keyset paging on `(created_at_ns, id)`).

## 2.11 Encryption at rest

- TDE at filesystem level (LUKS / sovereign HSM-rooted key).
- Column-level AEAD for: demographics, external IDs, free-text clinical
  notes, attachment metadata. Keys held in regional HSM; envelope key
  rotates yearly; data keys per-RSN per-month.
- Each encrypted column's HMAC counterpart uses a separate key class
  (search key) so HMAC theft does not enable decryption.

## 2.12 Backup, PITR, and DR

- Streaming WAL to two geographies + WORM hourly snapshot.
- PITR target: 5 min RPO, 30 min RTO inside an RSN, 4 h RTO if a whole
  RSN is destroyed (rebuild from event log on a peer).
- Quarterly destructive-restore drills mandatory and audited.
