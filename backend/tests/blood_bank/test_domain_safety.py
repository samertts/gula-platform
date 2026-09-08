from __future__ import annotations

import pytest

from app.blood_bank.compatibility import check_compatibility, get_compatible_groups
from app.blood_bank.domain.state_machine import transition
from app.blood_bank.exceptions import BloodBankWorkflowError


def test_compatibility_is_server_authoritative_and_strict() -> None:
    result = check_compatibility("A+", "O+", component="packed_rbc")
    assert result["compatible"] is True
    assert result["policy_version"] == "abo-rh-component-v1"

    malformed = check_compatibility("", "O+")
    assert malformed["compatible"] is False
    assert malformed["indeterminate"] is True

    unsupported = check_compatibility("A+", "O+", component="unknown_component")
    assert unsupported["compatible"] is False
    assert unsupported["indeterminate"] is True


def test_negative_patient_does_not_receive_positive_red_cells() -> None:
    result = check_compatibility("O-", "O+", component="packed_rbc")
    assert result["compatible"] is False
    assert result["rh_compatible"] is False


def test_compatible_groups_reject_unknown_input() -> None:
    assert get_compatible_groups("unknown") == []
    assert get_compatible_groups("A+")


def test_state_machine_rejects_issue_from_quarantine() -> None:
    with pytest.raises(BloodBankWorkflowError):
        transition("quarantined", "issued", entity="blood_unit")


def test_state_machine_allows_issue_after_release() -> None:
    assert transition("released", "issued", entity="blood_unit") == "issued"


def test_state_machine_rejects_completion_without_start() -> None:
    with pytest.raises(BloodBankWorkflowError):
        transition("verified", "completed", entity="transfusion")


def test_reserved_unit_can_return_to_the_available_pool() -> None:
    """Regression: the shared transition table must not shadow the unit lifecycle.

    "reserved" is reachable by both a blood unit and an order.  When the order
    entry was declared a second time it silently replaced the unit entry, so a
    reserved unit could never be released back into stock.
    """
    assert transition("reserved", "available", entity="blood_unit") == "available"
    assert transition("reserved", "released", entity="blood_unit") == "released"


def test_reserved_order_transitions_are_still_allowed() -> None:
    assert transition("reserved", "issued", entity="blood_request") == "issued"
    assert transition("reserved", "cancelled", entity="blood_request") == "cancelled"
