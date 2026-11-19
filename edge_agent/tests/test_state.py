"""AgentState: encrypted on-disk state, previously with zero test coverage."""
from __future__ import annotations

import stat

from gula_edge_agent.state import AgentState, StateError


def test_set_and_get_round_trip(tmp_path):
    state = AgentState(str(tmp_path))
    state.set(device_id="DEV-1", agent_token="tok-abc", lab_id=42)

    assert state.get("device_id") == "DEV-1"
    assert state.get("agent_token") == "tok-abc"
    assert state.get("lab_id") == 42
    assert state.get("missing_key", "fallback") == "fallback"


def test_is_registered_requires_both_device_id_and_token(tmp_path):
    state = AgentState(str(tmp_path))
    assert state.is_registered() is False

    state.set(device_id="DEV-1")
    assert state.is_registered() is False  # no token yet

    state.set(agent_token="tok-abc")
    assert state.is_registered() is True


def test_state_file_is_actually_encrypted_at_rest(tmp_path):
    state = AgentState(str(tmp_path))
    state.set(private_key_pem="-----BEGIN PRIVATE KEY-----\nSECRET\n-----END PRIVATE KEY-----")

    raw = state.state_file.read_bytes()
    assert b"SECRET" not in raw
    assert b"BEGIN PRIVATE KEY" not in raw


def test_state_and_key_files_are_owner_only(tmp_path):
    state = AgentState(str(tmp_path))
    state.set(device_id="DEV-1")

    for f in (state.state_file, state.key_file):
        mode = stat.S_IMODE(f.stat().st_mode)
        assert mode & stat.S_IRWXG == 0, f"{f} is group-accessible: {oct(mode)}"
        assert mode & stat.S_IRWXO == 0, f"{f} is world-accessible: {oct(mode)}"


def test_persists_across_new_instances(tmp_path):
    AgentState(str(tmp_path)).set(device_id="DEV-1", agent_token="tok-abc")

    reopened = AgentState(str(tmp_path))
    assert reopened.get("device_id") == "DEV-1"
    assert reopened.is_registered() is True


def test_corrupt_state_file_raises_state_error(tmp_path):
    state = AgentState(str(tmp_path))
    state.set(device_id="DEV-1")  # creates state.key first

    state.state_file.write_bytes(b"not a valid fernet token")

    fresh = AgentState(str(tmp_path))  # fresh instance, no in-memory cache
    try:
        fresh.get("device_id")
        assert False, "expected StateError on corrupt state file"
    except StateError:
        pass
