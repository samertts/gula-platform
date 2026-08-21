#!/usr/bin/env python3
"""
GULA Citizen Portal & Patient Health Record (PHR) Module
------------------------------------------------------------------------
Description: Implements secure citizen accounts linked to the National ID (البطاقة الوطنية)
and Health Insurance ID (منصة ضماني)، allowing citizens to view their electronic health records,
lab results, prescriptions, and manage medical appointments securely.
"""

import hashlib
import json
import logging
import sqlite3
import time
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] GULA-CITIZEN-PORTAL: %(message)s'
)

CITIZEN_DB_PATH = "/home/ubuntu/gula_citizens.db"

class GulaCitizenPortal:
    def __init__(self, db_path: str = CITIZEN_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the secure citizen registry and PHR database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS citizens (
                national_id TEXT PRIMARY KEY,
                insurance_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_records (
                record_id TEXT PRIMARY KEY,
                national_id TEXT NOT NULL,
                hospital_name TEXT NOT NULL,
                diagnosis TEXT NOT NULL,
                prescription TEXT NOT NULL,
                lab_results TEXT NOT NULL,
                timestamp REAL,
                FOREIGN KEY (national_id) REFERENCES citizens (national_id)
            )
        ''')
        conn.commit()
        conn.close()
        logging.info("GULA Citizen Portal database initialized successfully.")

    def _hash_password(self, password: str) -> str:
        """Applies secure salted hashing to citizen passwords."""
        salt = "GULA_CITIZEN_SALT_2026"
        h = hashlib.sha256()
        h.update((password + salt).encode('utf-8'))
        return h.hexdigest()

    def register_citizen(self, national_id: str, insurance_id: str, full_name: str, phone_number: str, password: str) -> Dict[str, Any]:
        """Registers a citizen in the platform using National ID and Health Insurance ID (Dhamani integration)."""
        pwd_hash = self._hash_password(password)
        timestamp = time.time()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO citizens (national_id, insurance_id, full_name, phone_number, password_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (national_id, insurance_id, full_name, phone_number, pwd_hash, timestamp)
            )
            conn.commit()
            logging.info(f"Citizen '{full_name}' (National ID: {national_id}) registered successfully.")
            return {
                "status": "SUCCESS",
                "national_id": national_id,
                "insurance_id": insurance_id,
                "message": "Citizen account created successfully. Welcome to GULA & Dhamani Health Network."
            }
        except sqlite3.IntegrityError:
            logging.warning(f"Registration failed: National ID or Insurance ID already exists.")
            return {"status": "ERROR", "message": "National ID or Insurance ID is already registered."}
        finally:
            conn.close()

    def add_medical_record(self, national_id: str, hospital_name: str, diagnosis: str, prescription: str, lab_results: str) -> Dict[str, Any]:
        """Adds an electronic medical record (PHR) for a citizen."""
        record_id = f"REC-{int(time.time())}"
        timestamp = time.time()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO medical_records (record_id, national_id, hospital_name, diagnosis, prescription, lab_results, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (record_id, national_id, hospital_name, diagnosis, prescription, lab_results, timestamp)
        )
        conn.commit()
        conn.close()
        logging.info(f"Medical record '{record_id}' added for citizen '{national_id}'.")
        return {"status": "SUCCESS", "record_id": record_id, "message": "Medical record securely added."}

    def get_citizen_records(self, national_id: str, password: str) -> Dict[str, Any]:
        """Retrieves citizen medical records after verifying credentials."""
        pwd_hash = self._hash_password(password)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT full_name, insurance_id FROM citizens WHERE national_id = ? AND password_hash = ?", (national_id, pwd_hash))
        citizen = cursor.fetchone()

        if not citizen:
            conn.close()
            return {"status": "ERROR", "message": "Invalid National ID or password."}

        full_name, insurance_id = citizen

        cursor.execute("SELECT record_id, hospital_name, diagnosis, prescription, lab_results, timestamp FROM medical_records WHERE national_id = ?", (national_id,))
        rows = cursor.fetchall()
        conn.close()

        records = []
        for r in rows:
            records.append({
                "record_id": r[0],
                "hospital_name": r[1],
                "diagnosis": r[2],
                "prescription": r[3],
                "lab_results": r[4],
                "timestamp": r[5]
            })

        return {
            "status": "SUCCESS",
            "full_name": full_name,
            "national_id": national_id,
            "insurance_id": insurance_id,
            "medical_records": records
        }

if __name__ == "__main__":
    portal = GulaCitizenPortal()
    # Test citizen registration
    reg_res = portal.register_citizen(
        national_id="199012345678",
        insurance_id="DHAMANI-987654",
        full_name="Mohammed Al-Baghdadi",
        phone_number="07801234567",
        password="CitizenSecure2026!"
    )
    print("Registration:", reg_res)

    # Test adding medical record
    portal.add_medical_record(
        national_id="199012345678",
        hospital_name="مستشفى بغداد التعليمي",
        diagnosis="التهاب الحلق الحاد (Acute Pharyngitis)",
        prescription="Paracetamol 500mg, Amoxicillin 875mg",
        lab_results="WBC: 11,200 /uL (Slight Elevation)"
    )

    # Test fetching records
    fetch_res = portal.get_citizen_records(
        national_id="199012345678",
        password="CitizenSecure2026!"
    )
    print("Citizen Records Fetch:", json.dumps(fetch_res, ensure_ascii=False, indent=2))
