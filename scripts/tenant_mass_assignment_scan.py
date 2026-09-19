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
    python3 scripts/tenant_mass_assignment_scan.py --gate     # CI: fail on a NEW site

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


def _excludes_lab_id_from_copy(fn) -> bool:
    """`if k not in (..., "lab_id", ...): setattr(obj, k, v)`.

    A second, distinct way an update-shape site puts the real lab_id back:
    not reassigning it after the copy (what _reasserts_lab_id checks), but
    filtering it out of the copy in the first place. Missing this produced a
    real false positive: routes/care_continuum.py's
    api_update_primary_care_encounter excludes lab_id via exactly this guard
    and was still reported ASSIGNABLE.
    """
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        candidates = test.values if isinstance(test, ast.BoolOp) else [test]
        excludes = False
        for cand in candidates:
            if not (isinstance(cand, ast.Compare) and any(
                isinstance(op, ast.NotIn) for op in cand.ops
            )):
                continue
            container = cand.comparators[0]
            elts = getattr(container, "elts", None) or []
            if any(isinstance(e, ast.Constant) and e.value == "lab_id" for e in elts):
                excludes = True
                break
        if not excludes:
            continue
        if any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "setattr"
            for s in node.body for n in ast.walk(s)
        ):
            return True
    return False


def _setattr_target_model(fn, models: dict[str, str]) -> str | None:
    """Best-effort: which tenant-scoped model (if any) does this function's
    setattr loop mutate?

    The update shape records only "<setattr target>" (see SiteFinder.visit_For)
    because resolving a variable's class from a bare AST walk is not, in
    general, decidable. Two patterns cover most of this codebase's own style
    and are enough to fix a real false positive without claiming more
    precision than the heuristic has:

      1. The function's own return annotation names the model directly (the
         common CRUD shape: fetch it, mutate it, return the same object) --
         e.g. `def update_x(...) -> ClinicalNote | None:`.
      2. A local `VAR = db.query(Model)...` assignment in the same function.

    Returns the model name if found (whether or not it is tenant-scoped --
    the caller checks that), or None if neither pattern resolves.
    """
    if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) and fn.returns is not None:
        ann = ast.unparse(fn.returns)
        name = ann.replace("Optional[", "").rstrip("]").split("|")[0].strip().strip('"\'')
        if name in models or name not in ("dict", "Any", "None", "bool", "list"):
            return name
    for node in ast.walk(fn):
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
            continue
        value = node.value
        # VAR = db.query(Model)....first()  (any chain of attribute calls)
        while isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
            value = value.func.value
        if (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                and value.func.attr == "query" and value.args
                and isinstance(value.args[0], ast.Name)):
            return value.args[0].id
    return None


def classify(sites, trees, schemas, models):
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

        if s["shape"] == "update":
            resolved = _setattr_target_model(fn, models)
            if resolved is not None and resolved not in models:
                s["model"] = resolved
                s["verdict"] = f"NOT_TENANT_SCOPED: {resolved} has no lab_id column"
                continue
            if resolved is not None:
                s["model"] = resolved

        if _reasserts_lab_id(fn, s["line"]):
            s["verdict"] = "BLOCKED: raw dict, lab_id re-asserted"
        elif _excludes_lab_id_from_copy(fn):
            s["verdict"] = "BLOCKED: raw dict, lab_id excluded from the copy"
        else:
            s["verdict"] = "ASSIGNABLE: raw dict, no lab_id re-assertion"
    return sites


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="klass", help="print one class in full")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gate", action="store_true",
                    help="fail if an ASSIGNABLE site appears in a route module "
                         "that the baseline does not already record")
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

    sites = classify(sites, trees, pydantic_fields(trees), models)

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
    for v in ("ASSIGNABLE", "UNKNOWN", "BLOCKED", "NOT_TENANT_SCOPED"):
        print(f"  {len(verdicts[v]):3}  {v}")

    if args.gate:
        return run_gate(sites)

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


# ─── the gate (NR-148) ──────────────────────────────────────────────────────
#
# NR-146 and NR-148 were both found by hand, in the same week, by reading the
# three ASSIGNABLE sites that sit in a module declaring routes. That is a
# repeatable query, so it should not need a person next time. The gate pins the
# three known sites and fails on a fourth.
#
# It deliberately watches only route modules. A service-layer helper is a
# candidate; a handler is reachable, and reachable is what turns a candidate
# into a defect.

#: Sites already read and dispositioned. Each entry is "file:function".
KNOWN_ROUTE_SITES = {
    # NR-148 -- fixed: provenance is server-derived, scope is enforced.
    "backend/app/routes/canonical_patient.py:create_canonical",
    # NR-146 -- fixed: tenant filter on the lookup, lab_id excluded from the
    # settable keys.
    "backend/app/routes/care_continuum.py:api_update_primary_care_encounter",
    # NR-107 -- NOT a tenant defect: RiskPolicy extends IdentityBaseEntity,
    # which carries no lab_id. Kept here so the next reader does not re-open it.
    "backend/app/identity/adaptive_auth/routes.py:update_risk_policy",
}


def declares_routes(rel_path: str) -> bool:
    """True when this module mounts HTTP handlers of its own."""
    try:
        tree = ast.parse((ROOT / rel_path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    return any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr in {"get", "post", "put", "patch", "delete"}
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id in {"router", "app"}
        for n in ast.walk(tree)
    )


def run_gate(sites) -> int:
    reachable = {
        f"{s['file']}:{s['function']}"
        for s in sites
        if s["verdict"].startswith("ASSIGNABLE") and declares_routes(s["file"])
    }
    new = sorted(reachable - KNOWN_ROUTE_SITES)
    gone = sorted(KNOWN_ROUTE_SITES - reachable)

    for site in gone:
        print(f"  RESOLVED (no longer assignable): {site}")

    if not new:
        print(f"\nGATE PASS: {len(reachable)} reachable site(s), all dispositioned.")
        return 0

    print("\nGATE FAIL: a client-authored tenant reached a route handler that "
          "no one has read yet.")
    for site in new:
        print(f"  {site}")
    print("\nRead each one. If it is a real defect, fix it and add a regression "
          "test. If it is not (see RiskPolicy), add it to KNOWN_ROUTE_SITES with "
          "the reason. Do not add it blind -- two of the three above were live "
          "defects.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
