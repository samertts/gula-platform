# GULA Platform — Database Query Optimization Guide

## 1. Common Anti-Patterns

### N+1 Queries
```python
# BAD — N+1 queries
orders = db.query(LabOrder).all()
for order in orders:
    print(order.patient.name)  # Triggers N additional queries

# GOOD — Eager loading
from sqlalchemy.orm import joinedload
orders = db.query(LabOrder).options(joinedload(LabOrder.patient)).all()
```

### Missing Filters
```python
# BAD — No tenant isolation filter
patients = db.query(Patient).all()

# GOOD — Tenant isolation
patients = db.query(Patient).filter(Patient.lab_id == current_lab_id).all()
```

## 2. Index Strategy

### Required Indexes
```sql
-- Tenant isolation
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_lab_orders_lab_id_status 
    ON lab_orders (lab_id, status);

-- Patient lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_patients_lab_id_national_id 
    ON patients (lab_id, national_id) WHERE national_id IS NOT NULL;

-- Time-range queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_lab_results_lab_id_created_at 
    ON lab_results (lab_id, created_at DESC);

-- Audit log queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_audit_logs_lab_id_created_at 
    ON audit_logs (lab_id, created_at DESC);
```

### Partial Indexes
```sql
-- Only index critical results
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_results_critical 
    ON lab_results (lab_id, created_at DESC) WHERE flag = 'critical';
```

## 3. Query Optimization Patterns

### Use selectinload for collections
```python
# Instead of joinedload for collections
orders = db.query(LabOrder).options(
    selectinload(LabOrder.results)
).all()
```

### Batch loading
```python
# Process in batches to avoid memory issues
for batch in range(0, total, 100):
    items = db.query(LabOrder).offset(batch).limit(100).all()
    process(items)
```

### Use with_loader_criteria for global filters
```python
from sqlalchemy.orm import with_loader_criteria
query = db.query(LabOrder).execution_options(
    loader_criteria=[with_loader_criteria(LabOrder, LabOrder.lab_id == current_lab_id)]
)
```

## 4. EXPLAIN ANALYZE Patterns

```sql
-- Check query plan
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM lab_orders 
WHERE lab_id = 'abc' AND status = 'pending' 
ORDER BY created_at DESC LIMIT 20;

-- Look for:
-- Seq Scan on large tables (missing index)
-- Nested Loop with many rows (bad join order)
-- Sort with high memory (add index)
```

## 5. Connection Pool Tuning

```python
# Current budget: 2 workers × (5 pool + 10 overflow) = 30
# PG max_connections: 100
# Reserve 20 connections for admin/superuser

WEB_CONCURRENCY=3
DB_POOL_SIZE=6
DB_MAX_OVERFLOW=12
# Budget: 3 × (6 + 12) = 54 — under 100 ✓
```

## 6. Statement Timeout

```python
# Set per-connection
cursor.execute("SET statement_timeout = '30s'")
cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
```
