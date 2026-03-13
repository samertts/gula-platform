-- =============================================================================
-- GULA Platform - ClickHouse Analytics Schema
-- Executive Order 12: Analytics in dedicated database (not PostgreSQL)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS gula;

-- =============================================================================
-- LAB RESULTS ANALYTICS
-- High-performance analytics table (no foreign keys, denormalized for speed)
-- =============================================================================

CREATE TABLE IF NOT EXISTS gula.lab_results
(
    id              UUID DEFAULT generateUUIDv4(),
    order_id        UInt64,
    patient_id      UInt64,
    lab_id          UInt64,
    lab_name        String,
    city            String,
    test_code       String,
    test_name       String,
    category        String,
    value           String,
    numeric_value   Float64,
    unit            String,
    is_abnormal     UInt8,
    status          String,
    gender          String,
    age             UInt8,
    created_at      DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (lab_id, test_code, created_at)
TTL created_at + INTERVAL 5 YEAR;


-- =============================================================================
-- DISEASE OUTBREAK DETECTION
-- Population-level analysis (Executive Order 12)
-- =============================================================================

CREATE TABLE IF NOT EXISTS gula.disease_tracking
(
    id              UUID DEFAULT generateUUIDv4(),
    test_code       String,
    test_name       String,
    city            String,
    region          String,
    lab_id          UInt64,
    positive_count  UInt32,
    total_count     UInt32,
    positivity_rate Float32,
    report_date     Date DEFAULT today(),
    created_at      DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(report_date)
ORDER BY (test_code, city, report_date);


-- =============================================================================
-- LAB PERFORMANCE ANALYTICS
-- =============================================================================

CREATE TABLE IF NOT EXISTS gula.lab_performance
(
    lab_id              UInt64,
    lab_name            String,
    city                String,
    date                Date DEFAULT today(),
    total_orders        UInt32,
    completed_orders    UInt32,
    pending_orders      UInt32,
    avg_turnaround_hrs  Float32,
    abnormal_rate       Float32,
    created_at          DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (lab_id, date);


-- =============================================================================
-- MATERIALIZED VIEWS FOR REAL-TIME AGGREGATION
-- =============================================================================

-- Abnormal results by city per day
CREATE MATERIALIZED VIEW IF NOT EXISTS gula.mv_abnormal_by_city
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (city, test_code, day)
AS
SELECT
    city,
    test_code,
    test_name,
    toDate(created_at) AS day,
    countIf(is_abnormal = 1) AS abnormal_count,
    count() AS total_count
FROM gula.lab_results
GROUP BY city, test_code, test_name, day;


-- Test volume by lab per day
CREATE MATERIALIZED VIEW IF NOT EXISTS gula.mv_test_volume
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (lab_id, day)
AS
SELECT
    lab_id,
    lab_name,
    toDate(created_at) AS day,
    count() AS test_count,
    countIf(is_abnormal = 1) AS abnormal_count
FROM gula.lab_results
GROUP BY lab_id, lab_name, day;
