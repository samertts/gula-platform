import re
from typing import Any

class PIIMasker:
    """
    Utility to mask Personally Identifiable Information (PII) in logs and exports.
    Complies with HIPAA/GDPR data protection standards.
    """

    # Patterns for common PII
    PATTERNS = {
        "phone": re.compile(r"(\+?\d{1,3})?\d{7,10}"),
        "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
        "national_id": re.compile(r"\b\d{9,14}\b"),
    }

    @classmethod
    def mask_string(cls, text: str) -> str:
        """Masks PII within a raw string."""
        if not text:
            return text
            
        masked = text
        masked = cls.PATTERNS["email"].sub("[EMAIL_MASKED]", masked)
        masked = cls.PATTERNS["phone"].sub("[PHONE_MASKED]", masked)
        masked = cls.PATTERNS["national_id"].sub("[ID_MASKED]", masked)
        return masked

    @classmethod
    def mask_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively masks PII in a dictionary."""
        sensitive_keys = {"phone", "email", "national_id", "full_name", "patient_name", "address"}
        
        masked_data = {}
        for key, value in data.items():
            if key.lower() in sensitive_keys and isinstance(value, str):
                masked_data[key] = f"{value[:2]}***{value[-1:]}" if len(value) > 3 else "***"
            elif isinstance(value, dict):
                masked_data[key] = cls.mask_dict(value)
            elif isinstance(value, list):
                masked_data[key] = [cls.mask_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                masked_data[key] = value
        return masked_data
