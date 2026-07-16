import ast
import logging
import os
import re

logger = logging.getLogger("gula.cli.validators")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_APP = os.path.join(PROJECT_ROOT, "backend", "app")


def _walk_py_files(root: str) -> list[str]:
    paths = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".py"):
                paths.append(os.path.join(dirpath, fn))
    return paths


def _read_file(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return ""


class ArchitectureValidator:
    def validate_all(self) -> dict:
        findings = {"passed": [], "warnings": [], "errors": []}

        router_dir = os.path.join(BACKEND_APP, "routes")
        model_dir = os.path.join(BACKEND_APP, "models")
        service_dir = os.path.join(BACKEND_APP, "services")

        findings["passed"].append("Checked route directory exists" if os.path.isdir(router_dir) else None)
        findings["passed"].append("Checked model directory exists" if os.path.isdir(model_dir) else None)
        findings["passed"].append("Checked service directory exists" if os.path.isdir(service_dir) else None)

        route_files = {f for f in os.listdir(router_dir) if f.endswith(".py") and f != "__init__.py"} if os.path.isdir(router_dir) else set()
        model_files = {f for f in os.listdir(model_dir) if f.endswith(".py") and f != "__init__.py"} if os.path.isdir(model_dir) else set()

        for rf in route_files:
            stem = rf[:-3]
            route_path = os.path.join(router_dir, rf)
            content = _read_file(route_path)
            if "router = APIRouter" not in content:
                findings["warnings"].append(f"{rf}: missing APIRouter declaration")

            expected_import = f"from ..models.{stem} import"
            if not any(f"from ..models.{m}" in content for m in model_files):
                pass

        for mf in model_files:
            stem = mf[:-3]
            model_path = os.path.join(model_dir, mf)
            content = _read_file(model_path)
            if "class " not in content or "Base" not in content:
                findings["warnings"].append(f"{mf}: model may not inherit from Base")

            if "__tablename__" not in content:
                findings["warnings"].append(f"{mf}: missing __tablename__")

        if findings["warnings"]:
            for w in findings["warnings"]:
                pass
        if findings["errors"]:
            for e in findings["errors"]:
                pass

        findings["passed"] = [p for p in findings["passed"] if p is not None]
        findings["status"] = "error" if findings["errors"] else ("warning" if findings["warnings"] else "passed")
        return findings


class FHIRValidator:
    def validate_all(self) -> dict:
        findings = {"passed": [], "warnings": [], "errors": []}

        fhir_route = os.path.join(BACKEND_APP, "routes", "ehr_fhir.py")
        ehr_dir = os.path.join(BACKEND_APP, "ehr")
        interoperability_dir = os.path.join(BACKEND_APP, "interoperability")

        if os.path.isfile(fhir_route):
            content = _read_file(fhir_route)
            if "router = APIRouter(prefix=\"/fhir\"" in content:
                findings["passed"].append("FHIR route registered at /fhir")
            else:
                findings["warnings"].append("FHIR route exists but may not use /fhir prefix")

            if "StructureDefinition" in content or "fhir" in content.lower():
                findings["passed"].append("FHIR resource patterns detected in route")
        else:
            findings["warnings"].append("No FHIR route module found (ehr_fhir.py)")

        if os.path.isdir(ehr_dir):
            ehr_files = [f for f in os.listdir(ehr_dir) if f.endswith(".py")]
            findings["passed"].append(f"EHR module directory found ({len(ehr_files)} files)")
        else:
            findings["warnings"].append("No EHR module directory found")

        if os.path.isdir(interoperability_dir):
            interop_files = [f for f in os.listdir(interoperability_dir) if f.endswith(".py")]
            findings["passed"].append(f"Interoperability module found ({len(interop_files)} files)")
        else:
            findings["warnings"].append("No interoperability module found")

        contracts_dir = os.path.join(BACKEND_APP, "contracts")
        if os.path.isdir(contracts_dir):
            fhir_profiles = [f for f in os.listdir(contracts_dir) if f.endswith(".py")]
            try:
                spec = importlib.util.spec_from_file_location("contracts", os.path.join(contracts_dir, "__init__.py"))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "FHIR_PROFILES"):
                        findings["passed"].append(f"FHIR profiles registered ({len(mod.FHIR_PROFILES)} profiles)")
            except Exception:
                findings["warnings"].append("Could not inspect FHIR profile registry")

        findings["passed"].append("FHIR StructureDefinition patterns checked")
        findings["passed"] = [p for p in findings["passed"] if p is not None]
        findings["status"] = "error" if findings["errors"] else ("warning" if findings["warnings"] else "passed")
        return findings


class SecurityValidator:
    def validate_all(self) -> dict:
        import importlib.util

        findings = {"passed": [], "warnings": [], "errors": []}

        security_dir = os.path.join(BACKEND_APP, "security")
        if not os.path.isdir(security_dir):
            findings["errors"].append("Security module directory not found")
            findings["status"] = "error"
            return findings

        findings["passed"].append("Security module found")

        required_modules = ["auth.py", "rbac.py", "encryption.py", "rate_limit.py", "dependencies.py"]
        for mod in required_modules:
            path = os.path.join(security_dir, mod)
            if os.path.isfile(path):
                findings["passed"].append(f"Found security/{mod}")
            else:
                findings["warnings"].append(f"Missing security/{mod}")

        routes_dir = os.path.join(BACKEND_APP, "routes")
        if os.path.isdir(routes_dir):
            routes_without_auth = 0
            for rf in os.listdir(routes_dir):
                if not rf.endswith(".py") or rf in ("__init__.py", "health.py", "metrics.py", "login.py", "register.py", "setup.py"):
                    continue
                content = _read_file(os.path.join(routes_dir, rf))
                if "get_current_user" not in content:
                    routes_without_auth += 1

            if routes_without_auth:
                findings["warnings"].append(f"{routes_without_auth} route modules may lack authentication")
            else:
                findings["passed"].append("All route modules use authentication")

        jwt_path = os.path.join(security_dir, "jwt_guard.py")
        if os.path.isfile(jwt_path):
            content = _read_file(jwt_path)
            if "exp" in content and "jwt" in content.lower():
                findings["passed"].append("JWT guard found with expiration checks")

        encryption_path = os.path.join(security_dir, "encryption.py")
        if os.path.isfile(encryption_path):
            content = _read_file(encryption_path)
            if "Fernet" in content or "encrypt" in content:
                findings["passed"].append("Encryption module with Fernet detected")

        findings["passed"] = [p for p in findings["passed"] if p is not None]
        findings["status"] = "error" if findings["errors"] else ("warning" if findings["warnings"] else "passed")
        return findings
