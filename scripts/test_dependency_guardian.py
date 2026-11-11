from pathlib import Path

from scripts.dependency_guardian import (
    FileReport,
    PackageEntry,
    _classify_packages,
    _has_incompatible_specifiers,
)


def make_report(specifier: str) -> FileReport:
    report = FileReport(path=Path("requirements-test.txt"), label="test")
    report.packages.append(
        PackageEntry(
            name="example",
            specifier=specifier,
            line=1,
            source_file=report.path,
            _raw=f"example{specifier}",
        )
    )
    _classify_packages(report)
    return report


def test_exact_lock_pin_is_bounded():
    report = make_report("==1.2.3")
    assert report.no_min_bound == []


def test_compatible_range_and_lock_pin_are_not_a_conflict():
    assert _has_incompatible_specifiers([">=1.2.3", "==1.2.3"]) is False
    assert _has_incompatible_specifiers([">=1.2.3", "==1.4.0"]) is False


def test_incompatible_exact_pins_are_a_conflict():
    assert _has_incompatible_specifiers(["==1.2.3", "==1.4.0"]) is True


def test_disjoint_ranges_are_a_conflict():
    assert _has_incompatible_specifiers([">=1.0,<2.0", ">=3.0"]) is True
