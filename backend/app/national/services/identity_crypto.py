"""Wave 05.3 envelope-encryption boundary for national identity data.

This module is reversible, pure-Python and synthetic-data safe. It defines a
key-provider interface that a future approved KMS/HSM can implement and an
in-memory mock provider that generates ephemeral keys at runtime only. It does
not persist keys, add configuration secrets, change schema, or encrypt real
citizen data. The mock provider is never an approved production key store.

Canonical Fernet/HMAC helpers are reused; no parallel cryptographic primitive
is introduced.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from app._compat import UTC
from app.core.privacy import PIIMasker
from shared.security.encryption import decrypt_national_id as canonical_decrypt_national_id
from shared.security.encryption import encrypt_national_id as canonical_encrypt_national_id


class IdentityCryptoError(ValueError):
    """Base error for identity cryptographic-policy violations."""


class KeyUnavailableError(IdentityCryptoError):
    """Raised when a key version is missing or unavailable."""


class KeyRevokedError(IdentityCryptoError):
    """Raised when a revoked key version is requested."""


class KeyMaterialLeakError(IdentityCryptoError):
    """Raised when key material appears in text intended for logs or reports."""


class IdentityDataClassification(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED_PERSONAL_DATA = "RESTRICTED_PERSONAL_DATA"
    HIGHLY_RESTRICTED_IDENTITY_DATA = "HIGHLY_RESTRICTED_IDENTITY_DATA"
    CLINICAL_SENSITIVE_DATA = "CLINICAL_SENSITIVE_DATA"


HIGHLY_RESTRICTED_FIELDS = frozenset(
    {"national_id", "national_number", "card_image", "nfc_payload", "raw_nfc_data"},
)
CLINICAL_SENSITIVE_FIELDS = frozenset(
    {"diagnosis", "clinical_note", "laboratory_result", "prescription", "medical_record"},
)
RESTRICTED_PERSONAL_FIELDS = frozenset(
    {
        "full_name",
        "mother_name",
        "birth_date",
        "family_number",
        "birth_place",
        "card_issue_date",
        "card_expiry_date",
        "residence",
    },
)

_CLASSIFICATION_BY_FIELD: Mapping[str, IdentityDataClassification] = {
    **dict.fromkeys(HIGHLY_RESTRICTED_FIELDS, IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA),
    **dict.fromkeys(CLINICAL_SENSITIVE_FIELDS, IdentityDataClassification.CLINICAL_SENSITIVE_DATA),
    **dict.fromkeys(RESTRICTED_PERSONAL_FIELDS, IdentityDataClassification.RESTRICTED_PERSONAL_DATA),
}


def classify_identity_field(field_name: str) -> IdentityDataClassification:
    """Classify a field without reading or exposing its value."""
    return _CLASSIFICATION_BY_FIELD.get(
        field_name.strip().lower(),
        IdentityDataClassification.INTERNAL,
    )


class KeyAccessAction(StrEnum):
    ACCESS = "KEY_ACCESS"
    ROTATION = "KEY_ROTATION"
    REVOCATION = "KEY_REVOCATION"


@dataclass(frozen=True)
class KeyRecord:
    """A versioned key record. Material fields never appear in repr."""

    key_id: str
    version: int
    classification: IdentityDataClassification
    encryption_material: str = field(repr=False)
    hmac_material: str = field(repr=False)
    created_at: datetime
    revoked: bool = False
    revoked_at: datetime | None = None


@dataclass(frozen=True)
class KeyAccessAudit:
    action: KeyAccessAction
    key_id: str
    version: int
    classification: IdentityDataClassification
    actor: str
    purpose: str
    occurred_at: datetime
    reason: str | None = None


@dataclass(frozen=True)
class LookupToken:
    key_version: int
    token: str


@dataclass(frozen=True)
class EncryptedIdentityValue:
    classification: IdentityDataClassification
    key_id: str
    key_version: int
    ciphertext: str
    lookup_token: LookupToken
    masked_value: str
    encrypted_at: datetime


class KeyProvider(Protocol):
    """Future-approved KMS/HSM interface. No production implementation is added."""

    def get_active_key(
        self,
        classification: IdentityDataClassification,
        *,
        actor: str,
        purpose: str,
    ) -> KeyRecord: ...

    def get_key(
        self,
        classification: IdentityDataClassification,
        version: int,
        *,
        actor: str,
        purpose: str,
    ) -> KeyRecord: ...

    def rotate(
        self,
        classification: IdentityDataClassification,
        *,
        actor: str,
        approver: str,
        reason: str,
        rotated_at: datetime,
    ) -> KeyRecord: ...

    def revoke(
        self,
        classification: IdentityDataClassification,
        version: int,
        *,
        actor: str,
        approver: str,
        reason: str,
        revoked_at: datetime,
    ) -> None: ...

    def audit_events(self) -> tuple[KeyAccessAudit, ...]: ...


class SyntheticInMemoryKeyProvider:
    """Synthetic-only provider with ephemeral runtime keys.

    This is a test double. Keys are generated in memory, are never written to
    the database or repository, and are not a production KMS.
    """

    def __init__(self, *, key_id_prefix: str = "SYNTHETIC-KEY") -> None:
        self._key_id_prefix = key_id_prefix
        self._keys: dict[tuple[IdentityDataClassification, int], KeyRecord] = {}
        self._active: dict[IdentityDataClassification, int] = {}
        self._versions: dict[IdentityDataClassification, int] = {}
        self._audit: list[KeyAccessAudit] = []
        self._lock = threading.Lock()

    @staticmethod
    def _validate_context(actor: str, purpose: str) -> None:
        if not actor.strip() or not purpose.strip():
            raise IdentityCryptoError("key access requires actor and purpose")

    def _new_key(
        self,
        classification: IdentityDataClassification,
        version: int,
        *,
        created_at: datetime,
    ) -> KeyRecord:
        from cryptography.fernet import Fernet

        return KeyRecord(
            key_id=f"{self._key_id_prefix}-{classification.value}-{version}",
            version=version,
            classification=classification,
            encryption_material=Fernet.generate_key().decode("ascii"),
            hmac_material=secrets.token_hex(32),
            created_at=created_at,
        )

    def get_active_key(
        self,
        classification: IdentityDataClassification,
        *,
        actor: str,
        purpose: str,
    ) -> KeyRecord:
        self._validate_context(actor, purpose)
        with self._lock:
            version = self._active.get(classification)
            if version is None:
                version = 1
                self._versions[classification] = version
                self._keys[(classification, version)] = self._new_key(
                    classification,
                    version,
                    created_at=datetime.now(UTC),
                )
                self._active[classification] = version
            key = self._keys[(classification, version)]
            self._audit.append(
                KeyAccessAudit(
                    action=KeyAccessAction.ACCESS,
                    key_id=key.key_id,
                    version=key.version,
                    classification=classification,
                    actor=actor,
                    purpose=purpose,
                    occurred_at=datetime.now(UTC),
                ),
            )
            return key

    def get_key(
        self,
        classification: IdentityDataClassification,
        version: int,
        *,
        actor: str,
        purpose: str,
    ) -> KeyRecord:
        self._validate_context(actor, purpose)
        with self._lock:
            key = self._keys.get((classification, version))
            if key is None:
                raise KeyUnavailableError("requested key version is unavailable")
            if key.revoked:
                raise KeyRevokedError("requested key version is revoked")
            self._audit.append(
                KeyAccessAudit(
                    action=KeyAccessAction.ACCESS,
                    key_id=key.key_id,
                    version=key.version,
                    classification=classification,
                    actor=actor,
                    purpose=purpose,
                    occurred_at=datetime.now(UTC),
                ),
            )
            return key

    def rotate(
        self,
        classification: IdentityDataClassification,
        *,
        actor: str,
        approver: str,
        reason: str,
        rotated_at: datetime,
    ) -> KeyRecord:
        if not actor.strip() or not approver.strip() or not reason.strip():
            raise IdentityCryptoError("rotation requires actor, approver, and reason")
        if actor == approver:
            raise IdentityCryptoError("rotation requires separation of duties")
        with self._lock:
            current = self._active.get(classification, 0)
            version = current + 1
            key = self._new_key(classification, version, created_at=rotated_at)
            self._keys[(classification, version)] = key
            self._versions[classification] = version
            self._active[classification] = version
            self._audit.append(
                KeyAccessAudit(
                    action=KeyAccessAction.ROTATION,
                    key_id=key.key_id,
                    version=version,
                    classification=classification,
                    actor=actor,
                    purpose="KEY_ROTATION",
                    occurred_at=rotated_at,
                    reason=reason,
                ),
            )
            return key

    def revoke(
        self,
        classification: IdentityDataClassification,
        version: int,
        *,
        actor: str,
        approver: str,
        reason: str,
        revoked_at: datetime,
    ) -> None:
        if not actor.strip() or not approver.strip() or not reason.strip():
            raise IdentityCryptoError("revocation requires actor, approver, and reason")
        if actor == approver:
            raise IdentityCryptoError("revocation requires separation of duties")
        with self._lock:
            key = self._keys.get((classification, version))
            if key is None:
                raise KeyUnavailableError("requested key version is unavailable")
            if self._active.get(classification) == version:
                raise IdentityCryptoError("rotate before revoking the active key")
            if key.revoked:
                return
            revoked = KeyRecord(
                key_id=key.key_id,
                version=key.version,
                classification=key.classification,
                encryption_material=key.encryption_material,
                hmac_material=key.hmac_material,
                created_at=key.created_at,
                revoked=True,
                revoked_at=revoked_at,
            )
            self._keys[(classification, version)] = revoked
            self._audit.append(
                KeyAccessAudit(
                    action=KeyAccessAction.REVOCATION,
                    key_id=key.key_id,
                    version=version,
                    classification=classification,
                    actor=actor,
                    purpose="KEY_REVOCATION",
                    occurred_at=revoked_at,
                    reason=reason,
                ),
            )

    def audit_events(self) -> tuple[KeyAccessAudit, ...]:
        with self._lock:
            return tuple(self._audit)

    def key_materials(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(
                item
                for key in self._keys.values()
                for item in (key.encryption_material, key.hmac_material)
            )


def _require_value(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IdentityCryptoError(f"{label} is required")
    return value.strip()


def _lookup_digest(raw_value: str, key: KeyRecord) -> str:
    payload = b"gula-wave05-3-national-id-lookup|" + raw_value.strip().encode("utf-8")
    return hmac.new(key.hmac_material.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def encrypt_identity_value(
    raw_value: str,
    *,
    classification: IdentityDataClassification,
    provider: KeyProvider,
    actor: str,
    purpose: str,
    encrypted_at: datetime | None = None,
) -> EncryptedIdentityValue:
    """Encrypt a synthetic identity value using a versioned external key."""
    value = _require_value(raw_value, "identity value")
    key = provider.get_active_key(classification, actor=actor, purpose=purpose)
    ciphertext = canonical_encrypt_national_id(
        value,
        key.encryption_material,
        key.hmac_material,
    )
    lookup = LookupToken(key_version=key.version, token=f"v{key.version}.{_lookup_digest(value, key)}")
    return EncryptedIdentityValue(
        classification=classification,
        key_id=key.key_id,
        key_version=key.version,
        ciphertext=ciphertext,
        lookup_token=lookup,
        masked_value=PIIMasker.mask_string(value),
        encrypted_at=encrypted_at or datetime.now(UTC),
    )


def decrypt_identity_value(
    envelope: EncryptedIdentityValue,
    *,
    provider: KeyProvider,
    actor: str,
    purpose: str,
) -> str:
    """Decrypt using the exact key version recorded with the ciphertext."""
    key = provider.get_key(
        envelope.classification,
        envelope.key_version,
        actor=actor,
        purpose=purpose,
    )
    if key.key_id != envelope.key_id:
        raise IdentityCryptoError("key identifier does not match the ciphertext envelope")
    value = canonical_decrypt_national_id(
        envelope.ciphertext,
        key.encryption_material,
        key.hmac_material,
    )
    if value is None:
        raise IdentityCryptoError("ciphertext integrity check failed")
    return value


def verify_lookup_token(
    raw_value: str,
    token: LookupToken,
    *,
    classification: IdentityDataClassification,
    provider: KeyProvider,
    actor: str,
    purpose: str,
) -> bool:
    """Constant-time lookup-token verification with version support."""
    value = _require_value(raw_value, "identity value")
    key = provider.get_key(
        classification,
        token.key_version,
        actor=actor,
        purpose=purpose,
    )
    expected = f"v{token.key_version}.{_lookup_digest(value, key)}"
    return hmac.compare_digest(expected, token.token)


def assert_no_key_material(text: str, provider: SyntheticInMemoryKeyProvider) -> None:
    """Fail when mock key material appears in a log/report-facing string."""
    for material in provider.key_materials():
        if material and material in text:
            raise KeyMaterialLeakError("key material must not appear in logs or reports")
