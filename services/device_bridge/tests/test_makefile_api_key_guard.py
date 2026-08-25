from __future__ import annotations

from pathlib import Path

MAKEFILE = Path(__file__).resolve().parents[1] / "Makefile"


def test_makefile_requires_explicit_local_api_key() -> None:
    content = MAKEFILE.read_text(encoding="utf-8")

    assert "API_KEY ?= lablink-dev-key" not in content
    assert "API_KEY ?=" in content
    assert "run: require-api-key" in content
    assert "smoke: require-api-key" in content
    assert "API_KEY must be supplied for local development" in content
