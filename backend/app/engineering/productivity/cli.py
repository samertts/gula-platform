from __future__ import annotations

import argparse
import sys
from pathlib import Path

from backend.app.engineering.ci.quality_gates import QualityGates
from backend.app.engineering.crud.generator import CRUDGenerator, EntityField, EntitySpec
from backend.app.engineering.generators.capability import CapabilityGenerator, CapabilitySpec
from backend.app.engineering.generators.microservice import MicroserviceGenerator, MicroserviceSpec
from backend.app.engineering.generators.module import ModuleGenerator, ModuleSpec
from backend.app.engineering.generators.plugin import PluginGenerator, PluginSpec
from backend.app.engineering.generators.project import ProjectGenerator, ProjectSpec
from backend.app.engineering.validation.clean_arch import CleanArchitectureValidator
from backend.app.engineering.validation.solid import SOLIDValidator


PACKAGE = "backend.app.engineering"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gula",
        description="GULA Engineering Automation Platform",
        epilog="From now on, GULA builds GULA.",
    )
    sub = parser.add_subparsers(dest="command")

    # gula new
    new = sub.add_parser("new", help="Scaffold new artifacts")
    new_sub = new.add_subparsers(dest="new_type")

    _add_new_project(new_sub)
    _add_new_module(new_sub)
    _add_new_plugin(new_sub)
    _add_new_platform(new_sub)
    _add_new_capability(new_sub)
    _add_new_crud(new_sub)

    # gula generate
    gen = sub.add_parser("generate", help="Generate code artifacts")
    gen_sub = gen.add_subparsers(dest="generator")

    _add_generate_microservice(gen_sub)
    _add_generate_crud(gen_sub)
    _add_generate_rest(gen_sub)
    _add_generate_openapi(gen_sub)
    _add_generate_dto(gen_sub)
    _add_generate_repository(gen_sub)
    _add_generate_cqrs(gen_sub)
    _add_generate_tests(gen_sub)
    _add_generate_adr(gen_sub)
    _add_generate_architecture(gen_sub)
    _add_generate_diagram(gen_sub)
    _add_generate_ci(gen_sub)
    _add_generate_docker(gen_sub)
    _add_generate_compose(gen_sub)
    _add_generate_kubernetes(gen_sub)

    # gula validate
    validate = sub.add_parser("validate", help="Validate architecture")
    validate.add_argument("--dir", default=".", help="Project root directory")
    validate.add_argument(
        "--type",
        default="clean-arch",
        choices=["clean-arch", "solid", "ddd", "cqrs", "event-driven"],
        help="Validation type",
    )

    # gula quality
    quality = sub.add_parser("quality", help="Run quality gates")
    quality.add_argument("--dir", default=".", help="Project root directory")
    quality.add_argument(
        "--gates",
        nargs="*",
        default=["ruff", "pytest", "mypy", "coverage", "bandit"],
        choices=["ruff", "pytest", "mypy", "coverage", "bandit"],
        help="Gates to run",
    )
    quality.add_argument("--coverage-min", type=int, default=80, help="Minimum coverage percentage")

    # gula doctor
    doctor = sub.add_parser("doctor", help="System diagnostics")
    doctor.add_argument("--dir", default=".", help="Project root directory")

    # gula info
    info = sub.add_parser("info", help="Show platform info")

    args = parser.parse_args()

    if args.command == "new":
        _handle_new(args)
    elif args.command == "generate":
        _handle_generate(args)
    elif args.command == "validate":
        _handle_validate(args)
    elif args.command == "quality":
        _handle_quality(args)
    elif args.command == "doctor":
        _handle_doctor(args)
    elif args.command == "info":
        _handle_info()
    else:
        parser.print_help()


def _add_new_project(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("project", help="Scaffold a new project")
    p.add_argument("name", help="Project name")
    p.add_argument("--description", default="", help="Project description")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--version", default="0.1.0", help="Initial version")


def _add_new_module(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("module", help="Scaffold a new module (Clean Architecture)")
    p.add_argument("name", help="Module name")
    p.add_argument("--description", default="", help="Module description")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--no-entity", action="store_true", help="Skip entity generation")
    p.add_argument("--no-events", action="store_true", help="Skip event generation")
    p.add_argument("--no-commands", action="store_true", help="Skip command generation")
    p.add_argument("--no-queries", action="store_true", help="Skip query generation")


def _add_new_plugin(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("plugin", help="Scaffold a new plugin")
    p.add_argument("name", help="Plugin name")
    p.add_argument("--description", default="", help="Plugin description")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--hooks", nargs="*", default=["on_startup", "on_shutdown"], help="Plugin hooks")


def _add_new_platform(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("platform", help="Scaffold a new platform")
    p.add_argument("name", help="Platform name")
    p.add_argument("--description", default="", help="Platform description")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--modules", nargs="*", default=[], help="Initial modules to create")


def _add_new_capability(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("capability", help="Scaffold a new capability")
    p.add_argument("name", help="Capability name")
    p.add_argument("--description", default="", help="Capability description")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--domain", default="clinical", help="Domain")
    p.add_argument("--commands", nargs="*", default=[], help="Commands")
    p.add_argument("--events", nargs="*", default=[], help="Events")
    p.add_argument("--queries", nargs="*", default=[], help="Queries")


def _add_new_crud(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("crud", help="Scaffold CRUD for an entity")
    p.add_argument("name", help="Entity name (PascalCase)")
    p.add_argument("--fields", nargs="+", default=[], help="Fields in format name:type")
    p.add_argument("--dir", default=".", help="Target directory")


def _add_generate_microservice(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("microservice", help="Generate a microservice")
    p.add_argument("name", help="Service name")
    p.add_argument("--port", type=int, default=8000, help="Service port")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--description", default="", help="Service description")


def _add_generate_crud(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("crud", help="Generate CRUD for an entity")
    p.add_argument("name", help="Entity name (PascalCase)")
    p.add_argument("--fields", nargs="+", default=[], help="Fields in format name:type")
    p.add_argument("--dir", default=".", help="Target directory")


def _add_generate_rest(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("rest", help="Generate REST API endpoints")
    p.add_argument("name", help="Resource name")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--prefix", default="", help="URL prefix")
    p.add_argument("--operations", nargs="*", default=["list", "get", "create", "update", "delete"],
                   choices=["list", "get", "create", "update", "delete"], help="Operations to include")


def _add_generate_openapi(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("openapi", help="Generate OpenAPI spec")
    p.add_argument("title", help="API title")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--version", default="0.1.0", help="API version")
    p.add_argument("--description", default="", help="API description")


def _add_generate_dto(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("dto", help="Generate DTOs")
    p.add_argument("name", help="Entity name")
    p.add_argument("--fields", nargs="+", default=[], help="Fields in format name:type")
    p.add_argument("--dir", default=".", help="Target directory")


def _add_generate_repository(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("repository", help="Generate repository")
    p.add_argument("name", help="Entity name")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--methods", nargs="*", default=["get", "list", "create", "update", "delete", "count"],
                   choices=["get", "list", "create", "update", "delete", "count"], help="Repository methods")


def _add_generate_cqrs(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("cqrs", help="Generate CQRS pattern")
    p.add_argument("name", help="Module name")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--commands", nargs="*", default=["create", "update", "delete"], help="Commands")
    p.add_argument("--queries", nargs="*", default=["get", "list"], help="Queries")


def _add_generate_tests(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("tests", help="Generate tests")
    p.add_argument("module", help="Module name")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--types", nargs="*", default=["unit"],
                   choices=["unit", "integration", "performance", "security"], help="Test types")
    p.add_argument("--entities", nargs="*", default=[], help="Entities for fixtures/factories")


def _add_generate_adr(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("adr", help="Generate ADR")
    p.add_argument("title", help="ADR title")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--status", default="proposed", choices=["proposed", "accepted", "deprecated", "superseded"],
                   help="ADR status")
    p.add_argument("--context", default="", help="Context")
    p.add_argument("--decision", default="", help="Decision")


def _add_generate_architecture(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("architecture", help="Generate architecture docs")
    p.add_argument("name", help="System name")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--description", default="", help="System description")


def _add_generate_diagram(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("diagram", help="Generate diagram")
    p.add_argument("title", help="Diagram title")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--type", default="flowchart", choices=["flowchart", "sequence", "class", "c4", "plantuml"],
                   help="Diagram type")


def _add_generate_ci(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("ci", help="Generate CI pipeline")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--name", default="CI", help="Pipeline name")
    p.add_argument("--python", default="3.11", help="Python version")
    p.add_argument("--registry", default="", help="Docker registry")


def _add_generate_docker(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("docker", help="Generate Dockerfile")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--name", default="app", help="App name")
    p.add_argument("--python", default="3.11-slim", help="Python version")
    p.add_argument("--port", type=int, default=8000, help="Exposed port")
    p.add_argument("--entrypoint", default="uvicorn app.main:app --host 0.0.0.0 --port {port}",
                   help="Container entrypoint")
    p.add_argument("--multi-stage", action="store_true", help="Use multi-stage build")


def _add_generate_compose(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("compose", help="Generate docker-compose.yml")
    p.add_argument("--dir", default=".", help="Target directory")


def _add_generate_kubernetes(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("kubernetes", help="Generate K8s manifests")
    p.add_argument("name", help="App name")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument("--image", default="app:latest", help="Container image")
    p.add_argument("--replicas", type=int, default=3, help="Replica count")
    p.add_argument("--port", type=int, default=8000, help="Container port")
    p.add_argument("--namespace", default="default", help="K8s namespace")
    p.add_argument("--postgres", action="store_true", help="Include Postgres")
    p.add_argument("--redis", action="store_true", help="Include Redis")


def _handle_new(args: argparse.Namespace) -> None:
    target = Path(args.dir).resolve()

    if args.new_type == "project":
        spec = ProjectSpec(name=args.name, description=args.description, version=getattr(args, 'version', '0.1.0'))
        gen = ProjectGenerator(target_dir=target)
        result = gen.generate(spec=spec)
        _print_result("Project", result)

    elif args.new_type == "module":
        spec = ModuleSpec(
            name=args.name,
            description=args.description,
            has_entity=not args.no_entity,
            has_events=not args.no_events,
            has_commands=not args.no_commands,
            has_queries=not args.no_queries,
        )
        gen = ModuleGenerator(target_dir=target)
        result = gen.generate(spec=spec)
        _print_result("Module", result)

    elif args.new_type == "plugin":
        spec = PluginSpec(name=args.name, description=args.description, hooks=args.hooks)
        gen = PluginGenerator(target_dir=target)
        result = gen.generate(spec=spec)
        _print_result("Plugin", result)

    elif args.new_type == "platform":
        gen = ProjectGenerator(target_dir=target)
        result = gen.generate(spec=ProjectSpec(name=args.name, description=args.description))
        for mod_name in args.modules:
            mg = ModuleGenerator(target_dir=target / args.name)
            mg.generate(spec=ModuleSpec(name=mod_name))
        _print_result("Platform", result)

    elif args.new_type == "capability":
        spec = CapabilitySpec(
            name=args.name,
            description=args.description,
            domain=args.domain,
            commands=args.commands,
            events=args.events,
            queries=args.queries,
        )
        gen = CapabilityGenerator(target_dir=target)
        result = gen.generate(spec=spec)
        _print_result("Capability", result)

    elif args.new_type == "crud":
        _do_generate_crud(args, target)


def _handle_generate(args: argparse.Namespace) -> None:
    target = Path(args.dir).resolve()

    gen_map = {
        "microservice": lambda: _do_generate_microservice(args, target),
        "crud": lambda: _do_generate_crud(args, target),
        "rest": lambda: _do_generate_rest(args, target),
        "openapi": lambda: _do_generate_openapi(args, target),
        "dto": lambda: _do_generate_dto(args, target),
        "repository": lambda: _do_generate_repository(args, target),
        "cqrs": lambda: _do_generate_cqrs(args, target),
        "tests": lambda: _do_generate_tests(args, target),
        "adr": lambda: _do_generate_adr(args, target),
        "architecture": lambda: _do_generate_architecture(args, target),
        "diagram": lambda: _do_generate_diagram(args, target),
        "ci": lambda: _do_generate_ci(args, target),
        "docker": lambda: _do_generate_docker(args, target),
        "compose": lambda: _do_generate_compose(target),
        "kubernetes": lambda: _do_generate_kubernetes(args, target),
    }

    handler = gen_map.get(args.generator)
    if handler:
        handler()
    else:
        print(f"Unknown generator: {args.generator}")


def _do_generate_microservice(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.generators.microservice import MicroserviceGenerator, MicroserviceSpec
    spec = MicroserviceSpec(name=args.name, description=args.description, port=args.port)
    gen = MicroserviceGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("Microservice", result)


def _do_generate_crud(args: argparse.Namespace, target: Path) -> None:
    fields = []
    if hasattr(args, 'fields') and args.fields:
        for f in args.fields:
            if ":" in f:
                name, typ = f.split(":", 1)
                indexed = ":indexed" in args.fields
                unique = ":unique" in args.fields
                fields.append(EntityField(name=name, type=typ, indexed=indexed, unique=unique))
            else:
                fields.append(EntityField(name=f, type="str"))
    spec = EntitySpec(name=args.name, fields=fields)
    gen = CRUDGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("CRUD", result)


def _do_generate_rest(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.rest.generator import RESTGenerator, RESTSpec
    spec = RESTSpec(name=args.name, prefix=args.prefix, operations=args.operations)
    gen = RESTGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("REST", result)


def _do_generate_openapi(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.openapi.generator import OpenAPIGenerator, OpenAPISpec
    spec = OpenAPISpec(title=args.title, version=args.version, description=args.description)
    gen = OpenAPIGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("OpenAPI", result)


def _do_generate_dto(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.dto.generator import DTOGenerator, DTOSpec, DTOField
    fields = []
    if hasattr(args, 'fields') and args.fields:
        for f in args.fields:
            if ":" in f:
                name, typ = f.split(":", 1)
                fields.append(DTOField(name=name, type=typ))
            else:
                fields.append(DTOField(name=f, type="str"))
    spec = DTOSpec(name=args.name, fields=fields)
    gen = DTOGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("DTO", result)


def _do_generate_repository(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.repository.generator import RepositoryGenerator, RepositorySpec
    spec = RepositorySpec(name=args.name, methods=args.methods)
    gen = RepositoryGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("Repository", result)


def _do_generate_cqrs(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.cqrs.generator import CQRSGenerator, CQRSSpec
    spec = CQRSSpec(name=args.name, commands=args.commands, queries=args.queries)
    gen = CQRSGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("CQRS", result)


def _do_generate_tests(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.testing.unit import UnitTestGenerator, IntegrationTestGenerator
    from backend.app.engineering.testing.performance import PerformanceTestGenerator, SecurityTestGenerator
    from backend.app.engineering.testing.fixtures import FixturesGenerator
    from backend.app.engineering.testing.factories import FactoriesGenerator

    entities = args.entities or [args.module.title()]

    for t in args.types:
        if t == "unit":
            gen = UnitTestGenerator(target_dir=target)
            result = gen.generate(module_path=args.module)
            _print_result("Unit Tests", result)
        elif t == "integration":
            gen = IntegrationTestGenerator(target_dir=target)
            result = gen.generate(module_path=args.module, entity=entities[0])
            _print_result("Integration Tests", result)
        elif t == "performance":
            gen = PerformanceTestGenerator(target_dir=target)
            result = gen.generate(module=args.module)
            _print_result("Performance Tests", result)
        elif t == "security":
            gen = SecurityTestGenerator(target_dir=target)
            result = gen.generate(module=args.module)
            _print_result("Security Tests", result)

    fg = FixturesGenerator(target_dir=target)
    fg.generate(module=args.module, entities=entities)

    fc = FactoriesGenerator(target_dir=target)
    fc.generate(module=args.module, entities=entities)

    print(f"  Generated fixtures and factories for: {', '.join(entities)}")


def _do_generate_adr(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.docs.adr import ADRGenerator, ADRSpec
    spec = ADRSpec(
        title=args.title,
        status=args.status,
        context=args.context,
        decision=args.decision,
    )
    gen = ADRGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("ADR", result)


def _do_generate_architecture(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.docs.adr import ArchitectureGenerator
    gen = ArchitectureGenerator(target_dir=target)
    result = gen.generate(name=args.name, description=args.description)
    _print_result("Architecture Docs", result)


def _do_generate_diagram(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.docs.mermaid import MermaidGenerator, PlantUMLGenerator
    if args.type == "plantuml":
        gen = PlantUMLGenerator(target_dir=target)
    else:
        gen = MermaidGenerator(target_dir=target)
    result = gen.generate(type=args.type, title=args.title)
    _print_result("Diagram", result)


def _do_generate_ci(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.deployment.github_actions import GitHubActionsGenerator, GitHubActionsSpec
    spec = GitHubActionsSpec(
        name=args.name,
        python_version=args.python,
        docker_registry=args.registry,
    )
    gen = GitHubActionsGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("CI Pipeline", result)


def _do_generate_docker(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.deployment.github_actions import DockerGenerator
    gen = DockerGenerator(target_dir=target)
    result = gen.generate(
        name=args.name,
        python_version=args.python,
        port=args.port,
        entrypoint=args.entrypoint,
        multi_stage=args.multi_stage,
    )
    _print_result("Dockerfile", result)


def _do_generate_compose(target: Path) -> None:
    from backend.app.engineering.deployment.github_actions import ComposeGenerator
    gen = ComposeGenerator(target_dir=target)
    result = gen.generate()
    _print_result("Docker Compose", result)


def _do_generate_kubernetes(args: argparse.Namespace, target: Path) -> None:
    from backend.app.engineering.deployment.github_actions import KubernetesGenerator
    gen = KubernetesGenerator(target_dir=target)
    result = gen.generate(
        name=args.name,
        image=args.image,
        replicas=args.replicas,
        port=args.port,
        namespace=args.namespace,
        postgres=args.postgres,
        redis=args.redis,
    )
    _print_result("Kubernetes", result)


def _handle_validate(args: argparse.Namespace) -> None:
    root = Path(args.dir).resolve()

    if args.type == "clean-arch":
        validator = CleanArchitectureValidator(project_root=root)
        issues = validator.validate()
        if not issues:
            print("  ✓ No Clean Architecture violations found.")
        else:
            for issue in issues:
                print(f"  [{issue.severity}] {issue.file}:{issue.line} — {issue.message}")
            print(f"\n  Found {len(issues)} violations.")

    elif args.type == "solid":
        validator = SOLIDValidator(project_root=root)
        issues = validator.validate()
        if not issues:
            print("  ✓ No SOLID principle violations found.")
        else:
            for issue in issues:
                print(f"  [{issue.severity}] {issue.file}:{issue.line} [{issue.principle}] {issue.message}")
            print(f"\n  Found {len(issues)} issues.")

    elif args.type == "ddd":
        _validate_ddd(root)

    elif args.type == "cqrs":
        _validate_cqrs(root)

    elif args.type == "event-driven":
        _validate_event_driven(root)


def _validate_ddd(root: Path) -> None:
    issues = []
    for py_file in root.rglob("*.py"):
        if "test" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        content = py_file.read_text()
        if "class" in content:
            if "domain" in py_file.parts and "entity" not in py_file.parts and "value_object" not in py_file.parts and "event" not in py_file.parts:
                issues.append(f"{py_file.relative_to(root)}: Domain file in unexpected location")

    if not issues:
        print("  ✓ DDD structure validation passed.")
    else:
        for i in issues:
            print(f"  [warning] {i}")
        print(f"\n  Found {len(issues)} DDD issues.")


def _validate_cqrs(root: Path) -> None:
    issues = []
    for py_file in root.rglob("*.py"):
        if "test" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        content = py_file.read_text()
        if "class" in content and "Repository" in content and "Command" in content:
            if "command" not in py_file.parts:
                issues.append(f"{py_file.relative_to(root)}: Repository found outside commands context")

    if not issues:
        print("  ✓ CQRS structure validation passed.")
    else:
        for i in issues:
            print(f"  [info] {i}")


def _validate_event_driven(root: Path) -> None:
    event_files = list(root.rglob("**/events/**/*.py"))
    handlers = list(root.rglob("**/handlers/**/*.py"))

    if not event_files and not handlers:
        print("  ℹ No event-driven patterns detected.")

    for ef in event_files:
        content = ef.read_text()
        if "class" not in content or "Event" not in content:
            print(f"  [info] {ef.relative_to(root)}: Event file may not define events")

    print(f"  ✓ Found {len(event_files)} event files, {len(handlers)} handler files.")


def _handle_quality(args: argparse.Namespace) -> None:
    gates = QualityGates(project_root=args.dir)

    gate_map = {
        "ruff": gates.run_ruff,
        "pytest": gates.run_pytest,
        "mypy": gates.run_mypy,
        "coverage": lambda: gates.run_coverage(min_pct=args.coverage_min),
        "bandit": gates.run_bandit,
    }

    for gate_name in args.gates:
        func = gate_map.get(gate_name)
        if func:
            result = func()
            status_icon = "✓" if result.passed else "✗"
            print(f"  {status_icon} {result.name}: {result.status} ({result.duration_ms:.0f}ms)")

    all_passed = all(gate_map[g]().passed for g in args.gates if g in gate_map)
    sys.exit(0 if all_passed else 1)


def _handle_doctor(args: argparse.Namespace) -> None:
    root = Path(args.dir).resolve()
    print("GULA Doctor — System Diagnostics")
    print(f"  Project root: {root}")
    print(f"  Python: {sys.version.split()[0]}")

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        print("  Config: pyproject.toml found")
    else:
        print("  Config: pyproject.toml not found")

    test_dir = root / "tests"
    print(f"  Tests: {'Found' if test_dir.exists() else 'Not found'}")

    docker = root / "Dockerfile"
    print(f"  Docker: {'Found' if docker.exists() else 'Not found'}")

    compose = root / "docker-compose.yml"
    print(f"  Compose: {'Found' if compose.exists() else 'Not found'}")

    github = root / ".github/workflows"
    print(f"  CI: {'Found' if github.exists() else 'Not found'}")

    import importlib
    checks = ["ruff", "pytest", "mypy", "coverage", "bandit"]
    for check in checks:
        try:
            importlib.import_module(check)
            print(f"  {check}: ✓ installed")
        except ImportError:
            print(f"  {check}: ✗ not installed")

    print("  Doctor check complete.")


def _handle_info() -> None:
    print("GULA Engineering Automation Platform")
    print("  Version: 2.1.0")
    print("  From now on, GULA builds GULA.")
    print()
    print("  Commands:")
    print("    gula new <type>      Scaffold projects, modules, plugins, platforms")
    print("    gula generate <type> Generate code, tests, docs, CI/CD")
    print("    gula validate <type> Validate architecture quality")
    print("    gula quality         Run quality gates")
    print("    gula doctor          System diagnostics")
    print("    gula info            Show this info")


def _print_result(name: str, result: object) -> None:
    files = getattr(result, 'files_created', [])
    skipped = getattr(result, 'files_skipped', [])
    errors = getattr(result, 'errors', [])
    print(f"  {name}: {len(files)} files created")
    if skipped:
        print(f"  {len(skipped)} files skipped (already exist)")
    if errors:
        for e in errors:
            print(f"  Error: {e}")


if __name__ == "__main__":
    main()
