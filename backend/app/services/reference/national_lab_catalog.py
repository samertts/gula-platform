from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app._compat import UTC

logger = logging.getLogger("gula.reference.lab_catalog")


@dataclass
class SpecimenTypeDef:
    code: str = ""
    name: str = ""
    name_ar: str = ""
    description: str = ""
    container_type: str = ""
    collection_volume: str = ""
    is_active: bool = True


@dataclass
class ContainerDef:
    code: str = ""
    name: str = ""
    name_ar: str = ""
    description: str = ""
    material: str = ""
    additive: str = ""
    is_active: bool = True


@dataclass
class MethodDef:
    code: str = ""
    name: str = ""
    name_ar: str = ""
    description: str = ""
    instrument_type: str = ""
    is_active: bool = True


@dataclass
class InstrumentDef:
    code: str = ""
    name: str = ""
    manufacturer: str = ""
    model: str = ""
    method: str = ""
    is_active: bool = True


@dataclass
class ReferenceRangeDef:
    id: str = ""
    gender: str = "all"
    age_min: float | None = None
    age_max: float | None = None
    age_unit: str = "years"
    low: float | None = None
    high: float | None = None
    low_text: str = ""
    high_text: str = ""
    unit: str = ""
    text: str = ""
    is_critical: bool = False

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class CriticalValueDef:
    id: str = ""
    low: float | None = None
    high: float | None = None
    unit: str = ""
    text: str = ""
    response_required: bool = True

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class LOINCMapping:
    loinc_code: str = ""
    loinc_name: str = ""
    loinc_long_name: str = ""
    loinc_class: str = ""
    loinc_version: str = "2.77"


@dataclass
class CPTMapping:
    cpt_code: str = ""
    cpt_name: str = ""
    cpt_category: str = ""
    cpt_version: str = "2026"


@dataclass
class BillingCodeDef:
    code: str = ""
    name: str = ""
    amount: float = 0.0
    currency: str = "IQD"
    insurance_coverage: bool = False
    is_active: bool = True


@dataclass
class LabTestDefinition:
    id: str = ""
    code: str = ""
    name: str = ""
    name_ar: str = ""
    description: str = ""
    category: str = ""
    department: str = ""
    specimen_types: list[str] = field(default_factory=list)
    preferred_container: str = ""
    method: str = ""
    turnaround_time: str = ""
    unit: str = ""
    reference_ranges: list[ReferenceRangeDef] = field(default_factory=list)
    critical_values: list[CriticalValueDef] = field(default_factory=list)
    loinc: LOINCMapping | None = None
    cpt: CPTMapping | None = None
    billing: BillingCodeDef | None = None
    version: int = 1
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class PanelDefinition:
    id: str = ""
    code: str = ""
    name: str = ""
    name_ar: str = ""
    description: str = ""
    tests: list[str] = field(default_factory=list)
    version: int = 1
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


class NationalLaboratoryCatalog:
    def __init__(self):
        self._tests: dict[str, LabTestDefinition] = {}
        self._panels: dict[str, PanelDefinition] = {}
        self._specimen_types: dict[str, SpecimenTypeDef] = {}
        self._containers: dict[str, ContainerDef] = {}
        self._methods: dict[str, MethodDef] = {}
        self._instruments: dict[str, InstrumentDef] = {}
        self._code_index: dict[str, str] = {}
        self._loinc_index: dict[str, str] = {}

    def seed_common_tests(self) -> None:
        common_tests = [
            ("CBC", "Complete Blood Count", "تعداد الدم الكامل", "hematology", "HEMA"),
            ("HGB", "Hemoglobin", "الهيموغلوبين", "hematology", "HEMA"),
            ("WBC", "White Blood Cell Count", "تعداد خلايا الدم البيضاء", "hematology", "HEMA"),
            ("PLT", "Platelet Count", "تعداد الصفائح الدموية", "hematology", "HEMA"),
            ("RBC", "Red Blood Cell Count", "تعداد خلايا الدم الحمراء", "hematology", "HEMA"),
            ("HCT", "Hematocrit", "الهيماتوكريت", "hematology", "HEMA"),
            ("GLU", "Glucose", "الجلوكوز", "chemistry", "CHEM"),
            ("BUN", "Blood Urea Nitrogen", "نيتروجين يوريا الدم", "chemistry", "CHEM"),
            ("CRE", "Creatinine", "الكرياتينين", "chemistry", "CHEM"),
            ("NA", "Sodium", "الصوديوم", "chemistry", "CHEM"),
            ("K", "Potassium", "البوتاسيوم", "chemistry", "CHEM"),
            ("CL", "Chloride", "الكلوريد", "chemistry", "CHEM"),
            ("CA", "Calcium", "الكالسيوم", "chemistry", "CHEM"),
            ("TP", "Total Protein", "البروتين الكلي", "chemistry", "CHEM"),
            ("ALB", "Albumin", "الألبومين", "chemistry", "CHEM"),
            ("AST", "AST (SGOT)", "AST", "chemistry", "CHEM"),
            ("ALT", "ALT (SGPT)", "ALT", "chemistry", "CHEM"),
            ("ALP", "Alkaline Phosphatase", "الفوسفاتاز القلوي", "chemistry", "CHEM"),
            ("TBIL", "Total Bilirubin", "البيليروبين الكلي", "chemistry", "CHEM"),
            ("TSH", "TSH", "TSH", "immunology", "IMMU"),
            ("FT4", "Free T4", "T4 الحر", "immunology", "IMMU"),
            ("CRP", "C-Reactive Protein", "بروتين سي التفاعلي", "immunology", "IMMU"),
            ("ESR", "Erythrocyte Sedimentation Rate", "سرعة ترسيب الدم", "hematology", "HEMA"),
            ("PT", "Prothrombin Time", "زمن البروثرومبين", "hematology", "HEMA"),
            ("APTT", "Activated Partial Thromboplastin Time", "APTT", "hematology", "HEMA"),
            ("INR", "International Normalized Ratio", "INR", "hematology", "HEMA"),
            ("U/A", "Urinalysis", "تحليل البول", "chemistry", "CHEM"),
            ("U-CUL", "Urine Culture", "زراعة البول", "microbiology", "MICRO"),
            ("B-CUL", "Blood Culture", "زراعة الدم", "microbiology", "MICRO"),
        ]

        for code, name, name_ar, category, dept in common_tests:
            test = LabTestDefinition(
                code=code,
                name=name,
                name_ar=name_ar,
                category=category,
                department=dept,
                unit=self._guess_unit(code),
            )
            self.register_test(test)

        common_panels = [
            ("CBC-P", "CBC Panel", "CBC", ["CBC", "HGB", "WBC", "PLT", "RBC", "HCT"]),
            ("LFT", "Liver Function Test", "وظائف الكبد", ["TBIL", "AST", "ALT", "ALP", "TP", "ALB"]),
            ("RFT", "Renal Function Test", "وظائف الكلى", ["BUN", "CRE", "NA", "K", "CL", "CA"]),
        ]
        for pcode, pname, pname_ar, tests in common_panels:
            panel = PanelDefinition(
                code=pcode,
                name=pname,
                name_ar=pname_ar,
                tests=tests,
            )
            self.register_panel(panel)

        specimen_types = [
            ("BLOOD", "Blood", "دم", "EDTA tube", "5 mL"),
            ("SERUM", "Serum", "مصل", "Plain tube", "5 mL"),
            ("PLASMA", "Plasma", "بلازما", "Heparin tube", "5 mL"),
            ("URINE", "Urine", "بول", "Sterile container", "50 mL"),
            ("STOOL", "Stool", "براز", "Sterile container", "10 g"),
            ("CSF", "CSF", "سائل نخاعي", "Sterile tube", "2 mL"),
            ("SWAB", "Swab", "مسحة", "Transport medium", "1 swab"),
        ]
        for scode, sname, sname_ar, container, vol in specimen_types:
            self.register_specimen_type(SpecimenTypeDef(
                code=scode, name=sname, name_ar=sname_ar,
                container_type=container, collection_volume=vol,
            ))

        logger.info(
            "National Lab Catalog seeded: %d tests, %d panels, %d specimen types",
            len(self._tests), len(self._panels), len(self._specimen_types),
        )

    def _guess_unit(self, code: str) -> str:
        unit_map = {
            "HGB": "g/dL", "WBC": "cells/uL", "PLT": "cells/uL",
            "RBC": "cells/uL", "HCT": "%",
            "GLU": "mg/dL", "BUN": "mg/dL", "CRE": "mg/dL",
            "NA": "mEq/L", "K": "mEq/L", "CL": "mEq/L", "CA": "mg/dL",
            "TP": "g/dL", "ALB": "g/dL",
            "AST": "U/L", "ALT": "U/L", "ALP": "U/L",
            "TBIL": "mg/dL",
            "TSH": "mIU/mL", "FT4": "ng/mL",
            "CRP": "mg/dL", "ESR": "mm/hr",
            "PT": "sec", "APTT": "sec", "INR": "ratio",
        }
        return unit_map.get(code, "")

    def register_test(self, test: LabTestDefinition) -> LabTestDefinition:
        existing = self._tests.get(test.code)
        if existing:
            test.version = existing.version + 1
        self._tests[test.code] = test
        self._code_index[test.code] = test.id
        if test.loinc and test.loinc.loinc_code:
            self._loinc_index[test.loinc.loinc_code] = test.code
        return test

    def register_panel(self, panel: PanelDefinition) -> PanelDefinition:
        self._panels[panel.code] = panel
        return panel

    def register_specimen_type(self, spec: SpecimenTypeDef) -> SpecimenTypeDef:
        self._specimen_types[spec.code] = spec
        return spec

    def register_container(self, container: ContainerDef) -> ContainerDef:
        self._containers[container.code] = container
        return container

    def register_method(self, method: MethodDef) -> MethodDef:
        self._methods[method.code] = method
        return method

    def register_instrument(self, instrument: InstrumentDef) -> InstrumentDef:
        self._instruments[instrument.code] = instrument
        return instrument

    def get_test(self, code: str) -> LabTestDefinition | None:
        return self._tests.get(code)

    def get_panel(self, code: str) -> PanelDefinition | None:
        return self._panels.get(code)

    def get_by_loinc(self, loinc_code: str) -> LabTestDefinition | None:
        test_code = self._loinc_index.get(loinc_code)
        if test_code:
            return self._tests.get(test_code)
        return None

    def list_tests(self, category: str | None = None) -> list[LabTestDefinition]:
        if category:
            return [t for t in self._tests.values() if t.category == category]
        return list(self._tests.values())

    def list_panels(self) -> list[PanelDefinition]:
        return list(self._panels.values())

    def list_specimen_types(self) -> list[SpecimenTypeDef]:
        return list(self._specimen_types.values())

    def list_containers(self) -> list[ContainerDef]:
        return list(self._containers.values())

    def search_tests(self, query: str) -> list[LabTestDefinition]:
        q = query.lower()
        return [
            t for t in self._tests.values()
            if q in t.code.lower() or q in t.name.lower() or q in t.name_ar.lower()
        ]

    def count(self) -> dict[str, int]:
        return {
            "tests": len(self._tests),
            "panels": len(self._panels),
            "specimen_types": len(self._specimen_types),
            "containers": len(self._containers),
            "methods": len(self._methods),
            "instruments": len(self._instruments),
        }
