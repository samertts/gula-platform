#!/usr/bin/env python3
"""Read-only verifier for the National Capability Registry static index.

This is a *governance utility*, not an application component:
  - stdlib only, no imports from ``backend/app/**``;
  - reads files, writes nothing, has no network/DB side effects;
  - the application does not import it and works if the index is absent.

It proves the index stays a *reference-only, non-executing* artifact and remains
consistent with the canonical engine inventory. A failure is reported, never
silently repaired.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

INDEX_REL = "GOVERNANCE/national_capability_index.json"
INVENTORY_REL = "GOVERNANCE/AUTONOMOUS_ENGINES_INVENTORY.md"

EXPECTED_COUNTS = {
    "INTEGRATION_VERIFIED": 9,
    "UNIT_VERIFIED": 15,
    "PARTIAL_VERIFIED": 2,
    "SOURCE_PRESENT": 11,
    "DORMANT": 1,
    "UNVERIFIABLE": 1,
    "RUNTIME_VERIFIED": 0,
    "PRODUCTION_VERIFIED": 0,
}
ALL_STATUSES = frozenset(EXPECTED_COUNTS)
EXPECTED_IDS = frozenset(
    [f"ENG-A{i:02d}" for i in range(1, 13)]
    + [f"ENG-B{i:02d}" for i in range(1, 13)]
    + [f"ENG-C{i:02d}" for i in range(1, 10)]
    + [f"ENG-D{i:02d}" for i in range(1, 7)]
)


def _find_app_imports(root: Path) -> list[str]:
    """Guard: no application module may import/execute the index."""
    needles = ("national_capability_index", "NATIONAL_CAPABILITY_REGISTRY")
    hits: list[str] = []
    for path in (root / "backend" / "app").rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(n in text for n in needles):
            hits.append(str(path.relative_to(root)))
    return sorted(hits)


def verify(root: Path, index_path: Path | None = None) -> dict:
    """Run all checks and return a deterministic result dict (never raises on a failed check)."""
    root = Path(root)
    target = Path(index_path) if index_path else root / INDEX_REL
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    # 1. File exists and parses.
    exists = target.is_file()
    check("index_file_exists", exists, str(target))
    doc: dict = {}
    if exists:
        try:
            doc = json.loads(target.read_text(encoding="utf-8"))
            check("index_json_parses", True)
        except (json.JSONDecodeError, OSError) as exc:
            check("index_json_parses", False, str(exc))

    # 2. Reference-only envelope (guard against an executing registry / SPOF).
    check("schema_version", doc.get("schema_version") == "1.0.0", str(doc.get("schema_version")))
    check("kind_reference_only", doc.get("kind") == "reference_only_static_index", str(doc.get("kind")))
    check("executing_false", doc.get("executing") is False, str(doc.get("executing")))
    authority = str(doc.get("authority", "")).lower()
    check("authority_none", authority.startswith("none") and "advisory" in authority, authority)
    check("no_runtime_dispatch_keys", not ({"routes", "handlers", "workers", "dispatch"} & set(doc)),
          ",".join(sorted(set(doc))))

    engines = doc.get("engines", [])
    # 3. Completeness / uniqueness.
    ids = [e.get("id") for e in engines if isinstance(e, dict)]
    check("engine_count_39", len(ids) == 39, str(len(ids)))
    check("engine_ids_unique", len(ids) == len(set(ids)), str(len(set(ids))))
    check("engine_ids_exact", frozenset(ids) == EXPECTED_IDS,
          f"missing={sorted(EXPECTED_IDS - set(ids))} extra={sorted(set(ids) - EXPECTED_IDS)}")

    # 4. Status taxonomy and distribution (frozen canonical 9/15/2/11/1/1, 0 runtime/prod).
    unknown = sorted({e.get("status") for e in engines if e.get("status") not in ALL_STATUSES})
    check("status_taxonomy_known", not unknown, str(unknown))
    recomputed = {s: 0 for s in EXPECTED_COUNTS}
    for e in engines:
        if isinstance(e, dict) and e.get("status") in recomputed:
            recomputed[e["status"]] += 1
    check("declared_counts_match_rows", doc.get("status_counts") == recomputed,
          f"declared={doc.get('status_counts')} rows={recomputed}")
    check("status_counts_canonical", recomputed == EXPECTED_COUNTS, str(recomputed))

    # 5. Dormant / unmounted invariants (never activate without approval).
    by_id = {e.get("id"): e for e in engines if isinstance(e, dict)}
    a12 = by_id.get("ENG-A12", {})
    b09 = by_id.get("ENG-B09", {})
    check("eng_a12_dormant", a12.get("status") == "DORMANT", str(a12.get("status")))
    check("eng_b09_unverifiable", b09.get("status") == "UNVERIFIABLE", str(b09.get("status")))
    a12_note = str(doc.get("special_states", {}).get("ENG-A12", "")).lower()
    b09_note = str(doc.get("special_states", {}).get("ENG-B09", "")).lower()
    check("eng_a12_stays_dormant_note", "dormant" in a12_note and "never activate" in a12_note, a12_note)
    check("eng_b09_unmounted_note", "unmounted" in b09_note and "do not enable" in b09_note, b09_note)

    # 6. Every indexed source path exists (index is a faithful pointer, not fiction).
    missing = [e.get("id") for e in engines if isinstance(e, dict)
               and not (root / "backend" / str(e.get("source", ""))).exists()]
    check("all_source_paths_exist", not missing, f"missing={missing}")

    # 7. Canonical inventory still carries exactly 39 engine rows.
    inv = root / INVENTORY_REL
    inv_rows = 0
    if inv.is_file():
        inv_rows = len(re.findall(r"^\|\s*ENG-[A-D]\d{2}\b", inv.read_text(encoding="utf-8"), re.M))
    check("inventory_has_39_rows", inv_rows == 39, str(inv_rows))

    # 8. No application module imports the index (it must never become executing).
    hits = _find_app_imports(root)
    check("app_does_not_import_index", not hits, ",".join(hits))

    failed = [c for c in checks if not c[1]]
    return {
        "verdict": "PASS" if not failed else "FAIL",
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failed),
        "failed_checks": [{"name": n, "detail": d} for n, ok, d in failed],
        "index": str(target),
        "engine_count": len(ids),
        "status_counts": recomputed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--index", default=None, help="override index path (negative-control testing)")
    args = parser.parse_args(argv)
    result = verify(Path(args.root), Path(args.index) if args.index else None)
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
