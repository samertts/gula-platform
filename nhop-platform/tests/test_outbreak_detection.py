"""Unit tests for the outbreak detection service."""
from datetime import datetime, timedelta, timezone

import pytest
from app.models.antibiotic_sensitivity import AntibioticSensitivity
from app.models.disease_case import DiseaseCase
from app.services.outbreak_detection import (
    CRITICAL_RATIO,
    WARNING_RATIO,
    check_outbreak,
    get_disease_heatmap,
    get_resistance_report,
)

from backend.app._compat import UTC

FROZEN_NOW = datetime(2026, 4, 19, 12, 0, tzinfo=UTC)


def _mk_case(db, *, disease, province, hours_ago, positive=True, name=None):
    row = DiseaseCase(
        disease_code=disease,
        disease_name=name or disease,
        province=province,
        is_positive=positive,
        reported_at=FROZEN_NOW - timedelta(hours=hours_ago),
    )
    db.add(row)
    return row


def test_no_cases_returns_empty(db_session):
    assert check_outbreak(db_session, now=FROZEN_NOW) == []


def test_below_warning_ratio_no_alert(db_session):
    # Baseline: 60 over 29 days = ~2/day. Current 24h: 3 (ratio 1.5).
    for i in range(60):
        _mk_case(db_session, disease="FLU", province="Baghdad", hours_ago=25 + i * 3)
    for i in range(3):
        _mk_case(db_session, disease="FLU", province="Baghdad", hours_ago=i * 3)
    db_session.flush()

    alerts = check_outbreak(db_session, now=FROZEN_NOW)
    assert alerts == []


def test_warning_ratio_emits_warning(db_session):
    # Baseline ~2/day. Current 24h: 7 (ratio 3.5 → warning, not critical).
    for i in range(60):
        _mk_case(db_session, disease="FLU", province="Baghdad", hours_ago=25 + i * 3)
    for i in range(7):
        _mk_case(db_session, disease="FLU", province="Baghdad", hours_ago=i * 3)
    db_session.flush()

    alerts = check_outbreak(db_session, now=FROZEN_NOW)
    assert len(alerts) == 1
    a = alerts[0]
    assert a.severity == "warning"
    assert a.current_count == 7
    assert WARNING_RATIO < a.ratio <= CRITICAL_RATIO


def test_critical_ratio_emits_critical(db_session):
    # Baseline ~2/day. Current 24h: 20 (ratio 10 → critical).
    for i in range(60):
        _mk_case(db_session, disease="CHOLERA", province="Basra", hours_ago=25 + i * 3)
    for i in range(20):
        _mk_case(db_session, disease="CHOLERA", province="Basra", hours_ago=i)
    db_session.flush()

    alerts = check_outbreak(db_session, now=FROZEN_NOW)
    assert len(alerts) == 1
    assert alerts[0].severity == "critical"
    assert alerts[0].province == "Basra"
    assert alerts[0].disease_code == "CHOLERA"


def test_min_cases_threshold_suppresses_noise(db_session):
    # Zero baseline, current 24h = 2 → ratio looks huge but below _MIN_CASES.
    for i in range(2):
        _mk_case(db_session, disease="RARE", province="Anbar", hours_ago=i)
    db_session.flush()

    assert check_outbreak(db_session, now=FROZEN_NOW) == []


def test_negative_results_ignored(db_session):
    # 100 negatives in the window must not trigger anything.
    for i in range(100):
        _mk_case(
            db_session, disease="FLU", province="Baghdad",
            hours_ago=i % 24, positive=False,
        )
    db_session.flush()

    assert check_outbreak(db_session, now=FROZEN_NOW) == []


def test_alerts_sorted_critical_first(db_session):
    # One warning (ratio ~3.5) and one critical (ratio 10); critical must sort first.
    for i in range(60):
        _mk_case(db_session, disease="FLU", province="Baghdad", hours_ago=25 + i * 3)
        _mk_case(db_session, disease="CHOLERA", province="Basra", hours_ago=25 + i * 3)
    for i in range(7):
        _mk_case(db_session, disease="FLU", province="Baghdad", hours_ago=i * 3)
    for i in range(20):
        _mk_case(db_session, disease="CHOLERA", province="Basra", hours_ago=i)
    db_session.flush()

    alerts = check_outbreak(db_session, now=FROZEN_NOW)
    assert len(alerts) == 2
    assert alerts[0].severity == "critical"
    assert alerts[1].severity == "warning"


def test_heatmap_by_province(db_session):
    for _ in range(5):
        _mk_case(db_session, disease="DENGUE", province="Baghdad", hours_ago=12)
    for _ in range(2):
        _mk_case(db_session, disease="DENGUE", province="Basra", hours_ago=30)
    # Outside window (> 7 days) — must be excluded.
    _mk_case(db_session, disease="DENGUE", province="Basra", hours_ago=24 * 10)
    # Different disease — must be excluded.
    _mk_case(db_session, disease="FLU", province="Baghdad", hours_ago=1)
    db_session.flush()

    data = get_disease_heatmap(db_session, "DENGUE", days=7, now=FROZEN_NOW)
    assert data["disease_code"] == "DENGUE"
    assert data["days"] == 7
    assert data["total"] == 7
    by_prov = {p["province"]: p["count"] for p in data["by_province"]}
    assert by_prov == {"Baghdad": 5, "Basra": 2}


def test_heatmap_rejects_invalid_days(db_session):
    with pytest.raises(ValueError):
        get_disease_heatmap(db_session, "FLU", days=0, now=FROZEN_NOW)


def test_resistance_report_rates(db_session):
    # E.coli vs Ampicillin in Baghdad: 3 resistant / 4 tested = 0.75.
    for is_r in (True, True, True, False):
        db_session.add(AntibioticSensitivity(
            bacterium="E.coli", antibiotic="Ampicillin",
            province="Baghdad", is_resistant=is_r,
            tested_at=FROZEN_NOW - timedelta(days=1),
        ))
    # Staph vs Vancomycin in Basra: 1 resistant / 5 = 0.2.
    for is_r in (True, False, False, False, False):
        db_session.add(AntibioticSensitivity(
            bacterium="Staph", antibiotic="Vancomycin",
            province="Basra", is_resistant=is_r,
            tested_at=FROZEN_NOW - timedelta(days=1),
        ))
    db_session.flush()

    report = get_resistance_report(db_session)
    assert report["total_pairs"] == 2
    # Higher rate first.
    first, second = report["pairs"]
    assert first["bacterium"] == "E.coli"
    assert first["resistance_rate"] == 0.75
    assert first["tested"] == 4 and first["resistant"] == 3
    assert second["bacterium"] == "Staph"
    assert second["resistance_rate"] == 0.2


def test_resistance_report_province_filter(db_session):
    db_session.add(AntibioticSensitivity(
        bacterium="E.coli", antibiotic="Ampicillin",
        province="Baghdad", is_resistant=True,
        tested_at=FROZEN_NOW,
    ))
    db_session.add(AntibioticSensitivity(
        bacterium="E.coli", antibiotic="Ampicillin",
        province="Basra", is_resistant=False,
        tested_at=FROZEN_NOW,
    ))
    db_session.flush()

    report = get_resistance_report(db_session, province="Baghdad")
    assert report["province_filter"] == "Baghdad"
    assert report["total_pairs"] == 1
    assert report["pairs"][0]["province"] == "Baghdad"
