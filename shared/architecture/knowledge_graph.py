from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.knowledge_graph")


@dataclass
class KnowledgeNode:
    id: str
    type: str
    name: str
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeEdge:
    source: str
    target: str
    relation: str
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, KnowledgeNode] = {}
        self._edges: list[KnowledgeEdge] = []

    def add_node(self, node: KnowledgeNode) -> None:
        self._nodes[node.id] = node

    def add_edge(self, edge: KnowledgeEdge) -> None:
        self._edges.append(edge)
        for nid in (edge.source, edge.target):
            if nid not in self._nodes:
                self._nodes[nid] = KnowledgeNode(id=nid, type="unknown", name=nid)

    def add_link(self, source: str, target: str, relation: str) -> None:
        self.add_edge(KnowledgeEdge(source=source, target=target, relation=relation))

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {nid: {"id": nid, "type": n.type, "name": n.name, "description": n.description, "metadata": n.metadata}
                      for nid, n in self._nodes.items()},
            "edges": [{"source": e.source, "target": e.target, "relation": e.relation} for e in self._edges],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def query(self, node_type: str | None = None, relation: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for edge in self._edges:
            if relation and edge.relation != relation:
                continue
            source = self._nodes.get(edge.source)
            target = self._nodes.get(edge.target)
            if node_type:
                if source and source.type != node_type and target and target.type != node_type:
                    continue
            results.append({
                "source": source.name if source else edge.source,
                "target": target.name if target else edge.target,
                "relation": edge.relation,
            })
        return results

    def find_path(self, start: str, end: str) -> list[list[str]]:
        adjacency: dict[str, list[str]] = defaultdict(list)
        for edge in self._edges:
            adjacency[edge.source].append(edge.target)
            adjacency[edge.target].append(edge.source)
        paths: list[list[str]] = []
        visited: set[str] = set()

        def dfs(current: str, target: str, path: list[str]) -> None:
            if current == target:
                paths.append(path + [current])
                return
            if current in visited:
                return
            visited.add(current)
            for neighbor in adjacency.get(current, []):
                dfs(neighbor, target, path + [current])
            visited.remove(current)

        dfs(start, end, [])
        return paths[:5]

    def export_mermaid(self) -> str:
        lines = ["graph TD"]
        for edge in self._edges:
            src = self._nodes.get(edge.source, KnowledgeNode(edge.source, "", ""))
            tgt = self._nodes.get(edge.target, KnowledgeNode(edge.target, "", ""))
            sid = edge.source.replace("-", "_").replace(" ", "_")
            tid = edge.target.replace("-", "_").replace(" ", "_")
            lines.append(f"    {sid}[\"{src.name}\"] -->|{edge.relation}| {tid}[\"{tgt.name}\"]")
        return "\n".join(lines)


def build_gula_knowledge_graph() -> KnowledgeGraph:
    kg = KnowledgeGraph()

    for nid, ntype, name, desc in [
        ("gula-platform", "repository", "GULA Platform", "Main monorepo"),
        ("device-bridge", "repository", "Device Bridge", "ASTM/HL7 device integration"),
        ("frontend-v2", "repository", "Frontend V2", "React + Firebase UI"),
        ("backend", "capability", "Backend API", "FastAPI monolith"),
        ("auth", "capability", "Authentication", "JWT + OAuth2"),
        ("patients", "capability", "Patient Management", "CRUD + MPI"),
        ("orders", "capability", "Order Management", "Lab order lifecycle"),
        ("results", "capability", "Result Management", "Lab result processing"),
        ("samples", "capability", "Sample Tracking", "Sample lifecycle"),
        ("integrations", "capability", "Integrations", "External system adapters"),
        ("analytics", "capability", "Analytics", "Stats + trends"),
        ("ai", "capability", "AI Engine", "Clinical intelligence"),
        ("notifications", "capability", "Notifications", "Push/SMS/Email"),
        ("compliance", "capability", "Compliance", "Regulatory compliance"),
        ("audit", "capability", "Audit", "Hash-chain audit trail"),
        ("edge", "capability", "Edge Platform", "Offline edge computing"),
        ("core", "module", "Core", "Startup guard, self-healing"),
        ("security-module", "module", "Security", "RBAC, rate limiting"),
        ("models", "module", "Models", "SQLAlchemy ORM models"),
        ("routes", "module", "Routes", "FastAPI route handlers"),
        ("services-layer", "module", "Services", "Business logic"),
        ("shared-lib", "module", "Shared Library", "Canonical shared modules"),
        ("lab-svc", "service", "Lab Service", "Lab management"),
        ("order-svc", "service", "Order Service", "Order management"),
        ("patient-svc", "service", "Patient Service", "Patient management"),
        ("result-svc", "service", "Result Service", "Result management"),
        ("notification-svc", "service", "Notification Service", "Notifications"),
        ("device-bridge-svc", "service", "Device Bridge", "Lab instrument integration"),
        ("postgres", "database", "PostgreSQL 16", "Primary database"),
        ("redis", "database", "Redis 7", "Cache + rate limiting"),
        ("rest-api", "api", "REST API", "FastAPI REST endpoints"),
        ("health-api", "api", "Health API", "/health endpoints"),
        ("backend-tests", "tests", "Backend Tests", "pytest suite (28 modules)"),
        ("docs", "documentation", "Documentation", "Architecture + deployment docs"),
        ("security-layer", "security", "Security Layer", "Auth + encryption"),
        ("prometheus", "metrics", "Prometheus Metrics", "Monitoring + alerting"),
    ]:
        kg.add_node(KnowledgeNode(nid, ntype, name, desc))

    for src, tgt, rel in [
        ("gula-platform", "backend", "contains"), ("gula-platform", "shared-lib", "contains"),
        ("gula-platform", "lab-svc", "contains"), ("gula-platform", "order-svc", "contains"),
        ("gula-platform", "patient-svc", "contains"), ("gula-platform", "result-svc", "contains"),
        ("gula-platform", "device-bridge-svc", "contains"), ("gula-platform", "notification-svc", "contains"),
        ("gula-platform", "docs", "has"),
        ("backend", "auth", "provides"), ("backend", "patients", "provides"),
        ("backend", "orders", "provides"), ("backend", "results", "provides"),
        ("backend", "samples", "provides"), ("backend", "integrations", "provides"),
        ("backend", "analytics", "provides"), ("backend", "ai", "provides"),
        ("backend", "notifications", "provides"), ("backend", "compliance", "provides"),
        ("backend", "audit", "provides"), ("backend", "edge", "provides"),
        ("backend", "core", "uses"), ("backend", "security-module", "uses"),
        ("backend", "models", "uses"), ("backend", "routes", "uses"),
        ("backend", "services-layer", "uses"), ("backend", "shared-lib", "uses"),
        ("backend", "postgres", "persists_to"), ("backend", "redis", "caches_in"),
        ("backend", "rest-api", "exposes"), ("backend", "health-api", "exposes"),
        ("backend", "security-layer", "implements"), ("backend", "backend-tests", "tested_by"),
        ("shared-lib", "auth", "includes"), ("shared-lib", "audit", "includes"),
        ("shared-lib", "security-module", "includes"), ("shared-lib", "core", "includes"),
        ("rest-api", "health-api", "includes"), ("rest-api", "postgres", "reads"),
        ("rest-api", "redis", "reads"),
    ]:
        kg.add_link(src, tgt, rel)

    return kg


def generate_report(kg: KnowledgeGraph) -> str:
    data = kg.to_dict()
    lines = ["# GULA Knowledge Graph\n", "## Nodes\n", f"Total: {len(data['nodes'])}\n"]
    for node in data["nodes"].values():
        lines.append(f"- **{node['name']}** ({node['type']}): {node['description']}")
    lines.extend(["", "## Edges\n", f"Total: {len(data['edges'])}\n"])
    for edge in data["edges"]:
        lines.append(f"- {edge['source']} → {edge['target']}: {edge['relation']}")
    lines.extend(["", "## Mermaid Diagram\n", "```mermaid", kg.export_mermaid(), "```"])
    return "\n".join(lines)


__all__ = ["KnowledgeNode", "KnowledgeEdge", "KnowledgeGraph", "build_gula_knowledge_graph", "generate_report"]
