from __future__ import annotations

from scripts.dependency_guardian import _specifier_entries_are_compatible


def test_lock_pin_satisfying_source_bounds_is_compatible() -> None:
    assert _specifier_entries_are_compatible([">=1.18.5", "==1.18.5"])


def test_incompatible_exact_pin_is_not_compatible() -> None:
    assert not _specifier_entries_are_compatible([">=2.0.0", "==1.18.5"])


def test_different_lower_bounds_without_pin_remain_unresolved() -> None:
    assert not _specifier_entries_are_compatible([">=1.18.5", ">=1.20.0"])
