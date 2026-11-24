#!/usr/bin/env python3
"""GLOSI registry validator and exporter (Python stdlib only)."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

WEIGHTS = {
    "functionality_fit": 15,
    "maturity_stability": 15,
    "security_privacy": 15,
    "interoperability": 15,
    "engineering_quality": 10,
    "license_sustainability": 10,
    "reliability_scalability": 10,
    "cost_maintenance": 5,
    "iraqi_context": 5,
}
BANDS = {
    "excellent": [90, 100],
    "strong_candidate": [80, 89],
    "needs_verification": [70, 79],
    "limited_study": [60, 69],
    "not_recommended": [0, 59],
}
CATEGORIES = {
    "A_health_systems",
    "B_laboratory",
    "C_public_health",
    "D_standards_interoperability",
    "E_identity_security_privacy",
    "F_infrastructure_reliability",
    "G_artificial_intelligence",
    "H_government_national",
}
SOURCE_TYPES = {
    "open_source_repository",
    "library_framework",
    "research_paper",
    "systematic_review",
    "clinical_study",
    "technical_documentation",
    "international_standard",
    "government_implementation",
    "national_program",
    "security_advisory",
    "benchmark",
    "case_study",
    "dataset",
    "simulation_environment",
}
DECISIONS = {"ADOPT", "INTEGRATE", "ADAPT", "REIMPLEMENT", "STUDY", "MONITOR", "REJECT"}
DECISION_STATUS = {"PROPOSED", "APPROVED", "REJECTED", "DEFERRED", "SUPERSEDED"}
EVAL_STATUS = {"NOT_EVALUATED", "PARTIAL", "COMPLETE"}
CONFIDENCE = {"LOW", "MEDIUM", "HIGH"}
LICENSE_REVIEW = {"NOT_REVIEWED", "IN_REVIEW", "REVIEWED", "BLOCKED"}
SECURITY_REVIEW = {"NOT_REVIEWED", "IN_REVIEW", "REVIEWED", "CLEARED", "BLOCKED"}
ID_RE = re.compile(r"^GLOSI-\d{4}$")
DECISION_ID_RE = re.compile(r"^GLOSI-DEC-\d{4}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TOP_KEYS = {"schema_version", "program", "updated", "scoring_model", "records"}
RECORD_SECTIONS = ("identity", "technical", "legal", "security", "operational", "gula", "evaluation", "decision", "evaluation_history")


class RegistryError(Exception):
    """Raised when the registry is structurally or semantically invalid."""


def _is_num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _date_ok(value: Any) -> bool:
    if not isinstance(value, str) or not DATE_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _url_ok(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("https://") and len(value) > len("https://")


def _require(errors: list[str], cond: bool, label: str, message: str) -> None:
    if not cond:
        errors.append(f"{label}: {message}")


def _check_str(errors: list[str], label: str, value: Any, *, allow_empty: bool = False) -> None:
    _require(errors, isinstance(value, str) and (allow_empty or bool(value.strip())), label, "must be a non-empty string")


def _check_str_list(errors: list[str], label: str, value: Any) -> None:
    _require(errors, isinstance(value, list) and all(isinstance(v, str) for v in value), label, "must be an array of strings")


def _check_section(errors: list[str], record: dict, name: str) -> dict:
    section = record.get(name)
    _require(errors, isinstance(section, dict), name, "must be an object")
    return section if isinstance(section, dict) else {}


def _expected_band(score: float) -> str:
    for name, (low, high) in BANDS.items():
        if low <= score <= high:
            return name
    raise AssertionError(f"score out of range: {score}")


def _weighted(dimensions: dict) -> float:
    return sum(dimensions[key]["score"] * weight for key, weight in WEIGHTS.items()) / 100.0


def _validate_identity(errors: list[str], record: dict, label: str) -> None:
    sec = _check_section(errors, record, "identity")
    for key in (
        "registry_id", "name", "category", "subcategory", "description",
        "official_url", "source_type", "organization", "country",
        "first_release", "last_verified",
    ):
        _check_str(errors, f"{label}.identity.{key}", sec.get(key))
    _require(errors, bool(ID_RE.match(str(sec.get("registry_id", "")))), label, "identity.registry_id must match GLOSI-NNNN")
    _require(errors, sec.get("category") in CATEGORIES, label, "identity.category is not an approved category")
    _require(errors, sec.get("source_type") in SOURCE_TYPES, label, "identity.source_type is not approved")
    _require(errors, _url_ok(sec.get("official_url")), label, "identity.official_url must be https")
    _require(errors, _date_ok(sec.get("last_verified")), label, "identity.last_verified must be YYYY-MM-DD")
    verification = sec.get("verification")
    _require(errors, isinstance(verification, dict), label, "identity.verification must be an object")
    if isinstance(verification, dict):
        for key in ("method", "repository", "evidence_url", "release_source", "retrieved_at"):
            _check_str(errors, f"{label}.identity.verification.{key}", verification.get(key))
        _require(errors, _url_ok(verification.get("evidence_url")), label, "identity.verification.evidence_url must be https")
        _require(errors, isinstance(verification.get("archived"), bool), label, "identity.verification.archived must be boolean")
        _check_str(errors, f"{label}.identity.verification.pushed_at", verification.get("pushed_at"))


def _validate_technical(errors: list[str], record: dict, label: str) -> None:
    sec = _check_section(errors, record, "technical")
    for key in (
        "architecture", "offline_capabilities", "scalability", "hardware_requirements",
        "dependencies", "latest_verified_version",
    ):
        _check_str(errors, f"{label}.technical.{key}", sec.get(key))
    for key in (
        "languages", "frameworks", "database_support", "api_support",
        "interoperability_standards", "deployment_options",
    ):
        _check_str_list(errors, f"{label}.technical.{key}", sec.get(key))


def _validate_legal(errors: list[str], record: dict, label: str) -> None:
    sec = _check_section(errors, record, "legal")
    for key in (
        "license", "license_compatibility", "commercial_use_permission",
        "modification_permission", "redistribution_permission", "attribution_requirements",
        "copyleft_obligations", "patent_trademark_considerations",
        "data_licensing_restrictions",
    ):
        _check_str(errors, f"{label}.legal.{key}", sec.get(key))
    _require(errors, sec.get("review_status") in LICENSE_REVIEW, label, "legal.review_status is invalid")
    _require(errors, _url_ok(sec.get("license_evidence_url")), label, "legal.license_evidence_url must be https")


def _validate_security(errors: list[str], record: dict, label: str) -> None:
    sec = _check_section(errors, record, "security")
    for key in (
        "security_policy", "vulnerability_disclosure", "known_cves", "dependency_risks",
        "authentication_model", "authorization_model", "encryption", "audit_logging",
        "sbom_availability", "maintenance_activity",
    ):
        _check_str(errors, f"{label}.security.{key}", sec.get(key))
    _require(errors, sec.get("security_review_status") in SECURITY_REVIEW, label, "security.security_review_status is invalid")


def _validate_operational(errors: list[str], record: dict, label: str) -> None:
    sec = _check_section(errors, record, "operational")
    for key in (
        "production_usage_evidence", "deployment_scale", "community_health", "release_frequency",
        "maintainer_responsiveness", "documentation_quality", "test_coverage", "ci_status",
        "backup_recovery", "upgrade_migration_complexity",
    ):
        _check_str(errors, f"{label}.operational.{key}", sec.get(key))


def _validate_gula(errors: list[str], record: dict, label: str) -> None:
    sec = _check_section(errors, record, "gula")
    for key in (
        "domain", "component", "architecture_layer", "integration_possibility",
        "required_adapter", "required_api", "required_changes", "dependencies_on_gula",
        "conflicts_with_existing_components", "estimated_integration_cost",
        "expected_benefits", "operational_risks",
    ):
        _check_str(errors, f"{label}.gula.{key}", sec.get(key))


def _validate_evaluation(errors: list[str], record: dict, label: str) -> None:
    sec = _check_section(errors, record, "evaluation")
    status = sec.get("status")
    _require(errors, status in EVAL_STATUS, label, "evaluation.status is invalid")
    _require(errors, sec.get("confidence") in CONFIDENCE, label, "evaluation.confidence is invalid")
    dimensions = sec.get("dimensions")
    _require(errors, isinstance(dimensions, dict), label, "evaluation.dimensions must be an object")
    if not isinstance(dimensions, dict):
        return
    _require(errors, set(dimensions) == set(WEIGHTS), label, "evaluation.dimensions must contain exactly the approved dimensions")
    numeric = 0
    for key, _weight in WEIGHTS.items():
        dim = dimensions.get(key)
        if not isinstance(dim, dict):
            errors.append(f"{label}.evaluation.dimensions.{key}: must be an object")
            continue
        if "score" not in dim or "evidence" not in dim:
            errors.append(f"{label}.evaluation.dimensions.{key}: score and evidence are required")
            continue
        score = dim["score"]
        evidence = dim["evidence"]
        _require(errors, isinstance(evidence, list) and all(isinstance(e, str) for e in evidence), label, f"evaluation.dimensions.{key}.evidence must be an array of strings")
        if score is None:
            continue
        _require(errors, _is_num(score) and 0 <= score <= 100, label, f"evaluation.dimensions.{key}.score must be null or 0-100")
        if _is_num(score):
            numeric += 1
            _require(errors, bool(evidence), label, f"evaluation.dimensions.{key}: a numeric score requires evidence")
    weighted_total = sec.get("weighted_total")
    band = sec.get("band")
    if status == "COMPLETE":
        _require(errors, numeric == len(WEIGHTS), label, "COMPLETE evaluation requires a numeric score for every dimension")
        if numeric == len(WEIGHTS):
            computed = round(_weighted(dimensions), 2)
            _require(errors, _is_num(weighted_total) and abs(float(weighted_total) - computed) <= 0.5, label, "weighted_total does not match dimension scores")
            expected = _expected_band(computed)
            _require(errors, band == expected, label, f"band must be {expected}")
    else:
        _require(errors, weighted_total is None, label, "non-COMPLETE evaluation must not have weighted_total")
        _require(errors, band is None, label, "non-COMPLETE evaluation must not have a band")
    _check_str(errors, f"{label}.evaluation.evaluated_version", sec.get("evaluated_version"))
    _require(errors, _date_ok(sec.get("evaluated_at")), label, "evaluation.evaluated_at must be YYYY-MM-DD")
    _check_str(errors, f"{label}.evaluation.notes", sec.get("notes"), allow_empty=True)


def _validate_decision(errors: list[str], record: dict, label: str) -> None:
    sec = _check_section(errors, record, "decision")
    for key in ("decision_id", "decision", "status", "date", "owner", "rationale"):
        _check_str(errors, f"{label}.decision.{key}", sec.get(key))
    _require(errors, bool(DECISION_ID_RE.match(str(sec.get("decision_id", "")))), label, "decision.decision_id must match GLOSI-DEC-NNNN")
    _require(errors, sec.get("decision") in DECISIONS, label, "decision.decision is invalid")
    _require(errors, sec.get("status") in DECISION_STATUS, label, "decision.status is invalid")
    _require(errors, _date_ok(sec.get("date")), label, "decision.date must be YYYY-MM-DD")
    reviewers = sec.get("reviewers")
    _require(errors, isinstance(reviewers, dict) and set(reviewers) >= {"technical", "security", "legal"}, label, "decision.reviewers must include technical/security/legal")
    evidence = sec.get("evidence")
    _require(errors, isinstance(evidence, list) and all(isinstance(e, str) for e in evidence) and bool(evidence), label, "decision.evidence must be a non-empty array of strings")
    adr = sec.get("adr_reference")
    _require(errors, adr is None or isinstance(adr, str), label, "decision.adr_reference must be string or null")
    if sec.get("status") == "APPROVED":
        evaluation = record.get("evaluation") or {}
        legal = record.get("legal") or {}
        security = record.get("security") or {}
        _require(errors, evaluation.get("status") == "COMPLETE", label, "APPROVED requires a COMPLETE evaluation")
        _require(errors, legal.get("license") != "UNKNOWN", label, "APPROVED requires a known license")
        _require(errors, legal.get("review_status") == "REVIEWED", label, "APPROVED requires legal review")
        _require(errors, security.get("security_review_status") in {"REVIEWED", "CLEARED"}, label, "APPROVED requires security review")
        _require(errors, isinstance(reviewers, dict) and all(isinstance(v, str) and v != "UNASSIGNED" for v in reviewers.values()), label, "APPROVED requires named reviewers")
        _require(errors, isinstance(adr, str) and bool(adr.strip()), label, "APPROVED requires an ADR reference")
    if sec.get("decision") in {"ADOPT", "INTEGRATE", "ADAPT"}:
        legal = record.get("legal") or {}
        security = record.get("security") or {}
        _require(errors, legal.get("license") != "UNKNOWN", label, "adoption requires a known license")
        _require(errors, legal.get("license_compatibility") != "INCOMPATIBLE", label, "adoption blocked by incompatible license")
        _require(errors, security.get("security_review_status") != "BLOCKED", label, "adoption blocked by critical security finding")


def _validate_history(errors: list[str], record: dict, label: str, evaluation_status: str) -> None:
    history = record.get("evaluation_history")
    _require(errors, isinstance(history, list), label, "evaluation_history must be an array")
    if not isinstance(history, list):
        return
    if evaluation_status in {"PARTIAL", "COMPLETE"}:
        _require(errors, bool(history), label, "PARTIAL/COMPLETE records require evaluation_history")
    for index, entry in enumerate(history):
        prefix = f"{label}.evaluation_history[{index}]"
        _require(errors, isinstance(entry, dict), prefix, "must be an object")
        if not isinstance(entry, dict):
            continue
        _require(errors, _date_ok(entry.get("date")), prefix, "date must be YYYY-MM-DD")
        _check_str(errors, f"{prefix}.version", entry.get("version"))
        _require(errors, entry.get("evaluation_status") in EVAL_STATUS, prefix, "evaluation_status is invalid")
        _check_str(errors, f"{prefix}.summary", entry.get("summary"))
        refs = entry.get("evidence_refs")
        _require(errors, isinstance(refs, list) and all(isinstance(r, str) and r for r in refs), prefix, "evidence_refs must be a non-empty array of strings")


def validate_registry(data: dict) -> list[str]:
    errors: list[str] = []
    _require(errors, isinstance(data, dict), "registry", "must be an object")
    if not isinstance(data, dict):
        return errors
    _require(errors, set(data) == TOP_KEYS, "registry", f"top-level keys must be exactly {sorted(TOP_KEYS)}")
    _require(errors, data.get("schema_version") == "1.0.0", "registry", "schema_version must be 1.0.0")
    _require(errors, data.get("program") == "GLOSI", "registry", "program must be GLOSI")
    _require(errors, _date_ok(data.get("updated")), "registry", "updated must be YYYY-MM-DD")
    model = data.get("scoring_model")
    _require(errors, isinstance(model, dict), "registry", "scoring_model must be an object")
    if isinstance(model, dict):
        _require(errors, model.get("weights") == WEIGHTS, "registry", "scoring weights differ from the approved framework")
        _require(errors, model.get("bands") == BANDS, "registry", "scoring bands differ from the approved framework")
    records = data.get("records")
    _require(errors, isinstance(records, list) and bool(records), "registry", "records must be a non-empty array")
    if not isinstance(records, list):
        return errors
    ids: set[str] = set()
    decision_ids: set[str] = set()
    for index, record in enumerate(records):
        label = f"records[{index}]"
        _require(errors, isinstance(record, dict), label, "must be an object")
        if not isinstance(record, dict):
            continue
        missing = [section for section in RECORD_SECTIONS if section not in record]
        _require(errors, not missing, label, f"missing sections: {missing}")
        identity = record.get("identity") or {}
        rid = identity.get("registry_id") if isinstance(identity, dict) else None
        label = f"{rid or label}"
        _validate_identity(errors, record, label)
        _validate_technical(errors, record, label)
        _validate_legal(errors, record, label)
        _validate_security(errors, record, label)
        _validate_operational(errors, record, label)
        _validate_gula(errors, record, label)
        _validate_evaluation(errors, record, label)
        _validate_decision(errors, record, label)
        evaluation = record.get("evaluation") or {}
        status = evaluation.get("status") if isinstance(evaluation, dict) else ""
        _validate_history(errors, record, label, status)
        if isinstance(rid, str):
            _require(errors, rid not in ids, label, "duplicate registry_id")
            ids.add(rid)
        decision = record.get("decision") or {}
        did = decision.get("decision_id") if isinstance(decision, dict) else None
        if isinstance(did, str):
            _require(errors, did not in decision_ids, label, "duplicate decision_id")
            decision_ids.add(did)
    return errors


def load_registry(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def canonical_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def export_registry(path: str | Path, out: str | Path | None = None) -> str:
    data = load_registry(path)
    errors = validate_registry(data)
    if errors:
        raise RegistryError("\n".join(errors))
    payload = canonical_json(data)
    if out is not None:
        Path(out).write_text(payload, encoding="utf-8")
    return payload


def _deep_merge(target: dict, patch: dict) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def update_record(
    registry: dict,
    registry_id: str,
    patch: dict,
    *,
    update_date: str,
    summary: str,
    evidence_refs: list[str],
) -> dict:
    """Apply a patch while retaining evaluation history."""
    if not _date_ok(update_date):
        raise RegistryError("update_date must be YYYY-MM-DD")
    if not summary.strip() or not evidence_refs:
        raise RegistryError("summary and evidence_refs are required")
    record = next((r for r in registry.get("records", []) if r.get("identity", {}).get("registry_id") == registry_id), None)
    if record is None:
        raise RegistryError(f"unknown registry_id: {registry_id}")
    before = record.get("evaluation", {})
    _deep_merge(record, patch)
    evaluation = record.get("evaluation", {})
    record.setdefault("evaluation_history", []).append(
        {
            "date": update_date,
            "version": evaluation.get("evaluated_version", "UNKNOWN"),
            "evaluation_status": evaluation.get("status", before.get("status", "UNKNOWN")),
            "summary": summary,
            "evidence_refs": list(evidence_refs),
        }
    )
    registry["updated"] = update_date
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GLOSI registry validator/exporter")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a registry file")
    validate.add_argument("path")

    export = sub.add_parser("export", help="validate and export canonical JSON")
    export.add_argument("path")
    export.add_argument("--out")

    summary = sub.add_parser("summary", help="print registry counts")
    summary.add_argument("path")

    args = parser.parse_args(argv)
    try:
        data = load_registry(args.path)
        errors = validate_registry(data)
        if args.command == "validate":
            if errors:
                print(f"FAIL {args.path} ({len(errors)} errors)")  # noqa: T201
                for error in errors:
                    print(f"  - {error}")  # noqa: T201
                return 1
            print(f"PASS {args.path} records={len(data['records'])}")  # noqa: T201
            return 0
        if args.command == "summary":
            if errors:
                print(f"FAIL {len(errors)} errors")  # noqa: T201
                return 1
            proposed = sum(1 for r in data["records"] if r["decision"]["status"] == "PROPOSED")
            print(f"records={len(data['records'])} proposed={proposed} updated={data['updated']}")  # noqa: T201
            return 0
        payload = export_registry(args.path, args.out)
        print(f"PASS exported {len(payload.encode('utf-8'))} bytes" + (f" to {args.out}" if args.out else ""))  # noqa: T201
        if args.out is None:
            sys.stdout.write(payload)
        return 0
    except (OSError, json.JSONDecodeError, RegistryError) as exc:
        print(f"FAIL {exc}")  # noqa: T201
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
