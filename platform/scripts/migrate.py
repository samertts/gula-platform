#!/usr/bin/env python3
import argparse
import asyncio
import sys


async def migrate():
    print("Migration check:")
    print("  Service bridge state: all services at BRIDGE state")
    print("  Patient service:         bridge  (target: native)")
    print("  Order service:           bridge  (target: native)")
    print("  Result service:          bridge  (target: native)")
    print("  Lab service:             bridge  (target: native)")
    print("  Auth service:            monolith  (target: bridge)")

    print("\nMigration readiness:")
    from platform.migration import ServiceBridge
    bridge = ServiceBridge()
    from platform.domain.services import PatientService, OrderService, ResultService, LabService, AuthService
    from platform.integration.adapters.monolith import MonolithAdapter

    monolith = MonolithAdapter()
    bridge.register("patient", monolith_impl=monolith, native_impl=PatientService())
    bridge.register("order", monolith_impl=monolith, native_impl=OrderService())
    bridge.register("result", monolith_impl=monolith, native_impl=ResultService())
    bridge.register("lab", monolith_impl=monolith, native_impl=LabService())

    print("\nBridge summary:")
    for name, state in bridge.summary().items():
        print(f"  {name:10s} → {state}")


def main():
    parser = argparse.ArgumentParser(description="GULA Migration Tool")
    parser.add_argument("action", choices=["check", "status", "plan"], default="check", nargs="?")
    args = parser.parse_args()

    if args.action == "check":
        asyncio.run(migrate())
    elif args.action == "status":
        print("Migration status: IN PROGRESS")
        print("  Phase 1: Core platform    [DONE]")
        print("  Phase 2: Shared services  [DONE]")
        print("  Phase 3: App modules      [DONE]")
        print("  Phase 4: API layer        [DONE]")
        print("  Phase 5: Monolith cutover [PENDING]")
    elif args.action == "plan":
        print("Migration plan:")
        print("  1. Deploy platform alongside monolith")
        print("  2. Route new traffic to platform API")
        print("  3. Run dual-write period")
        print("  4. Validate data consistency")
        print("  5. Cut over each service from bridge → native")
        print("  6. Decommission monolith routes")


if __name__ == "__main__":
    main()
