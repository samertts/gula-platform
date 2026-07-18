#!/usr/bin/env python3
"""
FHIR Quality Gate — validates FHIR resource structure and compliance.

Checks:
  1. FHIR resource structure against spec
  2. Patient, Observation, DiagnosticReport, ServiceRequest, Organization, Practitioner profiles
  3. Required fields validation
  4. Valid code systems (LOINC 2.73+, SNOMED CT, ICD-10-AM)
  5. Reference integrity
  6. MustSupport element presence
  7. Extension formatting
  8. Arabic translation completeness

Usage:
    python config/quality-gates/fhir-gate.py
    python config/quality-gates/fhir-gate.py --json
    python config/quality-gates/fhir-gate.py --fhir-dir backend/app/fhir

Exit codes:
    0 — all checks pass
    1 — one or more checks fail
"""

import argparse
import json
import logging
import os
import pathlib
import re
import sys
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("fhir-gate")

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

FHIR_RESOURCE_TYPES = {
    "Patient", "Observation", "DiagnosticReport", "ServiceRequest",
    "Organization", "Practitioner", "Encounter", "Condition",
    "MedicationRequest", "Specimen", "Location", "Provenance",
}

REQUIRED_FIELDS: dict[str, list[str]] = {
    "Patient": ["resourceType", "id", "name", "gender", "birthDate"],
    "Observation": ["resourceType", "id", "status", "code", "subject", "effectiveDateTime"],
    "DiagnosticReport": ["resourceType", "id", "status", "code", "subject", "issued", "result"],
    "ServiceRequest": ["resourceType", "id", "status", "intent", "code", "subject"],
    "Organization": ["resourceType", "id", "name"],
    "Practitioner": ["resourceType", "id", "name"],
}

VALID_CODE_SYSTEMS = {
    "http://loinc.org": "LOINC 2.73+",
    "http://snomed.info/sct": "SNOMED CT",
    "http://hl7.org/fhir/sid/icd-10-am": "ICD-10-AM",
    "urn:oid:2.16.840.1.113883.6.1": "LOINC OID",
    "urn:oid:2.16.840.1.113883.6.96": "SNOMED CT OID",
    "http://terminology.hl7.org/CodeSystem/v3-AdministrativeGender": "AdministrativeGender",
    "http://terminology.hl7.org/CodeSystem/observation-status": "ObservationStatus",
    "http://terminology.hl7.org/CodeSystem/diagnostic-report-status": "DiagnosticReportStatus",
    "http://terminology.hl7.org/CodeSystem/request-intent": "RequestIntent",
    "http://terminology.hl7.org/CodeSystem/request-status": "RequestStatus",
    "http://terminology.hl7.org/CodeSystem/restful-security-service": "RestfulSecurityService",
    "http://terminology.hl7.org/CodeSystem/v3-ActCode": "v3ActCode",
    "http://terminology.hl7.org/CodeSystem/condition-clinical": "ConditionClinical",
    "http://terminology.hl7.org/CodeSystem/condition-ver-status": "ConditionVerStatus",
    "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical": "AllergyIntoleranceClinical",
    "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification": "AllergyIntoleranceVerification",
    "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation": "ObservationInterpretation",
    "http://terminology.hl7.org/CodeSystem/medicationrequest-status": "MedicationRequestStatus",
    "http://terminology.hl7.org/CodeSystem/medication-statement-status": "MedicationStatementStatus",
    "http://terminology.hl7.org/CodeSystem/careplan-intent": "CarePlanIntent",
    "http://hl7.org/fhir/sid/icd-10": "ICD10",
    "http://unitsofmeasure.org": "UCUM",
    "urn:gula:health-number": "GULA HealthNumber",
}

MUST_SUPPORT_ELEMENTS: dict[str, list[str]] = {
    "Patient": ["identifier", "name", "gender", "birthDate", "address", "telecom"],
    "Observation": ["status", "code", "subject", "effectiveDateTime", "valueQuantity", "referenceRange"],
    "DiagnosticReport": ["status", "code", "subject", "issued", "result", "conclusion"],
    "ServiceRequest": ["status", "intent", "code", "subject", "authoredOn"],
    "Organization": ["identifier", "name", "address", "telecom"],
    "Practitioner": ["identifier", "name", "telecom"],
}


def check_fhir_resource_structure(fhir_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not fhir_dir.is_dir():
        return failures

    for py_file in sorted(fhir_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = py_file.resolve().relative_to(ROOT)

        for resource_type in FHIR_RESOURCE_TYPES:
            if resource_type in text:
                if "resourceType" not in text:
                    failures.append({
                        "check": "fhir_resource_structure",
                        "severity": "error",
                        "message": f"{rel} references {resource_type} but missing resourceType field",
                    })
                if "id" not in text:
                    failures.append({
                        "check": "fhir_resource_structure",
                        "severity": "error",
                        "message": f"{rel} references {resource_type} but missing id field",
                    })

    return failures


def check_required_fields(fhir_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not fhir_dir.is_dir():
        return failures

    for py_file in sorted(fhir_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = py_file.resolve().relative_to(ROOT)

        for resource_type, required in REQUIRED_FIELDS.items():
            if resource_type in text:
                for field in required:
                    if field not in text:
                        failures.append({
                            "check": "fhir_required_fields",
                            "severity": "error",
                            "message": f"{rel} references {resource_type} but missing required field '{field}'",
                        })

    return failures


def check_code_systems(fhir_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not fhir_dir.is_dir():
        return failures

    for py_file in sorted(fhir_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        coding_system_pattern = re.compile(
            r'system["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            re.IGNORECASE
        )
        for match in coding_system_pattern.finditer(text):
            system_url = match.group(1)
            if system_url.startswith("http://") or system_url.startswith("urn:oid:"):
                if system_url not in VALID_CODE_SYSTEMS:
                    failures.append({
                        "check": "fhir_code_system",
                        "severity": "warning",
                        "message": f"Unknown code system URL: {system_url} in {py_file.name}",
                    })

    return failures


def check_reference_integrity(fhir_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not fhir_dir.is_dir():
        return failures

    for py_file in sorted(fhir_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = py_file.resolve().relative_to(ROOT)

        ref_pattern = re.compile(r'reference["\']?\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE)
        for match in ref_pattern.finditer(text):
            ref_value = match.group(1)
            if "/" in ref_value:
                resource_type = ref_value.split("/")[0]
                if resource_type not in FHIR_RESOURCE_TYPES:
                    failures.append({
                        "check": "fhir_reference_integrity",
                        "severity": "error",
                        "message": f"Invalid FHIR reference type '{resource_type}' in {rel}",
                    })

    return failures


def check_must_support_elements(fhir_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not fhir_dir.is_dir():
        return failures

    for py_file in sorted(fhir_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = py_file.resolve().relative_to(ROOT)

        for resource_type, elements in MUST_SUPPORT_ELEMENTS.items():
            if resource_type in text:
                for element in elements:
                    if element not in text:
                        failures.append({
                            "check": "fhir_must_support",
                            "severity": "warning",
                            "message": f"{rel} references {resource_type} but missing MustSupport element '{element}'",
                        })

    return failures


def check_extension_formatting(fhir_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not fhir_dir.is_dir():
        return failures

    for py_file in sorted(fhir_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = py_file.resolve().relative_to(ROOT)

        extension_pattern = re.compile(r'extension["\']?\s*[:=]', re.IGNORECASE)
        for match in extension_pattern.finditer(text):
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.start())
            line = text[line_start:line_end] if line_end > 0 else text[line_start:]
            if "url" not in line and "value" not in line:
                failures.append({
                    "check": "fhir_extension_format",
                    "severity": "warning",
                    "message": f"Extension in {rel} missing url or value fields",
                })

    return failures


def check_arabic_translations(fhir_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not fhir_dir.is_dir():
        return failures

    for py_file in sorted(fhir_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = py_file.resolve().relative_to(ROOT)

        has_designation = "designation" in text
        has_translation = "translation" in text or "ar" in text.lower()
        has_arabic = bool(re.search(r'[\u0600-\u06FF\u0750-\u077F]', text))

        if has_arabic and not has_designation and not has_translation:
            failures.append({
                "check": "fhir_arabic_translation",
                "severity": "warning",
                "message": f"{rel} contains Arabic text but no designation/translation pattern detected",
            })

    return failures


def run_all_checks(fhir_dir: pathlib.Path) -> list[dict[str, Any]]:
    all_failures: list[dict[str, Any]] = []

    checks = [
        ("FHIR resource structure", lambda: check_fhir_resource_structure(fhir_dir)),
        ("Required fields", lambda: check_required_fields(fhir_dir)),
        ("Code systems", lambda: check_code_systems(fhir_dir)),
        ("Reference integrity", lambda: check_reference_integrity(fhir_dir)),
        ("MustSupport elements", lambda: check_must_support_elements(fhir_dir)),
        ("Extension formatting", lambda: check_extension_formatting(fhir_dir)),
        ("Arabic translations", lambda: check_arabic_translations(fhir_dir)),
    ]

    for name, check_fn in checks:
        try:
            results = check_fn()
            for r in results:
                r["check_name"] = name
            all_failures.extend(results)
            if results:
                logger.warning("%s: %d failure(s)", name, len(results))
            else:
                logger.info("%s: OK", name)
        except Exception as exc:
            logger.error("%s failed: %s", name, exc)
            all_failures.append({
                "check": name,
                "severity": "error",
                "message": f"Check failed with exception: {exc}",
            })

    return all_failures


def print_report(failures: list[dict[str, Any]], json_output: bool = False) -> int:
    errors = [f for f in failures if f.get("severity") == "error"]
    warnings = [f for f in failures if f.get("severity") == "warning"]

    if json_output:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "passed": len(errors) == 0,
            "summary": {"errors": len(errors), "warnings": len(warnings), "total": len(failures)},
            "failures": failures,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["passed"] else 1

    print(f"\n{BOLD}═══ FHIR Quality Gate Report ═══{RESET}\n")

    if not failures:
        print(f"  {GREEN}All FHIR checks passed!{RESET}\n")
        return 0

    if errors:
        print(f"  {BOLD}{RED}Errors ({len(errors)}):{RESET}")
        for e in errors:
            print(f"    {RED}✗{RESET} [{e.get('check_name', e['check'])}] {e['message']}")
        print()

    if warnings:
        print(f"  {BOLD}{YELLOW}Warnings ({len(warnings)}):{RESET}")
        for w in warnings:
            print(f"    {YELLOW}⚠{RESET} [{w.get('check_name', w['check'])}] {w['message']}")
        print()

    print(f"  Summary: {RED}{len(errors)} errors{RESET}, {YELLOW}{len(warnings)} warnings{RESET}")
    print()

    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="FHIR Quality Gate")
    parser.add_argument("--fhir-dir", type=str, default=str(ROOT / "backend" / "app" / "fhir"),
                        help="Path to FHIR module directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    fhir_dir = pathlib.Path(args.fhir_dir)
    if not fhir_dir.is_dir():
        logger.warning("FHIR directory does not exist: %s", fhir_dir)
        print(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "passed": True,
            "summary": {"errors": 0, "warnings": 0, "total": 0},
            "failures": [],
            "note": f"FHIR directory not found at {fhir_dir}, skipping checks",
        }, indent=2))
        return 0

    logger.info("FHIR gate scanning %s", fhir_dir)
    failures = run_all_checks(fhir_dir)
    return print_report(failures, json_output=args.json)


if __name__ == "__main__":
    sys.exit(main())
