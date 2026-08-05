"""Phase 5 — Memory & Knowledge Graph.

Evolve the platform's permanent memory (project, engineering, decision,
architecture, deployment) and the knowledge graph of related artifacts.
Every evolution is stored under `.ai/core/memory/` and every knowledge item
is linked to its related artifacts so the search index can navigate from
problem to solution to skill to runbook.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import REPO_ROOT, utcnow
from scripts.learner.core import (
    MEMORY_KINDS,
    KnowledgeItem,
    KnowledgeStatus,
    read_json,
    write_json,
)

MEMORY_DIR = REPO_ROOT / ".ai" / "core" / "memory"
GRAPH_DIR = REPO_ROOT / ".ai" / "core" / "graph"
GRAPH_INDEX = GRAPH_DIR / "knowledge_graph.json"


def evolve_memory(
    kind: str,
    *,
    title: str = "",
    body: str = "",
    tags: list[str] | None = None,
) -> KnowledgeItem:
    """Record a durable memory entry of the given kind."""
    if kind not in MEMORY_KINDS:
        raise ValueError(f"invalid memory kind: {kind}")
    return KnowledgeItem(
        item_id=f"KNOW-{_next_knowledge_number()}",
        kind="memory",
        title=title or f"{kind.title()} Memory",
        status=KnowledgeStatus.EXTRACTED.value,
        confidence="high",
        tags=["memory", kind, *list(tags or [])],
        body=body,
    )


def persist_memory(item: KnowledgeItem) -> Path:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slug(item.title)
    path = MEMORY_DIR / f"{item.item_id}_{slug}.md"
    path.write_text(_render_memory(item), encoding="utf-8")
    return path


def link_item(item: KnowledgeItem, related: list[str]) -> KnowledgeItem:
    """Add related artifact IDs to a knowledge item's tags."""
    item.tags = list(dict.fromkeys(item.tags + related))
    return item


def add_graph_node(node_id: str, *, kind: str, title: str,
                   related: list[str] | None = None) -> None:
    """Add or refresh a knowledge-graph node with related edges."""
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    graph = read_json(GRAPH_INDEX)
    nodes = graph.setdefault("nodes", [])
    index = {node["id"]: position for position, node in enumerate(nodes)}
    node = {
        "id": node_id,
        "kind": kind,
        "title": title,
        "related": list(dict.fromkeys(related or [])),
        "updated_at": utcnow(),
    }
    if node_id in index:
        nodes[index[node_id]] = node
    else:
        nodes.append(node)
    graph["updated_at"] = utcnow()
    write_json(GRAPH_INDEX, graph)


def graph_nodes() -> list[dict]:
    return read_json(GRAPH_INDEX).get("nodes", [])


def graph_size() -> int:
    return len(graph_nodes())


def memory_exists(title: str) -> bool:
    """True when a memory entry with the same title already exists."""
    needle = _slug(title)
    if not MEMORY_DIR.exists():
        return False
    return any(_slug(p.stem.split("_", 1)[-1]) == needle for p in MEMORY_DIR.glob("KNOW-*.md"))


def find_memory_by_title(title: str) -> KnowledgeItem | None:
    """Return the existing memory entry matching a title (reuse, never duplicate)."""
    needle = _slug(title)
    if not MEMORY_DIR.exists():
        return None
    for path in MEMORY_DIR.glob("KNOW-*.md"):
        if _slug(path.stem.split("_", 1)[-1]) == needle:
            match = re.search(r"(KNOW-\d{6})", path.name)
            if match:
                return KnowledgeItem(
                    item_id=match.group(1),
                    kind="memory",
                    title=title,
                    status=KnowledgeStatus.EXTRACTED.value,
                    confidence="high",
                    body=path.read_text(encoding="utf-8", errors="replace"),
                )
    return None


def _render_memory(item: KnowledgeItem) -> str:
    return "\n".join([
        "---",
        f"id: {item.item_id}",
        "type: memory",
        f"title: {item.title}",
        f'version: "{item.version}"',
        f'created: "{utcnow()[:10]}"',
        f"status: {item.status}",
        f"confidence: {item.confidence}",
        f"tags: [{', '.join(item.tags)}]",
        "---",
        "",
        f"# {item.item_id}: {item.title}",
        "",
        item.body or "—",
        "",
    ])


def _next_knowledge_number() -> str:
    if not MEMORY_DIR.exists():
        return "000001"
    highest = 0
    for path in MEMORY_DIR.glob("KNOW-*.md"):
        number = path.name.split("_", 1)[0].split("-")[1]
        if number.isdigit():
            highest = max(highest, int(number))
    return f"{highest + 1:06d}"


def _slug(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")
    return cleaned[:48]
