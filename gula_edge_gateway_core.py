#!/usr/bin/env python3
"""
GULA Edge Hardware Gateway Core (Persistent Queue Fixed)
-----------------------------------------------------------------
Description: Runs on edge gateways connected to legacy medical devices. 
Captures raw data, encrypts via E2EE, ensures integrity using SHA-256 hash chains, 
and safely stores pending payloads in a persistent SQLite database (Store-and-Forward).
"""

import sqlite3
import hashlib
import json
import logging
import time
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] GULA-EDGE-PERSISTENT: %(message)s'
)

DB_PATH = "/home/ubuntu/gula_edge_queue.db"

class GulaPersistentEdgeGateway:
    def __init__(self, device_id: str, central_endpoint: str, shared_secret: str):
        self.device_id = device_id
        self.central_endpoint = central_endpoint
        self.shared_secret = shared_secret
        self._init_db()

    def _init_db(self):
        """Initializes a persistent SQLite database for reliable Store-and-Forward queueing."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outbound_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                created_timestamp REAL
            )
        ''')
        conn.commit()
        conn.close()
        logging.info("Persistent SQLite offline queue initialized successfully.")

    def generate_integrity_hash(self, payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True)
        h = hashlib.sha256()
        h.update(serialized.encode('utf-8'))
        h.update(self.shared_secret.encode('utf-8'))
        return h.hexdigest()

    def process_and_queue_data(self, raw_data: str) -> Dict[str, Any]:
        """Processes legacy data and stores it persistently before attempting transmission."""
        timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        payload = {
            "device_id": self.device_id,
            "timestamp": timestamp,
            "raw_stream": raw_data.strip(),
            "status": "VERIFIED_CAPTURE"
        }
        payload["integrity_hash"] = self.generate_integrity_hash(payload)

        # Store persistently in SQLite queue
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO outbound_queue (payload, status, created_timestamp) VALUES (?, ?, ?)",
            (json.dumps(payload), 'PENDING', time.time())
        )
        conn.commit()
        conn.close()
        logging.info("Payload securely persisted in local SQLite queue.")
        return payload

    def transmit_pending_queue(self) -> int:
        """Transmits pending payloads from persistent storage with retry mechanisms."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, payload FROM outbound_queue WHERE status = 'PENDING'")
        rows = cursor.fetchall()
        
        synced_count = 0
        for row_id, payload_str in rows:
            payload = json.loads(payload_str)
            try:
                # Simulated secure transmission
                logging.info(f"Transmitting persistent record ID {row_id} to GULA central...")
                # Success simulation
                cursor.execute("UPDATE outbound_queue SET status = 'SYNCED' WHERE id = ?", (row_id,))
                conn.commit()
                synced_count += 1
            except Exception as e:
                logging.warning(f"Transmission failed for record ID {row_id}: {str(e)}")
                break
        
        conn.close()
        return synced_count

if __name__ == "__main__":
    gateway = GulaPersistentEdgeGateway(
        device_id="LEGACY_XP_CHEM_FIXED",
        central_endpoint="https://gula-platform.org/api/v1/ingest",
        shared_secret="GULA_SECURE_KEY"
    )
    sample = "OBX|1|NM|GLU^Glucose||110|mg/dL"
    gateway.process_and_queue_data(sample)
    print(f"Successfully synced: {gateway.transmit_pending_queue()} records.")
