from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOTS = (ROOT / "backend/app", ROOT / "frontend-v2/src", ROOT / "frontend-v3/src")
SKIP_PARTS = {"__pycache__", "node_modules", "dist", "build", ".git"}
PATTERN = re.compile(
    r"\bLabUser\b|\blab_id\b|\blegacy_lab_id\b|\blegacy_lab_user_id\b|"
    r"LegacyAccountLink|ClinicalAuthorizationContext|legacy[_ -]?(?:auth|tenant|clinical)|"
    r"legacy endpoints?|legacy routes?",
    re.IGNORECASE,
)


def classification(path: Path, text: str) -> str:
    normalized = path.as_posix()
    if "frontend-v2" in normalized:
        return "DEPRECATE"
    if "frontend-v3" in normalized:
        return "MIGRATE" if any(token in text for token in ("/patients", "/orders", "workspaceScopedReads", "lab_id")) else "RETAIN"
    if any(token in normalized for token in (
        "clinical_authorization_context_service.py",
        "legacy_mapping_service.py",
        "legacy_account_link.py",
        "clinical_scope.py",
        "clinical_scope_bridge_service.py",
    )):
        return "ADAPTER"
    if "/identity/" in normalized:
        return "RETAIN"
    if "/routes/" in normalized or "/security/" in normalized or "/services/" in normalized:
        return "RETAIN"
    return "RETAIN"


def main() -> None:
    occurrences: list[dict[str, object]] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            matches = list(PATTERN.finditer(text))
            if not matches:
                continue
            rel = path.relative_to(ROOT).as_posix()
            status = classification(path, text)
            lines = text.splitlines()
            for match in matches:
                line_no = text.count("\n", 0, match.start()) + 1
                line = lines[line_no - 1].strip()[:240]
                occurrences.append({"file": rel, "line": line_no, "matched": match.group(0), "classification": status, "evidence": line})

    counts = Counter(item["classification"] for item in occurrences)
    report = ROOT / "reports/PHASE_10B_LEGACY_INVENTORY.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 10-B — Legacy Clinical Identity and Context Inventory",
        "",
        "This inventory is generated from source files, not inherited reports. It records every matched source occurrence for `LabUser`, `lab_id`, and legacy identity/context terms under the scanned application roots. No source was deleted or migrated by this inventory step.",
        "",
        "## Classification summary",
        "",
        "| Classification | Occurrences | Meaning |",
        "|---|---:|---|",
        "| RETAIN | %d | Existing source remains authoritative only within its current legacy boundary until an approved adapter replaces it. |" % counts.get("RETAIN", 0),
        "| MIGRATE | %d | Frontend or caller must move to the canonical gateway; it must not receive a legacy fallback. |" % counts.get("MIGRATE", 0),
        "| ADAPTER | %d | Existing reviewed identity/scope bridge may be reused only after canonical authorization. |" % counts.get("ADAPTER", 0),
        "| DEPRECATE | %d | Legacy frontend surface remains for compatibility but is not a new gateway authority. |" % counts.get("DEPRECATE", 0),
        "| REMOVE | 0 | No removal is authorized in Phase 10-B. |",
        "",
        "## Rules",
        "",
        "* `lab_id`, `organization_id`, `facility_id`, and `workspace_id` from a browser request are never authoritative.",
        "* `get_current_user`/`LabUser` remains a legacy boundary only; the new gateway must resolve `NiamActor` and trusted workspace context first.",
        "* Unmapped, ambiguous, inactive, or conflicting identities are blocked and audited.",
        "",
        "## Occurrences",
        "",
        "| File | Line | Match | Classification | Source evidence |",
        "|---|---:|---|---|---|",
    ]
    for item in occurrences:
        evidence = str(item["evidence"]).replace("|", "\\|")
        lines.append(f"| `{item['file']}` | {item['line']} | `{item['matched']}` | **{item['classification']}** | `{evidence}` |")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = ROOT / "reports/PHASE_10B_LEGACY_INVENTORY.json"
    json_path.write_text(json.dumps({"counts": counts, "occurrences": occurrences}, ensure_ascii=False, indent=2, default=int) + "\n", encoding="utf-8")
    print(f"legacy_occurrences={len(occurrences)}")
    print(json.dumps(dict(counts), sort_keys=True))


if __name__ == "__main__":
    main()
