"""
GULA Secure Registration Portal & User Onboarding Module.

This standalone SQLite sample is not a production identity service. Production
identity, MFA, RBAC, audit, and tenant controls must use the governed backend.
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
    format="%(asctime)s [%(levelname)s] GULA-REGISTRATION: %(message)s",
)

REG_DB_PATH = os.getenv("GULA_REG_DB_PATH", "/home/ubuntu/gula_users.db")
_PBKDF2_ITERATIONS = 600_000


class GulaRegistrationPortal:
    """Local sample registration with versioned password hashing."""

    def __init__(self, db_path: str = REG_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        """Initialize the local sample user registry and audit ledger."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    department TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    details TEXT
                );
                """
            )
        logging.info("GULA registration sample database initialized.")

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

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify only the versioned PBKDF2 format; reject legacy SHA-256 hashes."""
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

    def register_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str,
        department: str,
    ) -> dict[str, Any]:
        """Register a user with explicit role allowlisting and audit evidence."""
        allowed_roles = {"PHYSICIAN", "NURSE", "TECHNICIAN", "ADMIN"}
        role = role.upper()
        if role not in allowed_roles:
            return {"status": "ERROR", "message": "Invalid role."}
        try:
            password_hash = self._hash_password(password)
        except ValueError as exc:
            return {"status": "ERROR", "message": str(exc)}

        user_id = f"GULA-USR-{secrets.token_hex(12)}"
        timestamp = time.time()
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO users
                        (user_id, username, password_hash, full_name, role,
                         department, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        username,
                        password_hash,
                        full_name,
                        role,
                        department.upper(),
                        "ACTIVE",
                        timestamp,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO audit_logs (user_id, action, timestamp, details)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, "USER_REGISTERED", timestamp, "role assignment recorded"),
                )
        except sqlite3.IntegrityError:
            logging.warning("Registration rejected because the username exists.")
            return {"status": "ERROR", "message": "Username already exists."}

        logging.info("User registration completed without logging credentials or PII.")
        return {
            "status": "SUCCESS",
            "user_id": user_id,
            "role": role,
            "department": department.upper(),
            "message": "Registration completed successfully.",
        }


if __name__ == "__main__":
    raise SystemExit(
        "This standalone sample has no default demo credentials. "
        "Use synthetic fixtures explicitly through a test harness."
    )
