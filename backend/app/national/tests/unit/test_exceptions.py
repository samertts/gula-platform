from __future__ import annotations

from app.national.exceptions import (
    CitizenNotFoundError,
    ConsentNotGrantedError,
    DuplicateHealthNumberError,
    ForeignerRegistrationError,
    IdentityMergeError,
    InvalidStateTransitionError,
    NationalDomainError,
    NewbornRegistrationError,
    OptimisticLockError,
)


class TestExceptions:
    def test_citizen_not_found(self):
        exc = CitizenNotFoundError("CIT001")
        assert str(exc) == "Citizen not found: CIT001"
        assert exc.citizen_id == "CIT001"

    def test_duplicate_health_number(self):
        exc = DuplicateHealthNumberError("IQ12345678")
        assert "IQ12345678" in str(exc)

    def test_identity_merge_error(self):
        exc = IdentityMergeError("CIT001", "CIT002", "Duplicate NID")
        assert exc.primary_id == "CIT001"
        assert exc.secondary_id == "CIT002"

    def test_invalid_state_transition(self):
        exc = InvalidStateTransitionError("Encounter", "completed", "in_progress")
        assert "Encounter" in str(exc)

    def test_newborn_registration_error(self):
        exc = NewbornRegistrationError("Mother ID required")
        assert "Mother ID required" in str(exc)

    def test_foreigner_registration_error(self):
        exc = ForeignerRegistrationError("Passport required")
        assert "Passport required" in str(exc)

    def test_consent_not_granted(self):
        exc = ConsentNotGrantedError("PAT001", "research")
        assert exc.scope == "research"

    def test_optimistic_lock_error(self):
        exc = OptimisticLockError("Citizen", "CIT001", 3)
        assert exc.expected_version == 3

    def test_base_exception(self):
        exc = NationalDomainError("Domain error")
        assert isinstance(exc, Exception)
