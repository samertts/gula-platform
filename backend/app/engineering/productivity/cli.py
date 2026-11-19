from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.engineering.ci.quality_gates import QualityGates
from app.engineering.crud.generator import CRUDGenerator, EntityField, EntitySpec
from app.engineering.generators.capability import (
    CapabilityGenerator,
    CapabilitySpec,
)
from app.engineering.generators.microservice import MicroserviceGenerator, MicroserviceSpec
from app.engineering.generators.module import ModuleGenerator, ModuleSpec
from app.engineering.generators.plugin import PluginGenerator, PluginSpec
from app.engineering.generators.project import ProjectGenerator, ProjectSpec
from app.engineering.validation.clean_arch import CleanArchitectureValidator
from app.engineering.validation.solid import SOLIDValidator

PACKAGE = "app.engineering"


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

    # gula capability
    cap_cmd = sub.add_parser("capability", help="Manage capabilities in the registry")
    cap_sub = cap_cmd.add_subparsers(dest="cap_action")

    cap_list = cap_sub.add_parser("list", help="List all capabilities")
    cap_list.add_argument("--domain", default="", help="Filter by domain")
    cap_list.add_argument("--status", default="", help="Filter by status (active, draft, deprecated, retired)")
    cap_list.add_argument("--enabled-only", action="store_true", help="Show only enabled capabilities")

    cap_show = cap_sub.add_parser("show", help="Show capability details")
    cap_show.add_argument("name", help="Capability name")

    cap_enable = cap_sub.add_parser("enable", help="Enable a capability")
    cap_enable.add_argument("name", help="Capability name")

    cap_disable = cap_sub.add_parser("disable", help="Disable a capability")
    cap_disable.add_argument("name", help="Capability name")

    cap_impact = cap_sub.add_parser("impact", help="Show impact analysis for capability changes")
    cap_impact.add_argument("name", help="Capability name")

    cap_graph = cap_sub.add_parser("graph", help="Show dependency graph")
    cap_graph.add_argument("--format", default="text", choices=["text", "mermaid", "json"], help="Output format")

    cap_sub.add_parser("summary", help="Show capability registry summary")

    # gula info
    sub.add_parser("info", help="Show platform info")

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
    elif args.command == "capability":
        _handle_capability(args)
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
    p.add_argument("--domain", default="core", help="Domain (core, clinical, identity, financial, communication, infrastructure, observability, reporting, integration, platform)")
    p.add_argument("--layer", default="application", help="Layer (domain, application, infrastructure, presentation)")
    p.add_argument("--owner", default="platform-team", help="Capability owner")
    p.add_argument("--version", default="1.0.0", help="Initial semver")
    p.add_argument("--entities", nargs="*", default=[], help="Entities in format Name:type")
    p.add_argument("--commands", nargs="*", default=[], help="Commands")
    p.add_argument("--events", nargs="*", default=[], help="Events")
    p.add_argument("--queries", nargs="*", default=[], help="Queries")
    p.add_argument("--policies", nargs="*", default=[], help="Policy names")
    p.add_argument("--permissions", nargs="*", default=[], help="Permission names")
    p.add_argument("--dependencies", nargs="*", default=[], help="Dependency capability names")
    p.add_argument("--tags", nargs="*", default=[], help="Tags")
    p.add_argument("--no-api", action="store_true", help="Skip API routes")
    p.add_argument("--no-tests", action="store_true", help="Skip tests")
    p.add_argument("--no-adr", action="store_true", help="Skip ADR")
    p.add_argument("--no-docs", action="store_true", help="Skip docs")
    p.add_argument("--no-sbom", action="store_true", help="Skip SBOM")


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
    p.add_argument(
        "--operations",
        nargs="*",
        default=["list", "get", "create", "update", "delete"],
        choices=["list", "get", "create", "update", "delete"],
        help="Operations to include",
    )


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
    p.add_argument(
        "--methods",
        nargs="*",
        default=["get", "list", "create", "update", "delete", "count"],
        choices=["get", "list", "create", "update", "delete", "count"],
        help="Repository methods",
    )


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
    p.add_argument(
        "--types",
        nargs="*",
        default=["unit"],
        choices=["unit", "integration", "performance", "security"],
        help="Test types",
    )
    p.add_argument("--entities", nargs="*", default=[], help="Entities for fixtures/factories")


def _add_generate_adr(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("adr", help="Generate ADR")
    p.add_argument("title", help="ADR title")
    p.add_argument("--dir", default=".", help="Target directory")
    p.add_argument(
        "--status",
        default="proposed",
        choices=["proposed", "accepted", "deprecated", "superseded"],
        help="ADR status",
    )
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
    p.add_argument(
        "--type",
        default="flowchart",
        choices=["flowchart", "sequence", "class", "c4", "plantuml"],
        help="Diagram type",
    )


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
    p.add_argument(
        "--entrypoint",
        default="uvicorn app.main:app --host 0.0.0.0 --port {port}",
        help="Container entrypoint",
    )
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
        spec = ProjectSpec(
            name=args.name, description=args.description, version=getattr(args, "version", "0.1.0"),
        )
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
        entities = []
        for e in args.entities:
            if ":" in e:
                name, typ = e.split(":", 1)
                entities.append(EntityField(name=name, type=typ))
            else:
                entities.append(EntityField(name=e, type="str"))
        spec = CapabilitySpec(
            name=args.name,
            description=args.description,
            domain=args.domain,
            layer=args.layer,
            owner=args.owner,
            version=args.version,
            entities=entities or None,
            commands=args.commands,
            events=args.events,
            queries=args.queries,
            policies=args.policies,
            permissions=args.permissions,
            dependencies=args.dependencies,
            tags=args.tags,
            with_api=not args.no_api,
            with_tests=not args.no_tests,
            with_adr=not args.no_adr,
            with_docs=not args.no_docs,
            with_sbom=not args.no_sbom,
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
    spec = MicroserviceSpec(name=args.name, description=args.description, port=args.port)
    gen = MicroserviceGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("Microservice", result)


def _do_generate_crud(args: argparse.Namespace, target: Path) -> None:
    fields = []
    if hasattr(args, "fields") and args.fields:
        for f in args.fields:
            if ":" in f:
                name, typ = f.split(":", 1)
                indexed = ":indexed" in f
                unique = ":unique" in f
                fields.append(EntityField(name=name, type=typ, indexed=indexed, unique=unique))
            else:
                fields.append(EntityField(name=f, type="str"))
    spec = EntitySpec(name=args.name, fields=fields)
    gen = CRUDGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("CRUD", result)


def _do_generate_rest(args: argparse.Namespace, target: Path) -> None:
    from app.engineering.rest.generator import RESTGenerator, RESTSpec

    spec = RESTSpec(name=args.name, prefix=args.prefix, operations=args.operations)
    gen = RESTGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("REST", result)


def _do_generate_openapi(args: argparse.Namespace, target: Path) -> None:
    from app.engineering.openapi.generator import OpenAPIGenerator, OpenAPISpec

    spec = OpenAPISpec(title=args.title, version=args.version, description=args.description)
    gen = OpenAPIGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("OpenAPI", result)


def _do_generate_dto(args: argparse.Namespace, target: Path) -> None:
    from app.engineering.dto.generator import DTOField, DTOGenerator, DTOSpec

    fields = []
    if hasattr(args, "fields") and args.fields:
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
    from app.engineering.repository.generator import RepositoryGenerator, RepositorySpec

    spec = RepositorySpec(name=args.name, methods=args.methods)
    gen = RepositoryGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("Repository", result)


def _do_generate_cqrs(args: argparse.Namespace, target: Path) -> None:
    from app.engineering.cqrs.generator import CQRSGenerator, CQRSSpec

    spec = CQRSSpec(name=args.name, commands=args.commands, queries=args.queries)
    gen = CQRSGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("CQRS", result)


def _do_generate_tests(args: argparse.Namespace, target: Path) -> None:
    from app.engineering.testing.factories import FactoriesGenerator
    from app.engineering.testing.fixtures import FixturesGenerator
    from app.engineering.testing.performance import (
        PerformanceTestGenerator,
        SecurityTestGenerator,
    )
    from app.engineering.testing.unit import IntegrationTestGenerator, UnitTestGenerator

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
    from app.engineering.docs.adr import ADRGenerator, ADRSpec

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
    from app.engineering.docs.adr import ArchitectureGenerator

    gen = ArchitectureGenerator(target_dir=target)
    result = gen.generate(name=args.name, description=args.description)
    _print_result("Architecture Docs", result)


def _do_generate_diagram(args: argparse.Namespace, target: Path) -> None:
    from app.engineering.docs.mermaid import MermaidGenerator, PlantUMLGenerator

    if args.type == "plantuml":
        gen = PlantUMLGenerator(target_dir=target)
    else:
        gen = MermaidGenerator(target_dir=target)
    result = gen.generate(type=args.type, title=args.title)
    _print_result("Diagram", result)


def _do_generate_ci(args: argparse.Namespace, target: Path) -> None:
    from app.engineering.deployment.github_actions import (
        GitHubActionsGenerator,
        GitHubActionsSpec,
    )

    spec = GitHubActionsSpec(
        name=args.name,
        python_version=args.python,
        docker_registry=args.registry,
    )
    gen = GitHubActionsGenerator(target_dir=target)
    result = gen.generate(spec=spec)
    _print_result("CI Pipeline", result)


def _do_generate_docker(args: argparse.Namespace, target: Path) -> None:
    from app.engineering.deployment.github_actions import DockerGenerator

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
    from app.engineering.deployment.github_actions import ComposeGenerator

    gen = ComposeGenerator(target_dir=target)
    result = gen.generate()
    _print_result("Docker Compose", result)


def _do_generate_kubernetes(args: argparse.Namespace, target: Path) -> None:
    from app.engineering.deployment.github_actions import KubernetesGenerator

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
                print(
                    f"  [{issue.severity}] {issue.file}:{issue.line} [{issue.principle}] {issue.message}",
                )
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
        if "class" in content and (
            "domain" in py_file.parts
            and "entity" not in py_file.parts
            and "value_object" not in py_file.parts
            and "event" not in py_file.parts
        ):
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
                issues.append(
                    f"{py_file.relative_to(root)}: Repository found outside commands context",
                )

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


def _handle_capability(args: argparse.Namespace) -> None:
    from app.kernel.capabilities_registry_populator import _get_all_descriptors
    from app.kernel.types import CapabilityStatus

    all_caps = _get_all_descriptors()

    if args.cap_action == "list":
        filtered = all_caps
        if args.domain:
            filtered = [c for c in filtered if c.domain == args.domain]
        if args.status:
            filtered = [c for c in filtered if c.status.value == args.status]
        if args.enabled_only:
            filtered = [c for c in filtered if c.enabled]

        domain_order = ["identity_security", "clinical", "communication", "infrastructure",
                         "reporting", "platform", "financial", "observability", "integration"]
        filtered.sort(key=lambda c: (domain_order.index(c.domain) if c.domain in domain_order else 99, c.name))

        print(f"\n  Capability Registry — {len(filtered)} capabilities")
        print(f"  {'=' * 70}")
        if not filtered:
            print("  No capabilities match the filter.")
        for cap in filtered:
            status_icon = {"active": "🟢", "draft": "🟡", "deprecated": "🟠", "retired": "🔴"}
            icon = status_icon.get(cap.status.value, "⚪")
            deps_str = f" → depends on: {', '.join(cap.dependencies)}" if cap.dependencies else ""
            print(f"  {icon} {cap.name:30s} v{cap.version:8s} [{cap.domain:20s}]{deps_str}")
        print()

    elif args.cap_action == "show":
        cap = next((c for c in all_caps if c.name == args.name), None)
        if not cap:
            print(f"  Capability '{args.name}' not found.")
            return
        print(f"\n  Capability: {cap.name}")
        print(f"  {'=' * 50}")
        print(f"  Version:      {cap.version}")
        print(f"  Domain:       {cap.domain}")
        print(f"  Layer:        {cap.layer}")
        print(f"  Owner:        {cap.owner}")
        print(f"  Status:       {cap.status.value}")
        print(f"  Enabled:      {cap.enabled}")
        print(f"  Description:  {cap.description}")
        if cap.dependencies:
            print(f"  Dependencies: {', '.join(cap.dependencies)}")
        if cap.permissions:
            print(f"  Permissions:  {', '.join(cap.permissions)}")
        if cap.api_endpoints:
            print("  API Endpoints:")
            for ep in cap.api_endpoints:
                print(f"    {ep.method:7s} {ep.path}")
        print()

    elif args.cap_action == "enable":
        cap = next((c for c in all_caps if c.name == args.name), None)
        if not cap:
            print(f"  Capability '{args.name}' not found.")
            return
        cap.enabled = True
        print(f"  ✅ Capability '{args.name}' enabled.")

    elif args.cap_action == "disable":
        cap = next((c for c in all_caps if c.name == args.name), None)
        if not cap:
            print(f"  Capability '{args.name}' not found.")
            return
        cap.enabled = False
        print(f"  ✅ Capability '{args.name}' disabled.")

    elif args.cap_action == "impact":
        cap = next((c for c in all_caps if c.name == args.name), None)
        if not cap:
            print(f"  Capability '{args.name}' not found.")
            return
        direct = [c.name for c in all_caps if args.name in c.dependencies]
        transitive = set()
        queue = list(direct)
        while queue:
            current = queue.pop(0)
            for c in all_caps:
                if current in c.dependencies and c.name != args.name:
                    if c.name not in transitive and c.name not in direct:
                        transitive.add(c.name)
                        queue.append(c.name)
        print(f"\n  Impact Analysis: {args.name}")
        print(f"  {'=' * 50}")
        print(f"  Direct dependents ({len(direct)}):")
        for d in direct or ["(none)"]:
            print(f"    - {d}")
        print(f"  Transitive dependents ({len(transitive)}):")
        for t in transitive or ["(none)"]:
            print(f"    - {t}")
        unresolved = [d for d in cap.dependencies if d not in [c.name for c in all_caps]]
        if unresolved:
            print(f"  ⚠️  Unresolved dependencies: {', '.join(unresolved)}")
        print()

    elif args.cap_action == "graph":
        if args.format == "mermaid":
            domains = {}
            for cap in all_caps:
                domains.setdefault(cap.domain, []).append(cap)
            print("```mermaid")
            print("graph TD")
            for domain, caps in domains.items():
                print(f"    subgraph {domain}")
                for cap in caps:
                    safe_name = cap.name.replace("_", "_").replace("-", "_")
                    print(f"        {safe_name}[{cap.name}]")
                print("    end")
            for cap in all_caps:
                for dep in cap.dependencies:
                    safe_cap = cap.name.replace("_", "_").replace("-", "_")
                    safe_dep = dep.replace("_", "_").replace("-", "_")
                    print(f"    {safe_cap} --> {safe_dep}")
            print("```")
        elif args.format == "json":
            import json
            graph = {}
            for cap in all_caps:
                graph[cap.name] = {"dependencies": cap.dependencies, "domain": cap.domain}
            print(json.dumps(graph, indent=2))
        else:
            print(f"\n  Capability Dependency Graph ({len(all_caps)} capabilities)")
            print(f"  {'=' * 70}")
            for cap in all_caps:
                deps_str = f" → {', '.join(cap.dependencies)}" if cap.dependencies else ""
                print(f"    {cap.name:30s} [{cap.domain:20s}]{deps_str}")
            print()

    elif args.cap_action == "summary":
        domains = {}
        statuses = {}
        total_deps = 0
        enabled_count = 0
        for cap in all_caps:
            domains[cap.domain] = domains.get(cap.domain, 0) + 1
            statuses[cap.status.value] = statuses.get(cap.status.value, 0) + 1
            total_deps += len(cap.dependencies)
            if cap.enabled:
                enabled_count += 1
        print("\n  Capability Registry Summary")
        print(f"  {'=' * 50}")
        print(f"  Total:                {len(all_caps)}")
        print(f"  Enabled:              {enabled_count}")
        print(f"  Total Dependencies:   {total_deps}")
        print("  Domains:")
        for domain, count in sorted(domains.items(), key=lambda x: -x[1]):
            print(f"    {domain:25s} {count}")
        print("  Statuses:")
        for status, count in sorted(statuses.items(), key=lambda x: -x[1]):
            print(f"    {status:25s} {count}")
        draft = [c.name for c in all_caps if c.status == CapabilityStatus.DRAFT]
        if draft:
            print(f"  Draft Capabilities:   {', '.join(draft)}")
        print()


def _handle_info() -> None:
    print("GULA Engineering Automation Platform")
    print("  Version: 2.1.0")
    print("  From now on, GULA builds GULA.")
    print()
    print("  Commands:")
    print("    gula new <type>       Scaffold projects, modules, plugins, platforms, capabilities, CRUD")
    print("    gula generate <type>  Generate code, tests, docs, CI/CD")
    print("    gula validate <type>  Validate architecture quality (clean-arch, solid, ddd, cqrs, event-driven)")
    print("    gula quality          Run quality gates (ruff, pytest, mypy, coverage, bandit)")
    print("    gula doctor           System diagnostics")
    print("    gula capability       Manage capabilities (list, show, enable, disable, impact, graph, summary)")
    print("    gula info             Show this info")


def _print_result(name: str, result: object) -> None:
    files = getattr(result, "files_created", [])
    skipped = getattr(result, "files_skipped", [])
    errors = getattr(result, "errors", [])
    print(f"  {name}: {len(files)} files created")
    if skipped:
        print(f"  {len(skipped)} files skipped (already exist)")
    if errors:
        for e in errors:
            print(f"  Error: {e}")


if __name__ == "__main__":
    main()
