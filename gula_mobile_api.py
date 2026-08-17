#!/usr/init/env python3
"""
GULA Mobile API Connector for Citizen Portal & PHR Access
------------------------------------------------------------------------
Description: Provides RESTful endpoints and secure handlers for mobile applications
(React Native / Expo) allowing citizens to authenticate via National ID, access PHR records,
and sync health insurance (Dhamani) data securely.
"""

import hashlib
import json
import logging
import sqlite3
import time
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] GULA-MOBILE-API: %(message)s'
)

DB_PATH = "/home/ubuntu/gula_citizens.db"

class GulaMobileAPI:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def mobile_login(self, national_id: str, password_hash: str) -> Dict[str, Any]:
        """Authenticates mobile app user and issues a secure session token."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, insurance_id FROM citizens WHERE national_id = ? AND password_hash = ?", (national_id, password_hash))
        user = cursor.fetchone()
        conn.close()

        if not user:
            logging.warning(f"Mobile authentication failed for National ID: {national_id}")
            return {"status": "UNAUTHORIZED", "message": "Invalid credentials."}

        token = hashlib.sha256(f"{national_id}-{time.time()}-GULA_MOBILE".encode()).hexdigest()
        logging.info(f"Mobile login successful for citizen: {user[0]}")
        return {
            "status": "SUCCESS",
            "token": token,
            "full_name": user[0],
            "insurance_id": user[1],
            "expires_in": 86400
        }

    def fetch_mobile_phr(self, national_id: str) -> Dict[str, Any]:
        """Fetches citizen medical records optimized for mobile view."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT record_id, hospital_name, diagnosis, prescription, lab_results, timestamp FROM medical_records WHERE national_id = ?", (national_id,))
        rows = cursor.fetchall()
        conn.close()

        records = [{
            "record_id": r[0],
            "hospital": r[1],
            "diagnosis": r[2],
            "prescription": r[3],
            "lab_results": r[4],
            "date": time.strftime('%Y-%m-%d %H:%M', time.localtime(r[5]))
        } for r in rows]

        return {
            "status": "SUCCESS",
            "records_count": len(records),
            "phr_records": records
        }

if __name__ == "__main__":
    api = GulaMobileAPI()
    # Test mobile login simulation
    pwd_hash = hashlib.sha256(("CitizenSecure2026!" + "GULA_CITIZEN_SALT_2026").encode()).hexdigest()
    login_res = api.mobile_login("199012345678", pwd_hash)
    print("Mobile Login Response:", json.dumps(login_res, ensure_ascii=False, indent=2))

    if login_res["status"] == "SUCCESS":
        phr_res = api.fetch_mobile_phr("199012345678")
        print("Mobile PHR Response:", json.dumps(phr_res, ensure_ascii=False, indent=2))
