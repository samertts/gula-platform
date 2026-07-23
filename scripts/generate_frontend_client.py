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

    all_modules = {**niam_modules, **legacy_modules}
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
