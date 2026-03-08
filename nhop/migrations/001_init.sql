-- =======================================================
-- NHOP Platform Database Migration 001
-- Full Schema: Auth, Lab Workflow, Patients
-- =======================================================

-- Users (authentication for all roles)
CREATE TABLE IF NOT EXISTS users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          VARCHAR(200) NOT NULL,
  email         VARCHAR(200) UNIQUE NOT NULL,
  phone         VARCHAR(20),
  national_id   VARCHAR(20) UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role          VARCHAR(30) NOT NULL CHECK (role IN ('admin','lab_staff','doctor','patient','citizen')),
  is_active     BOOLEAN DEFAULT TRUE,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Patients (full profile linked to user)
CREATE TABLE IF NOT EXISTS patients (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID REFERENCES users(id) ON DELETE SET NULL,
  name          VARCHAR(200) NOT NULL,
  name_en       VARCHAR(200),
  national_id   VARCHAR(20) UNIQUE,
  birth_date    DATE,
  gender        VARCHAR(10) CHECK (gender IN ('male','female')),
  phone         VARCHAR(20),
  address       TEXT,
  blood_type    VARCHAR(5),
  notes         TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Test Catalog (available lab tests)
CREATE TABLE IF NOT EXISTS test_catalog (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code                 VARCHAR(30) UNIQUE NOT NULL,
  name_ar              VARCHAR(200) NOT NULL,
  name_en              VARCHAR(200) NOT NULL,
  category             VARCHAR(100) NOT NULL,
  sample_type          VARCHAR(50) NOT NULL DEFAULT 'blood',
  unit                 VARCHAR(30),
  normal_range_min     DECIMAL(12,4),
  normal_range_max     DECIMAL(12,4),
  normal_range_text    VARCHAR(200),
  price                DECIMAL(10,2) DEFAULT 0,
  turnaround_hours     INTEGER DEFAULT 24,
  is_active            BOOLEAN DEFAULT TRUE,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Lab Orders (doctors request tests for patients)
CREATE TABLE IF NOT EXISTS lab_orders (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id    UUID NOT NULL REFERENCES patients(id),
  doctor_id     UUID REFERENCES users(id) ON DELETE SET NULL,
  status        VARCHAR(30) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','received','processing','completed','cancelled')),
  priority      VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('normal','urgent','stat')),
  clinical_notes TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Lab Order Items (which tests in each order)
CREATE TABLE IF NOT EXISTS lab_order_items (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id        UUID NOT NULL REFERENCES lab_orders(id) ON DELETE CASCADE,
  test_catalog_id UUID NOT NULL REFERENCES test_catalog(id),
  status          VARCHAR(30) DEFAULT 'pending'
                    CHECK (status IN ('pending','collected','processing','resulted','approved')),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Samples (physical sample tracking)
CREATE TABLE IF NOT EXISTS samples (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id        UUID NOT NULL REFERENCES lab_orders(id),
  patient_id      UUID NOT NULL REFERENCES patients(id),
  barcode         VARCHAR(50) UNIQUE,
  sample_type     VARCHAR(50) NOT NULL,
  status          VARCHAR(30) DEFAULT 'ordered'
                    CHECK (status IN ('ordered','collected','received','processing','completed','rejected')),
  collected_at    TIMESTAMPTZ,
  received_at     TIMESTAMPTZ,
  collector_id    UUID REFERENCES users(id) ON DELETE SET NULL,
  rejection_reason VARCHAR(255),
  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Test Results (final results for each test)
CREATE TABLE IF NOT EXISTS test_results (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sample_id       UUID REFERENCES samples(id),
  order_item_id   UUID REFERENCES lab_order_items(id),
  test_catalog_id UUID NOT NULL REFERENCES test_catalog(id),
  patient_id      UUID NOT NULL REFERENCES patients(id),
  value           VARCHAR(200),
  value_numeric   DECIMAL(12,4),
  unit            VARCHAR(30),
  status          VARCHAR(30) DEFAULT 'draft'
                    CHECK (status IN ('draft','resulted','approved','released')),
  is_abnormal     BOOLEAN DEFAULT FALSE,
  abnormal_flag   VARCHAR(10),
  tech_id         UUID REFERENCES users(id) ON DELETE SET NULL,
  approved_by     UUID REFERENCES users(id) ON DELETE SET NULL,
  approved_at     TIMESTAMPTZ,
  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Refresh tokens (for auth security)
CREATE TABLE IF NOT EXISTS refresh_tokens (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash  VARCHAR(255) NOT NULL,
  expires_at  TIMESTAMPTZ NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_patients_national_id ON patients(national_id);
CREATE INDEX IF NOT EXISTS idx_lab_orders_patient ON lab_orders(patient_id);
CREATE INDEX IF NOT EXISTS idx_lab_orders_status ON lab_orders(status);
CREATE INDEX IF NOT EXISTS idx_samples_order ON samples(order_id);
CREATE INDEX IF NOT EXISTS idx_samples_barcode ON samples(barcode);
CREATE INDEX IF NOT EXISTS idx_test_results_patient ON test_results(patient_id);
CREATE INDEX IF NOT EXISTS idx_test_results_sample ON test_results(sample_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Seed: test catalog (common tests)
INSERT INTO test_catalog (code, name_ar, name_en, category, sample_type, unit, normal_range_min, normal_range_max, price, turnaround_hours)
VALUES
  ('CBC',    'صورة دم كاملة',           'Complete Blood Count',        'hematology',   'blood', 'cells/µL', NULL,   NULL,   15.00, 4),
  ('HGB',    'هيموجلوبين',              'Hemoglobin',                   'hematology',   'blood', 'g/dL',    12.0,   17.5,   8.00,  2),
  ('WBC',    'كريات بيضاء',             'White Blood Cells',            'hematology',   'blood', '10³/µL',  4.5,    11.0,   8.00,  2),
  ('PLT',    'صفائح دموية',             'Platelets',                    'hematology',   'blood', '10³/µL',  150.0,  400.0,  8.00,  2),
  ('GLU',    'سكر صائم',               'Fasting Glucose',              'chemistry',    'blood', 'mg/dL',   70.0,   100.0,  10.00, 4),
  ('HBA1C',  'سكر تراكمي',             'Hemoglobin A1C',               'chemistry',    'blood', '%',       4.0,    5.6,    30.00, 24),
  ('CHOL',   'كولسترول كلي',            'Total Cholesterol',            'lipids',       'blood', 'mg/dL',   NULL,   200.0,  20.00, 24),
  ('LDL',    'كولسترول ضار',            'LDL Cholesterol',              'lipids',       'blood', 'mg/dL',   NULL,   100.0,  20.00, 24),
  ('HDL',    'كولسترول نافع',           'HDL Cholesterol',              'lipids',       'blood', 'mg/dL',   40.0,   NULL,   20.00, 24),
  ('TG',     'ثلاثيات الجليسريد',       'Triglycerides',                'lipids',       'blood', 'mg/dL',   NULL,   150.0,  20.00, 24),
  ('CREA',   'كرياتينين',              'Creatinine',                   'kidney',       'blood', 'mg/dL',   0.7,    1.3,    15.00, 8),
  ('BUN',    'يوريا',                  'Blood Urea Nitrogen',          'kidney',       'blood', 'mg/dL',   7.0,    20.0,   12.00, 8),
  ('ALT',    'إنزيم الكبد ALT',         'Alanine Aminotransferase',     'liver',        'blood', 'U/L',     7.0,    56.0,   15.00, 8),
  ('AST',    'إنزيم الكبد AST',         'Aspartate Aminotransferase',   'liver',        'blood', 'U/L',     10.0,   40.0,   15.00, 8),
  ('TSH',    'هرمون الغدة الدرقية',     'Thyroid Stimulating Hormone',  'endocrine',    'blood', 'mIU/L',   0.4,    4.0,    40.00, 48),
  ('T3',     'ثلاثي يودوثيرونين',       'Triiodothyronine',             'endocrine',    'blood', 'ng/dL',   80.0,   200.0,  35.00, 48),
  ('T4',     'ثيروكسين',               'Thyroxine',                    'endocrine',    'blood', 'µg/dL',   5.0,    12.0,   35.00, 48),
  ('UA',     'تحليل البول',             'Urinalysis',                   'urine',        'urine', NULL,      NULL,   NULL,   12.00, 4),
  ('URIC',   'حمض اليوريك',            'Uric Acid',                    'chemistry',    'blood', 'mg/dL',   3.5,    7.2,    15.00, 8),
  ('CRP',    'بروتين سي التفاعلي',      'C-Reactive Protein',           'inflammation', 'blood', 'mg/L',    NULL,   5.0,    25.00, 8),
  ('ESR',    'سرعة ترسب الكريات',       'Erythrocyte Sedimentation Rate','inflammation','blood', 'mm/hr',   NULL,   20.0,   12.00, 4),
  ('VITD',   'فيتامين د',              'Vitamin D (25-OH)',             'vitamins',     'blood', 'ng/mL',   30.0,   100.0,  50.00, 72),
  ('VITB12', 'فيتامين ب12',             'Vitamin B12',                  'vitamins',     'blood', 'pg/mL',   200.0,  900.0,  40.00, 72),
  ('FERR',   'فيريتين',               'Ferritin',                     'hematology',   'blood', 'ng/mL',   12.0,   300.0,  30.00, 24),
  ('IRON',   'حديد',                  'Serum Iron',                   'hematology',   'blood', 'µg/dL',   60.0,   170.0,  20.00, 8),
  ('COVID',  'كوفيد-19 PCR',           'COVID-19 PCR',                 'microbiology', 'nasal', NULL,      NULL,   NULL,  100.00, 24),
  ('CULT',   'مزرعة وتحسس',            'Culture & Sensitivity',        'microbiology', 'varies',NULL,      NULL,   NULL,   60.00, 72)
ON CONFLICT (code) DO NOTHING;
