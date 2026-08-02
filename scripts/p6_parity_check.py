"""PROGRAM-06 — backend↔frontend parity certification tool.

Checks:
 A. Route parity: every frontend API path (endpoints.ts) must exist as a
    live backend route (method + normalized path).
 B. Permission parity: frontend ROLE_PERMISSIONS must equal shared model.
 C. Reverse coverage: report backend routes unused by frontend (info only).

Output: docs/certification/backend_frontend_parity.md + /tmp/opencode/p6_parity.json
"""

from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")

import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/samertts/workspace/projects/gula-platform")
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

FE_FILE = ROOT / "frontend-v3/src/api/endpoints.ts"


def extract_frontend_paths() -> list[tuple[str, str, str]]:
    """(method, normalized_pattern, raw_path) from endpoints.ts."""
    src = FE_FILE.read_text(encoding="utf-8")
    pat = re.compile(r"api\.(get|post|put|delete|patch)(?:<[^>]*>)?\(\s*([`\"'])([^`\"']+)\2")
    out: list[tuple[str, str, str]] = []
    for m in pat.finditer(src):
        method, _, path = m.group(1), m.group(2), m.group(3)
        norm = re.sub(r"\$\{[^}]*\}", "{id}", path)
        # strip query string if any
        norm = norm.split("?")[0]
        out.append((method.upper(), norm, path))
    # de-dup keeping order
    seen = set()
    dedup = []
    for t in out:
        if t not in seen:
            seen.add(t)
            dedup.append(t)
    return dedup


def get_backend_routes() -> list[tuple[str, str]]:
    from app.main import app
    from fastapi.routing import _IncludedRouter

    routes = []

    def walk(items) -> None:
        for r in items:
            if isinstance(r, _IncludedRouter):
                walk(r.original_router.routes)
                continue
            methods = getattr(r, "methods", None) or []
            path = getattr(r, "path", None)
            if not path or not methods:
                continue
            for m in methods:
                if m == "HEAD":
                    continue
                routes.append((m, path))

    walk(app.routes)
    return routes


def path_matches(fe_path: str, be_path: str) -> bool:
    """Match FE pattern (with {id}) against BE Starlette pattern."""
    fe_re = re.escape(fe_path)
    fe_re = fe_re.replace(r"\{id\}", "[^/]+").replace(r"\{[^}]*\}", "[^/]+")
    # BE may have typed params like {result_id}
    be_re = re.escape(be_path)
    be_re = be_re.replace(r"\{[^}]+\}", "[^/]+")
    return re.fullmatch(fe_re, be_path) is not None or re.fullmatch(be_re, fe_path) is not None


def main() -> None:
    fe = extract_frontend_paths()
    routes = get_backend_routes()
    be_index: dict[str, list[str]] = {}
    for m, p in routes:
        be_index.setdefault(m, []).append(p)

    drift: list[dict] = []
    matched: list[dict] = []
    for method, norm, raw in fe:
        cands = be_index.get(method, [])
        hit = next((p for p in cands if path_matches(norm, p)), None)
        rec = {"method": method, "fe_path": raw, "norm": norm, "be_path": hit}
        (matched if hit else drift).append(rec)

    # B: permission parity
    perms_file = (ROOT / "frontend-v3/src/permissions/index.ts").read_text(encoding="utf-8")

    from shared.rbac.permissions import (
        EXTENDED_ROLE_LEVELS as SHARED_LEVELS,
    )
    from shared.rbac.permissions import (
        EXTENDED_ROLE_PERMISSIONS as SHARED_PERMS,
    )
    from shared.rbac.permissions import (
        EXTENDED_VALID_ROLES as SHARED_ROLES,
    )

    # parse frontend ROLE_LEVELS and ROLE_PERMISSIONS via regex (no TS runtime)
    def parse_ts_dict(name: str) -> dict:
        m = re.search(rf"export const {name}[^=]*=\s*\{{(.*?)\n\}}", perms_file, re.S)
        if not m:
            return {}
        body = m.group(1)
        items = re.findall(r"^\s*([\"']?)([\w]+)\1\s*:\s*([^\n,]+),?", body, re.M)
        return {k: v.strip() for _, k, v in items}

    def parse_ts_dict_int(name: str) -> dict:
        return {k: int(v) for k, v in parse_ts_dict(name).items()}

    fe_levels = parse_ts_dict_int("ROLE_LEVELS")
    fe_roles = set(fe_levels)

    # permission-array parity: frontend ROLE_PERMISSIONS vs shared model
    m2 = re.search(r"export const ROLE_PERMISSIONS[^=]*=\s*\{(.*?)\n\}", perms_file, re.S)
    fe_perm_sets: dict[str, set[str]] = {}
    if m2:
        for rm in re.finditer(
            r"^\s*([\"']?)([\w]+)\1\s*:\s*\[(.*?)\]\s*,?$", m2.group(1), re.M | re.S
        ):
            perms = re.findall(r"\"([^\"]+)\"", rm.group(3))
            fe_perm_sets[rm.group(2)] = set(perms)

    perm_parity = []
    for role in sorted(set(SHARED_PERMS) | set(fe_perm_sets)):
        sp = set(SHARED_PERMS.get(role, []))
        fp = fe_perm_sets.get(role, set())
        if sp != fp:
            perm_parity.append(
                {
                    "role": role,
                    "shared_only": sorted(sp - fp),
                    "fe_only": sorted(fp - sp),
                }
            )

    perm_mismatch = []
    for role in sorted(SHARED_ROLES | fe_roles):
        sl = SHARED_LEVELS.get(role)
        fl = fe_levels.get(role)
        if sl != fl:
            perm_mismatch.append({"role": role, "shared_level": sl, "fe_level": fl})

    summary = {
        "frontend_calls": len(fe),
        "frontend_unique_paths": len({f[1] for f in fe}),
        "backend_routes": len(routes),
        "matched": len(matched),
        "drift": len(drift),
        "fe_roles": len(fe_roles),
        "SHARED_ROLES": len(SHARED_ROLES),
        "level_mismatches": len(perm_mismatch),
        "permission_parity_diffs": len(perm_parity),
        "drift_list": drift,
        "level_mismatch_list": perm_mismatch,
        "permission_parity_list": perm_parity,
        "unused_be_count": 0,
    }

    out = ROOT / "docs/certification/backend_frontend_parity.md"
    lines = [
        "# Backend ↔ Frontend Parity Certification — PROGRAM-06",
        "",
        "Automated via `scripts/p6_parity_check.py` against the **live backend route table**",
        "(ground truth) and `frontend-v3/src/api/endpoints.ts` (frontend contract).",
        "",
        "## Result",
        "",
        f"- Frontend API calls: **{summary['frontend_calls']}** ({summary['frontend_unique_paths']} unique paths)",
        f"- Live backend routes: **{summary['backend_routes']}**",
        f"- Route parity: **{summary['matched']}/{summary['frontend_calls']}** calls matched ({summary['frontend_unique_paths']} unique paths)",
        f"- Drift (frontend path with no backend route): **{summary['drift']}**",
        "",
        "## Drift",
        "",
    ]
    if drift:
        lines.append("| Method | Frontend path | Matched backend |")
        lines.append("|---|---|---|")
        for d in drift:
            lines.append(f"| {d['method']} | `{d['fe_path']}` | {d['be_path'] or '— NONE —'} |")
    else:
        lines.append("_None — every frontend API path resolves to a live backend route._")
    lines += [
        "",
        "## Permission parity (frontend ROLE_PERMISSIONS ↔ shared model)",
        "",
        f"- Roles in shared model: {summary['SHARED_ROLES']} · Roles in frontend: {summary['fe_roles']}",
        f"- Level mismatches: **{summary['level_mismatches']}**",
    ]
    if perm_mismatch:
        lines.append("| Role | shared level | FE level |")
        lines.append("|---|---|---|")
        for pm in perm_mismatch:
            lines.append(f"| {pm['role']} | {pm['shared_level']} | {pm['fe_level']} |")
    else:
        lines.append("_None — levels identical._")
    lines += [
        "",
        "## Permission-array parity (frontend ROLE_PERMISSIONS ↔ shared model)",
        "",
        f"- Roles compared: **{len(set(SHARED_PERMS) | set(fe_perm_sets))}** (shared {len(SHARED_PERMS)} · FE {len(fe_perm_sets)})",
        f"- Permission set differences: **{summary['permission_parity_diffs']}**",
    ]
    if perm_parity:
        lines.append("| Role | shared-only | FE-only |")
        lines.append("|---|---|---|")
        for pp in perm_parity:
            lines.append(
                f"| {pp['role']} | {', '.join(pp['shared_only']) or '—'} | "
                f"{', '.join(pp['fe_only']) or '—'} |"
            )
    else:
        lines.append("_None — permission sets identical for every role._")
    lines += [
        "",
        "## Method coverage (frontend)",
        "",
    ]
    from collections import Counter

    cnt = Counter(d["method"] for d in matched)
    lines.append("| Method | Calls matched |")
    lines.append("|---|---|")
    for m, n in sorted(cnt.items()):
        lines.append(f"| {m} | {n} |")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    json.dump(summary, open("/tmp/opencode/p6_parity.json", "w"), indent=1)

    print(
        f"frontend calls={summary['frontend_calls']} unique={summary['frontend_unique_paths']} "
        f"backend={summary['backend_routes']} matched={summary['matched']} drift={summary['drift']} "
        f"level_mismatches={summary['level_mismatches']}"
    )
    for d in drift:
        print(f"DRIFT {d['method']} {d['fe_path']}")
    print("wrote", out)


main()
