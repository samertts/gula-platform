#!/usr/bin/env python3
import argparse
import json
import sys


def cli():
    parser = argparse.ArgumentParser(description="GULA Platform CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    health_parser = subparsers.add_parser("health", help="Check platform health")
    health_parser.add_argument("--host", default="http://localhost:8000")

    modules_parser = subparsers.add_parser("modules", help="List registered modules")
    modules_parser.add_argument("--host", default="http://localhost:8000")

    seed_parser = subparsers.add_parser("seed", help="Seed test data")
    seed_parser.add_argument("--labs", type=int, default=3, help="Number of labs")
    seed_parser.add_argument("--patients", type=int, default=10, help="Number of patients per lab")

    migrate_parser = subparsers.add_parser("migrate", help="Migration status")
    migrate_parser.add_argument("--check", action="store_true", help="Check migration state")

    config_parser = subparsers.add_parser("config", help="Show platform configuration")
    config_parser.add_argument("--key", help="Specific config key to show")

    args = parser.parse_args()

    if args.command == "health":
        _cmd_health(args)
    elif args.command == "modules":
        _cmd_modules(args)
    elif args.command == "seed":
        _cmd_seed(args)
    elif args.command == "migrate":
        _cmd_migrate(args)
    elif args.command == "config":
        _cmd_config(args)
    else:
        parser.print_help()
        sys.exit(1)


def _cmd_health(args):
    print(f"Checking health at {args.host}...")
    print("  Health endpoint:   /health/live")
    print("  Readiness:         /health/ready")
    print("  Status:            /health/status")
    print("  Deep:              /health/deep")


def _cmd_modules(args):
    print("Registered modules:")
    modules = [
        ("gula.patient", "1.0.0", "Patient management"),
        ("gula.order", "1.0.0", "Order management"),
        ("gula.result", "1.0.0", "Result management"),
        ("gula.lab", "1.0.0", "Lab administration"),
        ("gula.user", "1.0.0", "User & auth"),
        ("gula.report", "1.0.0", "Reporting & analytics"),
    ]
    for name, version, desc in modules:
        print(f"  {name:22s} v{version:8s}  {desc}")


def _cmd_seed(args):
    print(f"Seeding {args.labs} labs with {args.patients} patients each...")
    print("  Total patients to create:", args.labs * args.patients)
    print("  Seed complete (mock)")


def _cmd_migrate(args):
    print("Migration state:")
    services = [
        ("patient", "bridge"),
        ("order", "bridge"),
        ("result", "bridge"),
        ("lab", "bridge"),
        ("auth", "monolith"),
    ]
    for svc, state in services:
        print(f"  {svc:10s} → {state}")


def _cmd_config(args):
    config = {
        "app_name": "gula-platform",
        "version": "1.0.0",
        "environment": "development",
        "database": "postgresql+asyncpg://localhost:5432/gula",
        "redis": "redis://localhost:6379/0",
    }
    if args.key:
        val = config.get(args.key, "not found")
        print(f"{args.key}: {val}")
    else:
        print(json.dumps(config, indent=2))
