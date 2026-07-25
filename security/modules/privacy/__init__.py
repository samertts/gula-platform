GSF-018: Privacy Module — Data privacy and consent.

Provides data privacy controls for the GULA platform including data
classification, anonymization, pseudonymization, consent management,
and privacy policy enforcement. Protects Personally Identifiable
Information (PII) and Protected Health Information (PHI) in
compliance with Iraqi, HIPAA, and GDPR privacy requirements.

Exports:
    PrivacyEngine: Privacy control orchestration
    DataClassifier: Automated data classification (PII/PHI detection)
    Anonymizer: Data anonymization (k-anonymity, l-diversity)
    Pseudonymizer: Data pseudonymization with cryptographic tokens
    ConsentManager: Patient consent lifecycle management
    PrivacyPolicyEnforcer: Privacy policy evaluation and enforcement
    DpaManager: Data Processing Agreement management
"""

from security.modules.privacy.engine import PrivacyEngine
from security.modules.privacy.classifier import DataClassifier
from security.modules.privacy.anonymizer import Anonymizer
from security.modules.privacy.pseudonymizer import Pseudonymizer
from security.modules.privacy.consent import ConsentManager
from security.modules.privacy.enforcer import PrivacyPolicyEnforcer
from security.modules.privacy.dpa import DpaManager

__all__ = [
    "PrivacyEngine",
    "DataClassifier",
    "Anonymizer",
    "Pseudonymizer",
    "ConsentManager",
    "PrivacyPolicyEnforcer",
    "DpaManager",
]
