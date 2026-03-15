import os
import sqlite3

DB = os.path.expanduser("~/lab-platform/global_test_library/tests.db")


def connect():
    return sqlite3.connect(DB)


def init_db():

    conn = connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS tests(
    id INTEGER PRIMARY KEY,
    name TEXT,
    code TEXT,
    category TEXT,
    unit TEXT,
    normal_min REAL,
    normal_max REAL
    )
    """)

    conn.commit()
    conn.close()
