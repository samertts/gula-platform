-- =============================================================================
-- GULA PLATFORM - Main Database Schema
-- Executive Orders 5, 9, 10, 11
-- =============================================================================

-- Create Keycloak database (safe idempotent)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak') THEN
    PERFORM dblink_exec('dbname=' || current_database(), 'CREATE DATABASE keycloak');
  END IF;
EXCEPTION WHEN others THEN
  -- dblink not available: run manually or keycloak will create it
  NULL;
END
$$;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- =============================================================================
-- LABORATORIES
-- =============================================================================
CREATE TABLE IF NOT EXISTS laboratories (
    id          BIGSERIAL PRIMARY KEY,
    lab_uuid    UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    lab_name    TEXT NOT NULL,
    city        TEXT,
    region      TEXT,
    contact_phone TEXT,
    email       TEXT,
    status      TEXT DEFAULT 'active' CHECK (status IN ('active','suspended','inactive')),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- USERS
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL PRIMARY KEY,
    user_uuid   UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    username    TEXT UNIQUE NOT NULL,
    email       TEXT UNIQUE,
    password_hash TEXT,
    role        TEXT DEFAULT 'lab_user'
                CHECK (role IN ('superadmin','admin','lab_manager','lab_user','viewer')),
    lab_id      BIGINT REFERENCES laboratories(id) ON DELETE SET NULL,
    keycloak_id TEXT UNIQUE,
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- PATIENTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS patients (
    id          BIGSERIAL PRIMARY KEY,
    patient_uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    lab_id      BIGINT REFERENCES laboratories(id),
    national_id TEXT,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    gender      TEXT CHECK (gender IN ('M','F','other')),
    date_of_birth DATE,
    age         INTEGER,
    phone       TEXT,
    email       TEXT,
    address     TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patients_lab_id ON patients(lab_id);
CREATE INDEX idx_patients_national_id ON patients(national_id);
CREATE INDEX idx_patients_name ON patients USING gin(to_tsvector('english', first_name || ' ' || last_name));

-- =============================================================================
-- MEDICAL TESTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS medical_tests (
    id          BIGSERIAL PRIMARY KEY,
    test_code   TEXT UNIQUE NOT NULL,
    test_name   TEXT NOT NULL,
    category    TEXT,
    description TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_parameters (
    id              BIGSERIAL PRIMARY KEY,
    test_id         BIGINT REFERENCES medical_tests(id) ON DELETE CASCADE,
    parameter_name  TEXT NOT NULL,
    unit            TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reference_ranges (
    id              BIGSERIAL PRIMARY KEY,
    parameter_id    BIGINT REFERENCES test_parameters(id) ON DELETE CASCADE,
    gender          TEXT,
    age_min         INTEGER,
    age_max         INTEGER,
    normal_min      FLOAT,
    normal_max      FLOAT
);

-- =============================================================================
-- TEST ORDERS
-- =============================================================================
CREATE TABLE IF NOT EXISTS test_orders (
    id          BIGSERIAL PRIMARY KEY,
    order_uuid  UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    lab_id      BIGINT REFERENCES laboratories(id),
    patient_id  BIGINT REFERENCES patients(id),
    test_id     BIGINT REFERENCES medical_tests(id),
    priority    TEXT DEFAULT 'routine' CHECK (priority IN ('stat','urgent','routine')),
    status      TEXT DEFAULT 'pending'
                CHECK (status IN ('pending','in_progress','completed','cancelled')),
    ordered_by  BIGINT REFERENCES users(id),
    ordered_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_lab_id ON test_orders(lab_id);
CREATE INDEX idx_orders_patient_id ON test_orders(patient_id);
CREATE INDEX idx_orders_status ON test_orders(status);
CREATE INDEX idx_orders_ordered_at ON test_orders(ordered_at);

-- =============================================================================
-- SAMPLES
-- =============================================================================
CREATE TABLE IF NOT EXISTS samples (
    id              BIGSERIAL PRIMARY KEY,
    sample_uuid     UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    order_id        BIGINT REFERENCES test_orders(id),
    barcode         TEXT UNIQUE,
    sample_type     TEXT,
    collection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    received_time   TIMESTAMP,
    status          TEXT DEFAULT 'collected'
                    CHECK (status IN ('collected','in_transit','received','processing','completed','rejected')),
    collected_by    BIGINT REFERENCES users(id),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_samples_order_id ON samples(order_id);
CREATE INDEX idx_samples_barcode ON samples(barcode);
CREATE INDEX idx_samples_status ON samples(status);

-- =============================================================================
-- TEST RESULTS - Partitioned by month (Executive Order 11)
-- =============================================================================
CREATE TABLE IF NOT EXISTS test_results (
    id              BIGSERIAL,
    result_uuid     UUID DEFAULT uuid_generate_v4(),
    order_id        BIGINT NOT NULL,
    sample_id       BIGINT,
    parameter_id    BIGINT,
    value           TEXT,
    numeric_value   FLOAT,
    unit            TEXT,
    status          TEXT DEFAULT 'pending'
                    CHECK (status IN ('pending','validated','rejected','flagged')),
    is_abnormal     BOOLEAN DEFAULT false,
    validated_by    BIGINT,
    validated_at    TIMESTAMP,
    file_url        TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for current year and next year
CREATE TABLE test_results_2024_01 PARTITION OF test_results
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE test_results_2024_02 PARTITION OF test_results
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
CREATE TABLE test_results_2024_03 PARTITION OF test_results
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');
CREATE TABLE test_results_2024_04 PARTITION OF test_results
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');
CREATE TABLE test_results_2024_05 PARTITION OF test_results
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');
CREATE TABLE test_results_2024_06 PARTITION OF test_results
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');
CREATE TABLE test_results_2024_07 PARTITION OF test_results
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');
CREATE TABLE test_results_2024_08 PARTITION OF test_results
    FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');
CREATE TABLE test_results_2024_09 PARTITION OF test_results
    FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');
CREATE TABLE test_results_2024_10 PARTITION OF test_results
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');
CREATE TABLE test_results_2024_11 PARTITION OF test_results
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');
CREATE TABLE test_results_2024_12 PARTITION OF test_results
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

CREATE TABLE test_results_2025_01 PARTITION OF test_results
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE test_results_2025_02 PARTITION OF test_results
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
CREATE TABLE test_results_2025_03 PARTITION OF test_results
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');
CREATE TABLE test_results_2025_04 PARTITION OF test_results
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');
CREATE TABLE test_results_2025_05 PARTITION OF test_results
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');
CREATE TABLE test_results_2025_06 PARTITION OF test_results
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');
CREATE TABLE test_results_2025_07 PARTITION OF test_results
    FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');
CREATE TABLE test_results_2025_08 PARTITION OF test_results
    FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
CREATE TABLE test_results_2025_09 PARTITION OF test_results
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
CREATE TABLE test_results_2025_10 PARTITION OF test_results
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
CREATE TABLE test_results_2025_11 PARTITION OF test_results
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
CREATE TABLE test_results_2025_12 PARTITION OF test_results
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

CREATE TABLE test_results_2026_01 PARTITION OF test_results
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE test_results_2026_02 PARTITION OF test_results
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE test_results_2026_03 PARTITION OF test_results
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE test_results_2026_04 PARTITION OF test_results
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
CREATE TABLE test_results_2026_05 PARTITION OF test_results
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE test_results_2026_06 PARTITION OF test_results
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE test_results_2026_07 PARTITION OF test_results
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE test_results_2026_08 PARTITION OF test_results
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE test_results_2026_09 PARTITION OF test_results
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE test_results_2026_10 PARTITION OF test_results
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE test_results_2026_11 PARTITION OF test_results
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE test_results_2026_12 PARTITION OF test_results
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

-- Default partition for future data
CREATE TABLE test_results_future PARTITION OF test_results
    FOR VALUES FROM ('2027-01-01') TO (MAXVALUE);

CREATE INDEX idx_results_order_id ON test_results(order_id, created_at);
CREATE INDEX idx_results_status ON test_results(status, created_at);

-- =============================================================================
-- QUALITY CONTROL
-- =============================================================================
CREATE TABLE IF NOT EXISTS quality_control (
    id          BIGSERIAL PRIMARY KEY,
    lab_id      BIGINT REFERENCES laboratories(id),
    test_id     BIGINT REFERENCES medical_tests(id),
    qc_value    FLOAT,
    qc_level    TEXT,
    in_range    BOOLEAN DEFAULT true,
    qc_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    performed_by BIGINT REFERENCES users(id)
);

-- =============================================================================
-- MEDICAL DEVICES
-- =============================================================================
CREATE TABLE IF NOT EXISTS medical_devices (
    id              BIGSERIAL PRIMARY KEY,
    device_uuid     UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    lab_id          BIGINT REFERENCES laboratories(id),
    device_name     TEXT NOT NULL,
    manufacturer    TEXT,
    model           TEXT,
    serial_number   TEXT UNIQUE,
    protocol        TEXT,
    ip_address      TEXT,
    port            INTEGER,
    status          TEXT DEFAULT 'online'
                    CHECK (status IN ('online','offline','maintenance','error')),
    last_seen       TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- DIAGNOSTIC REPORTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS diagnostic_reports (
    id          BIGSERIAL PRIMARY KEY,
    report_uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    patient_id  BIGINT REFERENCES patients(id),
    order_id    BIGINT,
    report_type TEXT,
    report_text TEXT,
    file_url    TEXT,
    minio_bucket TEXT,
    minio_key   TEXT,
    generated_by BIGINT REFERENCES users(id),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SAMPLE DATA
-- =============================================================================
INSERT INTO medical_tests (test_code, test_name, category) VALUES
('CBC','Complete Blood Count','Laboratory'),
('LFT','Liver Function Test','Laboratory'),
('KFT','Kidney Function Test','Laboratory'),
('GLUC','Blood Glucose','Laboratory'),
('HBA1C','Hemoglobin A1C','Laboratory'),
('LIPID','Lipid Profile','Laboratory'),
('THYROID','Thyroid Panel','Laboratory'),
('RXRAY','X-Ray Chest','Radiology'),
('CTSCAN','CT Scan Brain','Radiology'),
('MRI','MRI Spine','Radiology'),
('ECG','Electrocardiogram','Cardiology'),
('ECHO','Echocardiography','Cardiology'),
('PCR','PCR COVID','Molecular'),
('CULT','Blood Culture','Microbiology')
ON CONFLICT DO NOTHING;
