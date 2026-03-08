-- ==============================
-- Laboratory Platform Database
-- ==============================

-- جدول المرضى
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول الفحوصات
CREATE TABLE IF NOT EXISTS lab_tests (
    id SERIAL PRIMARY KEY,
    test_name TEXT NOT NULL,
    unit TEXT,
    normal_range TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول طلبات الفحص
CREATE TABLE IF NOT EXISTS test_orders (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    ordered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول نتائج الفحوصات
CREATE TABLE IF NOT EXISTS test_results (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES test_orders(id) ON DELETE CASCADE,
    test_id INTEGER REFERENCES lab_tests(id) ON DELETE CASCADE,
    result_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول المستخدمين (نظام تسجيل الدخول)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'lab_user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- بيانات أولية للنظام
-- ==============================

INSERT INTO lab_tests (test_name, unit, normal_range)
VALUES
('Hemoglobin', 'g/dL', '13-17'),
('WBC', 'x10^9/L', '4-10'),
('Platelets', 'x10^9/L', '150-400'),
('Glucose', 'mg/dL', '70-110'),
('Creatinine', 'mg/dL', '0.6-1.3')
ON CONFLICT DO NOTHING;

-- جدول مراقبة الجودة
CREATE TABLE IF NOT EXISTS quality_control (
    id SERIAL PRIMARY KEY,
    test_id INTEGER REFERENCES lab_tests(id) ON DELETE CASCADE,
    qc_value FLOAT,
    qc_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول المختبرات
CREATE TABLE IF NOT EXISTS laboratories (
    id SERIAL PRIMARY KEY,
    lab_name TEXT NOT NULL,
    city TEXT,
    contact_phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- NATIONAL DIAGNOSTIC PLATFORM DATABASE
-- FINAL SCHEMA
-- =========================================

-- -----------------------------
-- LABORATORIES
-- -----------------------------
CREATE TABLE IF NOT EXISTS laboratories (
    id SERIAL PRIMARY KEY,
    lab_name TEXT NOT NULL,
    city TEXT,
    contact_phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------
-- USERS
-- -----------------------------
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT,
    lab_id INTEGER REFERENCES laboratories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------
-- PATIENTS
-- -----------------------------
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    lab_id INTEGER REFERENCES laboratories(id),
    first_name TEXT,
    last_name TEXT,
    gender TEXT,
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------
-- MEDICAL TESTS (ALL TYPES)
-- -----------------------------
CREATE TABLE IF NOT EXISTS medical_tests (
    id SERIAL PRIMARY KEY,
    test_name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------
-- TEST PARAMETERS
-- -----------------------------
CREATE TABLE IF NOT EXISTS test_parameters (
    id SERIAL PRIMARY KEY,
    test_id INTEGER REFERENCES medical_tests(id),
    parameter_name TEXT,
    unit TEXT
);

-- -----------------------------
-- REFERENCE RANGES
-- -----------------------------
CREATE TABLE IF NOT EXISTS reference_ranges (
    id SERIAL PRIMARY KEY,
    parameter_id INTEGER REFERENCES test_parameters(id),
    gender TEXT,
    age_min INTEGER,
    age_max INTEGER,
    normal_min FLOAT,
    normal_max FLOAT
);

-- -----------------------------
-- TEST ORDERS
-- -----------------------------
CREATE TABLE IF NOT EXISTS test_orders (
    id SERIAL PRIMARY KEY,
    lab_id INTEGER REFERENCES laboratories(id),
    patient_id INTEGER REFERENCES patients(id),
    test_id INTEGER REFERENCES medical_tests(id),
    ordered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------
-- TEST RESULTS
-- -----------------------------
CREATE TABLE IF NOT EXISTS test_results (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES test_orders(id),
    parameter_id INTEGER REFERENCES test_parameters(id),
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------
-- DIAGNOSTIC REPORTS
-- -----------------------------
CREATE TABLE IF NOT EXISTS diagnostic_reports (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    test_id INTEGER REFERENCES medical_tests(id),
    report_text TEXT,
    file_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------
-- QUALITY CONTROL
-- -----------------------------
CREATE TABLE IF NOT EXISTS quality_control (
    id SERIAL PRIMARY KEY,
    test_id INTEGER REFERENCES medical_tests(id),
    qc_value FLOAT,
    qc_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------
-- MEDICAL DEVICES
-- -----------------------------
CREATE TABLE IF NOT EXISTS medical_devices (
    id SERIAL PRIMARY KEY,
    device_name TEXT,
    manufacturer TEXT,
    protocol TEXT,
    ip_address TEXT,
    port INTEGER
);

-- =========================================
-- SAMPLE DATA
-- =========================================

INSERT INTO medical_tests (test_name,category) VALUES
('Complete Blood Count','Laboratory'),
('Liver Function Test','Laboratory'),
('Kidney Function Test','Laboratory'),
('X-Ray Chest','Radiology'),
('CT Scan Brain','Radiology'),
('MRI Spine','Radiology'),
('ECG','Cardiology'),
('Echocardiography','Cardiology'),
('PCR COVID','Molecular'),
('Blood Culture','Microbiology')
ON CONFLICT DO NOTHING;
