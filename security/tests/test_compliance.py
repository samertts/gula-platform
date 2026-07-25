from typing import Any, Dict, List

import pytest

from security.modules.compliance.asvs import ASVSValidator
from security.modules.compliance.engine import ComplianceEngine
from security.modules.compliance.gdpr import GDPRValidator
from security.modules.compliance.hipaa import HIPAAValidator
from security.modules.compliance.iso27001 import ISO27001Validator
from security.modules.compliance.mapper import ComplianceMapper, MappedControl
from security.modules.compliance.models import (
    ComplianceControl,
    ComplianceFramework,
    ComplianceReport,
    ControlStatus,
)
from security.modules.compliance.nist import NISTCSFValidator


class TestASVSControls:
    def test_asvs_control_mapping(self):
        v = ASVSValidator()
        controls = v.get_all_controls()
        assert len(controls) > 0
        assert "ASVS-2.1.1" in controls
        assert controls["ASVS-2.1.1"].framework == ComplianceFramework.OWASP_ASVS

    def test_asvs_control_update(self):
        v = ASVSValidator()
        result = v.update_control_status(
            "ASVS-2.1.1", ControlStatus.IMPLEMENTED,
            evidence=["password hashing: argon2id", "cost factors: t=3, m=65536"],
        )
        assert result is True
        control = v.get_control("ASVS-2.1.1")
        assert control.implementation_status == ControlStatus.IMPLEMENTED

    def test_asvs_control_verification(self):
        v = ASVSValidator()
        result = v.verify_control("2.1.1", {"password_hashing": "argon2id"})
        assert result["found"] is True
        assert result["automated_check_passed"] is True

    def test_asvs_control_verification_failure(self):
        v = ASVSValidator()
        result = v.verify_control("2.1.1", {"password_hashing": "md5"})
        assert result["automated_check_passed"] is False

    def test_asvs_report_generation(self):
        v = ASVSValidator()
        report = v.generate_report()
        assert report.framework == ComplianceFramework.OWASP_ASVS
        assert report.control_count > 0
        assert report.passed >= 0
        assert report.failed >= 0

    def test_asvs_gap_analysis(self):
        v = ASVSValidator()
        gaps = v.gap_analysis()
        assert gaps["total_controls"] > 0
        assert "by_chapter" in gaps

    def test_asvs_controls_by_chapter(self):
        v = ASVSValidator()
        chapters = v.get_controls_by_chapter()
        assert len(chapters) > 0


class TestNISTControls:
    def test_nist_report_generation(self):
        v = NISTCSFValidator()
        report = v.generate_report()
        assert report.framework == ComplianceFramework.NIST_CSF
        assert report.control_count > 0

    def test_nist_control_update(self):
        v = NISTCSFValidator()
        result = v.update_control("PR.AC-1", ControlStatus.IMPLEMENTED,
                                   evidence=["mfa enabled for all privileged users"])
        assert result is True
        report = v.generate_report()
        assert report.passed >= 1

    def test_nist_tier_assessment(self):
        v = NISTCSFValidator()
        v.set_tier_assessment(v._current_tier, v._target_tier)
        gap = v.get_tier_gap()
        assert "current_tier" in gap
        assert "target_tier" in gap

    def test_nist_controls_by_function(self):
        v = NISTCSFValidator()
        by_fn = v.get_controls_by_function()
        assert len(by_fn) >= 1


class TestComplianceEngine:
    def test_engine_report_asvs(self):
        engine = ComplianceEngine()
        report = engine.generate_report(ComplianceFramework.OWASP_ASVS)
        assert report.framework == ComplianceFramework.OWASP_ASVS
        assert report.control_count > 0

    def test_engine_report_nist(self):
        engine = ComplianceEngine()
        report = engine.generate_report(ComplianceFramework.NIST_CSF)
        assert report.framework == ComplianceFramework.NIST_CSF
        assert report.control_count > 0

    def test_engine_all_reports(self):
        engine = ComplianceEngine()
        reports = engine.generate_all_reports()
        assert len(reports) >= 2

    def test_engine_update_control(self):
        engine = ComplianceEngine()
        result = engine.update_control(
            ComplianceFramework.OWASP_ASVS, "ASVS-2.1.1", ControlStatus.IMPLEMENTED,
            evidence=["test"],
        )
        assert result is True


class TestComplianceMapper:
    def test_mapped_controls(self):
        mapper = ComplianceMapper()
        mapped = mapper.get_mapped_controls(ComplianceFramework.HIPAA)
        assert len(mapped) >= 0

    def test_composite_score(self):
        mapper = ComplianceMapper()
        v = ASVSValidator()
        report = v.generate_report()
        score = mapper.calculate_composite_score([report])
        assert score["composite_score"] >= 0
        assert "overall_status" in score

    def test_unified_report(self):
        mapper = ComplianceMapper()
        v = ASVSValidator()
        report = v.generate_report()
        unified = mapper.generate_unified_report([report])
        assert "composite_score" in unified

    def test_framework_view(self):
        mapper = ComplianceMapper()
        v = ASVSValidator()
        report = v.generate_report()
        view = mapper.get_framework_view([report], ComplianceFramework.OWASP_ASVS)
        assert "status" in view or "controls" in view or "report" in view


class TestFrameworkSpecific:
    def test_hipaa_validator(self):
        v = HIPAAValidator()
        report = v.generate_report()
        assert report.framework == ComplianceFramework.HIPAA

    def test_gdpr_validator(self):
        v = GDPRValidator()
        report = v.generate_report()
        assert report.framework == ComplianceFramework.GDPR

    def test_iso27001_validator(self):
        v = ISO27001Validator()
        report = v.generate_report()
        assert report.framework == ComplianceFramework.ISO_27001
