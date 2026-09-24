import ast
import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path("/home/user/gula-platform"); APP = ROOT/"backend"/"app"
SP = Path(os.getenv("GULA_SCAN_DIR", "/tmp/gula-scan")); SP.mkdir(parents=True, exist_ok=True)
physical = {l.strip() for l in (SP/"physical_tables.txt").read_text().splitlines() if l.strip()}
orm = {}
for p in APP.rglob("*.py"):
    if "__pycache__" in p.parts: continue
    try: tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError: continue
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for st in node.body:
                if isinstance(st, ast.Assign):
                    for t in st.targets:
                        if isinstance(t,ast.Name) and t.id=="__tablename__" and isinstance(st.value, ast.Constant):
                            orm.setdefault(st.value.value, []).append(str(p.relative_to(ROOT)))
missing = sorted(set(orm) - physical)
extra   = sorted(physical - set(orm))
by_dom = Counter()
for t in missing:
    by_dom[sorted(orm[t])[0].split("/")[2] if len(sorted(orm[t])[0].split("/"))>2 else "?"] += 1
print(json.dumps({
 "orm_tables": len(orm), "physical_tables": len(physical),
 "orm_without_physical": len(missing),
 "physical_without_orm": len(extra),
 "missing_by_domain_top25": by_dom.most_common(25),
 "sample_missing": missing[:15],
 "sample_extra": extra[:15],
}, indent=2))
json.dump({"missing": missing, "extra": extra, "orm": {k: v for k, v in orm.items()}},
          open(SP/"orm_physical_delta.json","w"), indent=1)
