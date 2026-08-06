"""PROGRAM-STABLE-004 — Domain Platform Framework CLI.

Commands:
  domain-audit    resolve the 11 canonical Domains from source
  domain-isolate  run the Phase 3 isolation scan
  domain-certify  run the Phase 7 certification
  domain-docs     regenerate the 7 official DOMAIN_*.md documents
  domain-report   write state/DATA.json + docs (full pipeline)
  domain-check    full pipeline, assert platform certification PASS
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import STATE_DIR
from .pipeline import run_pipeline
from .report import generate_all


def _load(state_path: Path = STATE_DIR / "DATA.json") -> dict:
    if not state_path.exists():
        print(f"no state at {state_path} — run `domain-report` first", file=sys.stderr)
        sys.exit(2)
    return json.loads(state_path.read_text(encoding="utf-8"))


def cmd_audit() -> int:
    data = run_pipeline()
    for manifest in data["manifests"]:
        print(f"{manifest['code']:<16} v{manifest['version']:<8} {manifest['name_en']}  "
              f"[{len(manifest['modules'])} modules]")
    return 0


def cmd_isolate() -> int:
    data = run_pipeline()
    iso = data["isolation"]
    print(f"isolation passes: {iso['passes']}")
    for key, label in (
        ("cross_domain", "cross-domain imports"),
        ("circular", "circular dependencies"),
        ("shared_state", "shared mutable state"),
        ("permission_leaks", "permission leakage"),
        ("db_coupling", "direct database coupling"),
        ("table_overlaps", "table overlaps"),
    ):
        print(f"  {label:<28} {len(iso[key])}")
    return 0 if iso["passes"] else 1


def cmd_certify() -> int:
    data = run_pipeline()
    for cert in data["certifications"]:
        verdict = "CERTIFIED" if cert["passed"] else "NOT CERTIFIED"
        print(f"{cert['domain_code']:<16} {verdict:<14} {cert['score']}%")
    platform = data["platform_certification"]
    print(f"\nplatform: {platform['verdict']} — {platform['passed']}/{platform['total']} "
          f"({platform['score']}%)")
    return 0 if platform["verdict"] == "CERTIFIED" else 1


def cmd_docs() -> int:
    data = run_pipeline()
    written = generate_all(data)
    for path in written.values():
        print(f"wrote {path.name}")
    return 0


def cmd_report() -> int:
    data = run_pipeline()
    state_dir = STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "DATA.json"
    state_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    written = generate_all(data)
    print(f"state written: {state_path}")
    platform = data["platform_certification"]
    print(f"platform: {platform['verdict']} — {platform['passed']}/{platform['total']} ({platform['score']}%)")
    for name in written:
        print(f"docs: {name}")
    return 0


def cmd_check() -> int:
    data = run_pipeline()
    platform = data["platform_certification"]
    iso_ok = data["isolation"]["passes"]
    cert_ok = platform["verdict"] == "CERTIFIED"
    print(f"isolation: {'PASS' if iso_ok else 'FAIL'} | certification: "
          f"{platform['passed']}/{platform['total']} "
          f"({'PASS' if cert_ok else 'FAIL'})")
    return 0 if iso_ok and cert_ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="domains", description=__doc__)
    parser.add_argument("command", choices=["audit", "isolate", "certify", "docs", "report", "check"])
    args = parser.parse_args(argv)
    return {
        "audit": cmd_audit,
        "isolate": cmd_isolate,
        "certify": cmd_certify,
        "docs": cmd_docs,
        "report": cmd_report,
        "check": cmd_check,
    }[args.command]()


DOMAINS_COMMANDS = {
    "domain-audit": cmd_audit,
    "domain-isolate": cmd_isolate,
    "domain-certify": cmd_certify,
    "domain-docs": cmd_docs,
    "domain-report": cmd_report,
    "domain-check": cmd_check,
}


if __name__ == "__main__":
    raise SystemExit(main())
