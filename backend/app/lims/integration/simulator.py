"""Analyzer Simulator — generates realistic instrument messages for testing.

Supports ASTM, HL7, and FHIR format simulation with configurable
test profiles and error injection.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime
from typing import Any


# Test profiles: test_code -> (test_name, unit, low, high, precision)
TEST_PROFILES: dict[str, tuple[str, str, float, float, int]] = {
    "WBC": ("White Blood Cell Count", "10^3/uL", 4.0, 11.0, 1),
    "RBC": ("Red Blood Cell Count", "10^6/uL", 4.5, 5.9, 2),
    "HGB": ("Hemoglobin", "g/dL", 12.0, 16.0, 1),
    "HCT": ("Hematocrit", "%", 36.0, 48.0, 1),
    "MCV": ("Mean Corpuscular Volume", "fL", 80.0, 100.0, 1),
    "PLT": ("Platelet Count", "10^3/uL", 150, 450, 0),
    "GLU": ("Glucose", "mg/dL", 70, 110, 1),
    "CRE": ("Creatinine", "mg/dL", 0.6, 1.2, 2),
    "BUN": ("Blood Urea Nitrogen", "mg/dL", 7, 20, 1),
    "NA": ("Sodium", "mmol/L", 136, 145, 0),
    "K": ("Potassium", "mmol/L", 3.5, 5.1, 1),
    "CL": ("Chloride", "mmol/L", 98, 107, 0),
    "CA": ("Calcium", "mg/dL", 8.5, 10.5, 1),
    "TP": ("Total Protein", "g/dL", 6.0, 8.3, 1),
    "ALB": ("Albumin", "g/dL", 3.5, 5.0, 1),
    "TBIL": ("Total Bilirubin", "mg/dL", 0.1, 1.2, 2),
    "ALP": ("Alkaline Phosphatase", "U/L", 44, 147, 0),
    "ALT": ("ALT (SGPT)", "U/L", 10, 40, 0),
    "AST": ("AST (SGOT)", "U/L", 10, 40, 0),
    "LDH": ("Lactate Dehydrogenase", "U/L", 140, 280, 0),
    "CK": ("Creatine Kinase", "U/L", 55, 170, 0),
    "AMY": ("Amylase", "U/L", 28, 100, 0),
}


def generate_value(test_code: str, inject_error: bool = False) -> float:
    """Generate a realistic test value, optionally with error."""
    profile = TEST_PROFILES.get(test_code)
    if not profile:
        return round(random.gauss(100, 20), 1)

    _, _, low, high, precision = profile
    if inject_error:
        # Generate out-of-range value
        if random.random() < 0.5:
            return round(low - random.uniform(1, 5), precision)
        else:
            return round(high + random.uniform(1, 5), precision)

    mean = (low + high) / 2
    sd = (high - low) / 4
    return round(random.gauss(mean, sd), precision)


def generate_astm_message(
    specimen_barcode: str | None = None,
    test_codes: list[str] | None = None,
    inject_error: bool = False,
) -> str:
    """Generate a simulated ASTM E1394 result message."""
    if not specimen_barcode:
        specimen_barcode = f"SMP-{uuid.uuid4().hex[:8].upper()}"
    if not test_codes:
        test_codes = ["WBC", "RBC", "HGB", "HCT", "PLT"]

    seq = 1
    lines = [
        f"H|\\^&|||SIMULATOR|||||ASTM_E1394|{seq:04d}|",
        f"P|1|{specimen_barcode}|||SIM^PATIENT|||M|19800101",
    ]

    for i, tc in enumerate(test_codes, 1):
        profile = TEST_PROFILES.get(tc)
        if not profile:
            continue
        name, unit, low, high, _ = profile
        value = generate_value(tc, inject_error)
        ref_range = f"{low:.1f}-{high:.1f}"
        flag = "N"
        if inject_error and random.random() < 0.3:
            flag = "H" if value > high else "L"

        lines.append(f"O|{i}|{specimen_barcode}|{tc}|||")
        lines.append(f"R|{i}|{uuid.uuid4().hex[:8]}|{tc}|{name}|{value}|{unit}|{ref_range}|{flag}")

    lines.append(f"L|1|N")
    return "\r".join(lines)


def generate_hl7_message(
    specimen_barcode: str | None = None,
    patient_id: str | None = None,
    test_codes: list[str] | None = None,
    inject_error: bool = False,
) -> str:
    """Generate a simulated HL7 ORU^R01 message."""
    if not specimen_barcode:
        specimen_barcode = f"SMP-{uuid.uuid4().hex[:8].upper()}"
    if not patient_id:
        patient_id = f"PAT-{uuid.uuid4().hex[:6].upper()}"
    if not test_codes:
        test_codes = ["GLU", "CRE", "BUN", "NA", "K"]

    now = datetime.now().strftime("%Y%m%d%H%M%S")
    msg_id = uuid.uuid4().hex[:8]

    segments = [
        f"MSH|^~\\&|SIMULATOR|SIMLAB|LIS|LAB|{now}||ORU^R01|{msg_id}|P|2.5.1",
        f"PID|||{patient_id}||SIM^PATIENT||19800101|M",
        f"SPM|1|{specimen_barcode}||SER^Serum",
        f"OBR|1|{specimen_barcode}^SIM|{msg_id}^SIM|GLU^Glucose|||{now}",
    ]

    for tc in test_codes:
        profile = TEST_PROFILES.get(tc)
        if not profile:
            continue
        name, unit, low, high, precision = profile
        value = generate_value(tc, inject_error)
        ref_range = f"{low:.1f}-{high:.1f}"
        flag = ""
        if value > high:
            flag = "H"
        elif value < low:
            flag = "L"

        segments.append(
            f"OBX|1|NM|{tc}^{name}||{value}|{unit}|{ref_range}|{flag}|||F"
        )

    segments.append(f"OBR|2|{specimen_barcode}")
    return "\r".join(segments)
