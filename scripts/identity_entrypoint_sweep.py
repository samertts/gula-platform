"""Classify how served routes obtain identity and tenant (NR-139).

Run against a live backend:
    python3 scripts/identity_entrypoint_sweep.py

A client-authored value is not a defect. The defect is one that becomes a
SECURITY FACT. This finds the candidates; each still has to be read.
"""
# ruff: noqa: T201 - the output IS the classification
import ast
import json
import pathlib
import urllib.request
from collections import Counter, defaultdict

SENSITIVE = {"account_uuid", "user_id", "person_id", "identity_id", "lab_id",
             "organization_id", "role", "permission", "session_id"}

# Served surface, enumerated from the running app.
spec = json.load(urllib.request.urlopen("http://127.0.0.1:8000/openapi.json", timeout=60))
served_ops = {
    op["operationId"]
    for ops in spec["paths"].values()
    for op in ops.values()
    if isinstance(op, dict) and op.get("operationId")
}
print(f"served operations: {len(served_ops)}")

root = pathlib.Path("backend/app")
findings = defaultdict(list)
counts = Counter()

class V(ast.NodeVisitor):
    def __init__(self, path):
        self.path = path
        self.fn = None
    def visit_FunctionDef(self, node):
        prev, self.fn = self.fn, node
        # Client-supplied parameters: those annotated Body/Query/Header/Path or
        # appearing on a pydantic payload, whose name is sensitive.
        for arg in list(node.args.args) + list(node.args.kwonlyargs):
            if arg.arg in SENSITIVE:
                counts[f"param:{arg.arg}"] += 1
                findings[f"param:{arg.arg}"].append(f"{self.path}:{node.lineno} {node.name}")
        self.generic_visit(node)
        self.fn = prev
    def visit_Attribute(self, node):
        # payload.lab_id / data.organization_id — a client-authored body field.
        if (
            node.attr in SENSITIVE
            and isinstance(node.value, ast.Name)
            and node.value.id in {"payload", "data", "body", "req", "request_data"}
        ):
                counts[f"body:{node.attr}"] += 1
                findings[f"body:{node.attr}"].append(f"{self.path}:{node.lineno}")
        self.generic_visit(node)

for p in sorted(root.rglob("*.py")):
    if "__pycache__" in p.parts:
        continue
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"))
    except SyntaxError:
        continue
    V(str(p.relative_to("backend"))).visit(tree)

print("\nCLIENT-AUTHORED identity/tenant surfaces in backend/app:")
for k, n in counts.most_common():
    print(f"  {n:4}  {k}")
print("\nTop body-field sites (highest risk: a client-named tenant/actor):")
for k in sorted(findings):
    if k.startswith("body:"):
        for site in findings[k][:6]:
            print(f"  {k:26} {site}")
