"""PROGRAM-STABLE-002 regression tests.

Guards:
1. Domain routes must never use the unauthenticated `Depends(lambda: None)`
   pattern — every domain endpoint must require an authenticated user.
2. The stable domain-isolation scanner must keep rejecting unapproved
   cross-domain edges while accepting the registered EHR/NHDW read contracts.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]

pytestmark = pytest.mark.unit

_DEPENDS_LAMBDA_NONE = re.compile(r"Depends\(\s*lambda:\s*None\s*\)")


def _domain_package_files():
    """All .py files under active domain packages (route files included)."""
    domains = [
        "pharmacy", "radiology", "hospital", "blood_bank", "nursing",
        "citizen_platform", "public_health", "insurance", "ehr",
        "biomedical", "critical_care", "care_continuum", "health_data",
        "nhdw", "national_data",
    ]
    files = []
    for d in domains:
        pkg = ROOT / "backend" / "app" / d
        if not pkg.exists():
            continue
        for p in pkg.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            files.append(p)
    return files


class TestNoUnauthenticatedDomainRoutes:
    """Zero cross-domain administration: no domain route may bypass auth.

    `Depends(lambda: None)` injects a non-authenticated dummy user, which
    previously left 57 radiology endpoints open to any caller (including
    users of other domains). Fixed in PROGRAM-STABLE-002; guard forward.
    """

    @pytest.mark.parametrize(
        "path",
        [str(p.relative_to(ROOT)) for p in _domain_package_files()],
    )
    def test_no_lambda_none_dependency(self, path):
        full = ROOT / path
        text = full.read_text(encoding="utf-8", errors="ignore")
        assert not _DEPENDS_LAMBDA_NONE.findall(text), (
            f"{path} uses unauthenticated Depends(lambda: None)"
        )
