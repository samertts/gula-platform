"""Exact attribution: only ORM classes a route module actually names.

Level 1 = model classes imported by the route module itself.
Level 2 = model classes imported by modules the route module imports *from
          within its own domain package* (route -> service -> models).
No transitive closure across domains, which previously attributed unrelated
tables to Pharmacy, whose 27 tables are all present.
"""
import ast
import collections
import json
import os
from pathlib import Path

ROOT = Path("/home/user/gula-platform"); APP = ROOT/"backend"/"app"
SP = Path(os.getenv("GULA_SCAN_DIR", "/tmp/gula-scan")); SP.mkdir(parents=True, exist_ok=True)
missing = set(json.loads((SP/"orm_physical_delta.json").read_text())["missing"])
routes = json.loads((SP/"reachable_routes.json").read_text())

cls_tbl = {}
imported_names, imported_mods = {}, {}
for p in APP.rglob("*.py"):
    if "__pycache__" in p.parts: continue
    rel = str(p.relative_to(APP)).replace("/__init__.py", "").replace(".py", "")
    mod = ("app." + rel.replace("/", ".")).rstrip(".")
    try: tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError: continue
    names, mods = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef):
            for st in n.body:
                if isinstance(st, ast.Assign):
                    for t in st.targets:
                        if isinstance(t, ast.Name) and t.id == "__tablename__" and isinstance(st.value, ast.Constant):
                            cls_tbl[n.name] = st.value.value
        elif isinstance(n, ast.ImportFrom):
            base = n.module or ""
            if n.level:
                parts = mod.split(".")
                base = ".".join(parts[:max(1, len(parts) - n.level)]) + (("." + n.module) if n.module else "")
            for a in n.names:
                names.add(a.name)
                if base.startswith("app"): mods.add(base + "." + a.name)
            if base.startswith("app"): mods.add(base)
    imported_names[mod], imported_mods[mod] = names, mods

def domain(mod):
    p = mod.split(".")
    return p[1] if len(p) > 1 else "?"

def tables_for(routemod):
    out = set()
    for n in imported_names.get(routemod, ()):
        if n in cls_tbl: out.add(cls_tbl[n])
    for m in imported_mods.get(routemod, ()):
        cand = m if m in imported_names else m.rsplit(".", 1)[0]
        if cand in imported_names and domain(cand) == domain(routemod):
            for n in imported_names[cand]:
                if n in cls_tbl: out.add(cls_tbl[n])
    return out

per_mod, rows = {}, []
for r in routes:
    m = r["module"]
    if m not in per_mod: per_mod[m] = tables_for(m)
    t = per_mod[m]
    rows.append({"path": r["path"], "module": m, "ops": len(r["methods"]),
                 "tables": sorted(t), "missing": sorted(t & missing)})

broken = sum(r["ops"] for r in rows if r["missing"])
total = sum(r["ops"] for r in rows)
unknown = sum(r["ops"] for r in rows if not r["tables"])
by_mod = collections.Counter()
for r in rows:
    if r["missing"]: by_mod[r["module"]] += r["ops"]
json.dump(rows, open(SP/"endpoint_backing_exact.json", "w"), indent=0)
print(json.dumps({
 "total_reachable_operations": total,
 "operations_on_a_missing_table": broken,
 "operations_with_all_tables_present": total - broken - unknown,
 "operations_with_no_resolvable_model": unknown,
 "route_modules_affected": len(by_mod),
 "pharmacy_check": {"ops": sum(r["ops"] for r in rows if r["module"]=="app.pharmacy.routes"),
                    "missing": sorted({t for r in rows if r["module"]=="app.pharmacy.routes" for t in r["missing"]}),
                    "tables_seen": len({t for r in rows if r["module"]=="app.pharmacy.routes" for t in r["tables"]})},
 "top_affected": by_mod.most_common(18),
}, indent=2))
