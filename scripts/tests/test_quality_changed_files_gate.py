from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from scripts.quality_changed_files_gate import (
    compare_counts,
    normalise_path,
    parse_mypy_text,
    parse_ruff_json,
)


def test_parse_ruff_json_normalises_paths_and_preserves_codes(tmp_path: Path) -> None:
    payload = json.dumps(
        [
            {
                "filename": str(tmp_path / "backend/app/security/auth.py"),
                "code": "RUF001",
                "message": "ambiguous unicode character",
                "location": {"row": 12, "column": 4},
            }
        ]
    )

    diagnostics = parse_ruff_json(tmp_path, payload)

    assert len(diagnostics) == 1
    assert diagnostics[0].path == "backend/app/security/auth.py"
    assert diagnostics[0].line == 12
    assert diagnostics[0].code == "RUF001"


def test_parse_mypy_text_accepts_error_codes(tmp_path: Path) -> None:
    output = (
        f"{tmp_path}/backend/app/security/auth.py:8: error: Missing return statement  "
        "[return]\n"
    )

    diagnostics = parse_mypy_text(tmp_path, output)

    assert len(diagnostics) == 1
    assert diagnostics[0].path == "backend/app/security/auth.py"
    assert diagnostics[0].line == 8
    assert diagnostics[0].code == "return"


def test_compare_counts_fails_only_on_increase() -> None:
    baseline = Counter({"a.py": 3, "b.py": 2})
    head = Counter({"a.py": 3, "b.py": 1, "c.py": 1})

    assert compare_counts(baseline, head, "gate") == [
        "gate: c.py: 0 -> 1 (+1)"
    ]


def test_normalise_path_handles_relative_and_absolute_paths(tmp_path: Path) -> None:
    assert normalise_path(tmp_path, "./backend/app/auth.py") == "backend/app/auth.py"
    assert normalise_path(tmp_path, str(tmp_path / "backend/app/auth.py")) == (
        "backend/app/auth.py"
    )
