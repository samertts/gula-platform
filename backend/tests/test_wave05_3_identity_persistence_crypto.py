"""Wave 05.3 identity persistence and cryptography tests.

Synthetic values only. No database DDL, migration, real key, real citizen data,
government call, OCR service, or NFC reader is used.
"""

from __future__ import annotations

from datetime import datetime
from itertools import cycle

import pytest
from app._compat import UTC
from app.national.exceptions import GulaCitizenIdentifierExhaustedError
from app.national.services.identity_crypto import (
    IdentityCryptoError,
    IdentityDataClassification,
    KeyRevokedError,
    KeyUnavailableError,
    SyntheticInMemoryKeyProvider,
    assert_no_key_material,
    classify_identity_field,
    decrypt_identity_value,
    encrypt_identity_value,
    verify_lookup_token,
)
from app.national.services.identity_persistence import (
    InMemoryIdempotencyStore,
    RegistrationCoordinatorError,
    RegistrationInProgressError,
    RegistrationRecord,
    RegistrationRequest,
    RegistrationState,
    assert_single_completed_registration,
    register_citizen_idempotently,
)

NOW = datetime(2026, 11, 25, 7, 2, 38, tzinfo=UTC)
SYNTHETIC_NID = "000000000001"
SYNTHETIC_SUBJECT = "SUBJECT-REF-0001"


def _request(key: str = "idem-1", subject: str = SYNTHETIC_SUBJECT) -> RegistrationRequest:
    return RegistrationRequest(
        idempotency_key=key,
        subject_reference=subject,
        birth_year=1990,
        requested_at=NOW,
    )


def test_classification_covers_all_required_classes() -> None:
    assert classify_identity_field("national_id") is IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA
    assert classify_identity_field("card_image") is IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA
    assert classify_identity_field("raw_nfc_data") is IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA
    assert classify_identity_field("diagnosis") is IdentityDataClassification.CLINICAL_SENSITIVE_DATA
    assert classify_identity_field("mother_name") is IdentityDataClassification.RESTRICTED_PERSONAL_DATA
    assert classify_identity_field("unknown_field") is IdentityDataClassification.INTERNAL


def test_encryption_round_trip_uses_versioned_key_and_masked_value() -> None:
    provider = SyntheticInMemoryKeyProvider()
    envelope = encrypt_identity_value(
        SYNTHETIC_NID,
        classification=IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA,
        provider=provider,
        actor="registration-officer",
        purpose="REGISTRATION",
        encrypted_at=NOW,
    )

    assert envelope.key_version == 1
    assert envelope.classification is IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA
    assert envelope.lookup_token.key_version == 1
    assert SYNTHETIC_NID not in repr(envelope)
    assert SYNTHETIC_NID not in envelope.masked_value
    assert verify_lookup_token(
        SYNTHETIC_NID,
        envelope.lookup_token,
        classification=IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA,
        provider=provider,
        actor="reviewer",
        purpose="REVIEW",
    )
    assert not verify_lookup_token(
        "000000000002",
        envelope.lookup_token,
        classification=IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA,
        provider=provider,
        actor="reviewer",
        purpose="REVIEW",
    )
    assert decrypt_identity_value(
        envelope,
        provider=provider,
        actor="reviewer",
        purpose="REVIEW",
    ) == SYNTHETIC_NID


def test_lookup_token_is_keyed_and_not_a_plain_hash() -> None:
    import hashlib

    provider = SyntheticInMemoryKeyProvider()
    envelope = encrypt_identity_value(
        SYNTHETIC_NID,
        classification=IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA,
        provider=provider,
        actor="actor",
        purpose="TEST",
    )
    digest = envelope.lookup_token.token.split(".", 1)[1]
    assert digest != hashlib.sha256(SYNTHETIC_NID.encode()).hexdigest()


def test_key_rotation_preserves_old_ciphertext_until_revocation() -> None:
    provider = SyntheticInMemoryKeyProvider()
    classification = IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA
    old = encrypt_identity_value(
        SYNTHETIC_NID,
        classification=classification,
        provider=provider,
        actor="actor",
        purpose="TEST",
    )
    rotated = provider.rotate(
        classification,
        actor="operator",
        approver="security-approver",
        reason="scheduled synthetic rotation",
        rotated_at=NOW,
    )
    new = encrypt_identity_value(
        SYNTHETIC_NID,
        classification=classification,
        provider=provider,
        actor="actor",
        purpose="TEST",
    )
    assert rotated.version == 2
    assert new.key_version == 2
    assert decrypt_identity_value(old, provider=provider, actor="actor", purpose="TEST") == SYNTHETIC_NID

    provider.revoke(
        classification,
        1,
        actor="operator",
        approver="security-approver",
        reason="synthetic retention window closed",
        revoked_at=NOW,
    )
    with pytest.raises(KeyRevokedError):
        decrypt_identity_value(old, provider=provider, actor="actor", purpose="TEST")


def test_key_lifecycle_requires_separation_of_duties_and_fail_closed_keys() -> None:
    provider = SyntheticInMemoryKeyProvider()
    classification = IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA
    with pytest.raises(IdentityCryptoError, match="separation of duties"):
        provider.rotate(
            classification,
            actor="same-actor",
            approver="same-actor",
            reason="synthetic",
            rotated_at=NOW,
        )
    provider.get_active_key(classification, actor="actor", purpose="TEST")
    with pytest.raises(IdentityCryptoError, match="rotate before revoking"):
        provider.revoke(
            classification,
            1,
            actor="operator",
            approver="approver",
            reason="synthetic",
            revoked_at=NOW,
        )
    with pytest.raises(KeyUnavailableError):
        provider.get_key(classification, 99, actor="actor", purpose="TEST")


def test_key_access_audit_records_do_not_contain_key_material() -> None:
    provider = SyntheticInMemoryKeyProvider()
    classification = IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA
    encrypt_identity_value(
        SYNTHETIC_NID,
        classification=classification,
        provider=provider,
        actor="registration-officer",
        purpose="REGISTRATION",
    )
    events = provider.audit_events()
    assert len(events) == 1
    assert events[0].actor == "registration-officer"
    assert events[0].purpose == "REGISTRATION"
    assert_no_key_material(repr(events), provider)


def test_idempotent_registration_replays_identifier_without_second_file() -> None:
    store = InMemoryIdempotencyStore()
    request = _request()
    first = register_citizen_idempotently(
        request,
        store=store,
        random_source=cycle([1]).__next__,
        now=NOW,
    )
    second = register_citizen_idempotently(
        request,
        store=store,
        random_source=cycle([999]).__next__,
        now=NOW,
    )

    assert first.state is RegistrationState.COMPLETED
    assert second == first
    assert first.reserved_identifier == "199000000001"
    assert len(store.records()) == 1
    assert assert_single_completed_registration(store.records(), SYNTHETIC_SUBJECT) == first


def test_concurrent_duplicate_request_is_not_permitted_to_create_a_second_file() -> None:
    store = InMemoryIdempotencyStore()
    request = _request()

    def duplicate_during_pending(_identifier: str) -> None:
        with pytest.raises(RegistrationInProgressError):
            register_citizen_idempotently(request, store=store, now=NOW)

    record = register_citizen_idempotently(
        request,
        store=store,
        random_source=cycle([1]).__next__,
        after_reservation=duplicate_during_pending,
        now=NOW,
    )
    assert record.state is RegistrationState.COMPLETED
    assert len(store.records()) == 1


def test_collision_retry_uses_next_reserved_candidate() -> None:
    store = InMemoryIdempotencyStore(collisions=frozenset({"199000000005"}))
    record = register_citizen_idempotently(
        _request(key="collision-1"),
        store=store,
        random_source=cycle([5, 6]).__next__,
        max_attempts=3,
        now=NOW,
    )
    assert record.reserved_identifier == "199000000006"


def test_exhausted_collisions_fail_closed_and_release_reservation() -> None:
    store = InMemoryIdempotencyStore(collisions=frozenset({"199000000007"}))
    with pytest.raises(GulaCitizenIdentifierExhaustedError):
        register_citizen_idempotently(
            _request(key="exhausted-1"),
            store=store,
            random_source=cycle([7]).__next__,
            max_attempts=2,
            now=NOW,
        )
    failed = store.records()[0]
    assert failed.state is RegistrationState.FAILED
    assert failed.failure_reason is not None

    retry = register_citizen_idempotently(
        _request(key="exhausted-2"),
        store=store,
        random_source=cycle([7, 8]).__next__,
        max_attempts=3,
        now=NOW,
    )
    assert retry.reserved_identifier == "199000000008"


def test_post_reservation_failure_releases_identifier_and_marks_request_failed() -> None:
    store = InMemoryIdempotencyStore()

    def boom(_identifier: str) -> None:
        raise RuntimeError("synthetic downstream failure")

    with pytest.raises(RuntimeError, match="synthetic downstream failure"):
        register_citizen_idempotently(
            _request(key="failure-1"),
            store=store,
            random_source=cycle([2]).__next__,
            after_reservation=boom,
            now=NOW,
        )
    assert store.records()[0].state is RegistrationState.FAILED

    retry = register_citizen_idempotently(
        _request(key="failure-2"),
        store=store,
        random_source=cycle([2, 3]).__next__,
        now=NOW,
    )
    assert retry.reserved_identifier == "199000000002"


def test_completed_registration_cannot_be_failed_or_changed() -> None:
    store = InMemoryIdempotencyStore()
    request = _request()
    record = register_citizen_idempotently(
        request,
        store=store,
        random_source=cycle([4]).__next__,
        now=NOW,
    )
    with pytest.raises(RegistrationCoordinatorError):
        store.fail(request.idempotency_key, "late failure", at=NOW)
    with pytest.raises(RegistrationCoordinatorError):
        store.complete(request.idempotency_key, "199000000099", at=NOW)
    assert record.reserved_identifier == "199000000004"


def test_subject_reference_cannot_be_a_raw_national_number() -> None:
    with pytest.raises(RegistrationCoordinatorError, match="raw national number"):
        _request(key="raw-ref", subject=SYNTHETIC_NID)


def test_assert_single_completed_registration_detects_duplicate_files() -> None:
    request_a = _request(key="a", subject=SYNTHETIC_SUBJECT)
    request_b = _request(key="b", subject=SYNTHETIC_SUBJECT)
    records = (
        RegistrationRecord(request_a, RegistrationState.COMPLETED, "199000000001"),
        RegistrationRecord(request_b, RegistrationState.COMPLETED, "199000000002"),
    )
    with pytest.raises(RegistrationCoordinatorError, match="found 2"):
        assert_single_completed_registration(records, SYNTHETIC_SUBJECT)
