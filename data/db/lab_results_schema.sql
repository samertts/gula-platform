CREATE TABLE IF NOT EXISTS device_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT,
    patient_id TEXT,
    test_code TEXT,
    result_value TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
