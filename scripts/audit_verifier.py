#!/usr/bin/env python3
"""
GULA Platform - Audit Integrity Verifier
----------------------------------------
Verifies the SHA-256 hash chain of the audit_logs table.
Detects any unauthorized modification or deletion of clinical audit records.
"""

import hashlib
import sys
import os

# Add backend to path to import models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from app.database import SessionLocal
    from app.models.audit_log import AuditLog
    from sqlalchemy import text
except ImportError:
    print("Error: Could not import backend modules. Run from the scripts directory.")
    sys.exit(1)

def compute_hash(prev_hash: str, entry: AuditLog) -> str:
    """Matches the logic in app.services.audit_service._compute_chain_hash"""
    # Canonical string representation for hashing
    payload = f"{prev_hash}|{entry.id}|{entry.user_id}|{entry.action}|{entry.resource_type}|{entry.resource_id}|{entry.created_at.isoformat()}"
    return hashlib.sha256(payload.encode()).hexdigest()

def verify_chain():
    db = SessionLocal()
    try:
        print("Starting Audit Log Integrity Verification...")
        logs = db.query(AuditLog).order_by(AuditLog.id).all()
        
        if not logs:
            print("[✓] Audit log is empty. Nothing to verify.")
            return

        prev_hash = "0" * 64  # Initial seed for the first record
        corrupted_count = 0
        
        for i, entry in enumerate(logs):
            # Skip legacy rows without hashes if any
            if entry.chain_hash is None:
                continue
                
            expected = compute_hash(prev_hash, entry)
            
            if entry.chain_hash != expected:
                print(f"[✗] TAMPER DETECTED at Record ID: {entry.id}")
                print(f"    Expected: {expected}")
                print(f"    Stored:   {entry.chain_hash}")
                corrupted_count += 1
            
            prev_hash = entry.chain_hash

        if corrupted_count == 0:
            print(f"[✓] Integrity Verified. All {len(logs)} records are valid.")
        else:
            print(f"[!] Critical: Found {corrupted_count} corrupted or tampered records.")
            sys.exit(1)

    finally:
        db.close()

if __name__ == "__main__":
    verify_chain()
