"""
GULA Citizen Portal & Patient Health Record (PHR) Module.

This standalone SQLite sample is not a production clinical service. Production
traffic must use the governed backend, encrypted storage, tenant controls, and
approved audit pipeline.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import secrets
import sqlite3
import time
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] GULA-CITIZEN-PORTAL: %(message)s",
)

CITIZEN_DB_PATH = os.getenv("GULA_CITIZEN_DB_PATH", "/home/ubuntu/gula_citizens.db")
_PBKDF2_ITERATIONS = 600_000


class GulaCitizenPortal:
    """Small local sample with authenticated access to synthetic records only."""

    def __init__(self, db_path: str = CITIZEN_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        """Initialize the local sample registry."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS citizens (
                    national_id TEXT PRIMARY KEY,
                    insurance_id TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS medical_records (
                    record_id TEXT PRIMARY KEY,
                    national_id TEXT NOT NULL,
                    hospital_name TEXT NOT NULL,
                    diagnosis TEXT NOT NULL,
                    prescription TEXT NOT NULL,
                    lab_results TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (national_id) REFERENCES citizens (national_id)
                );
                """
            )
        logging.info("GULA Citizen Portal sample database initialized.")

    def _hash_password(self, password: str) -> str:
        """Hash a password with a per-record random salt and PBKDF2."""
        if not password or len(password) < 12:
            raise ValueError("Password must contain at least 12 characters")
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            _PBKDF2_ITERATIONS,
        )
        return "pbkdf2_sha256${}${}${}".format(
            _PBKDF2_ITERATIONS,
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        )

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify only the versioned PBKDF2 format; legacy SHA-256 is rejected."""
        try:
            scheme, iterations, salt_text, digest_text = stored_hash.split("$", 3)
            if scheme != "pbkdf2_sha256":
                return False
            salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
            expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                int(iterations),
            )
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False

    def _authenticate(self, national_id: str, password: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT password_hash FROM citizens WHERE national_id = ?",
                (national_id,),
            ).fetchone()
        return bool(row and self._verify_password(password, row[0]))

    def register_citizen(
        self,
        national_id: str,
        insurance_id: str,
        full_name: str,
        phone_number: str,
        password: str,
    ) -> dict[str, Any]:
        """Register a synthetic citizen without logging the password or PII."""
        try:
            password_hash = self._hash_password(password)
        except ValueError as exc:
            return {"status": "ERROR", "message": str(exc)}

        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO citizens
                        (national_id, insurance_id, full_name, phone_number,
                         password_hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        national_id,
                        insurance_id,
                        full_name,
                        phone_number,
                        password_hash,
                        time.time(),
                    ),
                )
        except sqlite3.IntegrityError:
            logging.warning("Citizen registration rejected because an identifier exists.")
            return {"status": "ERROR", "message": "Citizen identifier is already registered."}

        logging.info("Citizen registration completed without logging identifiers.")
        return {
            "status": "SUCCESS",
            "message": "Citizen account created successfully.",
        }

    def add_medical_record(
        self,
        national_id: str,
        password: str,
        hospital_name: str,
        diagnosis: str,
        prescription: str,
        lab_results: str,
    ) -> dict[str, Any]:
        """Add a record only after authenticating the citizen."""
        if not self._authenticate(national_id, password):
            return {"status": "ERROR", "message": "Authentication failed."}

        record_id = f"REC-{secrets.token_hex(12)}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO medical_records
                    (record_id, national_id, hospital_name, diagnosis,
                     prescription, lab_results, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    national_id,
                    hospital_name,
                    diagnosis,
                    prescription,
                    lab_results,
                    time.time(),
                ),
            )
        logging.info("Medical record created after authenticated access.")
        return {"status": "SUCCESS", "record_id": record_id}

    def get_citizen_records(self, national_id: str, password: str) -> dict[str, Any]:
        """Retrieve records only after verifying the citizen credentials."""
        with self._connect() as conn:
            citizen = conn.execute(
                """
                SELECT full_name, insurance_id, password_hash
                FROM citizens
                WHERE national_id = ?
                """,
                (national_id,),
            ).fetchone()
            if not citizen or not self._verify_password(password, citizen[2]):
                return {"status": "ERROR", "message": "Authentication failed."}

            rows = conn.execute(
                """
                SELECT record_id, hospital_name, diagnosis, prescription,
                       lab_results, timestamp
                FROM medical_records
                WHERE national_id = ?
                ORDER BY timestamp DESC
                """,
                (national_id,),
            ).fetchall()

        return {
            "status": "SUCCESS",
            "full_name": citizen[0],
            "national_id": national_id,
            "insurance_id": citizen[1],
            "medical_records": [
                {
                    "record_id": row[0],
                    "hospital_name": row[1],
                    "diagnosis": row[2],
                    "prescription": row[3],
                    "lab_results": row[4],
                    "timestamp": row[5],
                }
                for row in rows
            ],
        }


if __name__ == "__main__":
    raise SystemExit(
        "This standalone sample has no default demo credentials. "
        "Use synthetic fixtures explicitly through a test harness."
    )
