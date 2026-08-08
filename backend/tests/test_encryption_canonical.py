"""Regression tests — Wave 5 encryption module surgery (PROGRAM-01 final closure).

Orders 20–21 (ADR-028 evidence-based migration):
  #2  national/ecosystem/transformation/engine.py::EncryptionEngine AES-256 branch
      now delegates the Fernet round-trip to canonical shared/security/encryption.py
      (key derivation SHA-256 preserved → tokens byte-identical).
  #1  document_intelligence/security.py::EncryptionService now delegates the Fernet
      round-trip to canonical shared/security/encryption.py encrypt_bytes/decrypt_bytes.

Behavior preserved: same plaintext/key → same ciphertext as the pre-migration
implementation (Fernet + SHA-256 derivation), full round-trip, cross-compatibility
with the canonical provider.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.security.encryption import decrypt_value, encrypt_value

# ═══════════════════════════════════════════════════════════════════
# #2 national/ecosystem/transformation/engine.py::EncryptionEngine
# ═══════════════════════════════════════════════════════════════════


class TestEncryptionEngineCanonical:
    def test_encrypt_round_trip(self) -> None:
        from app.national.ecosystem.transformation.engine import EncryptionEngine

        secret = "sensitive transformation payload"
        cipher = EncryptionEngine.encrypt(secret, "integration-secret")
        assert cipher != secret
        assert EncryptionEngine.decrypt(cipher, "integration-secret") == secret

    def test_wrong_key_rejected(self) -> None:
        from app.national.ecosystem.transformation.engine import EncryptionEngine

        secret = "payload"
        cipher = EncryptionEngine.encrypt(secret, "key-a")
        with pytest.raises(ValueError):
            EncryptionEngine.decrypt(cipher, "key-b")

    def test_token_identical_to_canonical(self) -> None:
        """SHA-256 derivation is preserved → same key as canonical → cross-decrypt works."""
        import base64
        import hashlib

        from app.national.ecosystem.transformation.engine import EncryptionEngine

        secret = "compat-payload"
        key = "shared-secret"
        derived_key = base64.urlsafe_b64encode(
            hashlib.sha256(key.encode()).digest(),
        )
        engine_token = EncryptionEngine.encrypt(secret, key)
        canonical_token = encrypt_value(secret, derived_key)
        assert engine_token != secret
        assert canonical_token != secret
        assert decrypt_value(engine_token, derived_key) == secret
        assert EncryptionEngine.decrypt(canonical_token, key) == secret

    def test_rsa_branch_unchanged(self) -> None:
        from app.national.ecosystem.transformation.engine import EncryptionEngine

        secret = "rsa-payload"
        with pytest.raises(ValueError):
            EncryptionEngine.encrypt(secret, "not-a-pem-key", algorithm="RSA")

    def test_unsupported_algorithm(self) -> None:
        from app.national.ecosystem.transformation.engine import EncryptionEngine

        with pytest.raises(ValueError):
            EncryptionEngine.encrypt("x", "y", algorithm="NOPE")


# ═══════════════════════════════════════════════════════════════════
# #1 document_intelligence/security.py::EncryptionService
# ═══════════════════════════════════════════════════════════════════


class TestDocumentIntelligenceEncryptionService:
    def test_encrypt_decrypt_round_trip(self) -> None:
        from app.document_intelligence.security import EncryptionService

        svc = EncryptionService(key=b"0123456789abcdef0123456789abcdef")
        data = b"sensitive patient data"
        encrypted = svc.encrypt(data)
        assert encrypted != data
        assert svc.decrypt(encrypted) == data

    def test_token_identical_to_canonical(self) -> None:
        """Same key as canonical → cross-decrypt compatibility (Fernet is randomized)."""
        import base64

        from app.document_intelligence.security import EncryptionService

        from shared.security.encryption import decrypt_bytes, encrypt_bytes

        svc = EncryptionService(key=b"0123456789abcdef0123456789abcdef")
        data = b"compat-doc-intel"
        canonical_key = base64.urlsafe_b64encode(b"0123456789abcdef0123456789abcdef")
        assert decrypt_bytes(svc.encrypt(data), canonical_key) == data
        assert svc.decrypt(encrypt_bytes(data, canonical_key)) == data

    def test_no_fernet_signal_in_module(self) -> None:
        """The module must no longer construct Fernet directly (canonical ownership)."""
        repo_root = Path(__file__).resolve().parents[2]
        module = repo_root / "backend/app/document_intelligence/security.py"
        assert module.exists()
        assert "Fernet(" not in module.read_text(encoding="utf-8")
        assert "cryptography.fernet" not in module.read_text(encoding="utf-8")

    def test_no_fernet_signal_in_engine_module(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        module = repo_root / "backend/app/national/ecosystem/transformation/engine.py"
        assert module.exists()
        assert "Fernet(" not in module.read_text(encoding="utf-8")
