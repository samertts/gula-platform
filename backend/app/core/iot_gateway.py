import hashlib
import hmac
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("gula.iot_gateway")

class MedicalIoTGateway:
    """
    Secure gateway for medical devices (Analyzers, Monitors).
    Enforces Zero-Trust principles for data ingestion.
    """

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.registered_devices = {} # device_id -> public_key/metadata

    def register_device(self, device_id: str, metadata: Dict):
        """Registers a new medical device with the gateway."""
        self.registered_devices[device_id] = metadata
        logger.info(f"[IOT-GATEWAY] Registered new device: {device_id}")

    def ingest_data(self, device_id: str, payload: Dict[str, Any], signature: str) -> bool:
        """
        Ingests and verifies data from a medical device.
        Ensures the data is authentic and hasn't been tampered with.
        """
        if device_id not in self.registered_devices:
            logger.error(f"[IOT-GATEWAY] Unregistered device attempt: {device_id}")
            return False

        # Verify Signature (HMAC-SHA256)
        expected_signature = self._generate_signature(payload)
        if not hmac.compare_digest(expected_signature, signature):
            logger.critical(f"[IOT-GATEWAY] DATA TAMPERING DETECTED from device: {device_id}")
            return False

        # Check for Replay Attacks (Timestamp check)
        timestamp = payload.get("timestamp", 0)
        if time.time() - timestamp > 300: # 5 minutes window
            logger.error(f"[IOT-GATEWAY] Replay attack or clock skew detected: {device_id}")
            return False

        logger.info(f"[IOT-GATEWAY] Data successfully verified and ingested from {device_id}")
        return True

    def _generate_signature(self, payload: Dict) -> str:
        """Generates a signature for the given payload."""
        message = str(payload).encode('utf-8')
        return hmac.new(self.secret_key.encode('utf-8'), message, hashlib.sha256).hexdigest()

class ClinicalDataIntegrity:
    """
    Ensures that once clinical data is ingested, it is immutable.
    Creates a 'Clinical Hash Chain'.
    """
    @staticmethod
    def seal_result(result_id: str, data: Dict) -> str:
        """Creates a cryptographic seal for a clinical result."""
        content = f"{result_id}:{str(data)}"
        seal = hashlib.sha256(content.encode('utf-8')).hexdigest()
        logger.info(f"[INTEGRITY] Result {result_id} sealed with hash: {seal}")
        return seal
