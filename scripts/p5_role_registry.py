"""P5.1 — Generate the definitive enterprise role registry and matrices.

Merges three sources of truth:
  - DB `roles` table (runtime truth: 19 seeded roles, level, mfa, delegatable)
  - shared/rbac/permissions.py EXTENDED_ROLE_LEVELS/PERMISSIONS (25 roles)
  - frontend-v3/src/permissions/index.ts ROLE_LEVELS/ROLE_PERMISSIONS (25 roles)

Emits: docs/certification/role_registry.md, role_visibility_matrix.csv,
       role_permission_matrix.csv
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "certification"


def db_roles() -> dict[str, dict]:
    cmd = [
        "docker", "exec", "gula-postgres", "psql", "-U", "postgres", "-d", "gula",
        "-t", "-A",
        "-c", "SELECT role_id || '|' || level || '|' || coalesce(parent_role_id,'-') || '|' || coalesce(is_temporary::text,'f') || '|' || coalesce(is_delegatable::text,'t') || '|' || coalesce(requires_mfa::text,'f') || '|' || is_active::text FROM roles ORDER BY level::int DESC",
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        print("DB query failed:", out.stderr)
        return {}
    roles: dict[str, dict] = {}
    for line in out.stdout.strip().splitlines():
        rid, level, parent, temp, deleg, mfa, active = line.split("|")
        roles[rid] = {
            "level": int(level),
            "parent": parent if parent != "-" else None,
            "temporary": temp == "true",
            "delegatable": deleg == "true",
            "requires_mfa": mfa == "true",
            "active": active == "true",
        }
    return roles


def parse_ts_roles() -> tuple[dict[str, int], dict[str, list[str]]]:
    src = ROOT / "frontend-v3" / "src" / "permissions" / "index.ts"
    text = src.read_text()
    levels: dict[str, int] = {}
    perms: dict[str, list[str]] = {}
    m = re.search(r"ROLE_LEVELS: Record<string, number> = \{(.*?)\};", text, re.S)
    if m:
        for name, val in re.findall(r"(\w+):\s*(\d+)", m.group(1)):
            levels[name] = int(val)
    m = re.search(r"ROLE_PERMISSIONS: Record<string, Permission\[\]> = \{(.*?)\n\};", text, re.S)
    if m:
        for block in re.finditer(r"(\w+):\s*\[(.*?)\]", m.group(1), re.S):
            role = block.group(1)
            perms[role] = re.findall(r'"([\w:]+)"', block.group(2))
    return levels, perms


def main() -> None:
    db = db_roles()
    sys.path.insert(0, str(ROOT))
    from shared.rbac.permissions import (  # noqa: E402
        EXTENDED_ROLE_LEVELS,
        EXTENDED_ROLE_PERMISSIONS,
    )

    ts_levels, ts_perms = parse_ts_roles()

    all_roles = sorted(set(db) | set(EXTENDED_ROLE_LEVELS), key=lambda r: -EXTENDED_ROLE_LEVELS.get(r, 0))
    print(f"Universe: {len(all_roles)} roles; DB-seeded: {len(db)}; shared: {len(EXTENDED_ROLE_LEVELS)}; frontend: {len(ts_levels)}")

    parity_ok = True
    for role in all_roles:
        lvl = EXTENDED_ROLE_LEVELS.get(role)
        tsl = ts_levels.get(role)
        if lvl != tsl:
            parity_ok = False
            print(f"  LEVEL MISMATCH {role}: shared={lvl} frontend={tsl}")
    missing_ts = set(EXTENDED_ROLE_LEVELS) - set(ts_levels)
    missing_sh = set(ts_levels) - set(EXTENDED_ROLE_LEVELS)
    if missing_ts or missing_sh:
        parity_ok = False
        print(f"  ROLES missing in frontend: {missing_ts or None}")
        print(f"  ROLES missing in shared: {missing_sh or None}")
    print("Level parity shared<->frontend:", "OK" if parity_ok else "FAIL")

    groups = {
        "National / Platform (level 70-100)": [r for r in all_roles if (EXTENDED_ROLE_LEVELS.get(r, 0) or 0) >= 70],
        "Facility Management (50-60)": [r for r in all_roles if 50 <= (EXTENDED_ROLE_LEVELS.get(r, 0) or 0) < 70],
        "Clinical (25-45)": [r for r in all_roles if 25 <= (EXTENDED_ROLE_LEVELS.get(r, 0) or 0) < 50],
        "Operational (20)": [r for r in all_roles if (EXTENDED_ROLE_LEVELS.get(r, 0) or 0) == 20],
        "Patient & External (5-10)": [r for r in all_roles if (EXTENDED_ROLE_LEVELS.get(r, 0) or 0) <= 10],
    }

    DOCS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Enterprise Role Registry — PROGRAM-05",
        "",
        f"*Generated {__import__('datetime').date.today().isoformat()} · {len(all_roles)} roles · "
        f"19 DB-seeded + 6 shared-model aliases*",
        "",
        "Sources of truth: `roles` table (runtime), `shared/rbac/permissions.py` (canonical 25-role model), "
        "`frontend-v3/src/permissions/index.ts` (UX gating).",
        "",
        "## Level parity check",
        f"- shared ↔ frontend level parity: **{'OK' if parity_ok else 'FAIL'}**",
        f"- DB-seeded roles: **{len(db)}/25** — DB is the runtime gate (`seed_roles`); "
        f"{sorted(set(EXTENDED_ROLE_LEVELS) - set(db))} are shared-model aliases assignable in code but not pre-seeded.",
        "",
    ]
    for group, members in groups.items():
        lines.append(f"## {group} ({len(members)})")
        lines.append("")
        lines.append("| Role | Level | DB seeded | MFA | Delegatable | Temporary | Parent | Scope / notes |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for role in members:
            info = db.get(role, {})
            perms = EXTENDED_ROLE_PERMISSIONS.get(role, [])
            scope = "platform" if role in (
                "master_admin", "ministry_admin", "organization_admin", "directorate_admin", "province_admin",
            ) else ("facility" if info.get("level", 0) and info["level"] >= 20 else "self")
            lines.append(
                f"| `{role}` | {EXTENDED_ROLE_LEVELS.get(role)} | "
                f"{'yes' if role in db else 'alias'} | {'yes' if info.get('requires_mfa') else 'no'} | "
                f"{'yes' if info.get('delegatable', True) else 'no'} | "
                f"{'yes' if info.get('temporary') else 'no'} | {info.get('parent') or '—'} | {scope} · {len(perms)} perms |"
            )
        lines.append("")
    lines += [
        "## Permission universe (16)",
        "",
        "| Permission | Roles holding it |",
        "|---|---|",
    ]
    perm_roles: dict[str, list[str]] = {}
    for role, perms in EXTENDED_ROLE_PERMISSIONS.items():
        for p in perms:
            perm_roles.setdefault(p, []).append(role)
    for p, roles in sorted(perm_roles.items()):
        lines.append(f"| `{p}` | {', '.join(sorted(roles, key=lambda r: -EXTENDED_ROLE_LEVELS.get(r,0)))} |")
    lines.append("")
    DOCS.joinpath("role_registry.md").write_text("\n".join(lines))
    print("wrote role_registry.md")

    # ── visibility matrix: NAV_ITEMS × roles (frontend sidebar truth) ──────────
    nav_src = (ROOT / "frontend-v3" / "src" / "permissions" / "index.ts").read_text()
    nav_blocks = re.findall(r"\{ label: \"([^\"]+)\", path: \"([^\"]+)\", icon: \"(\w+)\"(?:, permissions: \[([^\]]*)\])? \}", nav_src)
    with (DOCS / "role_visibility_matrix.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["path", "label", "icon", "required_permissions"] + sorted(all_roles, key=lambda r: -EXTENDED_ROLE_LEVELS.get(r, 0)))
        for label, path, icon, perms in nav_blocks:
            req = re.findall(r'"([\w:]+)"', perms or "")
            row = [path, label, icon, "|".join(req)]
            for role in sorted(all_roles, key=lambda r: -EXTENDED_ROLE_LEVELS.get(r, 0)):
                visible = not req or any(p in (EXTENDED_ROLE_PERMISSIONS.get(role) or []) for p in req)
                row.append("V" if visible else ".")
            w.writerow(row)
    print("wrote role_visibility_matrix.csv")

    # ── permission matrix: permission × role ───────────────────────────────────
    with (DOCS / "role_permission_matrix.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["permission"] + sorted(all_roles, key=lambda r: -EXTENDED_ROLE_LEVELS.get(r, 0)))
        for p in EXTENDED_ALL_PERMISSIONS if "EXTENDED_ALL_PERMISSIONS" in dir() else sorted(perm_roles):
            row = [p]
            for role in sorted(all_roles, key=lambda r: -EXTENDED_ROLE_LEVELS.get(r, 0)):
                row.append("Y" if p in (EXTENDED_ROLE_PERMISSIONS.get(role) or []) else ".")
            w.writerow(row)
    print("wrote role_permission_matrix.csv")

    # machine-readable digest for later phases
    digest = {
        "roles": {r: {"level": EXTENDED_ROLE_LEVELS.get(r), **db.get(r, {}), "permissions": EXTENDED_ROLE_PERMISSIONS.get(r, [])} for r in all_roles},
        "levels_parity": parity_ok,
        "db_seeded": sorted(db),
        "frontend_roles": ts_levels,
    }
    (Path("/tmp/opencode/p5_role_digest.json")).write_text(json.dumps(digest, indent=2, sort_keys=True))
    print("wrote /tmp/opencode/p5_role_digest.json")


if __name__ == "__main__":
    main()
