"""NR-107 — where a caller-supplied dict is copied onto a tenant-scoped model.

Two shapes recur across the platform:

    Model(**{k: v for k, v in data.items() if hasattr(Model, k)})    # create
    for k, v in data.items(): setattr(obj, k, v)                     # update

Both copy a dictionary onto a model whose table carries ``lab_id``, so the
tenant is assignable from the request body unless something else re-asserts it.

NR-107 measured this once by hand and kept no script, which ADR-027 exists to
forbid: evidence is derived from the authoritative source, never snapshotted.
This is that derivation. It reproduces the classification so the residual
classes -- the 37 that resolved to no route, and the 24 whose safety depends on
whether a Pydantic schema declares lab_id -- can be re-measured rather than
re-asserted.

    python3 scripts/tenant_mass_assignment_scan.py            # summary
    python3 scripts/tenant_mass_assignment_scan.py --class D  # one class, listed
    python3 scripts/tenant_mass_assignment_scan.py --json     # machine-readable

A site is not a defect by itself. It is a candidate; each still has to be read.
ASSIGNABLE is not "exploitable": it means lab_id can be copied onto the model
and nothing re-asserts it in that function. Reachability is a second axis this
scan deliberately does not claim to measure.
"""
# ruff: noqa: T201 - the output IS the measurement
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "backend" / "app"

#: Names that, as a base class, mean the model is tenant-scoped.
TENANT_BASES = {"TenantEntity", "TenantScopedMixin", "LabScopedMixin"}

#: Parameter names that carry a caller-supplied dictionary into a helper.
DICT_PARAM_HINTS = {"data", "payload", "body", "values", "fields", "updates",
                    "attrs", "request_data", "obj_in", "update_data"}


def modules():
    for path in sorted(APP.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            yield path, ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue


# ─── 1. which models are tenant-scoped ──────────────────────────────────────

def _declares_lab_id_column(stmt) -> bool:
    """True for `lab_id: Mapped[...] = mapped_column(...)` or `lab_id = Column(...)`."""
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        target, annotation, value = stmt.target.id, stmt.annotation, stmt.value
    elif (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
          and isinstance(stmt.targets[0], ast.Name)):
        target, annotation, value = stmt.targets[0].id, None, stmt.value
    else:
        return False
    if target != "lab_id":
        return False
    if annotation is not None and "Mapped" in ast.unparse(annotation):
        return True
    if value is not None and isinstance(value, ast.Call):
        fn = value.func
        name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "")
        return name in {"Column", "mapped_column", "relationship"}
    return False


def tenant_models(trees) -> dict[str, str]:
    """{class name: 'file:line'} for every model carrying lab_id."""
    found: dict[str, str] = {}
    for path, tree in trees:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {
                b.id if isinstance(b, ast.Name) else getattr(b, "attr", "")
                for b in node.bases
            }
            if bases & TENANT_BASES:
                found[node.name] = f"{path.relative_to(ROOT)}:{node.lineno}"
                continue
            # A declared lab_id COLUMN -- not merely an attribute named lab_id.
            # A Pydantic schema with `lab_id: UUID` is a request shape, not a
            # tenant-scoped table, and counting it inflates the denominator.
            for stmt in node.body:
                if not _declares_lab_id_column(stmt):
                    continue
                found[node.name] = f"{path.relative_to(ROOT)}:{node.lineno}"
                break
    return found


# ─── 2. the two shapes ──────────────────────────────────────────────────────

class SiteFinder(ast.NodeVisitor):
    def __init__(self, path, models):
        self.path = path
        self.models = models
        self.fn: list[ast.AST] = []
        self.sites: list[dict] = []

    def _enter(self, node):
        self.fn.append(node)
        self.generic_visit(node)
        self.fn.pop()

    def visit_FunctionDef(self, node):
        self._enter(node)

    def visit_AsyncFunctionDef(self, node):
        self._enter(node)

    def _record(self, node, model, shape, source):
        self.sites.append({
            "file": str(self.path.relative_to(ROOT)),
            "line": node.lineno,
            "function": self.fn[-1].name if self.fn else "<module>",
            "model": model,
            "shape": shape,
            "source": source,
        })

    def visit_Call(self, node):
        # Model(**{k: v for k, v in data.items() if hasattr(Model, k)})
        name = node.func.id if isinstance(node.func, ast.Name) else None
        if name in self.models:
            for kw in node.keywords:
                if kw.arg is not None:
                    continue
                src = _dict_source(kw.value)
                if src is not None:
                    self._record(node, name, "create", src)
        self.generic_visit(node)

    def visit_For(self, node):
        # for k, v in data.items(): setattr(obj, k, v)
        src = _items_source(node.iter)
        if src is None:
            # `for key in data:` / `for key in data.keys():` with setattr inside.
            iter_node = node.iter
            if (isinstance(iter_node, ast.Call)
                    and isinstance(iter_node.func, ast.Attribute)
                    and iter_node.func.attr == "keys"):
                iter_node = iter_node.func.value
            if isinstance(iter_node, ast.Name) and iter_node.id in DICT_PARAM_HINTS:
                src = iter_node.id
        # setattr ANYWHERE in the loop body, including under an `if`.
        if src is not None and any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "setattr"
            for s in node.body for n in ast.walk(s)
        ):
            self._record(node, "<setattr target>", "update", src)
        self.generic_visit(node)


def _dict_source(node) -> str | None:
    """The name of the dict a create-shape copies from, if there is one."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.DictComp):
        for gen in node.generators:
            src = _items_source(gen.iter)
            if src is not None:
                return src
        return None
    # Model(**payload.model_dump()) / (**payload.dict(exclude_unset=True)) --
    # the same copy, one method call further along.
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"model_dump", "dict", "to_dict", "copy"}):
        inner = node.func.value
        while isinstance(inner, ast.Attribute):
            inner = inner.value
        return inner.id if isinstance(inner, ast.Name) else None
    return None


def _items_source(node) -> str | None:
    """`data.items()` -> 'data'; `data.dict().items()` -> 'data'."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "items"):
        return None
    inner = node.func.value
    while isinstance(inner, ast.Call):
        inner = inner.func
    while isinstance(inner, ast.Attribute):
        inner = inner.value
    return inner.id if isinstance(inner, ast.Name) else None


# ─── 3. can lab_id actually be in that dict, and is it re-asserted? ─────────
#
# READ THE VERDICT NAMES LITERALLY. ASSIGNABLE means lab_id CAN be copied onto
# the model and nothing in the enclosing function puts the real one back. It
# does NOT mean a caller can reach it -- this scan does not trace routes, and
# calling such a site "live" would be a claim it never measured.
#
# Route-tracing was how NR-107 classified these, and it left 37 sites with "no
# route path resolved -- NOT proven safe". The question that decides the defect
# is narrower and answerable without a route: can lab_id BE in the dict, and
# does anything put the real one back afterwards.

def pydantic_fields(trees) -> dict[str, set[str]]:
    """{schema class: declared field names} for every BaseModel in the tree."""
    out: dict[str, set[str]] = {}
    for _path, tree in trees:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {
                b.id if isinstance(b, ast.Name) else getattr(b, "attr", "")
                for b in node.bases
            }
            if not (bases & {"BaseModel"} or any("Schema" in b for b in bases)):
                continue
            out[node.name] = {
                s.target.id
                for s in node.body
                if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)
            }
    return out


def _annotation_of(fn, param: str) -> str | None:
    args = list(fn.args.args) + list(fn.args.kwonlyargs) + list(fn.args.posonlyargs)
    for a in args:
        if a.arg == param:
            return ast.unparse(a.annotation) if a.annotation is not None else ""
    return None


def _reasserts_lab_id(fn, after_line: int) -> bool:
    """`obj.lab_id = <something>` below the copy, or lab_id= on the same call."""
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "lab_id":
                    return True
        if isinstance(node, ast.Assign) and node.lineno >= after_line:
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr == "lab_id":
                    return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "setattr" and len(node.args) >= 2 \
                and isinstance(node.args[1], ast.Constant) \
                and node.args[1].value == "lab_id":
            return True
    return False


def classify(sites, trees, schemas):
    """Attach a verdict to every site."""
    fns: dict[tuple[str, str], ast.AST] = {}
    for path, tree in trees:
        rel = str(path.relative_to(ROOT))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fns.setdefault((rel, node.name), node)

    for s in sites:
        fn = fns.get((s["file"], s["function"]))
        if fn is None:
            s["verdict"] = "UNKNOWN: enclosing function not found"
            continue

        annotation = _annotation_of(fn, s["source"])
        if annotation is None:
            s["verdict"] = "UNKNOWN: dict is not a parameter of this function"
            s["carrier"] = "<local>"
            continue
        s["carrier"] = annotation or "<unannotated>"

        schema = annotation.strip().strip('"\'').replace("Optional[", "").rstrip("]")
        if schema in schemas:
            if "lab_id" in schemas[schema]:
                s["verdict"] = ("ASSIGNABLE: schema declares lab_id"
                                if not _reasserts_lab_id(fn, s["line"])
                                else "BLOCKED: schema declares lab_id, but it is re-asserted")
            else:
                s["verdict"] = "BLOCKED: schema cannot carry lab_id"
            continue

        if annotation and "dict" not in annotation.lower() and "any" not in annotation.lower():
            s["verdict"] = f"UNKNOWN: carrier {annotation!r} is not a known schema"
            continue

        s["verdict"] = ("BLOCKED: raw dict, lab_id re-asserted"
                        if _reasserts_lab_id(fn, s["line"])
                        else "ASSIGNABLE: raw dict, no lab_id re-assertion")
    return sites


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="klass", help="print one class in full")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    trees = list(modules())
    models = tenant_models(trees)

    # Non-vacuity: a scan over an empty model set passes by finding nothing.
    if len(models) < 50:
        print(f"ABORT: only {len(models)} tenant-scoped models found; the scan "
              f"would report a clean result for the wrong reason", file=sys.stderr)
        return 2

    sites: list[dict] = []
    for path, tree in trees:
        finder = SiteFinder(path, models)
        finder.visit(tree)
        sites.extend(finder.sites)

    by_file = defaultdict(list)
    for s in sites:
        by_file[s["file"]].append(s)

    sites = classify(sites, trees, pydantic_fields(trees))

    if args.json:
        print(json.dumps({"models": len(models), "sites": sites}, indent=2))
        return 0

    verdicts = defaultdict(list)
    for s in sites:
        verdicts[s["verdict"].split(":")[0]].append(s)

    print(f"tenant-scoped models (lab_id): {len(models)}")
    print(f"mass-assignment sites:         {len(sites)}")
    print(f"  create shape: {sum(1 for s in sites if s['shape'] == 'create')}")
    print(f"  update shape: {sum(1 for s in sites if s['shape'] == 'update')}")
    print("\nverdicts:")
    for v in ("ASSIGNABLE", "UNKNOWN", "BLOCKED"):
        print(f"  {len(verdicts[v]):3}  {v}")

    if args.klass:
        want = args.klass.upper()
        print(f"\n─── {want} ───")
        for s in sorted(sites, key=lambda s: (s["file"], s["line"])):
            if s["verdict"].split(":")[0] != want:
                continue
            print(f"  {s['file']}:{s['line']}  {s['function']}()")
            print(f"      {s['shape']:6} from {s['source']!r}"
                  f"  carrier={s.get('carrier', '?')}")
            print(f"      {s['verdict']}")
    else:
        print("\nby module:")
        for f in sorted(by_file, key=lambda k: -len(by_file[k])):
            print(f"  {len(by_file[f]):3}  {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
