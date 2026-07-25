GSF Test Suite — Comprehensive test suite for the GULA Security Framework.

Tests are organized by module and cover all security-critical functionality:
- GSF-001/002: Secrets management (validation, rotation, scanning)
- GSF-002/003: Identity & authentication (RBAC, ABAC, JWT, MFA, passkeys)
- GSF-003: Cryptography (encryption, hashing, signing, key management)
- GSF-004/008: HTTP security headers (CSP, HSTS, CORS)
- GSF-006: Audit logging (immutable log chain, tamper detection)
"""

from pathlib import Path

TEST_DIR = Path(__file__).parent
FIXTURES_DIR = TEST_DIR / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)

__all__ = [
    "TEST_DIR",
    "FIXTURES_DIR",
]
