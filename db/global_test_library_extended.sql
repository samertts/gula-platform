CREATE TABLE IF NOT EXISTS lab_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_name TEXT,
    short_name TEXT,
    category TEXT,
    unit TEXT,
    ref_range TEXT
);

CREATE TABLE IF NOT EXISTS test_panels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    panel_name TEXT
);

CREATE TABLE IF NOT EXISTS panel_tests (
    panel_id INTEGER,
    test_id INTEGER
);

INSERT INTO lab_tests (test_name, short_name, category, unit, ref_range) VALUES
('Hemoglobin', 'Hb', 'Hematology', 'g/dL', '13-17'),
('White Blood Cells', 'WBC', 'Hematology', 'cells/µL', '4000-11000'),
('Platelets', 'PLT', 'Hematology', 'cells/µL', '150000-450000'),
('Glucose', 'GLU', 'Chemistry', 'mg/dL', '70-110'),
('HbA1c', 'HbA1c', 'Diabetes', '%', '4-5.6'),
('Creatinine', 'CRE', 'Kidney', 'mg/dL', '0.7-1.3'),
('Blood Urea Nitrogen', 'BUN', 'Kidney', 'mg/dL', '7-20'),
('ALT', 'ALT', 'Liver', 'U/L', '7-56'),
('AST', 'AST', 'Liver', 'U/L', '10-40'),
('ALP', 'ALP', 'Liver', 'U/L', '44-147'),
('TSH', 'TSH', 'Hormone', 'µIU/mL', '0.4-4.0'),
('Vitamin D', 'VitD', 'Vitamins', 'ng/mL', '20-50');

INSERT INTO test_panels (panel_name) VALUES
('CBC Panel'),
('Liver Panel'),
('Kidney Panel');

INSERT INTO panel_tests VALUES
(1,1),
(1,2),
(1,3),
(2,8),
(2,9),
(2,10),
(3,6),
(3,7);
