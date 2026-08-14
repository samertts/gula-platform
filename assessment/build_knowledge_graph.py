"""Repository Brain — Knowledge Graph Builder.
Generates JSON knowledge graph, Mermaid diagrams, and cross-references.
"""
import json, os, re, ast, hashlib
from pathlib import Path
from collections import defaultdict

REPO = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".mypy_cache",
             ".ruff_cache", ".pytest_cache", "__pycache__", "archive"}

class KnowledgeGraph:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.node_ids = {}
        self.node_by_path = {}
        self.module_imports = defaultdict(set)
        self.api_entities = defaultdict(set)
        self.db_entities = set()
        self.events = set()
        self.plugins = set()
        self.services = set()
        self.routes = set()
        self.models = set()

    def _node_id(self, name, kind):
        key = f"{kind}:{name}"
        if key not in self.node_ids:
            nid = f"n{len(self.nodes)}"
            self.node_ids[key] = nid
            self.nodes.append({"id": nid, "name": name, "kind": kind, "meta": {}})
        return self.node_ids[key]

    def add_edge(self, src, dst, kind, label=""):
        if isinstance(src, str): src = self._node_id(src, "module")
        if isinstance(dst, str): dst = self._node_id(dst, "module")
        self.edges.append({"source": src, "target": dst, "kind": kind, "label": label})

    def _scan_python_file(self, path):
        rel = path.relative_to(REPO)
        module_name = str(rel).replace("/", ".").replace(".py", "")
        code = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return
        mod_id = self._node_id(module_name, "module")
        self.node_by_path[str(rel)] = mod_id
        # imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.module_imports[module_name].add(alias.name.split(".")[0])
                    self.add_edge(module_name, alias.name.split(".")[0], "imports")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    self.module_imports[module_name].add(top)
                    self.add_edge(module_name, top, "imports")
            elif isinstance(node, ast.ClassDef):
                bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                self._node_id(f"{module_name}.{node.name}", "class")
                self.add_edge(module_name, f"{module_name}.{node.name}", "contains")
                for b in bases:
                    self._node_id(b, "class")
                    self.add_edge(f"{module_name}.{node.name}", b, "extends")
            elif isinstance(node, ast.FunctionDef):
                self._node_id(f"{module_name}.{node.name}", "function")
                self.add_edge(module_name, f"{module_name}.{node.name}", "contains")
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and (isinstance(node.value, ast.Call)):
                        c = node.value
                        if isinstance(c.func, ast.Attribute) and c.func.attr in ("get", "post", "put", "delete", "patch"):
                            # FastAPI route decorator
                            for arg in c.args:
                                if isinstance(arg, ast.Constant):
                                    self.routes.add((module_name, c.func.attr.upper(), arg.value))
                            continue
                        if isinstance(c.func, ast.Name) and c.func.id == "FastAPI":
                            continue  # app instance
                    # Detect SQLAlchemy model classes
                    if isinstance(t, ast.Name) and isinstance(node.value, ast.Call):
                        c = node.value
                        if isinstance(c.func, ast.Name) and c.func.id == "Table":
                            self.db_entities.add(t.id)

    def _scan_routes(self):
        routes_dir = REPO / "backend" / "app" / "routes"
        if not routes_dir.exists():
            return
        for f in sorted(routes_dir.glob("*.py")):
            code = f.read_text(encoding="utf-8", errors="replace")
            router_name = f.stem
            for match in re.finditer(r'@router\.(get|post|put|delete|patch)\(["\'](.+?)["\']', code):
                method, path = match.groups()
                self.routes.add((router_name, method.upper(), path))
            for match in re.finditer(r'@router\.(get|post|put|delete|patch)\(["\'](.+?)["\']', code):
                method, path = match.groups()
                func_match = re.search(r'async def (\w+)\(', code[match.end():match.end()+200])
                func_name = func_match.group(1) if func_match else "unknown"
                self.api_entities[router_name].add((method.upper(), path, func_name))

    def _scan_models(self):
        models_dir = REPO / "backend" / "app" / "models"
        if not models_dir.exists():
            return
        for f in sorted(models_dir.glob("*.py")):
            code = f.read_text(encoding="utf-8", errors="replace")
            for match in re.finditer(r'class (\w+)\(Base\)', code):
                self.models.add((f.stem, match.group(1)))

    def _scan_events(self):
        events_dir = REPO / "backend" / "app" / "kernel" / "event_bus"
        if events_dir.exists():
            for f in sorted(events_dir.glob("*.py")):
                code = f.read_text(encoding="utf-8", errors="replace")
                for m in re.finditer(r'class (\w+Event)\b', code):
                    self.events.add(m.group(1))
                for m in re.finditer(r'class (\w+)\(', code):
                    if "Event" in m.group(1):
                        self.events.add(m.group(1))

        # Also check kernel/events.py
        events_py = REPO / "backend" / "app" / "core" / "events.py"
        if events_py.exists():
            code = events_py.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r'class (\w+Event)\b', code):
                self.events.add(m.group(1))

    def _scan_plugins(self):
        plugins_dir = REPO / "backend" / "app" / "kernel" / "plugin"
        if plugins_dir.exists():
            for f in sorted(plugins_dir.glob("*.py")):
                code = f.read_text(encoding="utf-8", errors="replace")
                for m in re.finditer(r'class (\w+Plugin)\b', code):
                    self.plugins.add(m.group(1))
                for m in re.finditer(r'class (\w+Manager)\b', code):
                    self.plugins.add(m.group(1))

    def _scan_services(self):
        svc_dir = REPO / "backend" / "app" / "services"
        if svc_dir.exists():
            for f in sorted(svc_dir.glob("*.py")):
                if f.name == "__init__.py":
                    continue
                code = f.read_text(encoding="utf-8", errors="replace")
                for m in re.finditer(r'(?:class|def)\s+(\w+)', code):
                    self.services.add((f.stem, m.group(1)))

    def _scan_kernel_subsystems(self):
        kernel_dir = REPO / "backend" / "app" / "kernel"
        if not kernel_dir.exists():
            return {}
        subsystems = {}
        for d in sorted(kernel_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                py_files = list(d.glob("*.py"))
                non_init = [f for f in py_files if f.name != "__init__.py"]
                subsystems[d.name] = [f.stem for f in non_init]
        return subsystems

    def _scan_topology(self):
        """Build the top-level directory structure."""
        result = {}
        for entry in sorted(REPO.iterdir()):
            if entry.name.startswith(".") or entry.name in SKIP_DIRS:
                continue
            if entry.is_dir():
                child_count = len(list(entry.rglob("*.py"))) + len(list(entry.rglob("*.ts"))) + len(list(entry.rglob("*.js")))
                result[entry.name] = child_count
        return result

    def build(self):
        # Scan all Python files
        py_files = list(REPO.rglob("*.py"))
        for f in py_files:
            skip = False
            for skip_dir in SKIP_DIRS:
                if f"{os.sep}{skip_dir}{os.sep}" in str(f) or f.parent.name == skip_dir:
                    skip = True
                    break
            if skip:
                continue
            # Skip archived or legacy frontend trees; frontend-v3 is the active UI.
            if any(p in str(f) for p in ["/archive/", "/test_library/", "/nhop-platform/", "/frontend-v2/", "/frontend/",
                                          "/node_modules/", "/.venv/", "/mutants/", "/coverage_html/"]):
                continue
            self._scan_python_file(f)

        self._scan_routes()
        self._scan_models()
        self._scan_events()
        self._scan_plugins()
        self._scan_services()
        kernel_subs = self._scan_kernel_subsystems()
        topology = self._scan_topology()

        return {
            "metadata": {
                "repository": "gula-platform",
                "version": "2.1.0",
                "generated": "2026-07-14",
                "mission": "4.1 — Repository Brain"
            },
            "topology": topology,
            "nodes": self.nodes,
            "edges": self.edges,
            "routes": [{"module": r[0], "method": r[1], "path": r[2]} for r in sorted(self.routes, key=lambda x: str(x[0]) + str(x[1]) + str(x[2]))],
            "models": [{"module": m[0], "class": m[1]} for m in sorted(self.models)],
            "events": sorted(self.events),
            "plugins": sorted(self.plugins),
            "services": [{"module": s[0], "name": s[1]} for s in sorted(self.services)],
            "api_entities": {
                mod: [{"method": m, "path": p, "handler": f} for m, p, f in sorted(eps)]
                for mod, eps in sorted(self.api_entities.items())
            },
            "kernel_subsystems": kernel_subs,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "route_count": len(self.routes),
            "model_count": len(self.models),
            "event_count": len(self.events),
            "plugin_count": len(self.plugins),
        }

def generate_mermaid_architecture(knowledge):
    """Generate Mermaid architecture diagram."""
    lines = ["# Architecture Graph — GULA Platform", "",
             "graph TB", "    subgraph Infrastructure[Infrastructure Layer]",
             "        NGINX[nginx / TLS]", "        GW[api-gateway]",
             "        PG[(PostgreSQL 16)]", "        RD[(Redis 7)]",
             "    end", "",
             "    subgraph Backend[Backend Layer]",
             "        FA[FastAPI / uvicorn]", "        MU[Middleware Stack]",
             "        RT[36 Route Modules]", "        MD[17 ORM Models]",
             "        SV[14 Service Modules]", "        EN[Engineering Factory]",
             "    end", "",
             "    subgraph Kernel[Kernel Subsystems]",
             "        RTK[Runtime / DI]", "        EB[Event Bus + Outbox]",
             "        PL[Plugin System]", "        MDK[Module System]",
             "        BG[Background Tasks]", "        FT[Feature Flags]",
             "        CF[Config Engine]", "        TN[Tenant Isolation]",
             "        GWY[Internal Gateway]", "        VL[Validation Engine]",
             "    end", "",
             "    subgraph AI[AI Layer]",
             "        AI_CL[Clinical AI]", "        AI_PO[Population AI]",
             "        AI_LB[Lab Business AI]", "        AI_PR[Preventive AI]",
             "        AI_OUT[Outbreak Detection]",
             "    end", "",
             "    subgraph Frontend[Frontends]",
             "        FEV3[React + Vite]", "        FE[Static PWA]",
             "        CL[tRPC Client]",
             "    end", "",
             "    subgraph Security[Security Layer]",
             "        JWT[JWT Auth]", "        RBAC[RBAC / Permissions]",
             "        ENC[Encryption]", "        MID[Intrusion Detection]",
             "        RATE[Rate Limiting]",
             "    end", "",
             "    subgraph Services[Microservices (Future)]",
             "        DB[Device Bridge]", "        AI_SVC[AI Service]",
             "        NHOP[NHOP Platform]",
             "    end", "",
             "    NGINX -->|TLS| GW", "    GW --> FA",
             "    FA --> MU", "    MU --> RT",
             "    RT --> MD", "    RT --> SV",
             "    FA --> RTK", "    RTK --> EB",
             "    RTK --> PL", "    RTK --> MDK",
             "    EB --> PG", "    BG --> RD",
             "    FA --> AI_CL", "    FA --> EN",
             "    FEV3 -->|API| FA", "    FE -->|API| FA",
             "    CL -->|tRPC| FA",
             "    DB -->|ASTM/HL7| FA",
             "    AI_SVC --> FA", "    NHOP --> PG",
    ]

    # Add Kernel dependencies
    for sub, deps in knowledge["kernel_subsystems"].items():
        sub_id = sub.upper()[:4]
        for dep in deps[:3]:  # first 3 files
            pass  # Already captured in subgraph

    return "\n".join(lines)


def generate_mermaid_db_erd():
    """Generate ER diagram for database models."""
    return """# Database Entity Relationship Diagram — GULA Platform

erDiagram
    labs ||--o{ lab_users : "has"
    labs ||--o{ lab_orders : "owns"
    labs ||--o{ lab_results : "owns"
    labs ||--o{ patients : "manages"
    labs ||--o{ samples : "tracks"

    patients ||--o{ lab_orders : "requests"
    patients ||--o{ lab_results : "has"
    patients ||--o{ consent : "grants"

    lab_orders ||--o{ lab_results : "contains"
    lab_orders ||--o{ samples : "references"
    lab_orders ||--o{ outbox_events : "generates"

    lab_results ||--o{ audit_logs : "audited_by"
    lab_results ||--o{ test_results : "includes"

    test_types ||--o{ lab_results : "defines"
    test_types ||--o{ quality_control : "tracks"

    lab_users ||--o{ audit_logs : "performs"
    lab_users ||--o{ outbox_events : "triggers"

    subscription ||--o{ labs : "tiers"
    claim ||--o{ lab_results : "references"
    consent ||--o{ patients : "protects"
    
    visits ||--o{ lab_orders : "sndhs_links"
    ai_interactions ||--o{ lab_results : "analyzes"
    ai_interactions ||--o{ quality_control : "monitors"

    labs {
        uuid id PK
        string name
        string type
        string license_number
        string director_name
        jsonb address
        jsonb contact
        jsonb settings
        timestamp created_at
    }

    patients {
        uuid id PK
        string first_name
        string father_name
        string last_name
        string phone UK
        date date_of_birth
        string national_id UK "encrypted"
        string sndhs_health_id
        jsonb metadata
        timestamp created_at
    }

    lab_orders {
        uuid id PK
        uuid lab_id FK
        uuid patient_id FK
        uuid visit_id FK "nullable"
        string status "state machine"
        string priority
        jsonb test_types
        jsonb metadata
        integer version
        timestamp created_at
    }

    lab_results {
        uuid id PK
        uuid order_id FK
        uuid patient_id FK
        uuid test_type_id FK
        string result_value
        string unit
        string status
        integer version "optimistic lock"
        timestamp created_at
    }
"""


def generate_mermaid_security():
    """Generate security architecture diagram."""
    return """# Security Architecture — GULA Platform

graph TB
    subgraph Perimeter[Perimeter Security]
        WAF[WAF / Rate Limiting]
        TLS[TLS 1.3]
        CSP[CSP Headers]
        HSTS[HSTS]
    end

    subgraph Auth[Authentication Layer]
        JWT[JWT Access Token]
        REF[Refresh Token]
        MFA[MFA (Future)]
        SESSION[Session Management]
    end

    subgraph Authz[Authorization Layer]
        RBAC[RBAC - 9 Roles]
        ABAC[ABAC (Future)]
        PERM[13 Permissions]
        LAB[Tenant Isolation]
    end

    subgraph Encryption[Data Protection]
        FERNET[Fernet Encryption]
        HMAC[HMAC Signatures]
        NID[National ID Encryption]
        QR[QR + HMAC Tokens]
    end

    subgraph Audit[Audit & Monitoring]
        AUD[Audit Log Chain]
        IDS[Intrusion Detection]
        MET[Metrics / Prometheus]
        ALERT[Alert Webhook]
    end

    subgraph Safety[Safety Measures]
        CB[Circuit Breaker]
        KILL[Kill Switch]
        AHEAL[Auto-Heal]
        ACL[Adaptive Concurrency]
    end

    TLS --> JWT
    JWT --> RBAC
    RBAC --> PERM
    PERM --> LAB
    FERNET --> NID
    HMAC --> QR
    AUD --> IDS
    CB --> AHEAL
"""


def generate_json_report(knowledge):
    """Generate the complete knowledge graph JSON."""
    return json.dumps(knowledge, indent=2, ensure_ascii=False, default=str)


def generate_markdown_report(knowledge):
    """Generate markdown documentation of the repository brain."""
    lines = [
        "# Repository Brain — GULA Platform v2.1.0",
        "",
        "## Overview",
        "",
        f"- **Total Nodes:** {knowledge['node_count']}",
        f"- **Total Edges:** {knowledge['edge_count']}",
        f"- **API Routes:** {knowledge['route_count']}",
        f"- **Database Models:** {knowledge['model_count']}",
        f"- **Events:** {knowledge['event_count']}",
        f"- **Plugins:** {knowledge['plugin_count']}",
        "",
        "## Topology",
        "",
    ]
    for name, count in sorted(knowledge["topology"].items()):
        lines.append(f"- **{name}/** — {count} source files")
    lines.append("")

    lines.extend([
        "## Kernel Subsystems",
        "",
    ])
    for sub, files in sorted(knowledge["kernel_subsystems"].items()):
        lines.append(f"- **{sub}/** — {', '.join(files)}")
    lines.append("")

    lines.extend([
        "## API Routes (by module)",
        "",
    ])
    for mod, eps in sorted(knowledge["api_entities"].items()):
        lines.append(f"### {mod}")
        for ep in eps:
            lines.append(f"- `{ep['method']} {ep['path']}` → `{ep['handler']}`")
    lines.append("")

    lines.extend([
        "## Models",
        "",
    ])
    for m in knowledge["models"]:
        lines.append(f"- **{m['class']}** (in `{m['module']}`)")
    lines.append("")

    lines.extend([
        "## Events",
        "",
    ])
    for ev in knowledge["events"]:
        lines.append(f"- `{ev}`")
    lines.append("")

    lines.extend([
        "## Plugins",
        "",
    ])
    for pl in knowledge["plugins"]:
        lines.append(f"- `{pl}`")
    lines.append("")

    return "\n".join(lines)


def generate_xref_engine(knowledge):
    """Generate a cross-reference query engine."""
    engine = {
        "impact_analysis": {},
        "dependents": defaultdict(list),
        "dependencies": defaultdict(list),
    }

    # Build dependency tree
    for edge in knowledge["edges"]:
        if edge["kind"] == "imports":
            src_id = edge["source"]
            tgt_id = edge["target"]
            src_name = next((n["name"] for n in knowledge["nodes"] if n["id"] == src_id), src_id)
            tgt_name = next((n["name"] for n in knowledge["nodes"] if n["id"] == tgt_id), tgt_id)
            engine["dependents"][tgt_name].append(src_name)
            engine["dependencies"][src_name].append(tgt_name)

    # Build impact analysis
    for node in knowledge["nodes"]:
        name = node["name"]
        kind = node["kind"]
        nid = node["id"]
        affected = engine["dependents"].get(name, [])
        if kind == "module" and affected:
            engine["impact_analysis"][name] = {
                "kind": kind,
                "direct_dependents": len(affected),
                "dependents": affected[:50],
            }

    return {
        "how_to_query": {
            "find_entity": "Search nodes array by name",
            "find_dependents": "Use dependents[name] to see what depends on entity",
            "find_dependencies": "Use dependencies[name] to see what entity imports",
            "impact_if_changed": "Use impact_analysis[name] to see affected modules",
        },
        "impact_analysis": engine["impact_analysis"],
        "dependents": dict(engine["dependents"]),
        "dependencies": dict(engine["dependencies"]),
    }


if __name__ == "__main__":
    kg = KnowledgeGraph()
    knowledge = kg.build()
    xref = generate_xref_engine(knowledge)

    output_dir = REPO / "assessment" / "brain"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON knowledge graph
    (output_dir / "knowledge_graph.json").write_text(generate_json_report(knowledge))

    # Write cross-reference JSON
    (output_dir / "cross_reference.json").write_text(json.dumps(xref, indent=2, ensure_ascii=False))

    # Write Mermaid diagrams
    (output_dir / "architecture_graph.mermaid").write_text(generate_mermaid_architecture(knowledge))
    (output_dir / "db_erd.mermaid").write_text(generate_mermaid_db_erd())
    (output_dir / "security_graph.mermaid").write_text(generate_mermaid_security())

    # Write markdown report
    (output_dir / "repository_brain.md").write_text(generate_markdown_report(knowledge))

    print(f"Repository Brain generated:")
    print(f"  - {knowledge['node_count']} nodes, {knowledge['edge_count']} edges")
    print(f"  - {knowledge['route_count']} API routes, {knowledge['model_count']} models")
    print(f"  - {knowledge['event_count']} events, {knowledge['plugin_count']} plugins")
    print(f"  - {len(xref['impact_analysis'])} impact analysis entries")
    print(f"Output: {output_dir}/")
