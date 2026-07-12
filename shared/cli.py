#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


class GulaCLI:
    def __init__(self) -> None:
        self._parser = argparse.ArgumentParser(prog="gula", description="GULA Platform Developer CLI")
        self._setup_subparsers()

    def _setup_subparsers(self) -> None:
        sub = self._parser.add_subparsers(dest="command")

        p_health = sub.add_parser("health", help="Check platform health")
        p_health.add_argument("--url", default=os.getenv("GULA_URL", "http://localhost:8080"))

        p_patient = sub.add_parser("patient", help="Patient operations")
        pp = p_patient.add_subparsers(dest="action")
        pc = pp.add_parser("create", help="Create a patient")
        pc.add_argument("--first-name", required=True)
        pc.add_argument("--last-name", required=True)
        pc.add_argument("--phone")
        pg = pp.add_parser("get", help="Get patient by ID")
        pg.add_argument("id", type=int)

        p_order = sub.add_parser("order", help="Order operations")
        po = p_order.add_subparsers(dest="action")
        oc = po.add_parser("create", help="Create an order")
        oc.add_argument("--patient-id", type=int, required=True)
        oc.add_argument("--tests", nargs="+", required=True)
        og = po.add_parser("get", help="Get order by ID")
        og.add_argument("id", type=int)

        p_gen = sub.add_parser("generate", help="Code generation")
        pgs = p_gen.add_subparsers(dest="generator")
        pgs.add_parser("module", help="Generate a module skeleton").add_argument("name")
        pgs.add_parser("migration", help="Generate migration").add_argument("message")

        p_config = sub.add_parser("config", help="Configuration")
        p_config.add_argument("--show", action="store_true")
        p_config.add_argument("--validate", action="store_true")

    def run(self, args: list[str] | None = None) -> int:
        parsed = self._parser.parse_args(args)
        cmd = parsed.command
        if not cmd:
            self._parser.print_help()
            return 1
        method = getattr(self, f"cmd_{cmd}", None)
        return method(parsed) if method else 1

    def cmd_health(self, args: argparse.Namespace) -> int:
        try:
            import httpx
            resp = httpx.get(f"{args.url}/health", timeout=10)
            _print_json(resp.json())
            return 0 if resp.status_code == 200 else 1
        except Exception as exc:
            print(f"Health check failed: {exc}", file=sys.stderr)
            return 1

    def cmd_patient(self, args: argparse.Namespace) -> int:
        from shared.sdk.client import GulaClient
        client = GulaClient(base_url=os.getenv("GULA_URL", "http://localhost:8080"))
        try:
            if args.action == "create":
                data = {"first_name": args.first_name, "last_name": args.last_name}
                if args.phone:
                    data["phone"] = args.phone
                _print_json(client.create_patient(data))
                return 0
            elif args.action == "get":
                _print_json(client.get_patient(args.id))
                return 0
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return 1

    def cmd_order(self, args: argparse.Namespace) -> int:
        from shared.sdk.client import GulaClient
        client = GulaClient(base_url=os.getenv("GULA_URL", "http://localhost:8080"))
        try:
            if args.action == "create":
                _print_json(client.create_order({"patient_id": args.patient_id, "test_types": args.tests}))
                return 0
            elif args.action == "get":
                _print_json(client.get_order(args.id))
                return 0
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return 1

    def cmd_generate(self, args: argparse.Namespace) -> int:
        if args.generator == "module":
            from shared.generators.module import ModuleGenerator
            ModuleGenerator(args.name).generate()
            return 0
        elif args.generator == "migration":
            from shared.generators.migration import MigrationGenerator
            MigrationGenerator(args.message).generate()
            return 0
        return 1

    def cmd_config(self, args: argparse.Namespace) -> int:
        if args.show:
            for key in sorted(os.environ):
                if key.startswith("GULA_") or key.startswith("ENABLE_") or key.startswith("SNDHS_"):
                    print(f"{key}={os.environ[key]}")
            return 0
        if args.validate:
            missing = [r for r in ["SECRET_KEY", "DATABASE_URL"] if not os.getenv(r)]
            if missing:
                print(f"Missing required config: {', '.join(missing)}", file=sys.stderr)
                return 1
            print("Configuration valid")
            return 0
        return 0


def main() -> None:
    GulaCLI().run()


if __name__ == "__main__":
    main()
