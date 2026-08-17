from app.national.services.encounter_service import FLOW_TRANSITIONS


def test_patient_flow_is_forward_only_for_terminal_states():
    assert FLOW_TRANSITIONS["planned"] == {"arrived", "cancelled"}
    assert FLOW_TRANSITIONS["arrived"] == {"triaged", "cancelled"}
    assert FLOW_TRANSITIONS["discharged"] == set()
    assert FLOW_TRANSITIONS["cancelled"] == set()


def test_patient_flow_does_not_skip_triage_or_admission():
    assert "admitted" not in FLOW_TRANSITIONS["arrived"]
    assert "discharged" not in FLOW_TRANSITIONS["triaged"]
    assert "discharged" in FLOW_TRANSITIONS["discharge_pending"]


def test_patient_flow_supports_explicit_transfer_handshake():
    assert "transfer_pending" in FLOW_TRANSITIONS["in_progress"]
    assert FLOW_TRANSITIONS["transfer_pending"] == {"admitted", "cancelled"}
