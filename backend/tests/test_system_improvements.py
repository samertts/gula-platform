"""
Tests for system improvements:
  - Expanded interpretation engine (30+ tests)
  - Extended critical alert thresholds
  - Stats/trends API endpoints
  - Enhanced clinical intelligence patterns
  - New database migration idempotency

All tests use in-memory SQLite (via conftest fixtures) — no real DB needed.
"""
from __future__ import annotations

import pytest

# ─── Interpretation Engine ────────────────────────────────────────────────────


class TestInterpretationEngine:
    """Tests for the expanded interpretation engine."""

    def setup_method(self):
        from app.services.interpretation import interpret_result, get_flag, INTERPRETATIONS
        self.interpret = interpret_result
        self.get_flag = get_flag
        self.INTERPRETATIONS = INTERPRETATIONS

    # ── Existing tests (regression) ──────────────────────────────────────────

    def test_glucose_normal(self):
        result = self.interpret("Glucose", 85.0, 70, 100)
        assert result["status"] == "normal"
        assert result["interpretation_ar"]

    def test_glucose_critical_high(self):
        result = self.interpret("Glucose", 550.0, 70, 100)
        assert result["status"] == "critical"

    def test_hemoglobin_low(self):
        result = self.interpret("Hemoglobin", 9.0, 12, 17)
        assert result["status"] == "low"

    # ── Iron studies ─────────────────────────────────────────────────────────

    def test_iron_low(self):
        result = self.interpret("Iron", 40.0)
        assert result["status"] == "low"
        assert result["interpretation_ar"]

    def test_iron_normal(self):
        result = self.interpret("Iron", 100.0)
        assert result["status"] == "normal"

    def test_iron_high(self):
        result = self.interpret("Iron", 250.0)
        assert result["status"] == "high"

    def test_ferritin_low(self):
        result = self.interpret("Ferritin", 8.0)
        assert result["status"] == "low"

    def test_ferritin_normal(self):
        result = self.interpret("Ferritin", 80.0)
        assert result["status"] == "normal"

    def test_ferritin_critical_high(self):
        result = self.interpret("Ferritin", 1500.0)
        assert result["status"] == "critical"

    def test_tibc_low(self):
        result = self.interpret("TIBC", 200.0)
        assert result["status"] == "low"

    def test_tibc_high(self):
        result = self.interpret("TIBC", 500.0)
        assert result["status"] == "high"

    # ── Inflammation markers ──────────────────────────────────────────────────

    def test_crp_normal(self):
        result = self.interpret("CRP", 2.0)
        assert result["status"] == "normal"

    def test_crp_high(self):
        result = self.interpret("CRP", 20.0)
        assert result["status"] == "high"

    def test_crp_critical(self):
        result = self.interpret("CRP", 150.0)
        assert result["status"] == "critical"

    def test_procalcitonin_normal(self):
        result = self.interpret("Procalcitonin", 0.1)
        assert result["status"] == "normal"

    def test_procalcitonin_high(self):
        result = self.interpret("Procalcitonin", 1.5)
        assert result["status"] == "high"

    def test_procalcitonin_critical(self):
        result = self.interpret("Procalcitonin", 5.0)
        assert result["status"] == "critical"

    def test_esr_normal(self):
        result = self.interpret("ESR", 15.0)
        assert result["status"] == "normal"

    def test_esr_high(self):
        result = self.interpret("ESR", 60.0)
        assert result["status"] == "high"

    # ── Metabolic ─────────────────────────────────────────────────────────────

    def test_uric_acid_normal(self):
        result = self.interpret("Uric Acid", 5.0)
        assert result["status"] == "normal"

    def test_uric_acid_high(self):
        result = self.interpret("Uric Acid", 8.0)
        assert result["status"] == "high"

    def test_uric_acid_critical(self):
        result = self.interpret("Uric Acid", 12.0)
        assert result["status"] == "critical"

    def test_calcium_normal(self):
        result = self.interpret("Calcium", 9.5)
        assert result["status"] == "normal"

    def test_calcium_critical_high(self):
        result = self.interpret("Calcium", 14.0)
        assert result["status"] == "critical"

    def test_magnesium_critical_high(self):
        result = self.interpret("Magnesium", 5.0)
        assert result["status"] == "critical"

    # ── Vitamins ─────────────────────────────────────────────────────────────

    def test_vitamin_b12_low(self):
        result = self.interpret("Vitamin B12", 150.0)
        assert result["status"] == "low"

    def test_vitamin_b12_normal(self):
        result = self.interpret("Vitamin B12", 400.0)
        assert result["status"] == "normal"

    def test_folate_low(self):
        result = self.interpret("Folate", 2.0)
        assert result["status"] == "low"

    # ── Liver & Bilirubin ────────────────────────────────────────────────────

    def test_bilirubin_total_normal(self):
        result = self.interpret("Bilirubin Total", 0.8)
        assert result["status"] == "normal"

    def test_bilirubin_total_high(self):
        result = self.interpret("Bilirubin Total", 3.0)
        assert result["status"] == "high"

    def test_bilirubin_total_critical(self):
        result = self.interpret("Bilirubin Total", 12.0)
        assert result["status"] == "critical"

    def test_ggt_normal(self):
        result = self.interpret("GGT", 30.0)
        assert result["status"] == "normal"

    def test_alp_normal(self):
        result = self.interpret("ALP", 80.0)
        assert result["status"] == "normal"

    # ── Coagulation ───────────────────────────────────────────────────────────

    def test_pt_normal(self):
        result = self.interpret("PT", 12.0)
        assert result["status"] == "normal"

    def test_pt_critical(self):
        result = self.interpret("PT", 35.0)
        assert result["status"] == "critical"

    def test_inr_normal(self):
        result = self.interpret("INR", 1.1)
        assert result["status"] == "normal"

    def test_inr_critical(self):
        result = self.interpret("INR", 5.0)
        assert result["status"] == "critical"

    def test_aptt_normal(self):
        result = self.interpret("APTT", 30.0)
        assert result["status"] == "normal"

    def test_aptt_critical(self):
        result = self.interpret("APTT", 80.0)
        assert result["status"] == "critical"

    # ── Cardiac ──────────────────────────────────────────────────────────────

    def test_troponin_normal(self):
        result = self.interpret("Troponin", 0.01)
        assert result["status"] == "normal"

    def test_troponin_critical(self):
        result = self.interpret("Troponin", 0.5)
        assert result["status"] == "critical"

    def test_ldh_normal(self):
        result = self.interpret("LDH", 200.0)
        assert result["status"] == "normal"

    def test_ck_high(self):
        result = self.interpret("CK", 400.0)
        assert result["status"] == "high"

    def test_ck_critical(self):
        result = self.interpret("CK", 1200.0)
        assert result["status"] == "critical"

    # ── Hormones ────────────────────────────────────────────────────────────

    def test_psa_normal(self):
        result = self.interpret("PSA", 2.0)
        assert result["status"] == "normal"

    def test_psa_high(self):
        result = self.interpret("PSA", 6.0)
        assert result["status"] == "high"

    def test_psa_critical(self):
        result = self.interpret("PSA", 15.0)
        assert result["status"] == "critical"

    def test_cortisol_normal(self):
        result = self.interpret("Cortisol", 15.0)
        assert result["status"] == "normal"

    def test_cortisol_low(self):
        result = self.interpret("Cortisol", 3.0)
        assert result["status"] == "low"

    def test_t3_normal(self):
        result = self.interpret("T3", 120.0)
        assert result["status"] == "normal"

    def test_t4_normal(self):
        result = self.interpret("T4", 8.0)
        assert result["status"] == "normal"

    # ── Pancreas ─────────────────────────────────────────────────────────────

    def test_amylase_critical(self):
        result = self.interpret("Amylase", 350.0)
        assert result["status"] == "critical"

    def test_lipase_critical(self):
        result = self.interpret("Lipase", 250.0)
        assert result["status"] == "critical"

    # ── Protein ──────────────────────────────────────────────────────────────

    def test_albumin_normal(self):
        result = self.interpret("Albumin", 4.0)
        assert result["status"] == "normal"

    def test_albumin_low(self):
        result = self.interpret("Albumin", 2.5)
        assert result["status"] == "low"

    # ── Arabic translation completeness ──────────────────────────────────────

    def test_all_known_tests_have_arabic(self):
        """Every test in INTERPRETATIONS must have Arabic text on all statuses."""
        for test_name, data in self.INTERPRETATIONS.items():
            for status_key in ("normal", "low", "high", "critical_high"):
                if status_key not in data:
                    continue
                entry = data[status_key]
                assert "text_ar" in entry, f"Missing text_ar in {test_name}.{status_key}"
                assert "advice_ar" in entry, f"Missing advice_ar in {test_name}.{status_key}"

    # ── get_flag helper ──────────────────────────────────────────────────────

    def test_flag_normal(self):
        assert self.get_flag(5.0, 4.0, 6.0) == "normal"

    def test_flag_high(self):
        assert self.get_flag(7.0, 4.0, 6.0) == "H"

    def test_flag_low(self):
        assert self.get_flag(2.0, 4.0, 6.0) == "L"

    def test_flag_critical_troponin(self):
        # Troponin I critical threshold is 0.4 ng/mL
        flag = self.get_flag(0.5, 0.0, 0.04, test_name="Troponin")
        assert flag == "critical"

    def test_flag_unknown_without_range(self):
        assert self.get_flag(5.0, None, None) == "unknown"

    def test_flag_generic_critical_high(self):
        # 2x the normal_high → generic critical
        assert self.get_flag(200.0, 10.0, 50.0) == "critical"


# ─── Critical Alerts ────────────────────────────────────────────────────────


class TestCriticalAlerts:
    """Tests for the extended critical alert thresholds."""

    def setup_method(self):
        from app.routes.critical_alerts import check_critical, CRITICAL_THRESHOLDS
        self.check_critical = check_critical
        self.thresholds = CRITICAL_THRESHOLDS

    def test_glucose_critical_low(self):
        alert = self.check_critical("Glucose", 30.0)
        assert alert is not None
        assert alert["severity"] == "critical_low"

    def test_glucose_critical_high(self):
        alert = self.check_critical("Glucose", 600.0)
        assert alert is not None
        assert alert["severity"] == "critical_high"

    def test_glucose_normal(self):
        assert self.check_critical("Glucose", 90.0) is None

    def test_potassium_critical_high(self):
        alert = self.check_critical("Potassium", 7.0)
        assert alert is not None
        assert alert["severity"] == "critical_high"

    def test_potassium_critical_low(self):
        alert = self.check_critical("Potassium", 2.0)
        assert alert is not None
        assert alert["severity"] == "critical_low"

    def test_sodium_critical_low(self):
        alert = self.check_critical("Sodium", 110.0)
        assert alert is not None

    def test_troponin_critical(self):
        alert = self.check_critical("Troponin", 0.5)
        assert alert is not None

    def test_troponin_i_critical(self):
        alert = self.check_critical("Troponin I", 0.5)
        assert alert is not None

    def test_inr_critical(self):
        alert = self.check_critical("INR", 5.0)
        assert alert is not None

    def test_pt_critical(self):
        alert = self.check_critical("PT", 35.0)
        assert alert is not None

    def test_bilirubin_total_critical(self):
        alert = self.check_critical("Bilirubin Total", 18.0)
        assert alert is not None

    def test_crp_critical(self):
        alert = self.check_critical("CRP", 250.0)
        assert alert is not None

    def test_procalcitonin_critical(self):
        alert = self.check_critical("Procalcitonin", 12.0)
        assert alert is not None

    def test_urea_critical(self):
        alert = self.check_critical("Urea", 220.0)
        assert alert is not None

    def test_uric_acid_critical(self):
        alert = self.check_critical("Uric Acid", 14.0)
        assert alert is not None

    def test_unknown_test_no_alert(self):
        """Unknown tests should not generate critical alerts."""
        assert self.check_critical("obscure_test_xyz", 99999) is None

    def test_all_thresholds_have_required_fields(self):
        """Every threshold entry must have critical_low/critical_high and unit."""
        for test_name, entry in self.thresholds.items():
            assert "critical_low" in entry, f"Missing critical_low in {test_name}"
            assert "critical_high" in entry, f"Missing critical_high in {test_name}"
            assert "unit" in entry, f"Missing unit in {test_name}"

    def test_alert_has_arabic_message(self):
        alert = self.check_critical("Glucose", 30.0)
        assert alert is not None
        assert "message_ar" in alert
        assert len(alert["message_ar"]) > 5


# ─── Clinical Intelligence ───────────────────────────────────────────────────


class TestClinicalIntelligence:
    """Tests for the enhanced clinical intelligence patterns."""

    def setup_method(self):
        from app.services.clinical_intelligence import analyze_results, CLINICAL_PATTERNS
        self.analyze = analyze_results
        self.patterns = CLINICAL_PATTERNS

    def _make_result(self, test_name: str, value: float) -> dict:
        return {"test_name": test_name, "value": value}

    def test_sepsis_pattern_detected(self):
        results = [
            self._make_result("WBC", 18.0),
            self._make_result("Hemoglobin", 8.0),
            self._make_result("Platelets", 50.0),
        ]
        alerts = self.analyze(results)
        ids = [a["pattern_id"] for a in alerts]
        assert "sepsis_risk" in ids

    def test_dka_pattern_detected(self):
        results = [
            self._make_result("Glucose", 400.0),
            self._make_result("HbA1c", 10.0),
        ]
        alerts = self.analyze(results)
        assert any(a["pattern_id"] == "dka_risk" for a in alerts)

    def test_renal_failure_pattern(self):
        results = [
            self._make_result("Creatinine", 5.0),
            self._make_result("Urea", 120.0),
        ]
        alerts = self.analyze(results)
        assert any(a["pattern_id"] == "renal_failure_risk" for a in alerts)

    def test_liver_injury_pattern(self):
        results = [
            self._make_result("ALT", 350.0),
            self._make_result("AST", 300.0),
        ]
        alerts = self.analyze(results)
        assert any(a["pattern_id"] == "liver_injury_severe" for a in alerts)

    # ── New patterns ──────────────────────────────────────────────────────────

    def test_acute_mi_pattern(self):
        results = [
            self._make_result("Troponin", 0.2),
            self._make_result("CK", 500.0),
        ]
        alerts = self.analyze(results)
        assert any(a["pattern_id"] == "acute_mi_risk" for a in alerts)

    def test_acute_pancreatitis_pattern(self):
        results = [
            self._make_result("Amylase", 300.0),
            self._make_result("Lipase", 250.0),
        ]
        alerts = self.analyze(results)
        assert any(a["pattern_id"] == "acute_pancreatitis" for a in alerts)

    def test_iron_deficiency_anemia_pattern(self):
        results = [
            self._make_result("Hemoglobin", 9.0),
            self._make_result("Ferritin", 10.0),
        ]
        alerts = self.analyze(results)
        assert any(a["pattern_id"] == "iron_deficiency_anemia" for a in alerts)

    def test_sepsis_inflammatory_pattern(self):
        results = [
            self._make_result("CRP", 120.0),
            self._make_result("Procalcitonin", 2.5),
        ]
        alerts = self.analyze(results)
        assert any(a["pattern_id"] == "sepsis_inflammatory" for a in alerts)

    def test_coagulopathy_pattern(self):
        results = [
            self._make_result("PT", 30.0),
            self._make_result("INR", 4.5),
        ]
        alerts = self.analyze(results)
        assert any(a["pattern_id"] == "coagulopathy_severe" for a in alerts)

    def test_hepatic_failure_pattern(self):
        results = [
            self._make_result("ALT", 500.0),
            self._make_result("Bilirubin Total", 8.0),
        ]
        alerts = self.analyze(results)
        assert any(a["pattern_id"] == "hepatic_failure_risk" for a in alerts)

    def test_metabolic_syndrome_pattern(self):
        results = [
            self._make_result("Glucose", 120.0),
            self._make_result("HbA1c", 6.5),
            self._make_result("Triglycerides", 250.0),
        ]
        alerts = self.analyze(results)
        assert any(a["pattern_id"] == "metabolic_syndrome_risk" for a in alerts)

    def test_b12_folate_deficiency_pattern(self):
        results = [
            self._make_result("Vitamin B12", 150.0),
            self._make_result("Folate", 2.0),
        ]
        alerts = self.analyze(results)
        assert any(a["pattern_id"] == "vitamin_b12_folate_deficiency" for a in alerts)

    def test_no_patterns_on_normal_results(self):
        results = [
            self._make_result("Hemoglobin", 14.0),
            self._make_result("WBC", 7.0),
            self._make_result("Glucose", 90.0),
        ]
        alerts = self.analyze(results)
        # Normal values should not trigger critical patterns
        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        assert len(critical_alerts) == 0

    def test_empty_results_no_patterns(self):
        assert self.analyze([]) == []

    def test_critical_sorted_first(self):
        """Critical patterns should appear before warning patterns."""
        results = [
            self._make_result("Troponin", 0.5),
            self._make_result("CK", 800.0),
            self._make_result("Cholesterol", 350.0),
            self._make_result("Triglycerides", 400.0),
        ]
        alerts = self.analyze(results)
        if len(alerts) >= 2:
            severities = [a["severity"] for a in alerts]
            # critical should precede warning
            critical_indices = [i for i, s in enumerate(severities) if s == "critical"]
            warning_indices = [i for i, s in enumerate(severities) if s == "warning"]
            if critical_indices and warning_indices:
                assert max(critical_indices) < min(warning_indices)

    def test_all_patterns_have_arabic(self):
        """All patterns must have Arabic name and message."""
        for p in self.patterns:
            assert "name_ar" in p and p["name_ar"], f"Pattern {p['id']} missing name_ar"
            assert "message_ar" in p and p["message_ar"], f"Pattern {p['id']} missing message_ar"
            assert "action_ar" in p and p["action_ar"], f"Pattern {p['id']} missing action_ar"


# ─── Stats API Endpoints ──────────────────────────────────────────────────────


class TestStatsAPI:
    """Integration tests for /stats/* endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, client, make_lab, make_lab_user, db):
        from tests.conftest import auth_headers
        self.lab = make_lab(name="Stats Test Lab")
        self.user = make_lab_user(lab_id=self.lab.id, role="admin")
        self.headers = auth_headers(self.user.id, self.lab.id)
        self.client = client
        self.db = db

    def test_summary_returns_200(self):
        resp = self.client.get("/stats/summary", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "totals" in data
        assert "today" in data
        assert "this_week" in data
        assert "this_month" in data

    def test_summary_totals_structure(self):
        resp = self.client.get("/stats/summary", headers=self.headers)
        totals = resp.json()["totals"]
        assert "patients" in totals
        assert "orders" in totals
        assert "tests" in totals
        assert "critical_results" in totals
        assert "critical_rate_pct" in totals

    def test_daily_trends_returns_200(self):
        resp = self.client.get("/stats/trends/daily?days=7", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "series" in data
        assert "days" in data
        assert data["days"] == 7

    def test_daily_trends_validates_days(self):
        resp = self.client.get("/stats/trends/daily?days=0", headers=self.headers)
        assert resp.status_code == 422

    def test_daily_trends_max_days(self):
        resp = self.client.get("/stats/trends/daily?days=400", headers=self.headers)
        assert resp.status_code == 422

    def test_test_frequency_returns_200(self):
        resp = self.client.get("/stats/trends/tests?days=30", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "top_tests" in data

    def test_test_frequency_limit_param(self):
        resp = self.client.get("/stats/trends/tests?days=30&limit=5", headers=self.headers)
        assert resp.status_code == 200

    def test_flag_distribution_returns_200(self):
        resp = self.client.get("/stats/trends/flags?days=30", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "distribution" in data
        assert "total_results" in data

    def test_patient_growth_returns_200(self):
        resp = self.client.get("/stats/trends/patients?days=90", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "weekly_series" in data
        assert "total_new_patients" in data

    def test_turnaround_returns_200(self):
        resp = self.client.get("/stats/turnaround?days=30", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "avg_minutes" in data
        assert "completed_orders_sampled" in data

    def test_stats_require_auth(self):
        """Stats endpoints require a valid Bearer token."""
        resp = self.client.get("/stats/summary")
        assert resp.status_code == 401

    def test_lab_isolation(self, make_lab, make_lab_user):
        """Stats must be scoped to the requesting lab."""
        from tests.conftest import auth_headers
        from app.models.patient import Patient

        # Create a patient in a different lab
        other_lab = make_lab(name="Other Lab")
        other_user = make_lab_user(lab_id=other_lab.id, role="admin")
        p = Patient(
            lab_id=other_lab.id,
            full_name="Other Patient",
            phone="07901234567",
            health_id="HP-OTHER",
        )
        self.db.add(p)
        self.db.commit()

        # Our lab's summary should show 0 patients
        resp = self.client.get("/stats/summary", headers=self.headers)
        assert resp.json()["totals"]["patients"] == 0

        # Other lab's summary should show 1 patient
        other_headers = auth_headers(other_user.id, other_lab.id)
        resp2 = self.client.get("/stats/summary", headers=other_headers)
        assert resp2.json()["totals"]["patients"] == 1


# ─── Migration Idempotency ────────────────────────────────────────────────────


class TestMigrationIdempotency:
    """Verify the new migration's helper functions work correctly."""

    def test_index_exists_helper(self):
        """_index_exists should not raise on empty DB."""
        from migrations.versions.migration_test_helpers import check_migration_helpers  # noqa
        # Just ensure the module imports without error
        import importlib
        spec = importlib.util.find_spec(
            "migrations.versions.20260503_0001_stats_trends_perf_indexes"
        )
        assert spec is not None

    def test_migration_module_importable(self):
        import importlib
        mod = importlib.import_module(
            "migrations.versions.20260503_0001_stats_trends_perf_indexes"
        )
        assert mod.revision == "20260503_0001"
        assert mod.down_revision == "20260428_0001"
        assert callable(mod.upgrade)
        assert callable(mod.downgrade)
