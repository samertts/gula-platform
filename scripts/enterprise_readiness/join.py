import collections
import json
import os
from pathlib import Path

SP = Path(os.getenv("GULA_SCAN_DIR", "/tmp/gula-scan")); SP.mkdir(parents=True, exist_ok=True)
delta = json.loads((SP/"orm_physical_delta.json").read_text())
routes = json.loads((SP/"reachable_routes.json").read_text())
inv = json.loads((SP/"inventory.json").read_text())
missing = set(delta["missing"]); orm = delta["orm"]

def dom_of_file(f):           # backend/app/<domain>/...
    parts = f.split("/")
    return parts[2] if len(parts) > 2 else "?"

tbl_dom = collections.Counter(); miss_dom = collections.Counter()
for t, files in orm.items():
    d = dom_of_file(sorted(files)[0])
    tbl_dom[d] += 1
    if t in missing:
        miss_dom[d] += 1

ops_dom = collections.Counter()
for r in routes:
    p = r["module"].split(".")
    ops_dom[p[1] if len(p) > 1 else "?"] += len(r["methods"])

doms = sorted(set(tbl_dom) | set(ops_dom) | set(inv["backend_domains"]))
rows = []
for d in doms:
    info = inv["backend_domains"].get(d, {})
    rows.append({
        "domain": d,
        "py_files": info.get("py_files", 0),
        "loc": info.get("loc", 0),
        "orm_tables": tbl_dom.get(d, 0),
        "tables_missing_physically": miss_dom.get(d, 0),
        "reachable_operations": ops_dom.get(d, 0),
    })
rows.sort(key=lambda r: (-r["tables_missing_physically"], -r["reachable_operations"]))
json.dump(rows, open(SP/"domain_matrix.json", "w"), indent=1)
print(f"{'domain':26}{'files':>6}{'loc':>8}{'orm_tbl':>9}{'missing':>9}{'ops':>7}")
for r in rows[:34]:
    print(f"{r['domain']:26}{r['py_files']:>6}{r['loc']:>8}{r['orm_tables']:>9}{r['tables_missing_physically']:>9}{r['reachable_operations']:>7}")
tot = lambda k: sum(r[k] for r in rows)
print("-"*66)
print(f"{'TOTAL':26}{tot('py_files'):>6}{tot('loc'):>8}{tot('orm_tables'):>9}{tot('tables_missing_physically'):>9}{tot('reachable_operations'):>7}")
