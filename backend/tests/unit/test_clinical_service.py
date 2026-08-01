"""Unit tests for clinical_service — terminology, knowledge, CDS, quality, AI stubs."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app.clinical.base import ClinicalBase
from app.clinical.cds.models import (
    CareBundle,
    CareBundleElement,
    ClinicalAlert,
    Contraindication,
    DuplicateOrderRule,
    OrderSet,
    OrderSetItem,
    PreventiveRecommendation,
)
from app.clinical.enums import (
    EvidenceLevel,
    GuidelineStatus,
    QualityIndicatorType,
    TerminologyStatus,
    TerminologySystem,
)
from app.clinical.knowledge.models import (
    ClinicalGuideline,
    ClinicalPathway,
    ClinicalProtocol,
    ClinicalRecommendation,
    GuidelineApproval,
    StandingOrder,
)
from app.clinical.quality.models import (
    BenchmarkValue,
    ClinicalAuditRecord,
    ComplianceCheck,
    IncidentReport,
    IndicatorMeasurement,
    MortalityReview,
    PatientSafetyEvent,
    QualityIndicator,
)
from app.clinical.terminology.models import (
    CodeSystem,
    ICD10Code,
    LOINCCode,
    SNOMEDCTCode,
    TerminologyCode,
    TerminologyMapping,
    TerminologyVersion,
    ValueSet,
    ValueSetMember,
)
from app.services import clinical_service
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    ClinicalBase.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        ClinicalBase.metadata.drop_all(bind=engine)


def _code(db, code="A01", display="Cholera", system=TerminologySystem.ICD10, status=TerminologyStatus.ACTIVE):
    obj = TerminologyCode(code=code, display=display, system=system, status=status)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _guideline(db, title="Sepsis", status=GuidelineStatus.ACTIVE, specialty="ICU"):
    obj = ClinicalGuideline(title=title, version="1.0", status=status, specialty=specialty)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _indicator(db, name="Hand hygiene", direction="lower_is_better", target_value=5.0):
    obj = QualityIndicator(
        name=name,
        code=name.lower().replace(" ", "_"),
        indicator_type=QualityIndicatorType.PROCESS,
        numerator="count",
        denominator="total",
        direction=direction,
        target_value=target_value,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


class TestTerminologyService:
    def test_search_codes(self, db_session):
        _code(db_session, "A01", "Cholera")
        _code(db_session, "A02", "Typhoid")
        _items, total = clinical_service.TerminologyService.search_codes(db_session)
        assert total == 2
        _items, total = clinical_service.TerminologyService.search_codes(db_session, query="chol")
        assert total == 1 and _items[0].code == "A01"
        _items, total = clinical_service.TerminologyService.search_codes(
            db_session, system="ICD10", status="active"
        )
        assert total == 2
        _items, total = clinical_service.TerminologyService.search_codes(
            db_session, system="LOINC"
        )
        assert total == 0

    def test_get_code_and_delete(self, db_session):
        c = _code(db_session)
        assert clinical_service.TerminologyService.get_code(db_session, c.id).id == c.id
        assert clinical_service.TerminologyService.delete_code(db_session, c.id) is True
        assert clinical_service.TerminologyService.get_code(db_session, c.id) is None
        assert clinical_service.TerminologyService.delete_code(db_session, "missing") is False

    def test_create_update_code(self, db_session):
        c = clinical_service.TerminologyService.create_code(
            db_session, {"code": "X99", "display": "Unknown", "system": TerminologySystem.ICD10}
        )
        assert c.id and c.status == TerminologyStatus.ACTIVE
        updated = clinical_service.TerminologyService.update_code(db_session, c.id, {"display": "Updated"})
        assert updated.display == "Updated"
        assert clinical_service.TerminologyService.update_code(db_session, "missing", {}) is None

    def test_versions(self, db_session):
        clinical_service.TerminologyService.create_version(
            db_session, {"system": TerminologySystem.ICD10, "version": "2024"}
        )
        _items, total = clinical_service.TerminologyService.get_versions(db_session)
        assert total == 1 and _items[0].version == "2024"
        _items, total = clinical_service.TerminologyService.get_versions(db_session, system="LOINC")
        assert total == 0

    def test_mapping_requires_codes(self, db_session):
        src = _code(db_session, "S1")
        tgt = _code(db_session, "T1")
        mapping = clinical_service.TerminologyService.create_mapping(
            db_session,
            {
                "source_system": TerminologySystem.ICD10,
                "source_code_id": src.id,
                "target_system": TerminologySystem.SNOMED_CT,
                "target_code_id": tgt.id,
            },
        )
        assert mapping.id and mapping.mapping_relationship == "equivalent"

    def test_value_sets(self, db_session):
        c = _code(db_session)
        vs = clinical_service.TerminologyService.create_value_set(db_session, {"name": "Acute abdomen"})
        member = clinical_service.TerminologyService.create_value_set_member(
            db_session, {"value_set_id": vs.id, "code_id": c.id}
        )
        assert member.id
        _items, total = clinical_service.TerminologyService.get_value_sets(db_session, name="acute")
        assert total == 1
        _items, total = clinical_service.TerminologyService.get_value_sets(db_session, name="nope")
        assert total == 0

    def test_code_systems(self, db_session):
        clinical_service.TerminologyService.create_code_system(
            db_session, {"name": "ICD-10", "system": TerminologySystem.ICD10}
        )
        _items, total = clinical_service.TerminologyService.get_code_systems(db_session)
        assert total == 1

    def test_search_icd10(self, db_session):
        icd = ICD10Code(code="E11", short_description="Type 2 diabetes", long_description="...", chapter="Endocrine")
        db_session.add(icd)
        db_session.commit()
        _items, total = clinical_service.TerminologyService.search_icd10(db_session, query="diab")
        assert total == 1
        _items, total = clinical_service.TerminologyService.search_icd10(db_session, chapter="Endocrine")
        assert total == 1
        _items, total = clinical_service.TerminologyService.search_icd10(db_session, chapter="Cardio")
        assert total == 0

    def test_search_loinc(self, db_session):
        loinc = LOINCCode(loinc_num="2345-7", component="Glucose", long_common_name="Glucose [Mass/volume]")
        db_session.add(loinc)
        db_session.commit()
        _items, total = clinical_service.TerminologyService.search_loinc(db_session, query="gluc")
        assert total == 1
        _items, total = clinical_service.TerminologyService.search_loinc(db_session, query="gluc", class_name="CHEM")
        assert total == 0

    def test_search_snomed(self, db_session):
        sn = SNOMEDCTCode(concept_id="73211009", fully_specified_name="Diabetes mellitus")
        db_session.add(sn)
        db_session.commit()
        _items, total = clinical_service.TerminologyService.search_snomed(db_session, query="diabet")
        assert total == 1


class TestClinicalKnowledgeService:
    def test_guideline_crud(self, db_session):
        g = clinical_service.ClinicalKnowledgeService.create_guideline(
            db_session, {"title": "Sepsis care", "version": "1.0", "status": GuidelineStatus.DRAFT}
        )
        assert g.id
        assert clinical_service.ClinicalKnowledgeService.get_guideline(db_session, g.id).id == g.id
        updated = clinical_service.ClinicalKnowledgeService.update_guideline(
            db_session, g.id, {"status": GuidelineStatus.ACTIVE}
        )
        assert updated.status == GuidelineStatus.ACTIVE
        assert clinical_service.ClinicalKnowledgeService.update_guideline(db_session, "x", {}) is None
        assert clinical_service.ClinicalKnowledgeService.get_guideline(db_session, "x") is None

    def test_list_guidelines_filters(self, db_session):
        _guideline(db_session, "Sepsis", specialty="ICU")
        _guideline(db_session, "Stroke", status=GuidelineStatus.DRAFT, specialty="Neuro")
        _items, total = clinical_service.ClinicalKnowledgeService.list_guidelines(db_session)
        assert total == 2
        _items, total = clinical_service.ClinicalKnowledgeService.list_guidelines(db_session, status="active")
        assert total == 1
        _items, total = clinical_service.ClinicalKnowledgeService.list_guidelines(db_session, specialty="ICU")
        assert total == 1

    def test_protocol_crud(self, db_session):
        p = clinical_service.ClinicalKnowledgeService.create_protocol(
            db_session, {"title": "RRT", "version": "1.0", "department": "ICU"}
        )
        assert p.id
        updated = clinical_service.ClinicalKnowledgeService.update_protocol(db_session, p.id, {"title": "RRT v2"})
        assert updated.title == "RRT v2"
        _items, total = clinical_service.ClinicalKnowledgeService.list_protocols(db_session, department="ICU")
        assert total == 1
        _items, total = clinical_service.ClinicalKnowledgeService.list_protocols(db_session, department="ER")
        assert total == 0

    def test_pathway_crud(self, db_session):
        pw = clinical_service.ClinicalKnowledgeService.create_pathway(
            db_session, {"name": "MI pathway", "version": "1.0", "condition": "Myocardial infarction"}
        )
        assert pw.id
        updated = clinical_service.ClinicalKnowledgeService.update_pathway(db_session, pw.id, {"name": "MI v2"})
        assert updated.name == "MI v2"
        _items, total = clinical_service.ClinicalKnowledgeService.list_pathways(db_session, condition="infarct")
        assert total == 1

    def test_approval_and_standing_orders(self, db_session):
        g = _guideline(db_session)
        appr = clinical_service.ClinicalKnowledgeService.create_approval(
            db_session,
            {"guideline_id": g.id, "approver_id": "u1", "approver_name": "Dr. Ali", "decision": "approved"},
        )
        assert appr.id
        clinical_service.ClinicalKnowledgeService.create_standing_order(
            db_session, {"title": "CXR", "order_type": "radiology", "order_details": "chest x-ray", "department": "ICU"}
        )
        clinical_service.ClinicalKnowledgeService.create_standing_order(
            db_session, {"title": "Old", "order_type": "lab", "order_details": "x", "department": "ICU", "is_active": False}
        )
        _items, total = clinical_service.ClinicalKnowledgeService.list_standing_orders(db_session)
        assert total == 1
        _items, total = clinical_service.ClinicalKnowledgeService.list_standing_orders(db_session, active_only=False)
        assert total == 2
        _items, total = clinical_service.ClinicalKnowledgeService.list_standing_orders(db_session, department="ICU")
        assert total == 1

    def test_recommendations(self, db_session):
        g = _guideline(db_session)
        rec = ClinicalRecommendation(
            guideline_id=g.id, title="Antibiotics", text="Give within 1h", evidence_level=EvidenceLevel.IA
        )
        db_session.add(rec)
        db_session.commit()
        _items, total = clinical_service.ClinicalKnowledgeService.get_recommendations(db_session, guideline_id=g.id)
        assert total == 1
        _items, total = clinical_service.ClinicalKnowledgeService.get_recommendations(db_session, evidence_level="1a")
        assert total == 1
        _items, total = clinical_service.ClinicalKnowledgeService.get_recommendations(db_session, evidence_level="2b")
        assert total == 0


class TestCDSService:
    def test_order_set_recommendations(self, db_session):
        os_obj = OrderSet(name="Chest pain", version="1.0", department="ER", condition="Chest pain", is_active=True)
        db_session.add(os_obj)
        db_session.flush()
        db_session.add(
            OrderSetItem(order_set_id=os_obj.id, item_type="lab", item_code="TROP", item_display="Troponin", is_required=True)
        )
        db_session.add(OrderSet(name="Old", version="1.0", department="ER", is_active=False))
        db_session.commit()
        results = clinical_service.CDSService.get_order_set_recommendations(db_session)
        assert len(results) == 1 and results[0]["items"][0]["item_code"] == "TROP"
        results = clinical_service.CDSService.get_order_set_recommendations(db_session, condition="chest")
        assert len(results) == 1
        results = clinical_service.CDSService.get_order_set_recommendations(db_session, department="ICU")
        assert results == []

    def test_check_contraindications(self, db_session):
        db_session.add(
            Contraindication(
                subject_code="DRUG_A",
                subject_system="rxnorm",
                contraindicated_code="DRUG_B",
                contraindicated_system="rxnorm",
                contraindicated_display="Drug B",
                relationship_type="absolute",
                severity="high",
                is_active=True,
                is_absolute=True,
            )
        )
        db_session.add(
            Contraindication(
                subject_code="DRUG_A",
                subject_system="rxnorm",
                contraindicated_code="DRUG_C",
                contraindicated_system="rxnorm",
                relationship_type="absolute",
                severity="low",
                is_active=False,
            )
        )
        db_session.commit()
        results = clinical_service.CDSService.check_contraindications(
            db_session, subject_code="DRUG_A", subject_system="rxnorm"
        )
        assert len(results) == 1 and results[0]["contraindicated_code"] == "DRUG_B"
        assert results[0]["is_absolute"] is True
        assert clinical_service.CDSService.check_contraindications(
            db_session, subject_code="OTHER", subject_system="rxnorm"
        ) == []

    def test_check_duplicate_order(self, db_session):
        db_session.add(
            DuplicateOrderRule(
                order_code="CBC",
                rule_name="Duplicate CBC",
                time_window_hours=24,
                action="warn",
                severity="medium",
                notification_message="CBC ordered recently",
            )
        )
        db_session.add(
            DuplicateOrderRule(order_code="CBC", rule_name="Inactive", time_window_hours=24, action="warn", severity="low", is_active=False)
        )
        db_session.commit()
        alerts = clinical_service.CDSService.check_duplicate_order(db_session, patient_id="p1", order_code="CBC")
        assert len(alerts) == 1 and alerts[0]["time_window_hours"] == 24
        assert alerts[0]["notification_message"] == "CBC ordered recently"

    def test_check_drug_interactions(self, db_session):
        db_session.add(
            Contraindication(
                subject_code="WARF",
                subject_system="rxnorm",
                contraindicated_code="ASP",
                contraindicated_system="rxnorm",
                relationship_type="drug_interaction",
                severity="major",
                is_active=True,
                management="monitor INR",
            )
        )
        db_session.commit()
        meds = [{"code": "WARF", "name": "Warfarin"}, {"code": "ASP", "name": "Aspirin"}]
        results = clinical_service.CDSService.check_drug_interactions(db_session, medications=meds)
        assert len(results) == 1 and results[0]["severity"] == "major"
        assert results[0]["management"] == "monitor INR"
        unrelated = [{"code": "A"}, {"code": "B"}]
        assert clinical_service.CDSService.check_drug_interactions(db_session, medications=unrelated) == []

    def test_alerts_lifecycle(self, db_session):
        clinical_service.CDSService.create_alert(
            db_session, {"patient_id": "p1", "alert_type": "critical", "severity": "high", "title": "Alert", "message": "msg"}
        )
        clinical_service.CDSService.create_alert(
            db_session, {"patient_id": "p2", "alert_type": "critical", "severity": "high", "title": "Resolved", "message": "msg", "resolved": True}
        )
        _items, total = clinical_service.CDSService.get_active_alerts(db_session)
        assert total == 1
        _items, total = clinical_service.CDSService.get_active_alerts(db_session, patient_id="p1")
        assert total == 1
        _items, total = clinical_service.CDSService.get_active_alerts(db_session, patient_id="p2")
        assert total == 0

    def test_acknowledge_alert(self, db_session):
        alert = clinical_service.CDSService.create_alert(
            db_session, {"patient_id": "p1", "alert_type": "critical", "severity": "high", "title": "A", "message": "m"}
        )
        acked = clinical_service.CDSService.acknowledge_alert(db_session, alert.id, "u1")
        assert acked.acknowledged is True and acked.acknowledged_by == "u1"
        assert clinical_service.CDSService.acknowledge_alert(db_session, "missing", "u1") is None

    def test_patient_reminders(self, db_session):
        clinical_service.CDSService.create_alert(
            db_session, {"patient_id": "p1", "alert_type": "reminder", "severity": "low", "title": "Reminder", "message": "m"}
        )
        clinical_service.CDSService.create_alert(
            db_session, {"patient_id": "p1", "alert_type": "critical", "severity": "high", "title": "Not reminder", "message": "m"}
        )
        _items, total = clinical_service.CDSService.get_patient_reminders(db_session, patient_id="p1")
        assert total == 1

    def test_care_bundle_compliance(self, db_session):
        bundle = CareBundle(name="VAP bundle", version="1.0", compliance_threshold=80)
        db_session.add(bundle)
        db_session.flush()
        db_session.add_all(
            [
                CareBundleElement(care_bundle_id=bundle.id, element_code="E1", element_name="Elevation"),
                CareBundleElement(care_bundle_id=bundle.id, element_code="E2", element_name="Sedation hold"),
                CareBundleElement(care_bundle_id=bundle.id, element_code="E3", element_name="PUD"),
            ]
        )
        db_session.commit()
        result = clinical_service.CDSService.check_care_bundle_compliance(db_session, bundle_id=bundle.id, completed_elements=["E1", "E3"])
        assert result["compliance_percentage"] == 66.67
        assert result["met_target"] is False
        full = clinical_service.CDSService.check_care_bundle_compliance(db_session, bundle_id=bundle.id, completed_elements=["E1", "E2", "E3"])
        assert full["met_target"] is True and full["compliance_percentage"] == 100.0
        assert clinical_service.CDSService.check_care_bundle_compliance(db_session, bundle_id="x", completed_elements=[])["error"]

    def test_care_bundle_empty_elements(self, db_session):
        bundle = CareBundle(name="Empty", version="1.0")
        db_session.add(bundle)
        db_session.commit()
        result = clinical_service.CDSService.check_care_bundle_compliance(db_session, bundle_id=bundle.id, completed_elements=[])
        assert result["compliance_percentage"] == 100.0 and result["met_target"] is True


class TestQualityService:
    def test_indicator_crud_and_list(self, db_session):
        ind = clinical_service.QualityService.create_indicator(
            db_session,
            {
                "name": "Hand hygiene",
                "code": "hh",
                "indicator_type": QualityIndicatorType.PROCESS,
                "numerator": "a",
                "denominator": "b",
            },
        )
        assert ind.id
        _items, total = clinical_service.QualityService.list_indicators(db_session)
        assert total == 1
        _items, total = clinical_service.QualityService.list_indicators(db_session, indicator_type="process")
        assert total == 1
        _items, total = clinical_service.QualityService.list_indicators(db_session, indicator_type="outcome")
        assert total == 0

    def test_record_measurement_percentage_and_target(self, db_session):
        ind = _indicator(db_session, target_value=5.0, direction="lower_is_better")
        measurement = clinical_service.QualityService.record_measurement(
            db_session,
            {"indicator_id": ind.id, "measurement_date": date.today(), "numerator_value": 2.0, "denominator_value": 10.0},
        )
        assert measurement.percentage == 20.0
        assert measurement.met_target is False

    def test_record_measurement_meets_target(self, db_session):
        ind = _indicator(db_session, target_value=5.0, direction="lower_is_better")
        measurement = clinical_service.QualityService.record_measurement(
            db_session,
            {"indicator_id": ind.id, "measurement_date": date.today(), "numerator_value": 0.0, "denominator_value": 10.0},
        )
        assert measurement.percentage == 0.0
        assert measurement.met_target is True

    def test_audit_records(self, db_session):
        clinical_service.QualityService.create_audit_record(
            db_session,
            {"patient_id": "p1", "audit_type": "clinical", "audit_date": date.today(), "compliance": "pass", "department": "ICU"},
            audited_by="u1",
        )
        _items, total = clinical_service.QualityService.get_audit_records(db_session)
        assert total == 1 and _items[0].audited_by == "u1"
        _items, total = clinical_service.QualityService.get_audit_records(db_session, patient_id="p1", audit_type="clinical")
        assert total == 1
        _items, total = clinical_service.QualityService.get_audit_records(db_session, department="ER")
        assert total == 0

    def test_compliance_checks_and_dashboard(self, db_session):
        clinical_service.QualityService.create_compliance_check(
            db_session, {"check_type": "lab", "check_date": date.today(), "result": "pass", "standard": "ISO15189", "department": "Lab"}, checked_by="u1"
        )
        clinical_service.QualityService.create_compliance_check(
            db_session, {"check_type": "lab", "check_date": date.today(), "result": "fail", "standard": "ISO15189", "department": "Lab"}, checked_by="u1"
        )
        _items, total = clinical_service.QualityService.get_compliance_checks(db_session, standard="ISO")
        assert total == 2
        dash = clinical_service.QualityService.get_compliance_dashboard(db_session)
        assert dash["total_checks"] == 2 and dash["compliance_rate"] == 50.0
        dash_er = clinical_service.QualityService.get_compliance_dashboard(db_session, department="ER")
        assert dash_er["total_checks"] == 0 and dash_er["compliance_rate"] == 0.0

    def test_benchmarks(self, db_session):
        ind = _indicator(db_session)
        db_session.add(BenchmarkValue(indicator_id=ind.id, benchmark_name="National", value=90.0, year=2025))
        db_session.commit()
        _items, total = clinical_service.QualityService.get_benchmarks(db_session, indicator_id=ind.id, year=2025)
        assert total == 1
        _items, total = clinical_service.QualityService.get_benchmarks(db_session, year=2024)
        assert total == 0

    def test_mortality_incident_safety(self, db_session):
        m = clinical_service.QualityService.create_mortality_review(
            db_session, {"patient_id": "p1", "date_of_death": date.today(), "review_date": date.today()}, reviewer="u1"
        )
        assert m.id and m.reviewer == "u1"
        i = clinical_service.QualityService.create_incident_report(
            db_session, {"incident_type": "medication_error", "incident_date": datetime.now(UTC), "severity": "high"}, reporter_id="u1"
        )
        assert i.id and i.reporter_id == "u1"
        s = clinical_service.QualityService.create_safety_event(
            db_session, {"category": "fall", "event_type": "patient_fall", "event_date": datetime.now(UTC), "severity": "medium"}, reported_by="u1"
        )
        assert s.id and s.reported_by == "u1"

    def test_kpi_summary(self, db_session):
        ind = _indicator(db_session)
        clinical_service.QualityService.record_measurement(
            db_session,
            {"indicator_id": ind.id, "measurement_date": date.today(), "numerator_value": 1.0, "denominator_value": 4.0},
        )
        summary = clinical_service.QualityService.get_kpi_summary(db_session)
        assert len(summary) == 1
        assert summary[0]["latest_value"] == 25.0
        assert summary[0]["met_target"] is False
        assert summary[0]["target_value"] == 5.0


class TestResearchAndAI:
    def test_registries_stub_empty(self, db_session):
        _items, total = clinical_service.ResearchService.list_registries(db_session)
        assert _items == [] and total == 0
        _items, total = clinical_service.ResearchService.list_cohorts(db_session)
        assert _items == [] and total == 0

    def test_export_deidentified_stub(self, db_session):
        result = clinical_service.ResearchService.export_deidentified_dataset(db_session, cohort_id="c1")
        assert result["status"] == "stub" and result["format"] == "FHIR NDJSON"

    def test_ai_stubs(self, db_session):
        copilot = clinical_service.ClinicalAIService.clinical_copilot(
            db_session, patient_context={"age": 40, "gender": "M", "chief_complaint": "fever"}, clinical_findings=[]
        )
        assert copilot["status"] == "stub"
        risk = clinical_service.ClinicalAIService.predict_risk(db_session, patient_id="p1", risk_type="mortality", clinical_data={})
        assert risk["risk_level"] == "unknown"
        diag = clinical_service.ClinicalAIService.diagnostic_assistant(db_session, symptoms=[], findings=[], patient_context={})
        assert diag["possible_diagnoses"] == []
        expl = clinical_service.ClinicalAIService.get_explanation(db_session, recommendation_id="r1", recommendation_type="order")
        assert expl["status"] == "stub" and expl["evidence_sources"] == []

    def test_detect_care_gaps(self, db_session):
        db_session.add(
            PreventiveRecommendation(
                title="Colonoscopy", recommendation_type="screening", priority="high", evidence_level=EvidenceLevel.IA, is_active=True
            )
        )
        db_session.add(
            PreventiveRecommendation(
                title="Retired", recommendation_type="screening", priority="low", is_active=False
            )
        )
        db_session.commit()
        result = clinical_service.ClinicalAIService.detect_care_gaps(db_session, patient_id="p1", clinical_data={})
        assert result["status"] == "stub"
        assert len(result["care_gaps"]) == 1
        assert result["care_gaps"][0]["recommendation"] == "Colonoscopy"
        assert result["care_gaps"][0]["evidence_level"] == "1a"
