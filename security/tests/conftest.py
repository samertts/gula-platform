from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from security.modules.audit.immutable import ImmutableAuditLog
from security.modules.audit.models import AuditEvent, AuditPolicy
from security.modules.audit.service import AuditService
from security.modules.compliance.asvs import ASVSValidator
from security.modules.compliance.engine import ComplianceEngine
from security.modules.compliance.mapper import ComplianceMapper
from security.modules.compliance.nist import NISTCSFValidator
from security.modules.crypto.aes import AES256CBCWithHMACCipher, AES256GCMCipher
from security.modules.crypto.argon import Argon2idHasher
from security.modules.crypto.field_encryption import FieldEncryptor
from security.modules.crypto.hashing import SHA256Hasher, SHA512Hasher
from security.modules.crypto.key_rotation import KeyRotationManager
from security.modules.crypto.phi_encryption import PHIEncryptor
from security.modules.crypto.random import SecureRandom
from security.modules.crypto.signing import ECDSA256Signer, Ed25519Signer, HMACSigner
from security.modules.headers.cors import StrictCORSManager
from security.modules.headers.csp import CSPBuilder
from security.modules.headers.csrf import CSRFProtector
from security.modules.headers.middleware import SecurityMiddlewareFactory
from security.modules.headers.models import (
    CORSConfig,
    CSPConfig,
    CSRFConfig,
    SanitizerConfig,
    SecurityHeadersConfig,
)
from security.modules.headers.sanitizer import InputSanitizer
from security.modules.headers.security_headers import SecurityHeadersManager
from security.modules.identity.abac import ABACEngine, ConditionOperator, Effect, Policy
from security.modules.identity.jwt import JWTManager
from security.modules.identity.mfa import MFAManager
from security.modules.identity.pkce import PKCEManager
from security.modules.identity.rbac import RBACEngine
from security.modules.identity.risk_engine import RiskEngine
from security.modules.identity.session import SessionManager
from security.modules.secrets.models import SecretConfig, SecretType, SecretValidationResult


@pytest.fixture
def aes_key() -> bytes:
    return AES256GCMCipher.generate_key()


@pytest.fixture
def aes_cbc_hmac_key() -> bytes:
    return AES256CBCWithHMACCipher.generate_key()


@pytest.fixture
def ed25519_key_pair() -> tuple[bytes, bytes]:
    return Ed25519Signer.generate_key_pair()


@pytest.fixture
def ecdsa_key_pair() -> tuple[bytes, bytes]:
    return ECDSA256Signer.generate_key_pair()


@pytest.fixture
def hmac_key() -> bytes:
    return HMACSigner.generate_key()


@pytest.fixture
def crypto_aes256_gcm() -> AES256GCMCipher:
    return AES256GCMCipher()


@pytest.fixture
def crypto_aes256_cbc_hmac() -> AES256CBCWithHMACCipher:
    return AES256CBCWithHMACCipher()


@pytest.fixture
def crypto_argon2id() -> Argon2idHasher:
    return Argon2idHasher()


@pytest.fixture
def crypto_sha256() -> SHA256Hasher:
    return SHA256Hasher()


@pytest.fixture
def crypto_sha512() -> SHA512Hasher:
    return SHA512Hasher()


@pytest.fixture
def crypto_ed25519_signer() -> Ed25519Signer:
    priv, _ = Ed25519Signer.generate_key_pair()
    return Ed25519Signer(private_key=priv)


@pytest.fixture
def crypto_ecdsa_signer() -> ECDSA256Signer:
    priv, _ = ECDSA256Signer.generate_key_pair()
    return ECDSA256Signer(private_key=priv)


@pytest.fixture
def crypto_hmac_signer() -> HMACSigner:
    return HMACSigner()


@pytest.fixture
def crypto_secure_random() -> type[SecureRandom]:
    return SecureRandom


@pytest.fixture
def field_encryptor() -> FieldEncryptor:
    master_key = AES256GCMCipher.generate_key()
    return FieldEncryptor(master_key=master_key)


@pytest.fixture
def phi_encryptor() -> PHIEncryptor:
    master_key = AES256GCMCipher.generate_key()
    return PHIEncryptor(master_key=master_key)


@pytest.fixture
def key_rotation_manager() -> KeyRotationManager:
    return KeyRotationManager()


@pytest.fixture
def rbac_engine() -> RBACEngine:
    return RBACEngine()


@pytest.fixture
def abac_engine() -> ABACEngine:
    return ABACEngine()


@pytest.fixture
def jwt_manager() -> JWTManager:
    return JWTManager()


@pytest.fixture
def mfa_manager() -> MFAManager:
    return MFAManager()


@pytest.fixture
def pkce_manager() -> PKCEManager:
    return PKCEManager()


@pytest.fixture
def risk_engine() -> RiskEngine:
    return RiskEngine()


@pytest.fixture
def session_manager() -> SessionManager:
    return SessionManager()


@pytest.fixture
def csp_builder() -> CSPBuilder:
    return CSPBuilder()


@pytest.fixture
def cors_manager() -> StrictCORSManager:
    return StrictCORSManager()


@pytest.fixture
def csrf_protector() -> CSRFProtector:
    return CSRFProtector()


@pytest.fixture
def input_sanitizer() -> InputSanitizer:
    return InputSanitizer()


@pytest.fixture
def security_headers_manager() -> SecurityHeadersManager:
    return SecurityHeadersManager()


@pytest.fixture
def audit_service() -> AuditService:
    return AuditService()


@pytest.fixture
def immutable_audit_log(tmp_path) -> ImmutableAuditLog:
    return ImmutableAuditLog(storage_path=str(tmp_path))


@pytest.fixture
def sample_audit_event() -> AuditEvent:
    return AuditEvent(
        event_id="evt-001",
        actor_id="user-001",
        action="user.login",
        resource_type="session",
        resource_id="sess-001",
        outcome="success",
    )


@pytest.fixture
def asvs_validator() -> ASVSValidator:
    return ASVSValidator()


@pytest.fixture
def compliance_engine() -> ComplianceEngine:
    return ComplianceEngine()


@pytest.fixture
def compliance_mapper() -> ComplianceMapper:
    return ComplianceMapper()
