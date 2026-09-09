"""One-time deterministic GULA repository inventory.

Written once so the numbers below are never rediscovered by hand. Re-run it
after a batch instead of re-scanning ad hoc.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path("/home/user/gula-platform")
APP = ROOT / "backend" / "app"

def py_files(base: Path):
    return [p for p in base.rglob("*.py") if "__pycache__" not in p.parts]

out: dict = {}

# ── backend domains ────────────────────────────────────────────────────────
domains = {}
for d in sorted(APP.iterdir()):
    if not d.is_dir() or d.name == "__pycache__":
        continue
    files = py_files(d)
    domains[d.name] = {
        "py_files": len(files),
        "loc": sum(len(f.read_text(encoding="utf-8", errors="replace").splitlines()) for f in files),
    }
out["backend_domains"] = domains

# ── routes and endpoints ───────────────────────────────────────────────────
DEC = re.compile(r"@(?:\w+)\.(get|post|put|patch|delete)\s*\(", re.I)
endpoints = Counter()
route_files = []
for p in py_files(APP):
    txt = p.read_text(encoding="utf-8", errors="replace")
    n = len(DEC.findall(txt))
    if n:
        rel = str(p.relative_to(ROOT))
        route_files.append(rel)
        endpoints[rel] = n
out["endpoints"] = {
    "total": sum(endpoints.values()),
    "files_with_endpoints": len(route_files),
    "top_20": endpoints.most_common(20),
}

# ── ORM models ─────────────────────────────────────────────────────────────
models = []
bases = Counter()
for p in py_files(APP):
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        continue
    src = p.read_text(encoding="utf-8", errors="replace")
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            names = [b.id for b in node.bases if isinstance(b, ast.Name)]
            if any("Base" in n or "Entity" in n or "Mixin" in n for n in names):
                tbl = None
                for st in node.body:
                    if isinstance(st, ast.Assign):
                        for t in st.targets:
                            if isinstance(t, ast.Name) and t.id == "__tablename__":
                                if isinstance(st.value, ast.Constant):
                                    tbl = st.value.value
                if tbl:
                    models.append({"class": node.name, "table": tbl,
                                   "file": str(p.relative_to(ROOT)), "bases": names})
                    for n in names:
                        bases[n] += 1
out["orm_models"] = {"total": len(models), "distinct_tables": len({m["table"] for m in models}),
                     "bases": bases.most_common()}

# declarative_base() instances
decl = subprocess.run(["grep", "-rn", "declarative_base()", str(APP)],
                      capture_output=True, text=True).stdout.splitlines()
out["declarative_bases"] = {"count": len(decl),
                            "files": sorted({l.split(":")[0].replace(str(ROOT) + "/", "") for l in decl})}

# ── migrations ─────────────────────────────────────────────────────────────
mig = sorted((ROOT / "backend" / "migrations" / "versions").glob("*.py"))
out["migrations"] = {"total": len(mig), "latest": [p.name for p in mig[-5:]]}

# ── tests ──────────────────────────────────────────────────────────────────
def count_tests(base: Path):
    files = [p for p in base.rglob("test_*.py") if "__pycache__" not in p.parts]
    fn = 0
    for p in files:
        fn += len(re.findall(r"^\s*(?:async )?def test_", p.read_text(encoding="utf-8", errors="replace"), re.M))
    return len(files), fn
bf, bt = count_tests(ROOT / "backend" / "tests")
out["tests"] = {"backend_files": bf, "backend_test_functions": bt}
sf, st = count_tests(ROOT / "scripts" / "tests") if (ROOT / "scripts" / "tests").exists() else (0, 0)
out["tests"]["scripts_files"], out["tests"]["scripts_test_functions"] = sf, st

# ── frontends ──────────────────────────────────────────────────────────────
fronts = {}
for name in ["frontend-v3", "frontend", "frontend-v2", "client", "mobile", "mobile-expo",
             "hospital_desktop", "nhop-platform", "apps", "packages"]:
    d = ROOT / name
    if not d.exists():
        continue
    pkg = d / "package.json"
    tsx = [p for p in d.rglob("*.tsx") if "node_modules" not in p.parts]
    fronts[name] = {"exists": True, "has_package_json": pkg.exists(), "tsx_files": len(tsx)}
out["frontends"] = fronts

# ── CI ─────────────────────────────────────────────────────────────────────
wf = sorted((ROOT / ".github" / "workflows").glob("*.yml")) + sorted((ROOT / ".github" / "workflows").glob("*.yaml"))
out["ci_workflows"] = {"total": len(wf), "names": [p.name for p in wf]}

# ── docs ───────────────────────────────────────────────────────────────────
docs = [p for p in (ROOT / "docs").rglob("*.md")]
out["docs"] = {"total_md": len(docs),
               "top_dirs": Counter(str(p.relative_to(ROOT / "docs")).split("/")[0] for p in docs).most_common(15)}

# ── detectors ──────────────────────────────────────────────────────────────
det = subprocess.run(["grep", "-rln", "GULA-SCHEMA-002\\|GULA-MIG-001\\|GULA-ARCH-001\\|GULA-STATE-001",
                      str(ROOT / "scripts"), str(ROOT / "backend")], capture_output=True, text=True).stdout.splitlines()
out["detectors"] = sorted({l.replace(str(ROOT) + "/", "") for l in det})

print(json.dumps(out, indent=2, default=str))
