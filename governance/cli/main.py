from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from governance.catalogs.dependency_registry import DependencyRegistry
from governance.catalogs.technology_catalog import TechnologyCatalog
from governance.compiler.constitution_compiler import ConstitutionCompiler
from governance.constitution_engine import ConstitutionEngine
from governance.engine.architecture_decision_engine import ArchitectureDecisionEngine
from governance.engine.compliance_monitor import ContinuousComplianceMonitor
from governance.engine.dashboards import CostDashboard, SovereigntyDashboard
from governance.engine.procurement_engine import ProcurementEngine
from governance.engine.recommendation_engine import AIRecommendationEngine
from governance.engine.review_engine import AutonomousReviewEngine


class GovernanceCLI:
    def __init__(self) -> None:
        self.compiler = ConstitutionCompiler()
        self.engine = ConstitutionEngine()
        self.catalog = TechnologyCatalog()
        self.registry = DependencyRegistry()
        self.procurement = ProcurementEngine()
        self.arch_engine = ArchitectureDecisionEngine()
        self.recommender = AIRecommendationEngine()
        self.reviewer = AutonomousReviewEngine()
        self.compliance = ContinuousComplianceMonitor()
        self.cost_dashboard = CostDashboard()
        self.sovereignty_dashboard = SovereigntyDashboard()

    def run(self, argv: list[str] | None = None) -> int:
        parser = argparse.ArgumentParser(description="GULA Autonomous Governance CLI")
        sub = parser.add_subparsers(dest="command", help="Available commands")

        p_constitution = sub.add_parser("constitution", help="Constitution operations")
        p_constitution.add_argument("action", choices=["check", "compile", "export", "graph"])

        p_recommend = sub.add_parser("recommend", help="Get AI recommendation")
        p_recommend.add_argument("query", help="What to recommend")
        p_recommend.add_argument("--category", "-c", default="", help="Technology category")

        p_dep = sub.add_parser("dependency", help="Dependency operations")
        p_dep.add_argument("action", choices=["audit", "list", "search"])
        p_dep.add_argument("--query", "-q", default="", help="Search query")
        p_dep.add_argument("--risk", "-r", default="", help="Filter by risk level")

        p_proc = sub.add_parser("procurement", help="Procurement evaluation")
        p_proc.add_argument("requirement", help="What to procure")
        p_proc.add_argument("--cost", "-c", type=float, default=0, help="Estimated cost")

        p_arch = sub.add_parser("architecture", help="Architecture review")
        p_arch.add_argument("action", choices=["review", "adr"])
        p_arch.add_argument("--title", "-t", default="Architecture Decision", help="ADR title")
        p_arch.add_argument("--context", "-x", default="", help="ADR context")

        p_tech = sub.add_parser("technology", help="Technology catalog operations")
        p_tech.add_argument("action", choices=["search", "list", "categories"])
        p_tech.add_argument("--query", "-q", default="", help="Search query")
        p_tech.add_argument("--category", "-c", default="", help="Filter by category")

        p_cost = sub.add_parser("cost", help="Cost dashboard")
        p_cost.add_argument("action", choices=["report", "dashboard"])

        p_sovereignty = sub.add_parser("sovereignty", help="Sovereignty dashboard")
        p_sovereignty.add_argument("action", choices=["report", "dashboard"])

        p_compliance = sub.add_parser("compliance", help="Compliance operations")
        p_compliance.add_argument("action", choices=["check", "report", "monitor"])

        p_adr = sub.add_parser("adr", help="Architecture Decision Record")
        p_adr.add_argument("--title", "-t", default="Architecture Decision", help="Title")
        p_adr.add_argument("--context", "-x", default="", help="Context")

        args = parser.parse_args(argv)

        if args.command == "constitution":
            return self._handle_constitution(args)
        elif args.command == "recommend":
            return self._handle_recommend(args)
        elif args.command == "dependency":
            return self._handle_dependency(args)
        elif args.command == "procurement":
            return self._handle_procurement(args)
        elif args.command == "architecture":
            return self._handle_architecture(args)
        elif args.command == "technology":
            return self._handle_technology(args)
        elif args.command == "cost":
            return self._handle_cost(args)
        elif args.command == "sovereignty":
            return self._handle_sovereignty(args)
        elif args.command == "compliance":
            return self._handle_compliance(args)
        elif args.command == "adr":
            return self._handle_adr(args)
        else:
            parser.print_help()
            return 1

    def _handle_constitution(self, args: argparse.Namespace) -> int:
        if args.action == "check":
            report = self.engine.generate_compliance_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))
        elif args.action == "compile":
            compiled = self.compiler.compile_all()
            outputs = self.compiler.output_all()
            print(f"Compiled {compiled.document_count} documents with {compiled.rule_count} rules")
            print(f"Checksum: {compiled.checksum}")
            print(f"Conflicts detected: {compiled.conflict_count}")
        elif args.action == "export":
            self.compiler.export_json("governance/constitution.json")
            self.compiler.export_yaml("governance/constitution.yaml")
            self.compiler.export_db("governance/constitution.db")
            self.compiler.export_graph("governance/constitution.graph")
            print("Exported to: governance/constitution.{json,yaml,db,graph}")
        return 0

    def _handle_recommend(self, args: argparse.Namespace) -> int:
        rec = self.recommender.recommend(args.query, args.category)
        print(json.dumps(rec.to_dict(), indent=2, ensure_ascii=False))
        return 0

    def _handle_dependency(self, args: argparse.Namespace) -> int:
        if args.action == "audit":
            report = self.compliance.run_check()
            dep_alerts = [a for a in report["alerts"] if a["type"] in ("high_risk_dependency", "outdated_dependency", "cve_found")]
            print(json.dumps({"dependency_alerts": dep_alerts, "total": len(dep_alerts)}, indent=2))
        elif args.action == "list":
            deps = self.registry.dependencies
            for d in deps:
                print(f"{d.name:30s} v{d.version:15s} {d.risk:10s} {d.maintenance_status:15s}")
            print(f"\nTotal: {len(deps)} dependencies")
        elif args.action == "search":
            results = self.registry.search(args.query, risk=args.risk)
            for r in results:
                print(f"{r.name:30s} v{r.version:15s} {r.risk:10s}")
            print(f"\nFound: {len(results)}")
        return 0

    def _handle_procurement(self, args: argparse.Namespace) -> int:
        ctx = {"cost": args.cost} if args.cost else {}
        decision = self.procurement.evaluate(args.requirement, ctx)
        print(f"Requirement: {args.requirement}")
        print(f"Decision: {decision.decision}")
        print(f"Recommendation: {decision.recommendation}")
        print(f"Cost: {decision.cost_report}")
        return 0

    def _handle_architecture(self, args: argparse.Namespace) -> int:
        if args.action == "review":
            findings = self.reviewer.review_all()
            report = self.reviewer.get_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))
        elif args.action == "adr":
            adr = self.arch_engine.generate_adr(args.title, args.context or "Architecture decision context")
            print(json.dumps(adr.to_dict(), indent=2, ensure_ascii=False))
        return 0

    def _handle_technology(self, args: argparse.Namespace) -> int:
        if args.action == "search":
            results = self.catalog.search(args.query, args.category)
            for r in results:
                status = r.status.value
                print(f"{r.name:30s} {r.category:15s} {r.license_type:20s} {status:15s} cost=${r.cost}")
            print(f"\nFound: {len(results)}")
        elif args.action == "list":
            for t in self.catalog.technologies:
                print(f"{t.name:30s} {t.category:15s} {t.status.value:15s}")
            print(f"\nTotal: {len(self.catalog.technologies)} technologies")
        elif args.action == "categories":
            for c in self.catalog.get_categories():
                count = len(self.catalog.get_by_category(c))
                print(f"{c:20s} ({count} technologies)")
        return 0

    def _handle_cost(self, args: argparse.Namespace) -> int:
        metrics = self.cost_dashboard.get_metrics()
        if args.action == "report":
            print(json.dumps(metrics, indent=2, ensure_ascii=False))
        elif args.action == "dashboard":
            print("=== Cost Dashboard ===")
            print(f"Infrastructure Cost: ${metrics['infrastructure_cost']['monthly']}/mo")
            print(f"Free Technologies: {metrics['infrastructure_cost']['free_technologies']}")
            print(f"Open Source Ratio: {metrics['open_source_ratio']}%")
            print(f"Annual Savings: {metrics['savings']['open_source_savings']}")
            print(f"Vendor Lock-In Risks: {metrics['vendor_lock_in_risk']['count']}")
        return 0

    def _handle_sovereignty(self, args: argparse.Namespace) -> int:
        metrics = self.sovereignty_dashboard.get_metrics()
        if args.action == "report":
            print(json.dumps(metrics, indent=2, ensure_ascii=False))
        elif args.action == "dashboard":
            print("=== Sovereignty Dashboard ===")
            print(f"Self-Hosted: {metrics['self_hosted_percent']}%")
            print(f"Open Source: {metrics['open_source_percent']}%")
            print(f"Commercial: {metrics['commercial_percent']}%")
            print(f"National Control: {metrics['national_control_percent']}%")
            print(f"Foreign Dependencies: {metrics['foreign_dependency_percent']}%")
            print(f"Vendor Lock-In: {metrics['vendor_lock_in_percent']}%")
            print(f"Status: {metrics['status']}")
        return 0

    def _handle_compliance(self, args: argparse.Namespace) -> int:
        if args.action == "check":
            report = self.engine.generate_compliance_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))
        elif args.action == "report":
            report = self.compliance.run_check()
            print(json.dumps(report, indent=2, ensure_ascii=False))
        elif args.action == "monitor":
            report = self.compliance.run_check()
            print(f"Status: {report['status']}")
            print(f"Alerts: {report['total_alerts']} (Blockers: {report['blocker_alerts']}, High: {report['high_alerts']})")
            for a in report["alerts"][:5]:
                print(f"  [{a['severity']}] {a['message']}")
        return 0

    def _handle_adr(self, args: argparse.Namespace) -> int:
        adr = self.arch_engine.generate_adr(args.title, args.context or "Architecture decision context")
        print(f"ADR: {adr.title}")
        print(f"Decision: {adr.decision}")
        print(f"Rationale: {adr.rationale}")
        print(f"Alternatives: {len(adr.alternatives)} considered")
        print(f"Compliance: {adr.compliance_report.get('score', 0)}/100")
        return 0


def main(argv: list[str] | None = None) -> int:
    cli = GovernanceCLI()
    return cli.run(argv)


if __name__ == "__main__":
    sys.exit(main())
