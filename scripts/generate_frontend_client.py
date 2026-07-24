"""Frontend client generator — produces TypeScript types + API client from backend.

Usage:
    python scripts/generate_frontend_client.py

Output:
    frontend-v3/src/api/generated/types.ts    — All backend model types
    frontend-v3/src/api/generated/client.ts    — Typed API client with React Query hooks
    frontend-v3/src/api/generated/index.ts     — Barrel exports
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend" / "app"
FRONTEND_DIR = PROJECT_ROOT / "frontend-v3" / "src" / "api" / "generated"

# Type mapping: Python type -> TypeScript type
TYPE_MAP: dict[str, str] = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "bytes": "string",
    "datetime": "string",
    "date": "string",
    "UUID": "string",
    "Decimal": "number",
    "Any": "unknown",
    "Optional[str]": "string | null",
    "Optional[int]": "number | null",
    "Optional[float]": "number | null",
    "Optional[bool]": "boolean | null",
    "Optional[datetime]": "string | null",
    "Optional[dict]": "Record<string, unknown> | null",
    "Optional[list]": "unknown[] | null",
    "dict[str, Any]": "Record<string, unknown>",
    "dict[str, str]": "Record<string, string>",
    "list[str]": "string[]",
    "list[int]": "number[]",
    "list[Any]": "unknown[]",
}


def py_type_to_ts(py_type: str) -> str:
    """Convert a Python type annotation to TypeScript."""
    py_type = py_type.strip()
    # Direct mapping
    if py_type in TYPE_MAP:
        return TYPE_MAP[py_type]

    # Optional[X]
    opt_match = re.match(r"Optional\[(.+)\]", py_type)
    if opt_match:
        inner = py_type_to_ts(opt_match.group(1))
        return f"{inner} | null"

    # list[X]
    list_match = re.match(r"list\[(.+)\]", py_type)
    if list_match:
        inner = py_type_to_ts(list_match.group(1))
        return f"{inner}[]"

    # dict[str, X]
    dict_match = re.match(r"dict\[str,\s*(.+)\]", py_type)
    if dict_match:
        inner = py_type_to_ts(dict_match.group(1))
        return f"Record<string, {inner}>"

    # dict[X, Y]
    dict2_match = re.match(r"dict\[(.+),\s*(.+)\]", py_type)
    if dict2_match:
        k = py_type_to_ts(dict2_match.group(1))
        v = py_type_to_ts(dict2_match.group(2))
        return f"Record<{k}, {v}>"

    # Union types
    union_match = re.match(r"Union\[(.+)\]", py_type)
    if union_match:
        parts = [py_type_to_ts(p.strip()) for p in union_match.group(1).split(",")]
        return " | ".join(parts)

    # Handle Python 3.10+ union syntax (str | None, int | None, etc.)
    if " | " in py_type:
        parts = [py_type_to_ts(p.strip()) for p in py_type.split(" | ")]
        return " | ".join(parts)

    # Handle lowercase python types that weren't mapped
    low_to_ts = {"str": "string", "int": "number", "float": "number", "bool": "boolean", "bytes": "string", "none": "null"}
    if py_type.lower() in low_to_ts:
        return low_to_ts[py_type.lower()]

    return py_type


def extract_model_fields(content: str, class_name: str) -> list[dict[str, str]]:
    """Extract typed fields from a SQLAlchemy model class."""
    fields: list[dict[str, str]] = []
    # Match lines like: field_name: type = Column(...)
    col_pattern = re.compile(
        r'^\s+(\w+)\s*[=:]\s*(?:Column|association_proxy)\(.*$', re.MULTILINE
    )
    # Match annotated fields: field_name: type
    annot_pattern = re.compile(
        r'^\s+(\w+)\s*:\s*([^=#]+?)(?:\s*=|#|$)', re.MULTILINE
    )

    # Find the class definition
    class_start = content.find(f"class {class_name}")
    if class_start == -1:
        return fields

    # Find class body
    body_start = content.find(":", class_start) + 1
    # Find next class definition (same indent level)
    rest = content[body_start:]
    # Get lines until next top-level class or EOF
    class_lines = []
    indent = None
    for line in rest.splitlines():
        if not line.strip() or line.strip().startswith("#") or line.strip().startswith(
            "@"
        ):
            continue
        stripped = line.lstrip()
        if indent is None:
            if stripped:
                indent = len(line) - len(stripped)
        if stripped and not stripped.startswith("class "):
            if line and (len(line) - len(line.lstrip())) >= (indent or 0):
                class_lines.append(line)
            else:
                break
        elif stripped.startswith("class "):
            break

    body = "\n".join(class_lines)

    # Strip docstrings to avoid matching docstring sections like "Examples:"
    body = re.sub(r'""".*?"""', '', body, flags=re.DOTALL)

    # Extract Column fields
    skip_fields = {"uuid", "id", "is_active", "created_at", "updated_at", "tenant_id", "deleted_at", "deleted"}
    for match in col_pattern.finditer(body):
        field_name = match.group(1)
        if field_name.startswith("_") or field_name in skip_fields:
            continue
        fields.append({"name": field_name, "ts_type": "unknown"})

    # Extract annotation-only fields (no assignment)
    ann_fields: set[str] = set()
    for match in annot_pattern.finditer(body):
        field_name = match.group(1)
        py_type = match.group(2).strip()
        if field_name.startswith("_") or field_name in skip_fields:
            continue
        ts_type = py_type_to_ts(py_type)
        if field_name not in ann_fields:
            existing = [f for f in fields if f["name"] == field_name]
            if not existing:
                fields.append({"name": field_name, "ts_type": ts_type})
                ann_fields.add(field_name)

    return fields


def snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def generate_types() -> str:
    """Generate TypeScript type definitions for all backend models."""
    lines: list[str] = [
        "// AUTO-GENERATED — DO NOT EDIT",
        "// Generated from backend/ models",
        '// Run: python scripts/generate_frontend_client.py',
        "",
        "// =============================================================================",
        "// Domain Enums",
        "// =============================================================================",
        "",
    ]

    type_names_seen: set[str] = set()

    # Walk all model files
    for root, dirs, files in os.walk(BACKEND_DIR):
        for fname in sorted(files):
            if not fname.endswith(".py") or fname == "__init__.py":
                continue
            fpath = Path(root) / fname
            content = fpath.read_text(encoding="utf-8", errors="ignore")

            # Extract enums
            enum_pattern = re.compile(r"^class (\w+)\(.*str.*Enum.*\):", re.MULTILINE)
            enum_vals = re.compile(r"^\s+(\w+)\s*=\s*", re.MULTILINE)
            for em in enum_pattern.finditer(content):
                enum_name = em.group(1)
                if enum_name in type_names_seen:
                    continue
                type_names_seen.add(enum_name)
                # Find enum body — locate the end by searching for next top-level class
                ebody_start = content.find(f"class {enum_name}(")
                ebody_end_search = content.find("\nclass ", ebody_start + 1)
                ebody_end = ebody_end_search if ebody_end_search != -1 else len(content)
                ebody = content[ebody_start:ebody_end]

                vals = [ev.group(1) for ev in enum_vals.finditer(ebody)]
                if not vals:
                    continue
                lines.append(f"export type {enum_name} =")
                for v in vals:
                    lines.append(f'  | "{v}"')
                lines.append("")
                lines.append(f"export const {enum_name}Values = [")
                for v in vals:
                    lines.append(f'  "{v}",')
                lines.append("] as const;")
                lines.append("")

            # Extract model classes
            # Only process if this is in a models directory/file
            if "model" not in str(fpath).lower():
                continue

            class_pattern = re.compile(r"^class (\w+)\(.*\):", re.MULTILINE)
            for cm in class_pattern.finditer(content):
                class_name = cm.group(1)
                if class_name in ("Base", "IdentityBase", "AuditBase") or class_name in type_names_seen:
                    continue
                type_names_seen.add(class_name)
                fields = extract_model_fields(content, class_name)

                # Check for __tablename__
                tab_match = re.search(
                    rf'class {class_name}.*?:.*?__tablename__\s*=\s*"(\w+)"',
                    content,
                    re.DOTALL,
                )
                table_name = tab_match.group(1) if tab_match else ""

                lines.append(f"// backend model: {class_name}" + (f"  (table: {table_name})" if table_name else ""))
                lines.append(f"export interface {class_name} {{")
                lines.append(f'  uuid: string;')
                for f in fields:
                    ts_type = f.get("ts_type", "unknown")
                    lines.append(f"  {snake_to_camel(f['name'])}?: {ts_type};")
                lines.append("}")
                lines.append("")

    return "\n".join(lines)


def generate_api_client() -> str:
    """Generate typed API client using React Query hooks."""
    lines: list[str] = [
        "// AUTO-GENERATED API CLIENT — DO NOT EDIT",
        "// Generated from backend/ route files",
        '// Run: python scripts/generate_frontend_client.py',
        "",
        'import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";',
        'import { api } from "../client";',
        "",
    ]

    # NIAM route groups and their paths
    niam_modules = {
        "governance": {
            "prefix": "/niam/governance",
            "endpoints": [
                ("GET", "/authorities", "getAuthorities", "list"),
                ("POST", "/authorities", "createAuthority", "detail"),
                ("PUT", "/authorities/{authority_id}", "updateAuthority", "detail"),
                ("POST", "/councils", "createCouncil", "detail"),
                ("GET", "/councils", "getCouncils", "list"),
                ("POST", "/policies/submit", "submitPolicy", "detail"),
                ("POST", "/policies/{workflow_id}/approve", "approvePolicy", "detail"),
                ("POST", "/appeals", "submitAppeal", "detail"),
                ("POST", "/appeals/{appeal_id}/review", "reviewAppeal", "detail"),
                ("POST", "/suspensions", "suspendIdentity", "detail"),
                ("POST", "/suspensions/{suspension_id}/lift", "liftSuspension", "detail"),
                ("POST", "/restorations", "restoreIdentity", "detail"),
                ("POST", "/registries", "registerEntity", "detail"),
                ("GET", "/registries/{registry_type}", "getRegistry", "detail"),
                ("POST", "/review-board", "createReviewBoard", "detail"),
                ("GET", "/review-board/{board_id}", "getReviewBoard", "detail"),
            ],
        },
        "trust": {
            "prefix": "/niam/trust",
            "endpoints": [
                ("POST", "/frameworks", "createFramework", "detail"),
                ("GET", "/frameworks", "listFrameworks", "list"),
                ("GET", "/frameworks/{framework_id}", "getFramework", "detail"),
                ("POST", "/assurance-profiles", "createProfile", "detail"),
                ("GET", "/assurance-profiles", "listProfiles", "list"),
                ("POST", "/trust-anchors", "registerAnchor", "detail"),
                ("GET", "/trust-anchors", "listAnchors", "list"),
                ("POST", "/evaluate", "evaluateTrust", "detail"),
                ("POST", "/identity-proofing", "submitProofing", "detail"),
            ],
        },
        "lifecycle": {
            "prefix": "/niam/lifecycle",
            "endpoints": [
                ("POST", "/enterprise/register", "startRegistration", "detail"),
                ("POST", "/enterprise/{reg_id}/validate-license", "validateLicense", "detail"),
                ("POST", "/enterprise/{reg_id}/approve", "approveRegistration", "detail"),
                ("POST", "/enterprise/{reg_id}/reject", "rejectRegistration", "detail"),
                ("GET", "/enterprise/{org_id}", "getEnterpriseStatus", "detail"),
                ("POST", "/workforce/request", "requestEmployee", "detail"),
                ("POST", "/workforce/{request_id}/approve", "approveRequest", "detail"),
                ("POST", "/government/appointments", "createAppointment", "detail"),
                ("POST", "/government/appointments/{appointment_id}/approve", "approveAppointment", "detail"),
                ("POST", "/government/appointments/{appointment_id}/promote", "promoteEmployee", "detail"),
                ("POST", "/citizen/register", "registerCitizen", "detail"),
                ("POST", "/citizen/{citizen_id}/verify-otp", "verifyCitizenOtp", "detail"),
                ("POST", "/citizen/{citizen_id}/issue-health-id", "issueHealthId", "detail"),
                ("POST", "/citizen/{citizen_id}/deactivate", "deactivateCitizen", "detail"),
                ("GET", "/citizen/{person_id}", "getCitizenStatus", "detail"),
                ("POST", "/guardians", "createGuardianship", "detail"),
                ("GET", "/guardians/dependents/{guardian_person_id}", "getDependents", "list"),
            ],
        },
        "federation": {
            "prefix": "/niam/federation",
            "endpoints": [
                ("POST", "/providers", "registerProvider", "detail"),
                ("GET", "/providers", "listProviders", "list"),
                ("GET", "/providers/{provider_id}", "getProvider", "detail"),
                ("POST", "/identities/link", "linkIdentity", "detail"),
                ("GET", "/identities/{person_id}", "getPersonIdentities", "list"),
                ("POST", "/trust", "establishTrust", "detail"),
                ("GET", "/trust/{org_id}", "getTrustRelationships", "list"),
                ("POST", "/agreements", "createAgreement", "detail"),
                ("GET", "/agreements", "listAgreements", "list"),
            ],
        },
        "certificates": {
            "prefix": "/niam/certificates",
            "endpoints": [
                ("POST", "/issue", "issueCertificate", "detail"),
                ("POST", "/{certificate_id}/revoke", "revokeCertificate", "detail"),
                ("GET", "/{thumbprint}", "getCertificate", "detail"),
                ("GET", "/organization/{org_id}", "listOrgCertificates", "list"),
                ("GET", "/expiring", "listExpiring", "list"),
                ("POST", "/authorities", "registerCa", "detail"),
                ("GET", "/authorities", "listCas", "list"),
                ("POST", "/api-keys", "generateApiKey", "detail"),
                ("GET", "/api-keys/organization/{org_id}", "listOrgApiKeys", "list"),
            ],
        },
        "workflows": {
            "prefix": "/niam/workflows",
            "endpoints": [
                ("POST", "/definitions", "createDefinition", "detail"),
                ("GET", "/definitions", "listDefinitions", "list"),
                ("GET", "/definitions/{def_id}", "getDefinition", "detail"),
                ("POST", "/instances", "startInstance", "detail"),
                ("GET", "/instances/{instance_id}", "getInstance", "detail"),
                ("POST", "/instances/{instance_id}/approve", "submitApproval", "detail"),
            ],
        },
        "notifications": {
            "prefix": "/niam/notifications",
            "endpoints": [
                ("POST", "/send", "sendNotification", "detail"),
                ("POST", "/templates", "createTemplate", "detail"),
                ("GET", "/templates", "listTemplates", "list"),
                ("GET", "/queue/{recipient_id}", "getQueue", "list"),
                ("GET", "/preferences/{recipient_id}", "getPreferences", "list"),
                ("PUT", "/preferences/{recipient_id}", "updatePreferences", "detail"),
            ],
        },
        "adaptive-auth": {
            "prefix": "/niam/adaptive-auth",
            "endpoints": [
                ("POST", "/evaluate", "evaluateRisk", "detail"),
                ("GET", "/risk-history/{account_id}", "getRiskHistory", "list"),
                ("POST", "/mfa/challenge", "createMfaChallenge", "detail"),
                ("POST", "/mfa/verify", "verifyMfa", "detail"),
                ("GET", "/policies", "listRiskPolicies", "list"),
                ("POST", "/session-policies", "createSessionPolicy", "detail"),
                ("GET", "/active-sessions/{account_id}", "getActiveSessionCount", "detail"),
            ],
        },
        "admin": {
            "prefix": "/niam/admin",
            "endpoints": [
                ("POST", "/portals", "createPortal", "detail"),
                ("GET", "/portals/organization/{org_id}", "listOrgPortals", "list"),
                ("POST", "/subscriptions", "createSubscription", "detail"),
                ("GET", "/subscriptions/{org_id}", "getSubscription", "detail"),
                ("GET", "/audit-log/{org_id}", "getAuditLog", "list"),
                ("POST", "/fhir-connections", "createFhirConnection", "detail"),
                ("GET", "/fhir-connections/organization/{org_id}", "listFhirConnections", "list"),
            ],
        },
        "compliance": {
            "prefix": "/niam/compliance",
            "endpoints": [
                ("POST", "/frameworks", "registerFramework", "detail"),
                ("GET", "/frameworks", "listFrameworks", "list"),
                ("GET", "/frameworks/{framework_id}", "getFramework", "detail"),
                ("POST", "/checks", "runCheck", "detail"),
                ("GET", "/checks/{target_type}/{target_id}", "listChecks", "list"),
                ("POST", "/reports", "generateReport", "detail"),
                ("GET", "/reports/{report_id}", "getReport", "detail"),
                ("GET", "/status/{org_id}", "getOrgComplianceStatus", "detail"),
            ],
        },
    }

    # Legacy API route groups
    legacy_modules = {
        "auth": {
            "prefix": "",
            "endpoints": [
                ("POST", "/login", "login", "detail"),
                ("POST", "/register", "register", "detail"),
            ],
        },
        "patients": {
            "prefix": "",
            "endpoints": [
                ("GET", "/patients", "listPatients", "list"),
                ("POST", "/patients", "createPatient", "detail"),
                ("GET", "/patients/{patient_id}", "getPatient", "detail"),
            ],
        },
    }



    # AUTO-GENERATED additional modules from backend inventory
    additional_modules = {
    "ai_fabric": {
        "prefix": "/ai/fabric",
        "endpoints": [
            ("GET", "/ai/fabric/health", "fabricHealth", "list"),
            ("POST", "/ai/fabric/chat", "fabricChat", "detail"),
            ("POST", "/ai/fabric/embed", "fabricEmbed", "detail"),
            ("GET", "/ai/fabric/gateway/providers", "listProviders", "list"),
            ("GET", "/ai/fabric/gateway/cost", "gatewayCost", "list"),
            ("GET", "/ai/fabric/local-ai/status", "localAiStatus", "list"),
            ("POST", "/ai/fabric/rag/query", "ragQuery", "detail"),
            ("POST", "/ai/fabric/rag/index", "ragIndex", "detail"),
            ("GET", "/ai/fabric/knowledge-graph/entity", "kgEntity", "list"),
            ("GET", "/ai/fabric/knowledge-graph/related", "kgRelated", "list"),
        ],
    },
    "biomedical.api": {
        "prefix": "/biomedical/work-orders",
        "endpoints": [
            ("GET", "/biomedical/devices", "listDevices", "list"),
            ("GET", "/biomedical/devices/{device_id}", "getDevice", "detail"),
            ("PUT", "/biomedical/devices/{device_id}/status", "updateDeviceStatus", "detail"),
            ("GET", "/biomedical/devices/due/pm", "devicesDueForPm", "list"),
            ("GET", "/biomedical/devices/due/calibration", "devicesDueForCalibration", "list"),
            ("GET", "/biomedical/devices/due/calibration", "createWorkOrder", "list"),
            ("GET", "/biomedical/work-orders", "listWorkOrders", "list"),
            ("GET", "/biomedical/work-orders/{wo_id}", "getWorkOrder", "detail"),
            ("POST", "/biomedical/work-orders/{wo_id}/complete", "completeWorkOrder", "detail"),
            ("POST", "/biomedical/work-orders/{wo_id}/complete", "recordCalibration", "detail"),
        ],
    },
    "blood_bank.api": {
        "prefix": "/blood-bank/transfusions",
        "endpoints": [
            ("GET", "/blood-bank/donors", "listDonors", "list"),
            ("GET", "/blood-bank/donors/{donor_id}", "getDonor", "detail"),
            ("POST", "/blood-bank/donors/{donor_id}/defer", "deferDonor", "detail"),
            ("POST", "/blood-bank/donors/{donor_id}/defer", "registerDonation", "detail"),
            ("POST", "/blood-bank/donations/{donation_id}/complete", "completeDonation", "detail"),
            ("POST", "/blood-bank/donations/{donation_id}/complete", "processComponent", "detail"),
            ("GET", "/blood-bank/inventory", "getInventory", "list"),
            ("GET", "/blood-bank/inventory/critical", "getCriticalInventory", "list"),
            ("POST", "/blood-bank/inventory/issue", "issueUnits", "detail"),
            ("POST", "/blood-bank/inventory/issue", "performCrossmatch", "detail"),
        ],
    },
    "capabilities.clinical_foundation": {
        "prefix": "/clinical-foundation",
        "endpoints": [
            ("GET", "/clinical-foundation/", "listClinicalFoundation", "list"),
            ("GET", "/clinical-foundation/{id}", "getClinicalFoundation", "detail"),
            ("POST", "/clinical-foundation/", "createClinicalFoundation", "detail"),
            ("PUT", "/clinical-foundation/{id}", "updateClinicalFoundation", "detail"),
            ("DELETE", "/clinical-foundation/{id}", "deleteClinicalFoundation", "detail"),
        ],
    },
    "capabilities.document_management": {
        "prefix": "/document-management",
        "endpoints": [
            ("GET", "/document-management/", "listDocumentManagement", "list"),
            ("GET", "/document-management/{id}", "getDocumentManagement", "detail"),
            ("POST", "/document-management/", "createDocumentManagement", "detail"),
            ("PUT", "/document-management/{id}", "updateDocumentManagement", "detail"),
            ("DELETE", "/document-management/{id}", "deleteDocumentManagement", "detail"),
        ],
    },
    "capabilities.encounter_management": {
        "prefix": "/encounter-management",
        "endpoints": [
            ("GET", "/encounter-management/", "listEncounterManagement", "list"),
            ("GET", "/encounter-management/{id}", "getEncounterManagement", "detail"),
            ("POST", "/encounter-management/", "createEncounterManagement", "detail"),
            ("PUT", "/encounter-management/{id}", "updateEncounterManagement", "detail"),
            ("DELETE", "/encounter-management/{id}", "deleteEncounterManagement", "detail"),
        ],
    },
    "capabilities.fhir_interoperability": {
        "prefix": "/fhir-interoperability",
        "endpoints": [
            ("GET", "/fhir-interoperability/", "listFhirInteroperability", "list"),
            ("GET", "/fhir-interoperability/{id}", "getFhirInteroperability", "detail"),
            ("POST", "/fhir-interoperability/", "createFhirInteroperability", "detail"),
            ("PUT", "/fhir-interoperability/{id}", "updateFhirInteroperability", "detail"),
            ("DELETE", "/fhir-interoperability/{id}", "deleteFhirInteroperability", "detail"),
        ],
    },
    "capabilities.healthcare_consent": {
        "prefix": "/healthcare-consent",
        "endpoints": [
            ("GET", "/healthcare-consent/", "listHealthcareConsent", "list"),
            ("GET", "/healthcare-consent/{id}", "getHealthcareConsent", "detail"),
            ("POST", "/healthcare-consent/", "createHealthcareConsent", "detail"),
            ("PUT", "/healthcare-consent/{id}", "updateHealthcareConsent", "detail"),
            ("DELETE", "/healthcare-consent/{id}", "deleteHealthcareConsent", "detail"),
        ],
    },
    "capabilities.provider_management": {
        "prefix": "/provider-management",
        "endpoints": [
            ("GET", "/provider-management/", "listProviderManagement", "list"),
            ("GET", "/provider-management/{id}", "getProviderManagement", "detail"),
            ("POST", "/provider-management/", "createProviderManagement", "detail"),
            ("PUT", "/provider-management/{id}", "updateProviderManagement", "detail"),
            ("DELETE", "/provider-management/{id}", "deleteProviderManagement", "detail"),
        ],
    },
    "capabilities.reporting_service": {
        "prefix": "/reporting-service",
        "endpoints": [
            ("GET", "/reporting-service/", "listReportingService", "list"),
            ("GET", "/reporting-service/{id}", "getReportingService", "detail"),
            ("POST", "/reporting-service/", "createReportingService", "detail"),
            ("PUT", "/reporting-service/{id}", "updateReportingService", "detail"),
            ("DELETE", "/reporting-service/{id}", "deleteReportingService", "detail"),
        ],
    },
    "capabilities.search_service": {
        "prefix": "/search-service",
        "endpoints": [
            ("GET", "/search-service/", "listSearchService", "list"),
            ("GET", "/search-service/{id}", "getSearchService", "detail"),
            ("POST", "/search-service/", "createSearchService", "detail"),
            ("PUT", "/search-service/{id}", "updateSearchService", "detail"),
            ("DELETE", "/search-service/{id}", "deleteSearchService", "detail"),
        ],
    },
    "capabilities.storage_service": {
        "prefix": "/storage-service",
        "endpoints": [
            ("GET", "/storage-service/", "listStorageService", "list"),
            ("GET", "/storage-service/{id}", "getStorageService", "detail"),
            ("POST", "/storage-service/", "createStorageService", "detail"),
            ("PUT", "/storage-service/{id}", "updateStorageService", "detail"),
            ("DELETE", "/storage-service/{id}", "deleteStorageService", "detail"),
        ],
    },
    "capabilities.workflow_engine": {
        "prefix": "/workflow-engine",
        "endpoints": [
            ("GET", "/workflow-engine/", "listWorkflowEngine", "list"),
            ("GET", "/workflow-engine/{id}", "getWorkflowEngine", "detail"),
            ("POST", "/workflow-engine/", "createWorkflowEngine", "detail"),
            ("PUT", "/workflow-engine/{id}", "updateWorkflowEngine", "detail"),
            ("DELETE", "/workflow-engine/{id}", "deleteWorkflowEngine", "detail"),
        ],
    },
    "certification": {
        "prefix": "/certification/dimensions",
        "endpoints": [
            ("POST", "/certification/evaluate/{module_path:path}", "evaluateModule", "detail"),
            ("GET", "/certification/level/{module_path:path}", "getCertificationLevel", "detail"),
            ("GET", "/certification/report/{module_path:path}", "getReport", "detail"),
            ("GET", "/certification/metrics", "getAllMetrics", "list"),
            ("GET", "/certification/metrics/{category}", "getMetricsByCategory", "detail"),
            ("POST", "/certification/release/check", "checkReleaseGates", "detail"),
            ("POST", "/certification/release/validate", "validateRelease", "detail"),
            ("GET", "/certification/dimensions", "listDimensions", "list"),
            ("GET", "/certification/dimensions/{dimension}/checks", "getDimensionChecks", "detail"),
        ],
    },
    "citizen_platform": {
        "prefix": "/citizen-platform/emergency-contacts",
        "endpoints": [
            ("GET", "/citizen-platform/dashboard/{citizen_id}", "getDashboard", "detail"),
            ("GET", "/citizen-platform/profile/{citizen_id}", "getProfile", "detail"),
            ("GET", "/citizen-platform/health-summary/{citizen_id}", "getHealthSummary", "detail"),
            ("GET", "/citizen-platform/appointments/{citizen_id}", "listAppointments", "detail"),
            ("POST", "/citizen-platform/appointments/{citizen_id}", "bookAppointment", "detail"),
            ("GET", "/citizen-platform/medications/{citizen_id}", "listMedications", "detail"),
            ("GET", "/citizen-platform/lab-results/{citizen_id}", "listLabResults", "detail"),
            ("GET", "/citizen-platform/radiology/{citizen_id}", "listRadiologyStudies", "detail"),
            ("GET", "/citizen-platform/family/{citizen_id}", "getFamily", "detail"),
            ("GET", "/citizen-platform/vaccinations/{citizen_id}", "getVaccinations", "detail"),
        ],
    },
    "command_center.api": {
        "prefix": "/command-center/after-action-reports",
        "endpoints": [
            ("GET", "/command-center/emergencies", "listEmergencies", "list"),
            ("GET", "/command-center/emergencies/{emergency_id}", "getEmergency", "detail"),
            ("POST", "/command-center/emergencies/{emergency_id}/resolve", "resolveEmergency", "detail"),
            ("POST", "/command-center/emergencies/{emergency_id}/resolve", "requestResource", "detail"),
            ("GET", "/command-center/resource-requests", "listResourceRequests", "list"),
            ("POST", "/command-center/resource-requests/{request_id}/fulfill", "fulfillResource", "detail"),
            ("POST", "/command-center/resource-requests/{request_id}/fulfill", "publishSituationReport", "detail"),
            ("GET", "/command-center/situation-reports", "listSituationReports", "list"),
            ("GET", "/command-center/situation-reports", "completeAfterAction", "list"),
            ("GET", "/command-center/after-action-reports", "listAfterActionReports", "list"),
        ],
    },
    "command_intelligence": {
        "prefix": "/intelligence/executive-dashboard",
        "endpoints": [
            ("GET", "/intelligence/situation-room", "getSituationRoom", "list"),
            ("GET", "/intelligence/kpis", "getKpis", "list"),
            ("GET", "/intelligence/kpis/{kpi_name}/trend", "getKpiTrend", "detail"),
            ("GET", "/intelligence/incidents", "getIncidents", "list"),
            ("GET", "/intelligence/incidents", "reportIncident", "list"),
            ("GET", "/intelligence/capacity", "getCapacity", "list"),
            ("GET", "/intelligence/capacity", "createRecommendation", "list"),
            ("GET", "/intelligence/executive-dashboard", "executiveDashboard", "list"),
            ("GET", "/intelligence/regional/{region}/dashboard", "regionalDashboard", "detail"),
        ],
    },
    "control_plane": {
        "prefix": "/control-plane/digital-twin",
        "endpoints": [
            ("GET", "/control-plane/registry/components", "listComponents", "list"),
            ("GET", "/control-plane/registry/components", "registerComponent", "list"),
            ("PUT", "/control-plane/registry/components/{name}", "updateComponent", "detail"),
            ("DELETE", "/control-plane/registry/components/{name}", "unregisterComponent", "detail"),
            ("GET", "/control-plane/registry/topology", "getTopology", "list"),
            ("GET", "/control-plane/health", "controlPlaneHealth", "list"),
            ("GET", "/control-plane/config/{scope}/{component}", "getConfig", "detail"),
            ("PUT", "/control-plane/config/{scope}/{component}", "setConfig", "detail"),
            ("POST", "/control-plane/config/reload", "reloadConfig", "detail"),
            ("GET", "/control-plane/policies", "listPolicies", "list"),
        ],
    },
    "critical_care.api": {
        "prefix": "/critical-care/admissions",
        "endpoints": [
            ("GET", "/critical-care/admissions", "listAdmissions", "list"),
            ("GET", "/critical-care/admissions/{admission_id}", "getAdmission", "detail"),
            ("POST", "/critical-care/admissions/{admission_id}/discharge", "dischargePatient", "detail"),
            ("POST", "/critical-care/admissions/{admission_id}/discharge", "registerBed", "detail"),
            ("GET", "/critical-care/beds/availability", "getBedAvailability", "list"),
            ("GET", "/critical-care/beds/availability", "recordVitals", "list"),
            ("GET", "/critical-care/vitals/{patient_id}", "getVitals", "detail"),
            ("GET", "/critical-care/vitals/{patient_id}", "setVentilator", "detail"),
            ("GET", "/critical-care/ventilator/{patient_id}", "getVentilatorSettings", "detail"),
            ("POST", "/critical-care/ews/{patient_id}", "calculateEws", "detail"),
        ],
    },
    "ems.api": {
        "prefix": "/ems/ambulances",
        "endpoints": [
            ("GET", "/ems/incidents", "listIncidents", "list"),
            ("GET", "/ems/incidents/{incident_id}", "getIncident", "detail"),
            ("PUT", "/ems/incidents/{incident_id}/status", "updateIncidentStatus", "detail"),
            ("PUT", "/ems/incidents/{incident_id}/status", "dispatchIncident", "detail"),
            ("PUT", "/ems/incidents/{incident_id}/status", "registerAmbulance", "detail"),
            ("GET", "/ems/ambulances", "listAmbulances", "list"),
            ("GET", "/ems/ambulances/{ambulance_id}", "getAmbulance", "detail"),
            ("PUT", "/ems/ambulances/{ambulance_id}/location", "updateAmbulanceLocation", "detail"),
            ("PUT", "/ems/ambulances/{ambulance_id}/status", "updateAmbulanceStatus", "detail"),
            ("PUT", "/ems/ambulances/{ambulance_id}/status", "registerCrew", "detail"),
        ],
    },
    "health_data": {
        "prefix": "/health-data/event-store",
        "endpoints": [
            ("GET", "/health-data/catalog", "listCatalog", "list"),
            ("GET", "/health-data/catalog/{dataset}", "getDatasetMetadata", "detail"),
            ("GET", "/health-data/lineage/{entity_type}/{entity_id}", "getLineage", "detail"),
            ("GET", "/health-data/governance/policies", "listPolicies", "list"),
            ("POST", "/health-data/governance/policies", "createPolicy", "detail"),
            ("GET", "/health-data/quality/metrics", "getQualityMetrics", "list"),
            ("POST", "/health-data/ingest", "triggerIngestion", "detail"),
            ("GET", "/health-data/event-store/events", "queryEventStore", "list"),
            ("GET", "/health-data/warehouse/query", "runWarehouseQuery", "list"),
            ("POST", "/health-data/canonical/map-patient", "mapFhirPatient", "detail"),
        ],
    },
    "identity.adaptive_auth": {
        "prefix": "/niam/adaptive-auth",
        "endpoints": [
            ("POST", "/niam/adaptive-auth/evaluate", "evaluateRisk", "detail"),
            ("GET", "/niam/adaptive-auth/risk-history/{account_id}", "getRiskHistory", "detail"),
            ("POST", "/niam/adaptive-auth/mfa/challenge", "createMfaChallenge", "detail"),
            ("POST", "/niam/adaptive-auth/mfa/verify", "verifyMfaChallenge", "detail"),
            ("GET", "/niam/adaptive-auth/policies", "listRiskPolicies", "list"),
            ("POST", "/niam/adaptive-auth/policies", "createRiskPolicy", "detail"),
            ("POST", "/niam/adaptive-auth/policies/{policy_id}", "updateRiskPolicy", "detail"),
            ("GET", "/niam/adaptive-auth/session-policies", "listSessionPolicies", "list"),
            ("POST", "/niam/adaptive-auth/session-policies", "createSessionPolicy", "detail"),
            ("PUT", "/niam/adaptive-auth/session-policies/{policy_id}", "updateSessionPolicy", "detail"),
        ],
    },
    "identity.admin": {
        "prefix": "/admin/fhir-connections",
        "endpoints": [
            ("POST", "/admin/portals", "createPortal", "detail"),
            ("GET", "/admin/portals/organization/{org_id}", "listOrgPortals", "detail"),
            ("POST", "/admin/portals/{portal_id}/branches", "addBranch", "detail"),
            ("POST", "/admin/branches/{branch_id}/facilities", "addFacility", "detail"),
            ("POST", "/admin/facilities/{facility_id}/departments", "addDepartment", "detail"),
            ("GET", "/admin/subscriptions/{org_id}", "getSubscription", "detail"),
            ("POST", "/admin/subscriptions", "createSubscription", "detail"),
            ("PUT", "/admin/subscriptions/{sub_id}", "updateSubscription", "detail"),
            ("POST", "/admin/fhir-connections", "createFhirConnection", "detail"),
            ("GET", "/admin/fhir-connections/organization/{org_id}", "listFhirConnections", "detail"),
        ],
    },
    "identity.certificates": {
        "prefix": "/certificates/organization",
        "endpoints": [
            ("POST", "/certificates/issue", "issueCertificate", "detail"),
            ("POST", "/certificates/{certificate_id}/revoke", "revokeCertificate", "detail"),
            ("POST", "/certificates/{certificate_id}/rotate", "rotateCertificate", "detail"),
            ("GET", "/certificates/{thumbprint}", "getCertificate", "detail"),
            ("GET", "/certificates/organization/{org_id}", "listOrgCertificates", "detail"),
            ("GET", "/certificates/expiring", "listExpiringCertificates", "list"),
            ("POST", "/certificates/authorities", "registerCa", "detail"),
            ("GET", "/certificates/authorities", "listCas", "list"),
            ("POST", "/certificates/authorities/{ca_id}/crl", "generateCrl", "detail"),
            ("POST", "/certificates/api-keys", "generateApiKey", "detail"),
        ],
    },
    "identity.compliance": {
        "prefix": "/compliance/frameworks",
        "endpoints": [
            ("POST", "/compliance/frameworks", "registerFramework", "detail"),
            ("GET", "/compliance/frameworks", "listFrameworks", "list"),
            ("GET", "/compliance/frameworks/{framework_id}", "getFramework", "detail"),
            ("POST", "/compliance/checks", "runCheck", "detail"),
            ("GET", "/compliance/checks/{target_type}/{target_id}", "listChecks", "detail"),
            ("POST", "/compliance/reports", "generateReport", "detail"),
            ("GET", "/compliance/reports/{report_id}", "getReport", "detail"),
            ("GET", "/compliance/status/{org_id}", "getOrgComplianceStatus", "detail"),
        ],
    },
    "identity.federation": {
        "prefix": "/federation/identities",
        "endpoints": [
            ("POST", "/federation/providers", "registerProvider", "detail"),
            ("GET", "/federation/providers", "listProviders", "list"),
            ("GET", "/federation/providers/{provider_id}", "getProvider", "detail"),
            ("PUT", "/federation/providers/{provider_id}", "updateProvider", "detail"),
            ("POST", "/federation/identities/link", "linkIdentity", "detail"),
            ("POST", "/federation/identities/unlink", "unlinkIdentity", "detail"),
            ("GET", "/federation/identities/{person_id}", "getPersonIdentities", "detail"),
            ("POST", "/federation/trust", "establishTrust", "detail"),
            ("GET", "/federation/trust/{org_id}", "getTrustRelationships", "detail"),
            ("POST", "/federation/agreements", "createAgreement", "detail"),
        ],
    },
    "identity.governance": {
        "prefix": "/niam/governance",
        "endpoints": [
            ("POST", "/niam/governance/authorities", "createAuthority", "detail"),
            ("GET", "/niam/governance/authorities", "listAuthorities", "list"),
            ("GET", "/niam/governance/authorities/{authority_id}", "getAuthority", "detail"),
            ("POST", "/niam/governance/authorities/{authority_id}/suspend", "suspendAuthority", "detail"),
            ("POST", "/niam/governance/authorities/{authority_id}/activate", "activateAuthority", "detail"),
            ("POST", "/niam/governance/councils", "createCouncil", "detail"),
            ("GET", "/niam/governance/councils", "listCouncils", "list"),
            ("GET", "/niam/governance/councils/{council_id}", "getCouncil", "detail"),
            ("POST", "/niam/governance/review-boards", "createReviewBoard", "detail"),
            ("POST", "/niam/governance/policy-approvals", "submitPolicyApproval", "detail"),
        ],
    },
    "identity.lifecycle": {
        "prefix": "/lifecycle/enterprise",
        "endpoints": [
            ("POST", "/lifecycle/enterprise/register", "startEnterpriseRegistration", "detail"),
            ("POST", "/lifecycle/enterprise/{reg_id}/validate-license", "validateEnterpriseLicense", "detail"),
            ("POST", "/lifecycle/enterprise/{reg_id}/inspect", "submitEnterpriseInspection", "detail"),
            ("POST", "/lifecycle/enterprise/{reg_id}/assess-risk", "assessEnterpriseRisk", "detail"),
            ("POST", "/lifecycle/enterprise/{reg_id}/approve", "approveEnterpriseRegistration", "detail"),
            ("POST", "/lifecycle/enterprise/{reg_id}/reject", "rejectEnterpriseRegistration", "detail"),
            ("GET", "/lifecycle/enterprise/{org_id}", "getEnterpriseStatus", "detail"),
            ("POST", "/lifecycle/workforce/request", "requestEmployee", "detail"),
            ("POST", "/lifecycle/workforce/{request_id}/validate-national-id", "validateWorkforceNationalId", "detail"),
            ("POST", "/lifecycle/workforce/{request_id}/validate-license", "validateWorkforceLicense", "detail"),
        ],
    },
    "identity.notifications": {
        "prefix": "/notifications/send-template",
        "endpoints": [
            ("POST", "/notifications/send", "sendNotification", "detail"),
            ("POST", "/notifications/templates", "createTemplate", "detail"),
            ("GET", "/notifications/templates", "listTemplates", "list"),
            ("GET", "/notifications/queue/{recipient_id}", "getQueue", "detail"),
            ("POST", "/notifications/queue/{queue_id}/read", "markRead", "detail"),
            ("GET", "/notifications/preferences/{recipient_id}", "getPreferences", "detail"),
            ("PUT", "/notifications/preferences/{recipient_id}", "updatePreferences", "detail"),
            ("POST", "/notifications/send-template", "sendTemplateNotification", "detail"),
            ("POST", "/notifications/queue/{queue_id}/sent", "markNotificationSent", "detail"),
            ("POST", "/notifications/queue/{queue_id}/delivered", "markNotificationDelivered", "detail"),
        ],
    },
    "identity.trust": {
        "prefix": "/niam/trust",
        "endpoints": [
            ("POST", "/niam/trust/frameworks", "createFramework", "detail"),
            ("GET", "/niam/trust/frameworks", "listFrameworks", "list"),
            ("GET", "/niam/trust/frameworks/{framework_id}", "getFramework", "detail"),
            ("PUT", "/niam/trust/frameworks/{framework_id}", "updateFramework", "detail"),
            ("POST", "/niam/trust/frameworks/{framework_id}/activate", "activateFramework", "detail"),
            ("POST", "/niam/trust/assurance-profiles", "createAssuranceProfile", "detail"),
            ("GET", "/niam/trust/assurance-profiles", "listAssuranceProfiles", "list"),
            ("GET", "/niam/trust/assurance-profiles/{profile_uuid}", "getAssuranceProfile", "detail"),
            ("GET", "/niam/trust/assurance-profiles/identity/{identity_id}", "getProfilesForIdentity", "detail"),
            ("POST", "/niam/trust/assurance-profiles/{profile_uuid}/revoke", "revokeAssuranceProfile", "detail"),
        ],
    },
    "identity.workflows": {
        "prefix": "/workflows/definitions",
        "endpoints": [
            ("POST", "/workflows/definitions", "createDefinition", "detail"),
            ("GET", "/workflows/definitions", "listDefinitions", "list"),
            ("GET", "/workflows/definitions/{def_id}", "getDefinition", "detail"),
            ("POST", "/workflows/instances", "startInstance", "detail"),
            ("GET", "/workflows/instances/{instance_id}", "getInstance", "detail"),
            ("POST", "/workflows/instances/{instance_id}/approve", "submitApproval", "detail"),
            ("POST", "/workflows/instances/{instance_id}/cancel", "cancelInstance", "detail"),
            ("GET", "/workflows/approvals/pending/{approver_id}", "getPendingApprovals", "detail"),
        ],
    },
    "integration": {
        "prefix": "/integration/connectors",
        "endpoints": [
            ("GET", "/integration/gateways", "listGateways", "list"),
            ("GET", "/integration/gateway/{protocol}", "getGateway", "detail"),
            ("POST", "/integration/gateway/{protocol}/send", "sendViaGateway", "detail"),
            ("POST", "/integration/gateway/{protocol}/receive", "receiveViaGateway", "detail"),
            ("GET", "/integration/catalog", "apiCatalog", "list"),
            ("GET", "/integration/connectors", "listIntegrationConnectors", "list"),
            ("GET", "/integration/standards", "standardsConformance", "list"),
            ("POST", "/integration/transform", "runTransformation", "detail"),
            ("GET", "/integration/monitoring/dashboard", "integrationHealthDashboard", "list"),
            ("POST", "/integration/test/run", "runIntegrationTests", "detail"),
        ],
    },
    "integration.connectors": {
        "prefix": "/integration/connectors",
        "endpoints": [
            ("GET", "/integration/connectors/status", "connectorsStatus", "list"),
            ("GET", "/integration/connectors/{name}", "getConnector", "detail"),
            ("POST", "/integration/connectors/{name}/connect", "connectConnector", "detail"),
            ("POST", "/integration/connectors/{name}/disconnect", "disconnectConnector", "detail"),
            ("GET", "/integration/connectors/{name}/health", "connectorHealth", "detail"),
            ("POST", "/integration/connectors/{name}/send", "sendThroughConnector", "detail"),
            ("POST", "/integration/connectors/{name}/configure", "configureConnector", "detail"),
        ],
    },
    "kernel": {
        "prefix": "/kernel/capabilities",
        "endpoints": [
            ("GET", "/kernel/status", "kernelStatus", "list"),
            ("GET", "/kernel/services", "kernelServices", "list"),
            ("GET", "/kernel/capabilities", "kernelCapabilities", "list"),
            ("GET", "/kernel/plugins", "kernelPlugins", "list"),
            ("GET", "/kernel/modules", "kernelModules", "list"),
            ("GET", "/kernel/config", "kernelConfig", "list"),
            ("GET", "/kernel/events/outbox", "kernelOutbox", "list"),
            ("GET", "/kernel/events/dlq", "kernelDeadLetterQueue", "list"),
            ("GET", "/kernel/tenants", "kernelTenants", "list"),
            ("GET", "/kernel/locks", "kernelLocks", "list"),
        ],
    },
    "lifecycle_platform.api": {
        "prefix": "/lifecycle/upgrade-paths",
        "endpoints": [
            ("GET", "/lifecycle/components", "listComponents", "list"),
            ("GET", "/lifecycle/components/{component_id}", "getComponent", "detail"),
            ("GET", "/lifecycle/components/name/{name}", "findComponent", "detail"),
            ("PUT", "/lifecycle/components/{component_id}/stage", "updateComponentStage", "detail"),
            ("PUT", "/lifecycle/components/{component_id}/stage", "createRelease", "detail"),
            ("GET", "/lifecycle/releases", "listReleases", "list"),
            ("GET", "/lifecycle/releases/{release_id}", "getRelease", "detail"),
            ("POST", "/lifecycle/releases/{release_id}/approve", "approveRelease", "detail"),
            ("POST", "/lifecycle/releases/{release_id}/approve", "recordCompatibility", "detail"),
            ("GET", "/lifecycle/compatibility/check", "checkCompatibility", "list"),
        ],
    },
    "national.background_platform.api": {
        "prefix": "/national/jobs",
        "endpoints": [
            ("GET", "/national/jobs/", "listJobs", "list"),
            ("GET", "/national/jobs/{job_id}", "getJob", "detail"),
            ("PUT", "/national/jobs/{job_id}", "updateJob", "detail"),
            ("PUT", "/national/jobs/{job_id}", "deleteJob", "detail"),
            ("POST", "/national/jobs/{job_id}/execute", "executeJobNow", "detail"),
            ("POST", "/national/jobs/{job_id}/cancel", "cancelJob", "detail"),
            ("POST", "/national/jobs/{job_id}/pause", "pauseJob", "detail"),
            ("POST", "/national/jobs/{job_id}/resume", "resumeJob", "detail"),
            ("GET", "/national/jobs/{job_id}/executions", "getExecutionHistory", "detail"),
            ("GET", "/national/jobs/{job_id}/schedules", "getSchedules", "detail"),
        ],
    },
    "national.document_platform.api": {
        "prefix": "/national/documents",
        "endpoints": [
            ("GET", "/national/documents/", "listDocuments", "list"),
            ("GET", "/national/documents/{document_id}", "getDocument", "detail"),
            ("PUT", "/national/documents/{document_id}", "updateDocument", "detail"),
            ("PUT", "/national/documents/{document_id}", "deleteDocument", "detail"),
            ("PUT", "/national/documents/{document_id}", "createVersion", "detail"),
            ("GET", "/national/documents/{document_id}/versions", "listVersions", "detail"),
            ("GET", "/national/documents/{document_id}/versions", "signDocument", "detail"),
            ("GET", "/national/documents/{document_id}/signatures", "listSignatures", "detail"),
            ("POST", "/national/documents/{document_id}/verify", "verifyDocument", "detail"),
            ("POST", "/national/documents/{document_id}/verify", "generateQrCode", "detail"),
        ],
    },
    "national.ecosystem": {
        "prefix": "/ecosystem/connectors",
        "endpoints": [
            ("POST", "/ecosystem/connectors/register", "registerConnector", "detail"),
            ("GET", "/ecosystem/connectors", "listConnectors", "list"),
            ("GET", "/ecosystem/connectors/{name}/health", "connectorHealth", "detail"),
            ("DELETE", "/ecosystem/connectors/{name}", "unregisterConnector", "detail"),
            ("POST", "/ecosystem/connectors/{name}/send", "connectorSend", "detail"),
            ("POST", "/ecosystem/connectors/{name}/receive", "connectorReceive", "detail"),
            ("POST", "/ecosystem/transform", "transformData", "detail"),
            ("GET", "/ecosystem/schemas", "listSchemas", "list"),
            ("POST", "/ecosystem/schemas", "registerSchema", "detail"),
            ("POST", "/ecosystem/schemas/{schema_name}/validate", "validateAgainstSchema", "detail"),
        ],
    },
    "national.ecosystem.gateway": {
        "prefix": "/gateway/policies",
        "endpoints": [
            ("POST", "/gateway/route", "routeRequest", "detail"),
            ("GET", "/gateway/status", "gatewayStatus", "list"),
            ("GET", "/gateway/policies", "listPolicies", "list"),
            ("POST", "/gateway/policies", "createPolicy", "detail"),
            ("PUT", "/gateway/policies/{policy_id}", "updatePolicy", "detail"),
            ("DELETE", "/gateway/policies/{policy_id}", "deletePolicy", "detail"),
            ("GET", "/gateway/catalog", "listApiCatalog", "list"),
            ("POST", "/gateway/catalog", "registerApi", "detail"),
        ],
    },
    "national.notification_platform.api": {
        "prefix": "/national/notifications",
        "endpoints": [
            ("GET", "/national/notifications/", "listNotifications", "list"),
            ("GET", "/national/notifications/dashboard", "getDashboard", "list"),
            ("GET", "/national/notifications/{notification_id}", "getNotification", "detail"),
            ("GET", "/national/notifications/{notification_id}", "cancelNotification", "detail"),
            ("GET", "/national/notifications/{notification_id}", "createTemplate", "detail"),
            ("GET", "/national/notifications/templates", "listTemplates", "list"),
            ("GET", "/national/notifications/templates/{template_id}", "getTemplate", "detail"),
            ("PUT", "/national/notifications/templates/{template_id}", "updateTemplate", "detail"),
            ("PUT", "/national/notifications/templates/{template_id}", "deleteTemplate", "detail"),
            ("POST", "/national/notifications/templates/{template_id}/render", "renderTemplate", "detail"),
        ],
    },
    "national.observability.api": {
        "prefix": "/national/observability",
        "endpoints": [
            ("GET", "/national/observability/metrics/query", "queryMetrics", "list"),
            ("GET", "/national/observability/metrics/query", "recordTraces", "list"),
            ("GET", "/national/observability/traces/{trace_id}", "getTrace", "detail"),
            ("GET", "/national/observability/traces/search", "searchTraces", "list"),
            ("POST", "/national/observability/health/checks/{name}", "runHealthCheck", "detail"),
            ("GET", "/national/observability/health/checks", "listHealthChecks", "list"),
            ("GET", "/national/observability/health/status", "healthStatus", "list"),
            ("GET", "/national/observability/health", "health", "list"),
            ("GET", "/national/observability/health", "createAlertRule", "list"),
            ("GET", "/national/observability/alerts/rules", "listAlertRules", "list"),
        ],
    },
    "national.rules_engine.api": {
        "prefix": "/national/rules",
        "endpoints": [
            ("POST", "/national/rules/evaluate", "evaluateRules", "detail"),
            ("POST", "/national/rules/simulate", "simulateRule", "detail"),
            ("POST", "/national/rules/simulate", "createRule", "detail"),
            ("GET", "/national/rules/", "listRules", "list"),
            ("GET", "/national/rules/{rule_id}", "getRule", "detail"),
            ("PUT", "/national/rules/{rule_id}", "updateRule", "detail"),
            ("PUT", "/national/rules/{rule_id}", "deleteRule", "detail"),
            ("POST", "/national/rules/{rule_id}/activate", "activateRule", "detail"),
            ("POST", "/national/rules/{rule_id}/deactivate", "deactivateRule", "detail"),
            ("POST", "/national/rules/{rule_id}/version", "createRuleVersion", "detail"),
        ],
    },
    "national.scheduling_platform.api": {
        "prefix": "/national/scheduling",
        "endpoints": [
            ("GET", "/national/scheduling/appointments", "listAppointments", "list"),
            ("GET", "/national/scheduling/appointments/{appointment_id}", "getAppointment", "detail"),
            ("PUT", "/national/scheduling/appointments/{appointment_id}", "updateAppointment", "detail"),
            ("PUT", "/national/scheduling/appointments/{appointment_id}", "cancelAppointment", "detail"),
            ("POST", "/national/scheduling/appointments/{appointment_id}/complete", "completeAppointment", "detail"),
            ("POST", "/national/scheduling/appointments/{appointment_id}/no-show", "markNoShow", "detail"),
            ("POST", "/national/scheduling/appointments/{appointment_id}/reschedule", "rescheduleAppointment", "detail"),
            ("POST", "/national/scheduling/availability/check", "checkAvailability", "detail"),
            ("GET", "/national/scheduling/availability/slots", "findAvailableSlots", "list"),
            ("GET", "/national/scheduling/availability/slots", "createResource", "list"),
        ],
    },
    "national.search_platform.api": {
        "prefix": "/national/search",
        "endpoints": [
            ("POST", "/national/search/search", "searchPost", "detail"),
            ("GET", "/national/search/search", "searchGet", "list"),
            ("POST", "/national/search/fhir/search", "fhirSearch", "detail"),
            ("GET", "/national/search/suggest", "suggest", "list"),
            ("GET", "/national/search/facets", "getFacets", "list"),
            ("GET", "/national/search/facets", "saveSearch", "list"),
            ("GET", "/national/search/saved", "listSavedSearches", "list"),
            ("GET", "/national/search/saved/{search_id}", "getSavedSearch", "detail"),
            ("GET", "/national/search/saved/{search_id}", "deleteSavedSearch", "detail"),
            ("POST", "/national/search/index/rebuild", "rebuildIndex", "detail"),
        ],
    },
    "national.task_engine.api": {
        "prefix": "/national/tasks",
        "endpoints": [
            ("POST", "/national/tasks/", "createTask", "detail"),
            ("POST", "/national/tasks/bulk", "bulkCreate", "detail"),
            ("GET", "/national/tasks/", "listTasks", "list"),
            ("GET", "/national/tasks/dashboard", "getDashboard", "list"),
            ("GET", "/national/tasks/{task_id}", "getTask", "detail"),
            ("PUT", "/national/tasks/{task_id}", "updateTask", "detail"),
            ("DELETE", "/national/tasks/{task_id}", "deleteTask", "detail"),
            ("POST", "/national/tasks/{task_id}/assign", "assignTask", "detail"),
            ("POST", "/national/tasks/{task_id}/start", "startTask", "detail"),
            ("POST", "/national/tasks/{task_id}/complete", "completeTask", "detail"),
        ],
    },
    "national.workflow_runtime.api": {
        "prefix": "/national/workflows",
        "endpoints": [
            ("POST", "/national/workflows/definitions", "createDefinition", "detail"),
            ("GET", "/national/workflows/definitions", "listDefinitions", "list"),
            ("GET", "/national/workflows/definitions/{definition_id}", "getDefinition", "detail"),
            ("DELETE", "/national/workflows/definitions/{definition_id}", "deleteDefinition", "detail"),
            ("POST", "/national/workflows/definitions/{definition_id}/execute", "executeWorkflow", "detail"),
            ("POST", "/national/workflows/execute", "executeByType", "detail"),
            ("GET", "/national/workflows/executions", "listExecutions", "list"),
            ("GET", "/national/workflows/executions/{execution_id}", "getExecution", "detail"),
            ("POST", "/national/workflows/executions/{execution_id}/cancel", "cancelExecution", "detail"),
            ("POST", "/national/workflows/executions/{execution_id}/pause", "pauseExecution", "detail"),
        ],
    },
    "pharmacy": {
        "prefix": "/pharmacy/dispense-queue",
        "endpoints": [
            ("GET", "/pharmacy/dispense-queue", "getDispenseQueue", "list"),
            ("POST", "/pharmacy/dispense-queue/{queue_id}/prepare", "prepareDispense", "detail"),
            ("POST", "/pharmacy/dispense-queue/{queue_id}/verify", "verifyDispense", "detail"),
            ("POST", "/pharmacy/dispense-queue/{queue_id}/dispense", "completeDispense", "detail"),
            ("POST", "/pharmacy/dispense-queue/{queue_id}/partial", "partialDispense", "detail"),
            ("POST", "/pharmacy/dispense-queue/{queue_id}/cancel", "cancelDispense", "detail"),
            ("POST", "/pharmacy/dispense-queue/{queue_id}/cancel", "createDispenseRecord", "detail"),
            ("POST", "/pharmacy/dispense-queue/{queue_id}/cancel", "getDispenseRecords", "detail"),
            ("POST", "/pharmacy/dispense-queue/{queue_id}/cancel", "checkInteractions", "detail"),
            ("POST", "/pharmacy/clinical/contraindications/check", "checkContraindications", "detail"),
        ],
    },
    "pilot_platform.api": {
        "prefix": "/pilot-platform/deployments",
        "endpoints": [
            ("GET", "/pilot-platform/pilots", "listPilots", "list"),
            ("GET", "/pilot-platform/pilots/{pilot_id}", "getPilot", "detail"),
            ("PUT", "/pilot-platform/pilots/{pilot_id}/phase", "advancePhase", "detail"),
            ("PUT", "/pilot-platform/pilots/{pilot_id}/phase", "enrollFacility", "detail"),
            ("GET", "/pilot-platform/pilots/{pilot_id}/facilities", "listPilotFacilities", "detail"),
            ("GET", "/pilot-platform/pilots/{pilot_id}/facilities", "assessReadiness", "detail"),
            ("GET", "/pilot-platform/facilities/{facility_id}/readiness", "getFacilityReadiness", "detail"),
            ("GET", "/pilot-platform/facilities/{facility_id}/readiness", "decideGate", "detail"),
            ("GET", "/pilot-platform/pilots/{pilot_id}/gates", "listGates", "detail"),
            ("GET", "/pilot-platform/pilots/{pilot_id}/gates", "recordDeployment", "detail"),
        ],
    },
    "platform": {
        "prefix": "/platform/capabilities",
        "endpoints": [
            ("GET", "/platform/health", "platformHealth", "list"),
            ("GET", "/platform/modules", "platformModules", "list"),
            ("GET", "/platform/capabilities", "platformCapabilities", "list"),
        ],
    },
    "public_health.api": {
        "prefix": "/public-health/surveillance-signals",
        "endpoints": [
            ("GET", "/public-health/disease-cases", "listCases", "list"),
            ("GET", "/public-health/disease-cases/{case_id}", "getCase", "detail"),
            ("GET", "/public-health/disease-cases/stats", "getCaseStats", "list"),
            ("GET", "/public-health/disease-cases/stats", "raiseAlert", "list"),
            ("GET", "/public-health/outbreak-alerts", "listAlerts", "list"),
            ("GET", "/public-health/outbreak-alerts/{alert_id}", "getAlert", "detail"),
            ("PUT", "/public-health/outbreak-alerts/{alert_id}/status", "updateAlertStatus", "detail"),
            ("PUT", "/public-health/outbreak-alerts/{alert_id}/status", "recordSignal", "detail"),
            ("GET", "/public-health/surveillance-signals", "listSignals", "list"),
            ("POST", "/public-health/analyze", "analyzeSurveillance", "detail"),
        ],
    },
    }

    all_modules = {**niam_modules, **legacy_modules, **additional_modules}
    functions: list[str] = []

    for mod_name, mod in sorted(all_modules.items()):
        ns = mod_name.replace("-", "_")
        prefix = mod["prefix"]
        lines.append(f"// ── {mod_name} ──")
        lines.append("")
        lines.append(f"export const {ns}Api = {{")

        for method, route, func_name, _category in mod["endpoints"]:
            # Build the full path
            full_path = prefix + route
            path_params = re.findall(r"\{(\w+)\}", full_path)
            has_path_params = bool(path_params)
            if has_path_params:
                clean_path = re.sub(r"\{(\w+)\}", r"${params.\1}", full_path)
            else:
                clean_path = full_path

            hook_name = func_name[0].upper() + func_name[1:]

            if method == "GET":
                if has_path_params:
                    sig = "params: Record<string, string | number>"
                    call = f"  {func_name}: ({sig}) =>\n    api.get(`{clean_path}`).then(r => r.data),"
                    hook_sig = f"({sig})"
                    hook_call = f"({{ queryKey: [, , p] }}) => {ns}Api.{func_name}(p as Record<string, string | number>)"
                    query_key = f"['{ns}', '{func_name}', params]"
                else:
                    sig = ""
                    call = f"  {func_name}: () =>\n    api.get(`{clean_path}`).then(r => r.data),"
                    hook_sig = "()"
                    hook_call = f"() => {ns}Api.{func_name}()"
                    query_key = f"['{ns}', '{func_name}']"
                lines.append(call)
                functions.append(
                    f"export function use{ns[0].upper() + ns[1:]}{hook_name}{hook_sig} {{\n"
                    f"  return useQuery({{\n"
                    f"    queryKey: {query_key},\n"
                    f"    queryFn: {hook_call},\n"
                    f"  }});\n"
                    f"}}"
                )
            else:
                if has_path_params:
                    sig = "data: unknown, params: Record<string, string | number>"
                    call = f"  {func_name}: ({sig}) =>\n    api.{method.lower()}(`{clean_path}`, data).then(r => r.data),"
                    mutation_call = "(variables: { data: unknown; params: Record<string, string | number> }) =>" + \
                                    f" {ns}Api.{func_name}(variables.data, variables.params)"
                else:
                    sig = "data: unknown"
                    call = f"  {func_name}: ({sig}) =>\n    api.{method.lower()}(`{clean_path}`, data).then(r => r.data),"
                    mutation_call = "(data: unknown) =>" + \
                                    f" {ns}Api.{func_name}(data)"
                lines.append(call)
                functions.append(
                    f"export function use{ns[0].upper() + ns[1:]}{hook_name}" +
                    "() {\n"
                    f"  const queryClient = useQueryClient();\n"
                    f"  return useMutation({{\n"
                    f"    mutationFn: {mutation_call},\n"
                    f"    onSuccess: () => queryClient.invalidateQueries({{ queryKey: ['{ns}'] }}),\n"
                    f"  }});\n"
                    f"}}"
                )

        lines.append("};")
        lines.append("")

    # Add hook exports
    lines.append("// ── React Query Hooks ──")
    lines.append("")
    lines.extend(functions)
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

    # Generate types
    types_ts = generate_types()
    (FRONTEND_DIR / "types.ts").write_text(types_ts)
    num_types = types_ts.count("export interface ") + types_ts.count("export type ")
    print(f"Generated types.ts — {num_types} types")

    # Generate API client
    api_ts = generate_api_client()
    (FRONTEND_DIR / "client.ts").write_text(api_ts)
    num_fns = api_ts.count("export function use")
    print(f"Generated client.ts — {num_fns} hooks")

    # Generate barrel export
    index_content = """// AUTO-GENERATED — DO NOT EDIT
export * from "./types";
export * from "./client";
"""
    (FRONTEND_DIR / "index.ts").write_text(index_content)
    print(f"Generated index.ts")
    print(f"\nAll outputs in {FRONTEND_DIR}")


if __name__ == "__main__":
    import os
    main()
