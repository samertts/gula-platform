"""Wave 05.3 synthetic performance and latency simulations.

These tests measure only in-memory helper behavior. They do not establish
production SLOs, database throughput, government latency, OCR speed, or NFC
reader performance. All values are synthetic.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timedelta

from app._compat import UTC
from app.gateways.base import DataTrustLevel
from app.national.services.government_verification import (
    AdapterPolicy,
    AuthorityRegistry,
    AuthorityRegistryEntry,
    SyntheticGovernmentVerificationAdapter,
    VerificationRequest,
    VerificationStatus,
)
from app.national.services.identity_crypto import (
    IdentityDataClassification,
    SyntheticInMemoryKeyProvider,
    encrypt_identity_value,
    verify_lookup_token,
)
from app.national.services.identity_persistence import (
    InMemoryIdempotencyStore,
    RegistrationRequest,
    RegistrationState,
    register_citizen_idempotently,
)

NOW = datetime(2026, 11, 25, 7, 2, 38, tzinfo=UTC)
SYNTHETIC_NID = "000000000001"
SYNTHETIC_HASH = hashlib.sha256(SYNTHETIC_NID.encode()).hexdigest()


def test_bulk_registration_simulation_keeps_one_record_per_subject() -> None:
    store = InMemoryIdempotencyStore()
    count = 500
    started = time.perf_counter()

    for index in range(count):
        record = register_citizen_idempotently(
            RegistrationRequest(
                idempotency_key=f"perf-idem-{index:04d}",
                subject_reference=f"SUBJECT-REF-{index:04d}",
                birth_year=1990,
                requested_at=NOW,
            ),
            store=store,
            random_source=lambda index=index: index,
            max_attempts=1,
            now=NOW,
        )
        assert record.state is RegistrationState.COMPLETED
        assert record.reserved_identifier == f"1990{index:08d}"

    elapsed = time.perf_counter() - started
    identifiers = {record.reserved_identifier for record in store.records()}
    assert len(identifiers) == count
    assert len(store.records()) == count
    assert elapsed >= 0


def test_bulk_keyed_lookup_simulation_uses_constant_time_comparison() -> None:
    provider = SyntheticInMemoryKeyProvider()
    classification = IdentityDataClassification.HIGHLY_RESTRICTED_IDENTITY_DATA
    envelope = encrypt_identity_value(
        SYNTHETIC_NID,
        classification=classification,
        provider=provider,
        actor="actor",
        purpose="SIMULATION",
        encrypted_at=NOW,
    )
    count = 500
    started = time.perf_counter()

    for _ in range(count):
        assert verify_lookup_token(
            SYNTHETIC_NID,
            envelope.lookup_token,
            classification=classification,
            provider=provider,
            actor="actor",
            purpose="SIMULATION",
        )

    elapsed = time.perf_counter() - started
    assert envelope.lookup_token.token != SYNTHETIC_NID
    assert elapsed >= 0


def test_bulk_adapter_simulation_returns_only_synthetic_non_authoritative_results() -> None:
    authority_id = "SYNTHETIC-AUTHORITY-PERF"
    registry = AuthorityRegistry()
    registry.register(
        AuthorityRegistryEntry(
            authority_id=authority_id,
            organization="SYNTHETIC-ORGANIZATION",
            service_name="SYNTHETIC-VERIFICATION-SERVICE",
            trust_level=DataTrustLevel.NON_CRITICAL,
            valid_from=NOW - timedelta(days=1),
            valid_until=NOW + timedelta(days=1),
            approval_reference="SYNTHETIC-APPROVAL-PERF",
            public_key_reference="SYNTHETIC-PUBLIC-KEY-REF-PERF",
            synthetic=True,
        ),
    )
    adapter = SyntheticGovernmentVerificationAdapter(
        policy=AdapterPolicy(rate_limit_per_minute=1000),
        status=VerificationStatus.NOT_VERIFIED,
    )
    count = 100
    started = time.perf_counter()

    for index in range(count):
        response = adapter.verify(
            VerificationRequest(
                correlation_id=f"CORR-PERF-{index:04d}",
                idempotency_key=f"IDEM-PERF-{index:04d}",
                subject_reference=f"SUBJECT-REF-{index:04d}",
                national_id_hash=SYNTHETIC_HASH,
                lookup_token=f"v1.{index:064x}",
                purpose="SIMULATION",
                actor="actor",
                organization_id="ORG-SYNTHETIC",
                facility_id="FACILITY-SYNTHETIC",
                requested_at=NOW,
            ),
            authority_id=authority_id,
            registry=registry,
            at=NOW,
        )
        assert response.status is VerificationStatus.NOT_VERIFIED
        assert response.synthetic is True
        assert SYNTHETIC_NID not in repr(response.public())

    elapsed = time.perf_counter() - started
    assert elapsed >= 0
