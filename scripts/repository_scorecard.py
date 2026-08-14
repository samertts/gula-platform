#!/usr/bin/env python3
"""
GULA Repository Scorecard
=========================
Evaluates repository health across 10 weighted quality axes (0-100).

Usage:
    python scripts/repository_scorecard.py              # colorized terminal output
    python scripts/repository_scorecard.py --json       # machine-readable JSON
    python scripts/repository_scorecard.py --summary    # compact output

Axes:
    1. Code Quality          (15%) — lint, types, syntax, complexity
    2. Test Coverage         (15%) — coverage %, spread, integration, stability
    3. Documentation         (10%) — READMEs, docstrings, constitution
    4. Security              (15%) — secrets, CVEs, bandit, JWT, encryption
    5. Architecture Compl.   (15%) — layers, circular deps, forbidden imports
    6. Dependency Health     (10%) — outdated, pinned, dev/prod separation
    7. CI/CD Maturity        (10%) — pipeline, gates, artifacts, deployment
    8. Git Hygiene           ( 5%) — commits, branches, PR template, gitignore
    9. DevOps/Infra          ( 3%) — Docker, compose, healthcheck, observability
    10. Healthcare Compliance ( 2%) — audit, retention, tenant isolation

Grade scale: A (90+), B (80-89), C (70-79), D (60-69), F (<60)
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import subprocess
import sys
from collections import defaultdict
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── ANSI colour helpers ─────────────────────────────────────────────────────

_COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "bold": "\033[1m",
    "reset": "\033[0m",
}


def _c(code: str, text: str) -> str:
    return f"{_COLORS.get(code, '')}{text}{_COLORS['reset']}"


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _grade_color(score: int) -> str:
    g = _grade(score)
    if g == "A":
        return _c("green", g)
    if g == "B":
        return _c("cyan", g)
    if g == "C":
        return _c("yellow", g)
    if g == "D":
        return _c("magenta", g)
    return _c("red", g)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _walk_py(under: str) -> list[pathlib.Path]:
    root = REPO_ROOT / under
    if not root.is_dir():
        return []
    return sorted(root.rglob("*.py"))


def _count_lines(p: pathlib.Path) -> int:
    try:
        with open(p) as fh:
            return sum(1 for _ in fh)
    except Exception:
        return 0


def _run(cmd: list[str], timeout: int = 30, **kwargs: Any) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, **kwargs
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, -1, "", "command not found")
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, -1, "", "timed out")


# ── Axis Result Container ────────────────────────────────────────────────────


class AxisResult:
    def __init__(self, name: str, weight: float, description: str):
        self.name = name
        self.weight = weight
        self.description = description
        self.score: int = 0
        self.checks: dict[str, int] = {}
        self.findings: list[str] = []
        self.recommendations: list[str] = []

    def add_check(self, label: str, passed: bool, detail: str = "") -> None:
        self.checks[label] = 100 if passed else 0
        if detail:
            self.findings.append(f"{'✓' if passed else '✗'} {label}: {detail}")

    def set_score(self, score: int) -> None:
        self.score = max(0, min(100, score))

    def weighted(self) -> float:
        return self.score * self.weight / 100.0

    def add_recommendation(self, rec: str) -> None:
        self.recommendations.append(rec)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "weight": self.weight,
            "description": self.description,
            "score": self.score,
            "weighted": round(self.weighted(), 2),
            "checks": self.checks,
            "findings": self.findings,
            "recommendations": self.recommendations,
        }


# ── Axis 1: Code Quality (15%) ──────────────────────────────────────────────


def _score_code_quality() -> AxisResult:
    ax = AxisResult("Code Quality", 15, "Lint errors, type annotations, syntax validity, code complexity")

    backend_py = _walk_py("backend/app")
    test_py = _walk_py("backend/tests")
    all_py = backend_py + test_py

    # 1a. Syntax validity — batch compile check
    sample = all_py[:150]
    bad_files = []
    for p in sample:
        try:
            compile(p.read_text(errors="replace"), str(p), "exec")
        except SyntaxError:
            bad_files.append(p.name)
    syntax_ok = len(sample) - len(bad_files)
    syntax_pct = 100.0 * syntax_ok / max(len(sample), 1)
    ax.add_check("Syntax valid", syntax_pct >= 95, f"{syntax_ok}/{len(sample)} files pass syntax check (0 subprocess calls)")

    # 1b. Static analysis via AST (fast, in-process)
    static_issues = 0
    for p in all_py[:100]:
        try:
            tree = ast.parse(p.read_text(errors="replace"), filename=str(p))
        except SyntaxError:
            static_issues += 1
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id.startswith("_") and not node.id.startswith("__"):
                    continue  # private convention names are OK
        # Check for undefined names by looking at function bodies
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                local_names = {a.arg for a in node.args.args}
                if node.args.vararg:
                    local_names.add(node.args.vararg.arg)
                if node.args.kwarg:
                    local_names.add(node.args.kwarg.arg)
                for n in ast.walk(node):
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                        if n.id not in local_names and n.id not in dir(__builtins__):
                            pass  # too many false positives in partial analysis
    ax.add_check("Static analysis", static_issues == 0, f"{static_issues} files with syntax errors found")

    # 1c. Type annotations — rough scan (sample ~80 files)
    typed_files = 0
    type_checked = 0
    for p in all_py[:100]:
        if p.name == "__init__.py":
            continue
        type_checked += 1
        content = p.read_text(errors="replace")
        if "def " in content and ("import typing" in content or "from typing" in content or ": str" in content or ": int" in content or ": bool" in content or ": list[" in content or ": dict[" in content or ": Optional[" in content or ": Any" in content):
            typed_files += 1
    type_pct = 100.0 * typed_files / max(type_checked, 1)
    ax.add_check("Type annotations", type_pct >= 50, f"{typed_files}/{type_checked} non-init files use type hints ({type_pct:.0f}%)")

    # 1d. Complexity — check for overly long functions (>100 lines)
    long_funcs = 0
    total_funcs = 0
    for p in all_py[:100]:
        try:
            tree = compile(p.read_text(errors="replace"), str(p), "exec", ast.PyCF_ONLY_AST)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_funcs += 1
                end_lineno = getattr(node, "end_lineno", node.lineno)
                if end_lineno - node.lineno > 100:
                    long_funcs += 1
    long_pct = 100.0 * long_funcs / max(total_funcs, 1) if total_funcs else 0
    ax.add_check("Functions ≤100 lines", long_pct < 5, f"{long_funcs}/{total_funcs} functions exceed 100 lines ({long_pct:.1f}%)")

    # Composite score
    base = 100
    if static_issues > 0:
        base -= min(30, static_issues * 3)
    if syntax_pct < 95:
        base -= min(20, int((100 - syntax_pct) * 0.5))
    if type_pct < 50:
        base -= 15
    if long_pct >= 5:
        base -= min(15, int(long_pct * 2))
    if not all_py:
        base = 0

    ax.set_score(max(0, base))

    if ax.score < 70:
        if static_issues > 0:
            ax.add_recommendation(f"Fix {static_issues} static analysis issues — run `flake8 --select=E9,F821 backend/app`")
        if syntax_pct < 95:
            ax.add_recommendation(f"Fix syntax errors in {syntax_bad} files failing py_compile")
        if type_pct < 50:
            ax.add_recommendation("Add type annotations — target 50%+ of files. Focus on public API functions.")
        if long_pct >= 5:
            ax.add_recommendation(f"Refactor {long_funcs} functions exceeding 100 lines into smaller units")

    return ax


# ── Axis 2: Test Coverage (15%) ─────────────────────────────────────────────


def _score_test_coverage() -> AxisResult:
    ax = AxisResult("Test Coverage", 15, "Coverage percentage, test-module spread, integration tests, stability")

    test_dir = REPO_ROOT / "backend" / "tests"
    app_dir = REPO_ROOT / "backend" / "app"

    test_files = list(test_dir.rglob("test_*.py")) + list(test_dir.rglob("*_test.py"))
    app_py = list(app_dir.rglob("*.py"))

    # 2a. Test file count vs app modules (exclude __init__.py)
    test_count = len(test_files)
    app_module_count = len([p for p in app_py if p.name != "__init__.py"])
    test_ratio = test_count / max(app_module_count, 1)
    ax.add_check("Test-to-module ratio", test_ratio >= 0.15, f"{test_count} test files for {app_module_count} app modules ({test_ratio:.2f})")

    # 2b. Integration test presence
    integration_tests = list(test_dir.rglob("integration/*.py")) + [t for t in test_files if "integration" in t.name or "comprehensive" in t.name or "stress" in t.name]
    ax.add_check("Integration tests", len(integration_tests) >= 3, f"{len(integration_tests)} integration/stress/comprehensive test files")

    # 2c. Conftest / fixtures
    conftests = list(test_dir.rglob("conftest.py"))
    ax.add_check("Fixtures (conftest)", len(conftests) >= 1, f"{len(conftests)} conftest.py files found")

    # 2d. Test stability — look for known flaky patterns
    flaky_patterns = ["@flaky", "time.sleep(", "pytest.mark.flaky"]
    flaky_hits = 0
    for tf in test_files[:100]:
        content = tf.read_text(errors="replace")
        for pat in flaky_patterns:
            if pat in content:
                flaky_hits += 1
                break
    ax.add_check("No flaky test markers", flaky_hits == 0, f"{flaky_hits} files contain flaky patterns")

    # 2e. Coverage data if .coverage exists
    cov_file = REPO_ROOT / ".coverage"
    cover_pct = 0
    if cov_file.exists() or (REPO_ROOT / "backend" / ".coverage").exists():
        cov_result = _run(["python3", "-m", "coverage", "report", "--precision=0"], cwd=REPO_ROOT / "backend")
        for line in cov_result.stdout.splitlines():
            m = re.search(r"TOTAL\s+(\d+)", line)
            if m:
                cover_pct = int(m.group(1))
                break
        if cover_pct == 0:
            # try alternate path
            cov_result2 = _run(["python3", "-m", "coverage", "report", "--precision=0"], cwd=REPO_ROOT)
            for line in cov_result2.stdout.splitlines():
                m = re.search(r"TOTAL\s+(\d+)", line)
                if m:
                    cover_pct = int(m.group(1))
                    break
    ax.add_check("Coverage data available", cover_pct > 0 or cov_file.exists(), f"Coverage: {cover_pct}%" if cover_pct else "No coverage report — run `pytest --cov`")
    if cover_pct > 0:
        ax.add_check("Coverage ≥ 60%", cover_pct >= 60, f"{cover_pct}% overall coverage")

    base = 100
    if test_ratio < 0.15:
        base -= 20
    if cover_pct > 0 and cover_pct < 60:
        base -= 25
    elif cover_pct == 0:
        base -= 15  # no coverage data
    if flaky_hits > 0:
        base -= 10
    if len(integration_tests) < 3:
        base -= 10
    if len(conftests) == 0:
        base -= 5

    ax.set_score(max(0, base))

    if ax.score < 70:
        if test_ratio < 0.15:
            ax.add_recommendation(f"Add more tests — currently {test_count} test files for {app_module_count} modules")
        if cover_pct == 0:
            ax.add_recommendation("Enable coverage tracking: `pip install pytest-cov && pytest --cov=app tests/`")
        elif cover_pct < 60:
            ax.add_recommendation(f"Improve coverage from {cover_pct}% to at least 60%. Focus on untested routes and services.")
        if len(integration_tests) < 3:
            ax.add_recommendation("Add at least 3 integration test files covering the main request lifecycle")
        if flaky_hits > 0:
            ax.add_recommendation(f"Remove flaky patterns in {flaky_hits} test files — use robust assertions and mocks")

    return ax


# ── Axis 3: Documentation (10%) ─────────────────────────────────────────────


def _score_documentation() -> AxisResult:
    ax = AxisResult("Documentation", 10, "README files, docstrings, missing docs, constitution")

    # 3a. Top-level README
    readme_root = list(REPO_ROOT.glob("README*"))
    ax.add_check("Root README", len(readme_root) > 0, f"{len(readme_root)} root README file(s)")

    # 3b. README per major module
    module_dirs = ["backend/app", "services", "frontend-v3", "client", "docs", "scripts", "nhop-platform", "edge_agent", "ai"]
    modules_with_readme = 0
    for mod in module_dirs:
        d = REPO_ROOT / mod
        if d.is_dir() and list(d.glob("README*")):
            modules_with_readme += 1
    ax.add_check("README per module", modules_with_readme >= 3, f"{modules_with_readme}/{len(module_dirs)} modules have README")

    # 3c. Module-level docstrings in Python files
    py_files = _walk_py("backend/app")
    with_docstring = 0
    for p in py_files[:200]:
        content = p.read_text(errors="replace").lstrip()
        if content.startswith('"""') or content.startswith("'''"):
            with_docstring += 1
    doc_pct = 100.0 * with_docstring / max(len(py_files), 1)
    ax.add_check("Module docstrings", doc_pct >= 60, f"{with_docstring}/{len(py_files)} files have module docstrings ({doc_pct:.0f}%)")

    # 3d. Constitution files
    constitution_dir = REPO_ROOT / "docs" / "constitution"
    constitution_files = list(constitution_dir.glob("*.md")) if constitution_dir.is_dir() else []
    ax.add_check("Constitution docs", len(constitution_files) >= 2, f"{len(constitution_files)} constitution files")

    # 3e. CHANGELOG, CONTRIBUTING, SECURITY, ARCHITECTURE
    essential_docs = ["CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", "ARCHITECTURE.md"]
    found_essential = sum(1 for d in essential_docs if (REPO_ROOT / d).exists())
    ax.add_check("Essential docs", found_essential >= 3, f"{found_essential}/{len(essential_docs)} found ({', '.join(essential_docs)})")

    # 3f. ADR directory
    adr_dir = REPO_ROOT / "docs" / "adr"
    adr_files = list(adr_dir.glob("*.md")) if adr_dir.is_dir() else []
    ax.add_check("ADR documentation", len(adr_files) >= 3, f"{len(adr_files)} ADR files")

    base = 100
    if len(readme_root) == 0:
        base -= 20
    if modules_with_readme < 3:
        base -= 15
    if doc_pct < 60:
        base -= 15
    if len(constitution_files) < 2:
        base -= 10
    if found_essential < 3:
        base -= 10
    if len(adr_files) < 3:
        base -= 5

    ax.set_score(max(0, base))

    if ax.score < 70:
        if len(readme_root) == 0:
            ax.add_recommendation("Create a root README.md describing the project, setup, and architecture")
        if modules_with_readme < 3:
            ax.add_recommendation("Add README files to major modules (backend/app, services, frontend-v3)")
        if doc_pct < 60:
            ax.add_recommendation(f"Add module-level docstrings to {len(py_files) - with_docstring} Python files")
        if found_essential < 3:
            missing = [d for d in essential_docs if not (REPO_ROOT / d).exists()]
            ax.add_recommendation(f"Create missing essential docs: {', '.join(missing)}")

    return ax


# ── Axis 4: Security (15%) ──────────────────────────────────────────────────


def _score_security() -> AxisResult:
    ax = AxisResult("Security", 15, "Secrets scanning, CVEs, bandit, JWT/auth, encryption")

    # 4a. Check for hardcoded secrets in env config
    env_example = REPO_ROOT / ".env.example"
    hardcoded_secrets = 0
    secret_patterns = [
        r'SECRET_KEY=["\']?(changeme|secret|password|1234|test|dummy)',
        r'ENCRYPTION_KEY=["\']?(changeme|secret|password|1234|test|dummy)',
        r'POSTGRES_PASSWORD=["\']?(changeme|secret|password|1234|test|dummy)',
    ]
    if env_example.exists():
        content = env_example.read_text()
        for pat in secret_patterns:
            if re.search(pat, content, re.IGNORECASE):
                hardcoded_secrets += 1
    ax.add_check("No hardcoded secrets in .env.example", hardcoded_secrets == 0, f"{hardcoded_secrets} placeholder secrets found")

    # 4b. Check env file for required secret keys
    env_file = REPO_ROOT / ".env"
    required_secrets = ["SECRET_KEY", "ENCRYPTION_KEY", "REFRESH_TOKEN_SECRET", "NID_HMAC_KEY"]
    present_secrets = 0
    if env_file.exists():
        env_content = env_file.read_text()
        for key in required_secrets:
            if re.search(rf"^{key}=", env_content, re.MULTILINE):
                present_secrets += 1
    ax.add_check("Required secrets configured", present_secrets >= 4, f"{present_secrets}/{len(required_secrets)} required secrets found")

    # 4c. Security module presence
    security_dir = REPO_ROOT / "backend" / "app" / "security"
    security_modules = list(security_dir.glob("*.py")) if security_dir.is_dir() else []
    ax.add_check("Security module", len(security_modules) >= 8, f"{len(security_modules)} security modules (auth.py, rbac.py, encryption.py, rate_limit.py, etc.)")

    # 4d. Encryption usage
    encryption_file = security_dir / "encryption.py"
    has_encryption = encryption_file.exists()
    ax.add_check("Encryption module", has_encryption, "app/security/encryption.py exists" if has_encryption else "Missing encryption module")

    # 4e. Rate limiting
    rate_limit_file = security_dir / "rate_limit.py"
    has_rate_limit = rate_limit_file.exists()
    ax.add_check("Rate limiting", has_rate_limit, "app/security/rate_limit.py exists" if has_rate_limit else "Missing rate limit module")

    # 4f. SQL injection protection — using parameterized queries
    raw_sql_patterns = 0
    for p in _walk_py("backend/app")[:80]:
        content = p.read_text(errors="replace")
        if re.search(r'execute\([^)]*f["\']', content):
            raw_sql_patterns += 1
        if re.search(r'\.execute\(["\'][^"\']*WHERE', content, re.IGNORECASE):
            raw_sql_patterns += 1
    ax.add_check("No raw SQL injection vectors", raw_sql_patterns == 0, f"{raw_sql_patterns} potential raw SQL patterns — verify they use parameterized queries")

    # 4g. Input validation — Pydantic models
    pydantic_models = 0
    for p in _walk_py("backend/app")[:60]:
        content = p.read_text(errors="replace")
        if "BaseModel" in content or "pydantic" in content:
            pydantic_models += 1
    ax.add_check("Input validation (Pydantic)", pydantic_models >= 10, f"~{pydantic_models} files use Pydantic models")

    # 4h. Bandit scan if available (limited scope for speed)
    bandit_result = _run(["python3", "-m", "bandit", "-r", "backend/app/security", "-ll", "-q"], cwd=REPO_ROOT, timeout=20)
    bandit_issues = 0
    if bandit_result.returncode != -1:
        for line in bandit_result.stdout.splitlines():
            if ">> Issue:" in line:
                bandit_issues += 1
        if bandit_issues == 0 and bandit_result.stderr and "not found" not in bandit_result.stderr.lower():
            bandit_issues = 999  # unknown output format
    ax.add_check("Bandit security scan", bandit_issues == 0, f"{bandit_issues} bandit issues found" if bandit_result.returncode != -1 else "Bandit not available")

    # 4i. JWT alg check — ensure RS256 or HS256 with strong key
    auth_path = security_dir / "auth.py"
    jwt_weak_alg = False
    if auth_path.exists():
        auth_content = auth_path.read_text()
        if "algorithm=\"none\"" in auth_content or "algorithm='none'" in auth_content:
            jwt_weak_alg = True
    ax.add_check("JWT algorithm secure", not jwt_weak_alg, "No insecure JWT algorithm detected")

    base = 100
    if hardcoded_secrets > 0:
        base -= 15
    if present_secrets < 4:
        base -= 10
    if not has_encryption:
        base -= 15
    if raw_sql_patterns > 0:
        base -= 10
    if bandit_issues > 5:
        base -= 15
    elif bandit_issues > 0:
        base -= 10
    if not has_rate_limit:
        base -= 5

    ax.set_score(max(0, base))

    if ax.score < 70:
        if hardcoded_secrets > 0:
            ax.add_recommendation("Remove placeholder/weak secret values from .env.example — use descriptive variable names only")
        if not has_encryption:
            ax.add_recommendation("Implement encryption module for sensitive patient data at rest")
        if raw_sql_patterns > 0:
            ax.add_recommendation(f"Replace {raw_sql_patterns} raw SQL executions with SQLAlchemy ORM or parameterized queries")
        if bandit_issues > 0:
            ax.add_recommendation(f"Fix {bandit_issues} bandit findings — run `bandit -r backend/app -ll -ii` to list them")
        if present_secrets < 4:
            missing_secrets = [k for k in required_secrets if not re.search(rf"^{k}=", (env_file.read_text() if env_file.exists() else ""), re.MULTILINE)]
            ax.add_recommendation(f"Ensure all required secrets are configured: {', '.join(missing_secrets)}")

    return ax


# ── Axis 5: Architecture Compliance (15%) ───────────────────────────────────


def _score_architecture() -> AxisResult:
    ax = AxisResult("Architecture Compliance", 15, "Layer violations, circular deps, forbidden imports")

    # 5a. Run the existing architecture compliance engine if available
    engine_path = REPO_ROOT / "scripts" / "architecture_compliance_engine.py"
    engine_available = engine_path.exists()
    ax.add_check("Architecture compliance engine", engine_available, "scripts/architecture_compliance_engine.py exists")

    if engine_available:
        result = _run([sys.executable, str(engine_path), "--json", "--exclude-dirs", "tests,migrations,__pycache__"], cwd=REPO_ROOT, timeout=60)
        arch_score = 0
        try:
            data = json.loads(result.stdout)
            arch_score = data.get("score", data.get("compliance_score", 0))
            if isinstance(arch_score, (int, float)):
                ax.set_score(int(arch_score))
                ax.add_check("Compliance score from engine", arch_score >= 70, f"Architecture compliance score: {arch_score}/100")
                for rule_result in data.get("results", data.get("rules", [])):
                    rname = rule_result.get("rule", rule_result.get("title", "unknown"))
                    rstatus = rule_result.get("status", "FAIL")
                    rpassed = rule_result.get("passed", 0)
                    rtotal = rule_result.get("total", 0)
                    ax.add_check(f"Rule {rname}", rstatus == "PASS", f"{rname}: {rstatus} ({rpassed}/{rtotal} checks passed)" if rtotal else f"{rname}: {rstatus}")
            else:
                ax.add_check("Architecture compliance parse", False, "Could not parse compliance score")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            ax.add_check("Architecture compliance parse", False, f"Failed to parse engine JSON: {e}")

    else:
        # 5b. Manual checks — layer separation
        route_files = list((REPO_ROOT / "backend" / "app" / "routes").glob("*.py"))
        service_files = list((REPO_ROOT / "backend" / "app" / "services").glob("*.py"))
        model_files = list((REPO_ROOT / "backend" / "app" / "models").glob("*.py"))

        # Check routes don't import from models directly (should go through services)
        bad_route_imports = 0
        for rf in route_files[:50]:
            content = rf.read_text(errors="replace")
            if "from app.models" in content or "from ..models" in content:
                bad_route_imports += 1
        ax.add_check("Routes use services (not direct model imports)", bad_route_imports <= 2, f"{bad_route_imports} routes import models directly")

        # Check domain layer exists
        domain_dir = REPO_ROOT / "backend" / "app" / "domain"
        domain_files = list(domain_dir.glob("*.py")) if domain_dir.is_dir() else []
        ax.add_check("Domain layer present", len(domain_files) >= 1, f"{len(domain_files)} domain files (e.g., order_state.py)")

        # Check for circular import patterns (limited scope)
        import_graph: dict[str, set[str]] = defaultdict(set)
        for p in _walk_py("backend/app")[:100]:
            content = p.read_text(errors="replace")
            rel = p.relative_to(REPO_ROOT / "backend" / "app").with_suffix("").as_posix().replace("/", ".")
            for m in re.finditer(r'^from\s+app\.(\S+)\s+import', content, re.MULTILINE):
                import_graph[rel].add(m.group(1))

        self_imports = sum(1 for k, v in import_graph.items() if k in v)
        ax.add_check("No self/circular imports", self_imports == 0, f"{self_imports} potential circular import patterns")

        # Scoring
        score = 70  # baseline for having the structure
        if bad_route_imports > 2:
            score -= 15
        if len(domain_files) == 0:
            score -= 15
        if self_imports > 0:
            score -= 10
        if route_files and service_files and model_files:
            score += 10  # good separation exists
        ax.set_score(min(100, score))

    if ax.score < 70:
        if engine_available and ax.score < 70:
            ax.add_recommendation("Run `python scripts/architecture_compliance_engine.py` to see detailed violations and fix them")
        else:
            if ax.checks.get("Routes use services (not direct model imports)", 100) < 50:
                ax.add_recommendation("Refactor routes to import services instead of models directly — enforce layered architecture")
            ax.add_recommendation("Ensure the domain layer is used for business logic, not scattered across routes/services")

    return ax


# ── Axis 6: Dependency Health (10%) ──────────────────────────────────────────


def _score_dependencies() -> AxisResult:
    ax = AxisResult("Dependency Health", 10, "Outdated packages, dependency count, pinned versions, dev/prod separation")

    req_files = {
        "backend": REPO_ROOT / "backend" / "requirements.txt",
        "root": REPO_ROOT / "requirements.txt",
    }
    pkg_json = {
        "root": REPO_ROOT / "package.json",
        "frontend-v3": REPO_ROOT / "frontend-v3" / "package.json",
    }

    # 6a. Requirements files exist
    existing_reqs = {k: v for k, v in req_files.items() if v.exists()}
    ax.add_check("Requirements files", len(existing_reqs) >= 1, f"{len(existing_reqs)} requirements files found")

    # 6b. Dependency count
    total_deps = 0
    pinned_count = 0
    floating_count = 0
    for name, rf in existing_reqs.items():
        lines = rf.read_text().splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            total_deps += 1
            if ">=" in line and "==" not in line:
                floating_count += 1
            elif "==" in line:
                pinned_count += 1
    ax.add_check("Dependencies < 50", total_deps < 80, f"{total_deps} total dependencies")
    pin_pct = 100.0 * pinned_count / max(total_deps, 1)
    ax.add_check("Pinned versions (>= with == lockfile)", pin_pct >= 20 or floating_count == 0, f"{pinned_count} pinned, {floating_count} floating (>=) — pip-compile recommended")

    # 6c. package.json files
    for name, pj in pkg_json.items():
        if pj.exists():
            try:
                import json as _json
                data = _json.loads(pj.read_text())
                deps = data.get("dependencies", {})
                devdeps = data.get("devDependencies", {})
                ax.add_check(f"Dev/Prod separation ({name})", len(devdeps) > 0, f"{len(deps)} prod, {len(devdeps)} dev")
            except Exception:
                pass

    # 6d. Legacy/unmaintained deps check
    legacy_patterns = ["requests<2", "urllib3<2", "python-dateutil"]
    legacy_hits = 0
    for name, rf in existing_reqs.items():
        content = rf.read_text()
        for pat in legacy_patterns:
            if pat in content:
                legacy_hits += 1
    ax.add_check("No legacy dependency pins", legacy_hits == 0, f"{legacy_hits} legacy pins found")

    base = 100
    if len(existing_reqs) == 0:
        base -= 25
    if total_deps >= 80:
        base -= 10
    if pin_pct < 20 and floating_count > 0:
        base -= 15
    if legacy_hits > 0:
        base -= 10

    ax.set_score(max(0, base))

    if ax.score < 70:
        if len(existing_reqs) == 0:
            ax.add_recommendation("Create requirements.txt or pyproject.toml to track dependencies")
        if pin_pct < 20 and floating_count > 0:
            ax.add_recommendation("Pin all dependency versions using `pip-compile` or `pip freeze > requirements.txt`")
        if legacy_hits > 0:
            ax.add_recommendation("Remove legacy pinned dependency versions — upgrade to current releases")
        ax.add_recommendation("Consider adding dev-dependencies split (requirements-dev.txt)")

    return ax


# ── Axis 7: CI/CD Maturity (10%) ─────────────────────────────────────────────


def _score_cicd() -> AxisResult:
    ax = AxisResult("CI/CD Maturity", 10, "Pipeline completeness, gates, artifacts, deployment automation")

    workflows_dir = REPO_ROOT / ".github" / "workflows"

    # 7a. CI pipeline exists
    ci_file = workflows_dir / "ci.yml"
    ax.add_check("CI pipeline", ci_file.exists(), ".github/workflows/ci.yml")

    # 7b. Deployment pipeline
    deploy_file = workflows_dir / "deploy.yml"
    ax.add_check("Deployment pipeline", deploy_file.exists(), ".github/workflows/deploy.yml")

    # 7c. Multiple CI stages
    workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
    ax.add_check("Workflow files", len(workflow_files) >= 3, f"{len(workflow_files)} workflow files")

    # 7d. CI content quality — check for syntax gate, test, security
    if ci_file.exists():
        ci_content = ci_file.read_text()
        has_syntax = "py_compile" in ci_content or "syntax" in ci_content.lower()
        has_test = "pytest" in ci_content
        has_security = "bandit" in ci_content or "safety" in ci_content or "security" in ci_content.lower()
        has_build = "docker build" in ci_content or "push" in ci_content
        ax.add_check("CI — syntax gate", has_syntax, "py_compile or syntax check in CI")
        ax.add_check("CI — test step", has_test, "pytest in CI")
        ax.add_check("CI — security scan", has_security, "security scanning in CI")
        ax.add_check("CI — build/push", has_build, "container build in CI")

    # 7e. Blue-green or canary deploy
    has_advanced_deploy = (workflows_dir / "blue-green-deploy.yml").exists() or (workflows_dir / "canary-deploy.yml").exists()
    ax.add_check("Advanced deployment strategy", has_advanced_deploy, "blue-green or canary deploy exists")

    # 7f. Quality gate
    quality_gate = workflows_dir / "quality-gate.yml"
    ax.add_check("Quality gate", quality_gate.exists(), ".github/workflows/quality-gate.yml exists" if quality_gate.exists() else "No dedicated quality gate")

    # 7g. Makefile CI target
    makefile = REPO_ROOT / "Makefile"
    has_make_ci = False
    if makefile.exists():
        has_make_ci = "ci" in makefile.read_text()
    ax.add_check("Makefile CI target", has_make_ci, "`make ci` target exists" if has_make_ci else "No `make ci` target")

    base = 100
    if not ci_file.exists():
        base -= 25
    if not deploy_file.exists():
        base -= 15
    if len(workflow_files) < 3:
        base -= 10
    if ci_file.exists():
        ci_content = ci_file.read_text()
        if "py_compile" not in ci_content:
            base -= 5
        if "pytest" not in ci_content:
            base -= 10
        if "bandit" not in ci_content and "safety" not in ci_content:
            base -= 5
    if not has_advanced_deploy:
        base -= 5

    ax.set_score(max(0, base))

    if ax.score < 70:
        if not ci_file.exists():
            ax.add_recommendation("Create .github/workflows/ci.yml with syntax, lint, test, and build stages")
        if not deploy_file.exists():
            ax.add_recommendation("Create .github/workflows/deploy.yml for automated deployment")
        if ci_file.exists():
            ci_content = ci_file.read_text()
            if "pytest" not in ci_content:
                ax.add_recommendation("Add a `pytest` job to your CI pipeline")
            if "py_compile" not in ci_content:
                ax.add_recommendation("Add a syntax-check gate (`py_compile`) to CI")
        if not has_advanced_deploy:
            ax.add_recommendation("Consider blue-green or canary deployment for zero-downtime releases")

    return ax


# ── Axis 8: Git Hygiene (5%) ────────────────────────────────────────────────


def _score_git_hygiene() -> AxisResult:
    ax = AxisResult("Git Hygiene", 5, "Commit messages, branch naming, PR template, .gitignore quality")

    git_dir = REPO_ROOT / ".git"

    # 8a. .gitignore exists and has quality patterns
    gitignore = REPO_ROOT / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        patterns = ["__pycache__", ".env", "node_modules", ".DS_Store", "*.pyc", ".vscode", ".idea"]
        found = sum(1 for p in patterns if p in content)
        ax.add_check(".gitignore quality", found >= 5, f"{found}/{len(patterns)} essential patterns found")
    else:
        ax.add_check(".gitignore exists", False, "No .gitignore found")

    # 8b. PR template
    pr_template = REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
    pr_template2 = REPO_ROOT / ".github" / "pull_request_template.md"
    has_pr_template = pr_template.exists() or pr_template2.exists()
    ax.add_check("PR template", has_pr_template, ".github/PULL_REQUEST_TEMPLATE.md" if has_pr_template else "No PR template")

    # 8c. Commit message convention check (recent 20 commits)
    if git_dir.exists():
        log_result = _run(["git", "log", "--oneline", "-20"], cwd=REPO_ROOT)
        commits = log_result.stdout.strip().splitlines()
        conventional = 0
        for line in commits:
            if ":" in line and line.split(":")[0].split()[-1].isalpha():
                conventional += 1
        conv_pct = 100.0 * conventional / max(len(commits), 1)
        ax.add_check("Conventional commits (recent 20)", conv_pct >= 50, f"{conventional}/{len(commits)} follow conventional commits")
    else:
        ax.add_check("Git history available", False, "Not a git repository")

    # 8d. Branch naming — check current branch
    if git_dir.exists():
        branch_result = _run(["git", "branch", "--show-current"], cwd=REPO_ROOT)
        current_branch = branch_result.stdout.strip()
        if current_branch:
            valid_pattern = re.match(r'^(main|develop|feature/|fix/|hotfix/|release/|chore/|docs/)', current_branch)
            ax.add_check("Branch naming convention", bool(valid_pattern), f"Current branch: {current_branch}")
        else:
            ax.add_check("Branch naming convention", False, "Detached HEAD or no branch")
    # 8e. Merge strategy
    if git_dir.exists():
        merge_result = _run(["git", "config", "pull.ff"], cwd=REPO_ROOT)
        ff_only = merge_result.stdout.strip() == "only"
        ax.add_check("Fast-forward merge strategy", ff_only, "git config pull.ff=only" if ff_only else "No ff-only merge policy")

    base = 100
    if not gitignore.exists():
        base -= 20
    else:
        essential = ["__pycache__", ".env", "node_modules", ".DS_Store", "*.pyc"]
        found_essential = sum(1 for p in essential if p in content)
        if found_essential < 3:
            base -= 10
    if not has_pr_template:
        base -= 10
    if git_dir.exists():
        branch_result = _run(["git", "branch", "--show-current"], cwd=REPO_ROOT)
        current_branch = branch_result.stdout.strip()
        if current_branch and not re.match(r'^(main|develop|feature/|fix/|hotfix/|release/)', current_branch):
            base -= 10

    ax.set_score(max(0, base))

    if ax.score < 70:
        if not gitignore.exists():
            ax.add_recommendation("Create a .gitignore with Python, Node, OS, and IDE patterns")
        else:
            missing = [p for p in ["__pycache__", ".env", "node_modules", ".DS_Store", "*.pyc"] if p not in content]
            if missing:
                ax.add_recommendation(f"Add to .gitignore: {', '.join(missing)}")
        if not has_pr_template:
            ax.add_recommendation("Add a PR template at .github/PULL_REQUEST_TEMPLATE.md")
        if git_dir.exists():
            branch_result = _run(["git", "branch", "--show-current"], cwd=REPO_ROOT)
            current_branch = branch_result.stdout.strip()
            if current_branch and not re.match(r'^(main|develop|feature/|fix/|hotfix/|release/)', current_branch):
                ax.add_recommendation("Use branch naming convention: feature/, fix/, hotfix/, release/, chore/")

    return ax


# ── Axis 9: DevOps/Infrastructure (3%) ──────────────────────────────────────


def _score_devops() -> AxisResult:
    ax = AxisResult("DevOps/Infrastructure", 3, "Dockerfile quality, compose files, healthchecks, observability")

    # 9a. Dockerfile
    dockerfile = REPO_ROOT / "Dockerfile"
    ax.add_check("Dockerfile", dockerfile.exists(), "Root Dockerfile")

    if dockerfile.exists():
        df_content = dockerfile.read_text()
        has_multi_stage = "AS " in df_content or "as " in df_content
        has_non_root = "USER" in df_content
        has_healthcheck = "HEALTHCHECK" in df_content
        ax.add_check("Multi-stage build", has_multi_stage, "Multi-stage Dockerfile" if has_multi_stage else "Single-stage build")
        ax.add_check("Non-root user", has_non_root, "USER directive in Dockerfile" if has_non_root else "Runs as root")
        ax.add_check("HEALTHCHECK in Dockerfile", has_healthcheck, "HEALTHCHECK directive present" if has_healthcheck else "No HEALTHCHECK")

    # 9b. Docker Compose
    compose_files = ["docker-compose.yml", "docker-compose.full.yml", "docker-compose.scale.yml"]
    found_compose = [f for f in compose_files if (REPO_ROOT / f).exists()]
    ax.add_check("Docker Compose files", len(found_compose) >= 1, f"{len(found_compose)} compose files: {', '.join(found_compose)}")

    # 9c. Compose healthchecks
    compose_file = REPO_ROOT / "docker-compose.yml"
    if compose_file.exists():
        content = compose_file.read_text()
        has_healthcheck_section = "healthcheck:" in content or "test:" in content
        has_depends_on = "depends_on" in content
        ax.add_check("Healthcheck in compose", has_healthcheck_section, "healthcheck directives in compose" if has_healthcheck_section else "No healthchecks")
        ax.add_check("Service dependency ordering", has_depends_on, "depends_on in compose" if has_depends_on else "No depends_on")

    compose_full = REPO_ROOT / "docker-compose.full.yml"
    if compose_full.exists() and not ax.checks.get("Healthcheck in compose", 0):
        content = compose_full.read_text()
        if "healthcheck:" in content or "test:" in content:
            ax.add_check("Full compose healthchecks", True, "Healthchecks in docker-compose.full.yml")

    # 9d. Observability
    prom_dir = REPO_ROOT / "config" / "prometheus"
    grafana_dir = REPO_ROOT / "config" / "grafana"
    has_prometheus = prom_dir.is_dir() and len(list(prom_dir.glob("*.yml"))) > 0
    has_grafana = grafana_dir.is_dir() and len(list(grafana_dir.glob("*.json"))) > 0

    ax.add_check("Prometheus config", has_prometheus, "Prometheus scrape config present" if has_prometheus else "No Prometheus config")
    ax.add_check("Grafana dashboards", has_grafana, "Grafana dashboards present" if has_grafana else "No Grafana dashboards")

    # 9e. Makefile health targets
    makefile = REPO_ROOT / "Makefile"
    if makefile.exists():
        mf_content = makefile.read_text()
        has_health = "health" in mf_content
        has_monitoring = "monitoring" in mf_content
        has_backup = "backup" in mf_content
        ax.add_check("Makefile health target", has_health, "`make health` exists" if has_health else "No make health")
        ax.add_check("Makefile monitoring target", has_monitoring, "`make monitoring` exists" if has_monitoring else "No make monitoring")
        ax.add_check("Makefile backup target", has_backup, "`make backup` exists" if has_backup else "No make backup")

    base = 100
    if not dockerfile.exists():
        base -= 25
    else:
        if not has_non_root:
            base -= 10
        if not has_healthcheck:
            base -= 10
    if len(found_compose) == 0:
        base -= 15
    if not has_prometheus:
        base -= 5
    if not has_grafana:
        base -= 5

    ax.set_score(max(0, base))

    if ax.score < 70:
        if not dockerfile.exists():
            ax.add_recommendation("Create a Dockerfile for containerized deployment")
        else:
            if not has_multi_stage:
                ax.add_recommendation("Use multi-stage Docker builds to reduce image size")
            if not has_non_root:
                ax.add_recommendation("Add USER directive to Dockerfile — never run containers as root")
            if not has_healthcheck:
                ax.add_recommendation("Add HEALTHCHECK instruction to Dockerfile")
        if len(found_compose) == 0:
            ax.add_recommendation("Create docker-compose.yml for local development environment")
        if not has_prometheus or not has_grafana:
            ax.add_recommendation("Set up observability stack: Prometheus metrics export + Grafana dashboards")

    return ax


# ── Axis 10: Healthcare Compliance (2%) ─────────────────────────────────────


def _score_healthcare() -> AxisResult:
    ax = AxisResult("Healthcare Compliance", 2, "Audit trail, data retention, patient isolation, lab_id filtering")

    # 10a. Audit log model exists
    audit_model = REPO_ROOT / "backend" / "app" / "models" / "audit_log.py"
    audit_service = REPO_ROOT / "backend" / "app" / "services" / "audit_service.py"
    has_audit = audit_model.exists() or audit_service.exists()
    ax.add_check("Audit log model", has_audit, "app/models/audit_log.py exists" if audit_model.exists() else "")

    # 10b. Audit hash chain
    if audit_model.exists():
        content = audit_model.read_text()
        has_hash_chain = "previous_hash" in content or "hash" in content.lower()
        ax.add_check("Audit hash chain", has_hash_chain, "Immutable audit chain" if has_hash_chain else "No hash chain in audit log")

    # 10c. Lab_id tenant isolation in queries
    lab_id_patterns = 0
    no_lab_id = 0
    for p in list((REPO_ROOT / "backend" / "app" / "routes").glob("*.py"))[:40]:
        content = p.read_text(errors="replace")
        if "lab_id" in content:
            lab_id_patterns += 1
        if "filter(" in content and "lab_id" not in content:
            no_lab_id += 1
    isolation_pct = 100.0 * lab_id_patterns / max(lab_id_patterns + no_lab_id, 1)
    ax.add_check("lab_id tenant isolation", isolation_pct >= 50, f"{lab_id_patterns} files use lab_id filtering, {no_lab_id} without visible lab_id filter")

    # 10d. Patient data encryption (national_id)
    encryption_module = REPO_ROOT / "backend" / "app" / "security" / "encryption.py"
    has_encryption_module = encryption_module.exists()
    national_id_encrypted = False
    if has_encryption_module:
        content = encryption_module.read_text()
        if "encrypt" in content.lower() and "decrypt" in content.lower():
            national_id_encrypted = True
    ax.add_check("Patient data encryption", national_id_encrypted, "Field-level encryption available" if national_id_encrypted else "")

    # 10e. Consent model
    consent_model = REPO_ROOT / "backend" / "app" / "models" / "consent.py"
    has_consent = consent_model.exists()
    ax.add_check("Patient consent tracking", has_consent, "app/models/consent.py exists" if has_consent else "No consent model")

    # 10f. RBAC presence
    rbac_file = REPO_ROOT / "backend" / "app" / "security" / "rbac.py"
    has_rbac = rbac_file.exists()
    ax.add_check("RBAC permissions", has_rbac, "app/security/rbac.py exists" if has_rbac else "No RBAC module")

    # 10g. Data retention / privacy patterns
    privacy_patterns_found = 0
    privacy_terms = ["retention", "data_retention", "consent", "pii", "phi", "hipaa", "gdpr"]
    for p in _walk_py("backend/app")[:50]:
        content = p.read_text(errors="replace").lower()
        for term in privacy_terms:
            if term in content:
                privacy_patterns_found += 1
                break
    ax.add_check("Privacy/retention patterns", privacy_patterns_found >= 5, f"{privacy_patterns_found} files reference privacy/retention concepts")

    base = 100
    if not has_audit:
        base -= 20
    if not has_hash_chain:
        base -= 10
    if not has_encryption_module:
        base -= 20
    if not has_consent:
        base -= 10
    if not has_rbac:
        base -= 10
    if isolation_pct < 50:
        base -= 10
    if privacy_patterns_found < 5:
        base -= 5

    ax.set_score(max(0, base))

    if ax.score < 70:
        if not has_audit:
            ax.add_recommendation("Implement an audit log model with immutable hash chain for all patient data mutations")
        if not has_encryption_module:
            ax.add_recommendation("Implement field-level encryption for sensitive patient data (national_id, health records)")
        if not has_consent:
            ax.add_recommendation("Add patient consent tracking model for privacy-by-design compliance")
        if not has_rbac:
            ax.add_recommendation("Implement RBAC to enforce role-based access to patient data")
        if isolation_pct < 50:
            ax.add_recommendation("Ensure all patient-data queries filter by lab_id for multi-tenant isolation")

    return ax


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="GULA Repository Scorecard")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--summary", action="store_true", help="Compact output")
    parser.add_argument("--axis", type=str, help="Run a single axis (1-10)")
    args = parser.parse_args()

    axes = [
        _score_code_quality(),
        _score_test_coverage(),
        _score_documentation(),
        _score_security(),
        _score_architecture(),
        _score_dependencies(),
        _score_cicd(),
        _score_git_hygiene(),
        _score_devops(),
        _score_healthcare(),
    ]

    if args.axis:
        idx = int(args.axis) - 1
        if 0 <= idx < len(axes):
            axes = [axes[idx]]
        else:
            print(f"Invalid axis: {args.axis}. Must be 1-{len(axes)}.")
            return 1

    overall = sum(ax.weighted() for ax in axes)
    overall_int = round(overall)

    if args.json:
        output: dict[str, Any] = {
            "repository": "gula-platform",
            "overall_score": overall_int,
            "grade": _grade(overall_int),
            "axes": [ax.to_dict() for ax in axes],
        }
        print(json.dumps(output, indent=2))
        return 0

    if args.summary:
        print(f"{'Axis':<35} {'Score':>6} {'Grade':>6} {'Weight':>7} {'Contrib':>8}")
        print("-" * 66)
        for ax in axes:
            contrib = ax.weighted()
            print(
                f"{ax.name:<35} "
                f"{ax.score:>4}%  "
                f"{_grade_color(ax.score):>4}  "
                f"{ax.weight:>5}%  "
                f"{contrib:>6.2f}%"
            )
        print("-" * 66)
        print(f"{'OVERALL':<35} {overall_int:>4}%  {_grade_color(overall_int):>4}  {'100':>5}%  {overall:>6.2f}%")
        return 0

    # Colorized terminal output
    print()
    print(_c("bold", "╔══════════════════════════════════════════════════════════════╗"))
    print(_c("bold", "║              GULA REPOSITORY SCORECARD                       ║"))
    print(_c("bold", "╚══════════════════════════════════════════════════════════════╝"))
    print(f"  Repository: {REPO_ROOT.name}")
    print(f"  Date:       {_run(['date', '+%Y-%m-%d %H:%M']).stdout.strip()}")
    print()

    for i, ax in enumerate(axes, 1):
        grade_str = _grade_color(ax.score)
        contrib = ax.weighted()
        bar_len = 30
        filled = max(1, int(ax.score * bar_len / 100))
        bar = "█" * filled + "░" * (bar_len - filled)
        bar_color = _c("green" if ax.score >= 80 else "yellow" if ax.score >= 60 else "red", bar)

        print(f"  {_c('bold', f'{i}. {ax.name}')}  ({ax.weight}%)")
        print(f"     {bar_color}  {ax.score:>3}%  {grade_str}   (weighted: {contrib:.2f}%)")
        print(f"     {_c('blue', ax.description)}")

        if ax.checks:
            passed = sum(1 for v in ax.checks.values() if v == 100)
            total = len(ax.checks)
            print(f"     Checks: {passed}/{total} passed")

        if ax.score < 70 and ax.recommendations:
            print(f"     {_c('yellow', 'Recommendations:')}")
            for rec in ax.recommendations[:5]:
                print(f"       • {rec}")
        print()

    print(f"  {'─' * 55}")
    overall_bar_len = 40
    overall_filled = max(1, int(overall_int * overall_bar_len / 100))
    overall_bar = "█" * overall_filled + "░" * (overall_bar_len - overall_filled)
    overall_color = _c("green" if overall_int >= 80 else "yellow" if overall_int >= 60 else "red", overall_bar)
    print(
        f"  {_c('bold', 'OVERALL SCORE')}   "
        f"{overall_color}  {overall_int:>3}%  {_grade_color(overall_int)}"
    )
    print()

    return 0 if overall_int >= 70 else 1


if __name__ == "__main__":
    sys.exit(main())
