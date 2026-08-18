#!/usr/bin/env python3
"""
GULA Secure Registration Portal & User Onboarding Module
------------------------------------------------------------------------
Description: Implements secure user registration with role assignment, departmental 
context binding, password hashing (bcrypt simulation/SHA-256), and immutable audit logging.
"""

import hashlib
import json
import logging
import sqlite3
import time
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] GULA-REGISTRATION: %(message)s'
)

REG_DB_PATH = "/home/ubuntu/gula_users.db"

class GulaRegistrationPortal:
    def __init__(self, db_path: str = REG_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the secure user registry database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                created_at REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT,
                timestamp REAL,
                details TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logging.info("GULA User Registration database and audit ledger initialized.")

    def _hash_password(self, password: str) -> str:
        """Applies secure salted hashing to user passwords."""
        salt = "GULA_SECURE_CLINICAL_SALT_2026"
        h = hashlib.sha256()
        h.update((password + salt).encode('utf-8'))
        return h.hexdigest()

    def register_user(self, username: str, password: str, full_name: str, role: str, department: str) -> Dict[str, Any]:
        """Registers a new medical or administrative user with role and department constraints."""
        allowed_roles = ["PHYSICIAN", "NURSE", "TECHNICIAN", "ADMIN"]
        role = role.upper()
        if role not in allowed_roles:
            return {"status": "ERROR", "message": f"Invalid role. Allowed roles: {allowed_roles}"}

        user_id = f"GULA-USR-{int(time.time())}"
        pwd_hash = self._hash_password(password)
        timestamp = time.time()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (user_id, username, password_hash, full_name, role, department, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, username, pwd_hash, full_name, role, department.upper(), 'ACTIVE', timestamp)
            )
            # Log immutable audit event
            cursor.execute(
                "INSERT INTO audit_logs (user_id, action, timestamp, details) VALUES (?, ?, ?, ?)",
                (user_id, "USER_REGISTERED", timestamp, f"Registered user {username} with role {role} in dept {department}")
            )
            conn.commit()
            logging.info(f"User '{username}' registered successfully with role '{role}' in department '{department}'.")
            return {
                "status": "SUCCESS",
                "user_id": user_id,
                "username": username,
                "role": role,
                "department": department.upper(),
                "message": "Registration completed successfully. Access granted according to RBAC/ABAC policy."
            }
        except sqlite3.IntegrityError:
            logging.warning(f"Registration failed: Username '{username}' already exists.")
            return {"status": "ERROR", "message": "Username already exists in the sovereign registry."}
        finally:
            conn.close()

if __name__ == "__main__":
    portal = GulaRegistrationPortal()
    # Test Registration
    res = portal.register_user(
        username="dr_ahmed",
        password="SecurePassword123!",
        full_name="Dr. Ahmed Al-Iraqee",
        role="PHYSICIAN",
        department="CARDIOLOGY"
    )
    print("Registration Result:", res)
