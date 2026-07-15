# Performance — National Healthcare Platform

## Expected Query Performance

### Baseline Expectations

| Query Type | Expected Latency (p50) | Expected Latency (p95) | Expected Latency (p99) |
|-----------|----------------------|----------------------|----------------------|
| Single entity by PK | < 5ms | < 15ms | < 50ms |
| Single entity by unique index | < 10ms | < 25ms | < 80ms |
| List by patient (indexed) | < 20ms | < 50ms | < 150ms |
| List by date range (indexed) | < 30ms | < 80ms | < 200ms |
| Full-text search | < 100ms | < 300ms | < 1000ms |
| Patient summary (aggregate) | < 50ms | < 150ms | < 400ms |
| FHIR search | < 200ms | < 500ms | < 1500ms |
| Canonical ETL write | < 100ms | < 300ms | < 800ms |
| Event store append | < 10ms | < 25ms | < 80ms |
| MDM match evaluation | < 200ms | < 500ms | < 2000ms |

### Factors Affecting Performance

- **Data volume per patient** — patients with > 100 problem list items,
  > 50 medications, or > 200 clinical notes will degrade beyond p50
- **Facility size** — hospitals with > 500 beds or > 1000 daily encounters
  require increased connection pool capacity
- **Terminology cache** — uncold terminology lookups add 10-50ms per query
- **Cross-domain joins** — queries joining ehr_* with national_* tables
  incur FK traversal overhead

---

## Index Strategies

### Common Index Patterns

Every table implements these index categories:

1. **Primary Key** — ULID (String(26)) with B-tree for range scans and
   point lookups; ULID monotonicity ensures clustering-friendly inserts
2. **Patient/Citizen FK** — always indexed; most queries filter by
   patient_id or citizen_id
3. **Status + Patient** — composite index on (patient_id, status) for
   "active problems for patient" queries
4. **Date/Time** — event_date, administration_date, authored_at indexed
   for time-range queries
5. **Code** — medical codes (ICD-10, LOINC, SNOMED, vaccine codes)
   indexed for terminology-based lookups
6. **Soft Delete Filter** — composite index on (is_deleted, patient_id)
   to support the common pattern of "WHERE is_deleted = false"

### Table-Specific Indexes

| Table | Key Index | Pattern | Purpose |
|-------|-----------|---------|---------|
| `ehr_problem_list_items` | (patient_id, status) | Composite | Active problem list |
| `ehr_allergies` | (patient_id, status) | Composite | Active allergies |
| `ehr_medication_statements` | (patient_id, status) | Composite | Current medications |
| `ehr_medication_requests` | (patient_id, status) | Composite | Active prescriptions |
| `ehr_clinical_notes` | (patient_id, note_type) | Composite | Notes by type |
| `ehr_immunizations` | administration_date | B-tree | Due/overdue vaccines |
| `ehr_patient_timeline` | (patient_id, event_date) | Composite | Chronological timeline |
| `ehr_risk_factors` | (patient_id, risk_type) | Composite | Risk assessments |
| `ehr_conditions` | (patient_id, clinical_status) | Composite | Condition list |
| `ehr_diagnoses` | (patient_id, diagnosis_type) | Composite | Encounter diagnoses |
| `ehr_family_history` | (patient_id) | B-tree | Family history |
| `ehr_social_history` | (patient_id) | B-tree | Social history |
| `ehr_clinical_attachments` | (source_type, source_id) | Composite | Source-linked attachments |
| `cc_referral_requests` | (referring_facility_id, status) | Composite | Facility referrals |
| `cc_chronic_disease_registry` | (patient_id, disease_type) | Composite | Disease registry |
| `cc_pregnancy_records` | (patient_id) | B-tree | Pregnancy records |
| `cc_immunization_schedules` | (due_date, status) | Composite | Overdue schedules |
| `clinical_terminology_codes` | (system, code) | Composite | Code lookup |
| `clinical_terminology_mappings` | (source_code_id) | B-tree | Cross-system maps |

### Partial Indexes

```sql
-- Active only (soft-delete filtered)
CREATE INDEX ix_ehr_problem_active
  ON ehr_problem_list_items (patient_id, status)
  WHERE is_deleted = false;

-- Critical timeline events
CREATE INDEX ix_ehr_timeline_critical
  ON ehr_patient_timeline (event_date)
  WHERE is_critical = true;

-- Overdue immunization schedules
CREATE INDEX ix_cc_immunization_overdue
  ON cc_immunization_schedules (due_date)
  WHERE status = 'scheduled' AND due_date < CURRENT_DATE;
```

---

## Connection Pooling Configuration

### Formula

```
Max connections used = WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW)
```

### Production Defaults

| Parameter | Value | Description |
|-----------|-------|-------------|
| `WEB_CONCURRENCY` | 3 | Gunicorn worker processes |
| `DB_POOL_SIZE` | 6 | Persistent connections per worker |
| `DB_MAX_OVERFLOW` | 12 | Overflow connections per worker |
| `DB_POOL_TIMEOUT` | 30s | Wait for connection |
| `DB_POOL_RECYCLE` | 300s | Recycle connections |
| `DB_POOL_PRE_PING` | True | Validate before use |
| `DB_MAX_RETRIES` | 3 | Retry on connection failure |
| `DB_RETRY_DELAY` | 1s | Delay between retries |

**Budget:** 3 × (6 + 12) = 54 connections (PostgreSQL default max = 100)

### Pool Behavior

- **Steady state:** 3 workers × 6 pool = 18 persistent connections
- **Burst handling:** Up to 3 × 12 = 36 additional overflow connections
- **Timeout handling:** If pool exhausted for > 30s, return 503 Service Unavailable
- **Connection recycling:** Every 300s to prevent server-side connection drop
- **Health check:** Pre-ping on every connection checkout to detect stale connections

### Scaling

| Workers | Pool Size | Max Overflow | Total Budget | PostgreSQL max_connections |
|---------|-----------|-------------|--------------|---------------------------|
| 3 | 6 | 12 | 54 | 100 (default) |
| 5 | 5 | 10 | 75 | 120 |
| 10 | 4 | 8 | 120 | 200 |
| 15 | 3 | 6 | 135 | 200+ |
| 20 | 3 | 5 | 160 | 250+ |

When scaling beyond 5 workers, increase `postgres.max_connections` in
`docker-compose.yml` and adjust kernel `SHMMAX`.

---

## Caching Strategy

### Cache Layers

```
┌──────────┐      ┌──────────┐      ┌──────────┐
│  L1: App  │      │  L2: Redis│      │  L3: DB  │
│  (dict)   │────► │  (shared) │────► │  (disk)  │
│  per-     │      │  cluster  │      │  SSD     │
│  request  │      │           │      │          │
└──────────┘      └──────────┘      └──────────┘
```

### Cacheable Data

| Data Type | TTL | Invalidation | Strategy |
|-----------|-----|-------------|----------|
| Patient summary | 60s | On EHR mutation | Redis hash |
| Reference data (governorates, etc.) | 3600s | Manual refresh | Redis string |
| Terminology codes | 3600s | Terminology update | Redis hash |
| FHIR search results | 30s | On data mutation | Redis sorted set |
| Rate limit counters | Window | Automatic TTL | Redis sorted set |
| JWT blacklist | Until token expiry | On token revoke | Redis set |
| Feature flags | 300s | Manual refresh | Redis hash |
| User session | 3600s | On logout | Redis string |

### Cache-Aside Pattern (Implementation)

```python
def get_patient_summary(patient_id: str, db: Session) -> dict:
    # 1. Check cache
    key = f"patient_summary:{patient_id}"
    cached = redis.get(key)
    if cached:
        return json.loads(cached)

    # 2. Cache miss — load from DB
    summary = build_summary_from_db(patient_id, db)

    # 3. Store in cache
    redis.setex(key, 60, json.dumps(summary))

    return summary
```

### Write-Through Cache

For high-write scenarios (e.g., lab results), use write-through:

```python
def write_medication_administration(data, db):
    # 1. Write to DB
    record = MedicationAdministration(**data)
    db.add(record)
    db.commit()

    # 2. Invalidate related caches
    redis.delete(f"patient_summary:{data['patient_id']}")
    redis.delete(f"medications:{data['patient_id']}")
    redis.delete(f"timeline:{data['patient_id']}")

    return record
```

---

## Query Optimization Patterns

### 1. N+1 Query Prevention

**Bad:**
```python
referrals = db.query(ReferralRequest).all()
for r in referrals:  # N queries
    practitioner = db.get(Practitioner, r.referring_practitioner_id)
```

**Good:**
```python
referrals = db.query(ReferralRequest).all()
practitioner_ids = [r.referring_practitioner_id for r in referrals]
practitioners = {
    p.id: p for p in db.query(Practitioner).filter(
        Practitioner.id.in_(practitioner_ids)
    ).all()
}
for r in referrals:
    practitioner = practitioners.get(r.referring_practitioner_id)
```

### 2. Eager Loading

```python
# Bad
notes = db.query(ClinicalNote).filter(...).all()
for note in notes:
    author = note.author  # lazy load, N queries

# Good
notes = db.query(ClinicalNote).options(
    joinedload(ClinicalNote.author)
).filter(...).all()
```

### 3. Pagination

Always paginate list endpoints with cursor-based pagination:

```python
def list_medications(
    patient_id: str,
    cursor: str | None = None,
    limit: int = 50,
):
    query = db.query(MedicationStatement).filter(
        MedicationStatement.patient_id == patient_id,
        MedicationStatement.is_deleted == False,
    )
    if cursor:
        query = query.filter(MedicationStatement.id > cursor)
    return query.order_by(MedicationStatement.created_at.desc()).limit(limit).all()
```

### 4. Selective Column Loading

```python
# Bad — loads all columns (including large Text/JSON fields)
notes = db.query(ClinicalNote).filter(...).all()

# Good — load only needed columns
notes = db.query(
    ClinicalNote.id,
    ClinicalNote.title,
    ClinicalNote.note_type,
    ClinicalNote.authored_at,
).filter(...).all()
```

### 5. Bulk Operations

```python
# Bad — individual commits
for item in items:
    db.add(item)
    db.commit()

# Good — single commit
db.bulk_insert_mappings(MedicationAdministration, items_data)
db.commit()
```

### 6. Materialized Views

For frequent aggregate queries (dashboard, reporting), use materialized views:

```sql
CREATE MATERIALIZED VIEW patient_medication_count AS
SELECT patient_id, COUNT(*) as medication_count, status
FROM ehr_medication_statements
WHERE is_deleted = false
GROUP BY patient_id, status;
```

Refresh on schedule or on-demand:

```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY patient_medication_count;
```

### 7. Query Plan Analysis

Profile slow queries using EXPLAIN ANALYZE:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM ehr_clinical_notes
WHERE patient_id = 'ABC123'
  AND note_type = 'discharge_summary'
  AND is_deleted = false
ORDER BY authored_at DESC;
```

Look for:
- **Seq Scan** on large tables — add index
- **Bitmap Heap Scan** with high row estimates — analyze/update statistics
- **Nested Loop** with large inner table — consider hash join
- **Sort** on unindexed column — add index

### 8. Dead Query Detection

Monitor long-running queries:

```sql
SELECT pid, now() - pg_stat_activity.query_start AS duration,
       query, state
FROM pg_stat_activity
WHERE state != 'idle'
  AND query_start < now() - interval '5 seconds'
ORDER BY duration DESC;
```

### 9. Vacuum Strategy

Configure aggressive autovacuum for high-churn tables:

```sql
ALTER TABLE ehr_patient_timeline SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.005,
    autovacuum_vacuum_threshold = 1000
);
```

### 10. FHIR Search Optimization

FHIR search parameters that involve text matching use PostgreSQL
`pg_trgm` extension for trigram-based `ILIKE` search:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX ix_patient_name_trgm ON national_citizens
  USING gin (full_name_ar gin_trgm_ops);
```

This enables fast `WHERE full_name_ar ILIKE '%search_term%'` queries
for FHIR `name:contains` searches.
