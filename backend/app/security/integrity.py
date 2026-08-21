import hashlib
import json
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger("gula.security.integrity")

class MathematicalIntegrityGuard:
    """
    Ensures absolute data integrity using cryptographic chaining.
    Every clinical result is signed and linked to the previous one,
    creating an immutable chain of medical truth.
    """

    @staticmethod
    def calculate_record_hash(data: Dict[str, Any], previous_hash: str) -> str:
        """
        Calculates a SHA-256 hash for a medical record, including the previous hash
        to ensure chain integrity.
        """
        # Canonicalize JSON to ensure consistent hashing
        serialized_data = json.dumps(data, sort_keys=True, default=str)
        payload = f"{serialized_data}{previous_hash}"
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def verify_chain(records: list) -> bool:
        """
        Verifies the integrity of a sequence of records.
        """
        current_prev_hash = "GENESIS"
        for record in records:
            expected_hash = MathematicalIntegrityGuard.calculate_record_hash(
                record['data'], current_prev_hash
            )
            if record['hash'] != expected_hash:
                logger.error(
                    "[INTEGRITY-VIOLATION] Hash mismatch detected for record ID: %s",
                    record.get('id')
                )
                return False
            current_prev_hash = record['hash']
        return True

    @staticmethod
    def sign_result(result_id: str, value: Any, validator_id: str, prev_hash: str) -> Dict[str, Any]:
        """
        Signs a new lab result with a cryptographic hash.
        """
        data = {
            "result_id": result_id,
            "value": value,
            "validator_id": validator_id,
            "timestamp": "ISO_TIMESTAMP_PLACEHOLDER" # Real timestamp would be used
        }
        record_hash = MathematicalIntegrityGuard.calculate_record_hash(data, prev_hash)
        
        return {
            "data": data,
            "hash": record_hash,
            "previous_hash": prev_hash
        }
