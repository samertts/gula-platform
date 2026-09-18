"""_load_config(): regression test for a real config-loading bug.

Before this fix, the function read:

    import tomllib
    with cfg_path.open("rb") as f:
        return tomllib.load(f)
    import tomli                       # unreachable — the return above
    with cfg_path.open("rb") as f:      # already exited the function
        return tomli.load(f)

requirements.txt declares `tomli>=2.2.1; python_version < "3.11"`, so the
agent is meant to run on Python <3.11 too — but on those versions,
`import tomllib` raises ModuleNotFoundError immediately (tomllib is
stdlib-only from 3.11), and the dead `tomli` fallback below the early
`return` could never run. The agent would crash on startup on any
supported-per-requirements.txt Python <3.11.

This test can't switch the interpreter version to prove the <3.11 crash
directly, but it does prove the actual load path is correct and exercised
(not just "doesn't raise because we're on 3.11 anyway").
"""
from __future__ import annotations

import sys

import pytest
from gula_edge_agent.cli import _load_config


def test_load_config_reads_a_real_toml_file(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        '[storage]\nstate_dir = "/tmp/state"\n\n'
        '[backend]\nurl = "https://gula.example"\n'
    )
    monkeypatch.delenv("GULA_EDGE_CONFIG", raising=False)

    cfg = _load_config(str(cfg_file))

    assert cfg["storage"]["state_dir"] == "/tmp/state"
    assert cfg["backend"]["url"] == "https://gula.example"


def test_load_config_missing_file_exits_with_a_clear_message(tmp_path):
    missing = tmp_path / "does-not-exist.toml"
    with pytest.raises(SystemExit) as exc_info:
        _load_config(str(missing))
    assert "config not found" in str(exc_info.value)


def test_load_config_falls_back_to_tomli_when_tomllib_is_unavailable(tmp_path, monkeypatch):
    """Simulate Python <3.11 (no stdlib tomllib) without needing a second
    interpreter: hide tomllib from import and confirm the function still
    loads the file via the tomli fallback instead of crashing."""
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text('[device]\nrole_mode = "lab"\n')

    monkeypatch.setitem(sys.modules, "tomllib", None)  # `import tomllib` -> ImportError

    cfg = _load_config(str(cfg_file))

    assert cfg["device"]["role_mode"] == "lab"
