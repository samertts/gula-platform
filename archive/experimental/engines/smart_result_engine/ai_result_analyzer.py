import os
import sqlite3

LIB = os.path.expanduser("~/lab-platform/global_test_library/tests.db")


def analyze(test, value):

    conn = sqlite3.connect(LIB)
    c = conn.cursor()

    c.execute("SELECT normal_min,normal_max FROM tests WHERE name=?", (test,))
    row = c.fetchone()

    conn.close()

    if not row:
        return "Unknown test"

    low, high = row

    value = float(value)

    if value < low:
        return "LOW"

    if value > high:
        return "HIGH"

    return "NORMAL"
