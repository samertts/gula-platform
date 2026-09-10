"""Classify every workflow by whether it actually gates a pull request.

PR #258 read 6/6 green while the pipeline holding the backend test suite had
never run on it: ``ci.yml`` fires only for pull requests into ``main`` or
``staging``, and the stacked PRs target each other. A count of passing checks
says nothing about coverage unless you know which tier those checks belong to.

    python3 scripts/enterprise_readiness/ci_truth.py [--json]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

WORKFLOWS = pathlib.Path(__file__).resolve().parents[2] / ".github" / "workflows"


def classify(source: str) -> dict[str, object]:
    name_match = re.search(r"^name:\s*(.+)$", source, re.M)
    on_match = re.search(r"^on:\s*\n((?:[ \t]+.*\n|\n)*?)(?=^\w|\Z)", source, re.M)
    block = on_match.group(1) if on_match else ""
    pull_request = re.search(r"^\s{2}pull_request:\s*\n((?:\s{4,}.*\n)*)", block, re.M)
    branches = (
        re.search(r"branches:\s*\[([^\]]*)\]", pull_request.group(1))
        if pull_request
        else None
    )
    return {
        "name": name_match.group(1).strip().strip("\"'") if name_match else "",
        "pull_request": bool(pull_request),
        "pr_branches": (
            [b.strip().strip("\"'") for b in branches.group(1).split(",")]
            if branches
            else ("ALL" if pull_request else None)
        ),
        "schedule": "schedule:" in block,
        "push": "push:" in block,
        "workflow_dispatch": "workflow_dispatch:" in block,
    }


def tier(row: dict[str, object]) -> str:
    if not row["pull_request"]:
        return "not-a-pr-check"
    return "every-pr" if row["pr_branches"] == "ALL" else "protected-branch-prs-only"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args(argv)

    rows = []
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        row = classify(path.read_text(encoding="utf-8"))
        row["file"] = path.name
        row["tier"] = tier(row)
        rows.append(row)

    every_pr = [r for r in rows if r["tier"] == "every-pr"]
    if args.json:
        print(json.dumps({"workflows": rows, "every_pr": [r["file"] for r in every_pr]}, indent=1))
        return 0

    for want, label in (
        ("every-pr", "runs on EVERY pull request"),
        ("protected-branch-prs-only", "runs only on PRs into a protected branch"),
        ("not-a-pr-check", "never gates a pull request"),
    ):
        selected = [r for r in rows if r["tier"] == want]
        print(f"\n{label} ({len(selected)}):")
        for row in selected:
            suffix = "" if row["pr_branches"] in (None, "ALL") else f"  -> {','.join(row['pr_branches'])}"
            print(f"  {row['file']:34}{suffix}")
    print(
        f"\n{len(every_pr)} of {len(rows)} workflows gate every PR. "
        "A stacked PR is gated by those alone."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
