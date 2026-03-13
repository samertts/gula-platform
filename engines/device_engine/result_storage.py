import sqlite3
from datetime import datetime

from test_library.test_search import find_test

DB_PATH = "../db/lab_database.db"


def save_results(device, patient_id, parsed_results):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for r in parsed_results:
        cursor.execute(
            """
            INSERT INTO device_results
            (device_name, patient_id, test_code, result_value)
            VALUES (?, ?, ?, ?)
        """,
            (device, patient_id, r["test_code"], r["value"]),
        )

    conn.commit()
    conn.close()
