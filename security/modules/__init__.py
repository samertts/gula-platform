"""GSF Module Registry.

This package contains all GSF security modules (GSF-001 through GSF-020).
Modules are organized by security domain and follow a consistent interface
pattern for composability.

Module Index:
    GSF-001  identity          Identity provider and user management
    GSF-002  secrets           Encrypted secret storage
    GSF-003  crypto            Cryptographic operations
    GSF-004  authentication    Authentication methods and MFA
    GSF-005  authorization     RBAC/ABAC policy engine
    GSF-006  audit             Immutable audit logging
    GSF-007  compliance        Compliance framework mapping
    GSF-008  headers           Zero-Trust HTTP security headers
    GSF-009  network           Network security and mTLS
    GSF-010  database          Database encryption and masking
    GSF-011  container         Container security
    GSF-012  kubernetes        Kubernetes security policies
    GSF-013  terraform         Infrastructure policy-as-code
    GSF-014  github            GitHub repository security
    GSF-015  ci                CI/CD pipeline security
    GSF-016  supply_chain      Supply chain security (import from supply_chain)
    GSF-017  fhir              FHIR R4 security enforcement
    GSF-018  privacy           Data privacy and consent
    GSF-019  threat_detection  Threat detection and monitoring (import from threat_detection)
    GSF-020  integrity         System integrity verification

Note:
    Modules with hyphens in directory names (supply-chain, threat-detection)
    cannot be imported directly by their filesystem name in Python. Use
    the underscore aliases:
        from security.modules.supply_chain import ...
        from security.modules.threat_detection import ...
"""

MODULE_REGISTRY = {
    "GSF-001": "identity",
    "GSF-002": "secrets",
    "GSF-003": "crypto",
    "GSF-004": "authentication",
    "GSF-005": "authorization",
    "GSF-006": "audit",
    "GSF-007": "compliance",
    "GSF-008": "headers",
    "GSF-009": "network",
    "GSF-010": "database",
    "GSF-011": "container",
    "GSF-012": "kubernetes",
    "GSF-013": "terraform",
    "GSF-014": "github",
    "GSF-015": "ci",
    "GSF-016": "supply-chain",
    "GSF-017": "fhir",
    "GSF-018": "privacy",
    "GSF-019": "threat-detection",
    "GSF-020": "integrity",
}

__all__ = [
    "MODULE_REGISTRY",
]
