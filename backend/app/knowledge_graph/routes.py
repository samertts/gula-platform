"""Platform Knowledge Graph — Routes API.

Provides a complete navigable map of the GULA platform ecosystem,
including all modules, classes, routes, models, events, and their
relationships.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user, require_permission
from .engine import engine as kg_engine
from .models import EdgeType, NodeType

logger = logging.getLogger("gula.knowledge_graph")

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


# ── Pydantic request/response models ──────────────────────────────────────────


class AddNodeRequest(BaseModel):
    node_type: str
    name: str
    qualified_name: str
    description: str = ""
    metadata: dict | None = None
    source_path: str = ""
    tags: list[str] | None = None
    version: str = "1.0.0"


class AddEdgeRequest(BaseModel):
    source_qualified_name: str
    target_qualified_name: str
    edge_type: str
    metadata: dict | None = None
    weight: float = 1.0


class PathQueryParams(BaseModel):
    source: str
    target: str


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/nodes")
def add_node(
    body: AddNodeRequest,
    current_user: LabUser = Depends(require_permission("admin")),
):
    """Add a node to the knowledge graph."""
    try:
        node_type = NodeType(body.node_type.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid node_type: {body.node_type}") from e

    import asyncio
    node = asyncio.run(
        kg_engine.add_node(
            node_type=node_type,
            name=body.name,
            qualified_name=body.qualified_name,
            description=body.description,
            metadata=body.metadata,
            source_path=body.source_path,
            tags=body.tags,
            version=body.version,
        )
    )
    return {
        "id": node.id,
        "node_type": node.node_type,
        "name": node.name,
        "qualified_name": node.qualified_name,
        "created_at": node.created_at.isoformat() if node.created_at else None,
    }


@router.post("/edges")
def add_edge(
    body: AddEdgeRequest,
    current_user: LabUser = Depends(require_permission("admin")),
):
    """Add an edge between two nodes."""
    try:
        edge_type = EdgeType(body.edge_type.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid edge_type: {body.edge_type}") from e

    import asyncio
    edge = asyncio.run(
        kg_engine.add_edge(
            source_qualified_name=body.source_qualified_name,
            target_qualified_name=body.target_qualified_name,
            edge_type=edge_type,
            metadata=body.metadata,
            weight=body.weight,
        )
    )
    if edge is None:
        raise HTTPException(
            status_code=404,
            detail="Could not create edge — source or target node not found",
        )
    return {
        "id": edge.id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "edge_type": edge.edge_type,
        "weight": edge.weight,
    }


@router.get("/nodes/{qualified_name:path}")
def get_node(
    qualified_name: str = Path(..., description="Fully qualified node name (dot-separated)"),
    current_user: LabUser = Depends(get_current_user),
):
    """Get details for a single knowledge graph node."""
    import asyncio
    node = asyncio.run(kg_engine.get_node(qualified_name))
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{qualified_name}' not found")
    return {
        "id": node.id,
        "node_type": node.node_type,
        "name": node.name,
        "qualified_name": node.qualified_name,
        "description": node.description,
        "metadata": node.extra_metadata,
        "source_path": node.source_path,
        "tags": node.tags,
        "version": node.version,
        "created_at": node.created_at.isoformat() if node.created_at else None,
        "updated_at": node.updated_at.isoformat() if node.updated_at else None,
    }


@router.get("/nodes/{qualified_name:path}/neighbors")
def get_neighbors(
    qualified_name: str = Path(..., description="Fully qualified node name"),
    depth: int = Query(1, ge=1, le=5, description="Traversal depth"),
    edge_types: str | None = Query(None, description="Comma-separated edge type filter"),
    current_user: LabUser = Depends(get_current_user),
):
    """Get neighboring nodes with configurable traversal depth."""
    parsed_types = None
    if edge_types:
        try:
            parsed_types = [EdgeType(et.strip().upper()) for et in edge_types.split(",")]
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid edge_type in filter") from e

    import asyncio
    neighbors = asyncio.run(
        kg_engine.get_neighbors(qualified_name, edge_types=parsed_types, max_depth=depth)
    )
    return {"qualified_name": qualified_name, "depth": depth, "neighbors": neighbors}


@router.get("/path")
def find_path(
    source: str = Query(..., description="Source qualified name"),
    target: str = Query(..., description="Target qualified name"),
    current_user: LabUser = Depends(get_current_user),
):
    """Find the shortest path between two nodes in the knowledge graph."""
    import asyncio
    path = asyncio.run(kg_engine.find_path(source, target))
    if not path:
        raise HTTPException(
            status_code=404,
            detail=f"No path found between '{source}' and '{target}'",
        )
    return {"source": source, "target": target, "path": path, "hops": len(path) - 1}


@router.get("/search")
def search_nodes(
    q: str = Query(..., min_length=1, description="Search query"),
    node_types: str | None = Query(None, description="Comma-separated node type filter"),
    current_user: LabUser = Depends(get_current_user),
):
    """Search knowledge graph nodes by name or description."""
    parsed_types = None
    if node_types:
        try:
            parsed_types = [NodeType(nt.strip().upper()) for nt in node_types.split(",")]
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid node_type in filter") from e

    import asyncio
    results = asyncio.run(kg_engine.search_nodes(q, node_types=parsed_types))
    return {"query": q, "total": len(results), "results": results}


@router.post("/scan/routes")
def scan_routes(
    current_user: LabUser = Depends(require_permission("admin")),
):
    """Scan and index all FastAPI routes into the knowledge graph."""
    import asyncio
    count = asyncio.run(kg_engine.scan_backend_routes())
    return {"scanned": True, "type": "routes", "nodes_created": count}


@router.post("/scan/models")
def scan_models(
    current_user: LabUser = Depends(require_permission("admin")),
):
    """Scan and index all SQLAlchemy data models."""
    import asyncio
    count = asyncio.run(kg_engine.scan_models())
    return {"scanned": True, "type": "models", "nodes_created": count}


@router.post("/scan/events")
def scan_events(
    current_user: LabUser = Depends(require_permission("admin")),
):
    """Scan and index all event definitions."""
    import asyncio
    count = asyncio.run(kg_engine.scan_events())
    return {"scanned": True, "type": "events", "nodes_created": count}


@router.post("/scan/full")
def scan_full(
    current_user: LabUser = Depends(require_permission("admin")),
):
    """Full platform scan — project, routes, models, and events."""
    import asyncio

    project_count = asyncio.run(kg_engine.scan_project())
    route_count = asyncio.run(kg_engine.scan_backend_routes())
    model_count = asyncio.run(kg_engine.scan_models())
    event_count = asyncio.run(kg_engine.scan_events())

    return {
        "scanned": True,
        "summary": {
            "project_nodes": project_count,
            "routes_indexed": route_count,
            "models_indexed": model_count,
            "events_indexed": event_count,
            "total_nodes_created": project_count + route_count + model_count + event_count,
        },
    }


@router.get("/snapshot")
def create_snapshot(
    current_user: LabUser = Depends(require_permission("admin")),
):
    """Create a snapshot of the current knowledge graph state."""
    import asyncio
    snap = asyncio.run(kg_engine.snapshot())
    return {
        "id": snap.id,
        "version": snap.version,
        "node_count": snap.node_count,
        "edge_count": snap.edge_count,
        "graph_hash": snap.graph_hash,
        "created_at": snap.created_at.isoformat() if snap.created_at else None,
    }


@router.get("/statistics")
def get_statistics(
    current_user: LabUser = Depends(get_current_user),
):
    """Get knowledge graph statistics and distribution."""
    import asyncio
    return asyncio.run(kg_engine.get_statistics())


@router.get("/dependency/{qualified_name:path}")
def get_dependency_graph(
    qualified_name: str = Path(..., description="Fully qualified node name"),
    current_user: LabUser = Depends(get_current_user),
):
    """Get dependency graph for a node (what it depends on and what depends on it)."""
    import asyncio
    result = asyncio.run(kg_engine.get_dependency_graph(qualified_name))
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
