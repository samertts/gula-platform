CREATE TABLE IF NOT EXISTS lab_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_name TEXT NOT NULL,
    short_name TEXT,
    category TEXT,
    unit TEXT,
    ref_range TEXT
);

INSERT INTO lab_tests (test_name, short_name, category, unit, ref_range) VALUES
('Complete Blood Count', 'CBC', 'Hematology', '', ''),
('Hemoglobin', 'Hb', 'Hematology', 'g/dL', '13-17'),
('White Blood Cells', 'WBC', 'Hematology', 'cells/µL', '4000-11000'),
('Platelets', 'PLT', 'Hematology', 'cells/µL', '150000-450000'),

('Glucose', 'GLU', 'Chemistry', 'mg/dL', '70-110'),
('HbA1c', 'HbA1c', 'Diabetes', '%', '4-5.6'),

('Cholesterol Total', 'CHOL', 'Lipid', 'mg/dL', '<200'),
('HDL Cholesterol', 'HDL', 'Lipid', 'mg/dL', '>40'),
('LDL Cholesterol', 'LDL', 'Lipid', 'mg/dL', '<100'),

('Alanine Aminotransferase', 'ALT', 'Liver', 'U/L', '7-56'),
('Aspartate Aminotransferase', 'AST', 'Liver', 'U/L', '10-40'),
('Alkaline Phosphatase', 'ALP', 'Liver', 'U/L', '44-147'),

('Creatinine', 'CRE', 'Kidney', 'mg/dL', '0.7-1.3'),
('Blood Urea Nitrogen', 'BUN', 'Kidney', 'mg/dL', '7-20'),

('Thyroid Stimulating Hormone', 'TSH', 'Hormones', 'µIU/mL', '0.4-4.0'),
('Free T4', 'FT4', 'Hormones', 'ng/dL', '0.8-1.8'),

('Vitamin D', 'VitD', 'Vitamins', 'ng/mL', '20-50'),
('Vitamin B12', 'B12', 'Vitamins', 'pg/mL', '200-900'),

('Ferritin', 'FER', 'Iron', 'ng/mL', '24-336'),
('Iron', 'Fe', 'Iron', 'µg/dL', '60-170');

sqlite3 lab_database.db

.read global_test_library.sql

.read global_test_library.sql

SELECT * FROM lab_tests;
