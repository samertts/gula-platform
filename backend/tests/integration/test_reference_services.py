from __future__ import annotations

import pytest
from app.services.reference.master_reference_data import (
    MasterReferenceDataService,
    ReferenceDataType,
    ReferenceEntry,
)
from app.services.reference.national_lab_catalog import (
    LabTestDefinition,
    LOINCMapping,
    NationalLaboratoryCatalog,
    PanelDefinition,
    SpecimenTypeDef,
)
from app.services.reference.universal_identifier import (
    IdentifierType,
    UniversalIdentifierService,
)


class TestMasterReferenceData:
    def test_seed_defaults(self):
        svc = MasterReferenceDataService()
        svc.seed_defaults()
        assert svc.count() > 0
        assert svc.get(ReferenceDataType.COUNTRY, "IQ") is not None
        assert svc.get(ReferenceDataType.GOVERNORATE, "BG") is not None
        assert svc.get(ReferenceDataType.LANGUAGE, "ar") is not None

    def test_upsert_and_get(self):
        svc = MasterReferenceDataService()
        entry = ReferenceEntry(code="TEST", name="Test", type="test_type")
        svc.upsert(entry)
        assert svc.get("test_type", "TEST") is entry

    def test_list_by_type(self):
        svc = MasterReferenceDataService()
        svc.seed_defaults()
        countries = svc.list_by_type(ReferenceDataType.COUNTRY)
        assert len(countries) >= 1
        assert any(c.code == "IQ" for c in countries)

    def test_list_by_parent(self):
        svc = MasterReferenceDataService()
        svc.seed_defaults()
        iraq_children = svc.list_by_parent("IQ")
        assert len(iraq_children) > 0

    def test_version_increment(self):
        svc = MasterReferenceDataService()
        e1 = ReferenceEntry(code="VER", name="v1", type="version_test")
        svc.upsert(e1)
        assert e1.version == 1
        e2 = ReferenceEntry(code="VER", name="v2", type="version_test")
        svc.upsert(e2)
        assert e2.version == 2

    def test_export_all(self):
        svc = MasterReferenceDataService()
        svc.seed_defaults()
        export = svc.export_all()
        assert "country" in export
        assert "governorate" in export
        assert len(export) > 0


class TestUniversalIdentifier:
    def test_generate_uuid_format(self):
        svc = UniversalIdentifierService()
        hnum = svc.generate(IdentifierType.HEALTH_NUMBER)
        assert hnum.startswith("HN-")
        assert svc.validate(hnum) is True

    def test_generate_sequential(self):
        svc = UniversalIdentifierService()
        id1 = svc.generate(IdentifierType.LAB_ORDER, format="sequential")
        id2 = svc.generate(IdentifierType.LAB_ORDER, format="sequential")
        assert id1 != id2
        assert id1.startswith("ORD-")

    def test_generate_hash_format(self):
        svc = UniversalIdentifierService()
        hnum = svc.generate(IdentifierType.HEALTH_NUMBER, format="hash", seed="test123")
        assert hnum.startswith("HN-")
        assert len(hnum) > 5

    def test_generate_with_tenant(self):
        svc = UniversalIdentifierService()
        ident = svc.generate(IdentifierType.SPECIMEN, tenant_id="LAB001")
        assert "LAB001" in ident
        assert ident.startswith("SPC-")

    def test_generate_different_types(self):
        svc = UniversalIdentifierService()
        types = [
            (IdentifierType.HEALTH_NUMBER, "HN-"),
            (IdentifierType.LAB_ORDER, "ORD-"),
            (IdentifierType.SPECIMEN, "SPC-"),
            (IdentifierType.REPORT, "RPT-"),
            (IdentifierType.VISIT, "VIS-"),
            (IdentifierType.ENCOUNTER, "ENC-"),
            (IdentifierType.APPOINTMENT, "APT-"),
            (IdentifierType.INVOICE, "INV-"),
            (IdentifierType.NOTIFICATION, "NTF-"),
            (IdentifierType.WORKFLOW, "WF-"),
            (IdentifierType.AUDIT_EVENT, "AUD-"),
        ]
        for id_type, prefix in types:
            ident = svc.generate(id_type)
            assert ident.startswith(prefix), f"{ident} should start with {prefix}"

    def test_prefix(self):
        svc = UniversalIdentifierService()
        assert svc.get_prefix(IdentifierType.HEALTH_NUMBER) == "HN"
        assert svc.get_prefix(IdentifierType.LAB_ORDER) == "ORD"


class TestNationalLabCatalog:
    def test_seed_common_tests(self):
        catalog = NationalLaboratoryCatalog()
        catalog.seed_common_tests()
        counts = catalog.count()
        assert counts["tests"] >= 20
        assert counts["panels"] >= 2
        assert counts["specimen_types"] >= 5

    def test_register_and_get_test(self):
        catalog = NationalLaboratoryCatalog()
        test = LabTestDefinition(code="XYZ", name="Test XYZ", name_ar="اختبار", category="chemistry")
        catalog.register_test(test)
        assert catalog.get_test("XYZ") is test

    def test_search_tests(self):
        catalog = NationalLaboratoryCatalog()
        catalog.seed_common_tests()
        results = catalog.search_tests("glucose")
        assert len(results) >= 1
        assert any("GLU" in r.code for r in results)

    def test_register_panel(self):
        catalog = NationalLaboratoryCatalog()
        panel = PanelDefinition(code="MET", name="Metabolic Panel", tests=["GLU", "BUN", "CRE"])
        catalog.register_panel(panel)
        assert catalog.get_panel("MET") is panel

    def test_specimen_types(self):
        catalog = NationalLaboratoryCatalog()
        catalog.seed_common_tests()
        types = catalog.list_specimen_types()
        assert len(types) > 0
        assert any(s.code == "BLOOD" for s in types)

    def test_loinc_mapping(self):
        catalog = NationalLaboratoryCatalog()
        test = LabTestDefinition(
            code="GLU",
            name="Glucose",
            loinc=LOINCMapping(loinc_code="2345-7", loinc_name="Glucose"),
        )
        catalog.register_test(test)
        found = catalog.get_by_loinc("2345-7")
        assert found is not None
        assert found.code == "GLU"
