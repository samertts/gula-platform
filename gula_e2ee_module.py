#!/usr/bin/env python3
"""
GULA - End-to-End Encryption (E2EE) Cryptography Module (Fixed & Persistent)
--------------------------------------------------------------------------------
Description: Implements persistent master key storage and AES-GCM encryption for 
medical data payloads exchanged between GULA edge gateways and national DHIS2 servers.
"""

import os
import json
import base64
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] GULA-E2EE: %(message)s'
)

KEY_STORAGE_PATH = "/home/ubuntu/gula_master.key"

class GulaE2EEEngine:
    def __init__(self, key_path: str = KEY_STORAGE_PATH):
        self.key_path = key_path
        self.master_key = self._load_or_generate_master_key()
        self.aesgcm = AESGCM(self.master_key)

    def _load_or_generate_master_key(self) -> bytes:
        """Loads existing master key or generates and securely saves a persistent one."""
        if os.path.exists(self.key_path):
            try:
                with open(self.key_path, "rb") as f:
                    encoded_key = f.read()
                    master_key = base64.b64decode(encoded_key)
                    if len(master_key) == 32:
                        logging.info("Loaded persistent master encryption key successfully.")
                        return master_key
            except Exception as e:
                logging.warning(f"Failed to load master key ({str.e}), generating new key.")

        # Generate new 256-bit key
        master_key = AESGCM.generate_key(bit_length=256)
        try:
            with open(self.key_path, "wb") as f:
                f.write(base64.b64encode(master_key))
            os.chmod(self.key_path, 0o600) # Restrict file permissions to owner only
            logging.info("Generated and securely stored new persistent master encryption key.")
        except Exception as e:
            logging.error(f"Critical: Could not persist master key: {str(e)}")
        
        return master_key

    def encrypt_payload(self, sensitive_data: dict) -> dict:
        """Encrypts clinical payload locally before transmission (E2EE)."""
        nonce = os.urandom(12) # 96-bit nonce for AES-GCM
        json_data = json.dumps(sensitive_data).encode('utf-8')
        
        ciphertext = self.aesgcm.encrypt(nonce, json_data, None)
        
        envelope = {
            "cipher": "AES-256-GCM",
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "status": "E2EE_SECURED"
        }
        logging.info("Clinical data successfully encrypted on edge device (Persistent E2EE applied).")
        return envelope

    def decrypt_payload(self, envelope: dict) -> dict:
        """Decrypts clinical payload at authorized destination."""
        if envelope.get("status") != "E2EE_SECURED":
            raise ValueError("Invalid encryption envelope status.")

        nonce = base64.b64decode(envelope["nonce"])
        ciphertext = base64.b64decode(envelope["ciphertext"])

        decrypted_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
        decrypted_data = json.loads(decrypted_bytes.decode('utf-8'))
        
        logging.info("Encrypted payload successfully decrypted at authorized endpoint.")
        return decrypted_data

if __name__ == "__main__":
    engine = GulaE2EEEngine()
    sample_record = {"patient_id": "IQ-PAT-2026-FIXED", "status": "Secure Persistent E2EE"}
    env = engine.encrypt_payload(sample_record)
    print("Encrypted:", env)
    print("Decrypted:", engine.decrypt_payload(env))
