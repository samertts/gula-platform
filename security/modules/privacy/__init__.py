"""
GSF-009: Privacy Module — Data privacy enforcement.

Exports:
    PrivacyEnforcer: Privacy enforcement with data masking, anonymization, and consent management
"""

from security.modules.privacy.enforcer import PrivacyEnforcer

__all__ = [
    "PrivacyEnforcer",
]
