from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app._compat import StrEnum
from app.knowledge_graph.engine import KnowledgeGraphEngine as _KGEngine

logger = logging.getLogger("gula.ai_fabric.knowledge_graph")


class EntityType(StrEnum):
    PATIENT = "patient"
    LABORATORY = "laboratory"
    TEST = "test"
    RESULT = "result"
    ORDER = "order"
    DISEASE = "disease"
    MEDICATION = "medication"
    OBSERVATION = "observation"
    PHYSICIAN = "physician"
    FACILITY = "facility"
    PROTOCOL = "protocol"
    INSTRUMENT = "instrument"


class RelationshipType(StrEnum):
    HAS_RESULT = "has_result"
    ORDERED_BY = "ordered_by"
    DIAGNOSED_WITH = "diagnosed_with"
    TREATED_WITH = "treated_with"
    CORRELATED_WITH = "correlated_with"
    FOLLOWS = "follows"
    PRECEDES = "precedes"
    ASSOCIATED_WITH = "associated_with"
    LOCATED_AT = "located_at"
    PERFORMED_BY = "performed_by"
    DERIVED_FROM = "derived_from"


@dataclass
class GraphEntity:
    id: str = ""
    type: EntityType = EntityType.OBSERVATION
    name: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class GraphRelationship:
    source_id: str = ""
    target_id: str = ""
    type: RelationshipType = RelationshipType.ASSOCIATED_WITH
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


@dataclass
class GraphPath:
    nodes: list[GraphEntity] = field(default_factory=list)
    edges: list[GraphRelationship] = field(default_factory=list)
    length: int = 0
    score: float = 0.0


class GraphQuery:
    def __init__(self, engine: _KGEngine | None = None) -> None:
        self._engine = engine or _KGEngine()

    async def find_entity(self, qualified_name: str) -> dict[str, Any] | None:
        node = await self._engine.get_node(qualified_name)
        if not node:
            return None
        return {
            "id": str(node.id),
            "name": node.name,
            "qualified_name": node.qualified_name,
            "node_type": node.node_type,
            "description": node.description,
            "tags": node.tags,
            "metadata": node.metadata,
        }

    async def find_related(
        self,
        qualified_name: str,
        relationship_types: list[str] | None = None,
        max_depth: int = 2,
    ) -> list[dict[str, Any]]:
        from app.knowledge_graph.models import EdgeType
        edge_types = None
        if relationship_types:
            edge_types = [EdgeType(rt) for rt in relationship_types if hasattr(EdgeType, rt.upper())]
        return await self._engine.get_neighbors(qualified_name, edge_types, max_depth)

    async def find_path(
        self,
        source_name: str,
        target_name: str,
    ) -> list[dict[str, Any]]:
        return await self._engine.find_path(source_name, target_name)

    async def search_entities(
        self,
        query: str,
        entity_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        from app.knowledge_graph.models import NodeType
        node_types = None
        if entity_types:
            node_types = [NodeType(et) for et in entity_types if hasattr(NodeType, et.upper())]
        return await self._engine.search_nodes(query, node_types)

    async def get_statistics(self) -> dict[str, Any]:
        return await self._engine.get_statistics()


class GraphBuilder:
    def __init__(self, engine: _KGEngine | None = None) -> None:
        self._engine = engine or _KGEngine()

    async def add_entity(
        self,
        entity: GraphEntity,
        source_path: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        from app.knowledge_graph.models import NodeType
        node_type_map = {
            EntityType.PATIENT: NodeType.MODEL,
            EntityType.LABORATORY: NodeType.MODEL,
            EntityType.TEST: NodeType.MODEL,
            EntityType.RESULT: NodeType.MODEL,
            EntityType.ORDER: NodeType.MODEL,
            EntityType.DISEASE: NodeType.MODEL,
            EntityType.MEDICATION: NodeType.MODEL,
            EntityType.OBSERVATION: NodeType.MODEL,
            EntityType.PHYSICIAN: NodeType.USER,
            EntityType.FACILITY: NodeType.MODEL,
            EntityType.PROTOCOL: NodeType.CLASS,
            EntityType.INSTRUMENT: NodeType.MODEL,
        }
        node_type = node_type_map.get(entity.type, NodeType.MODEL)
        node = await self._engine.add_node(
            node_type=node_type,
            name=entity.name,
            qualified_name=entity.id or f"{entity.type.value}:{entity.name}",
            description=entity.properties.get("description", ""),
            metadata=entity.properties,
            source_path=source_path,
            tags=tags or [entity.type.value],
        )
        return {
            "id": str(node.id),
            "qualified_name": node.qualified_name,
            "name": node.name,
        }

    async def add_relationship(
        self,
        relationship: GraphRelationship,
    ) -> dict[str, Any] | None:
        from app.knowledge_graph.models import EdgeType
        edge_type_map = {
            RelationshipType.HAS_RESULT: EdgeType.REFERENCES,
            RelationshipType.ORDERED_BY: EdgeType.DEPENDS_ON,
            RelationshipType.DIAGNOSED_WITH: EdgeType.REFERENCES,
            RelationshipType.TREATED_WITH: EdgeType.REFERENCES,
            RelationshipType.CORRELATED_WITH: EdgeType.REFERENCES,
            RelationshipType.FOLLOWS: EdgeType.DEPENDS_ON,
            RelationshipType.PRECEDES: EdgeType.DEPENDS_ON,
            RelationshipType.ASSOCIATED_WITH: EdgeType.REFERENCES,
            RelationshipType.LOCATED_AT: EdgeType.CONTAINS,
            RelationshipType.PERFORMED_BY: EdgeType.IMPLEMENTS,
            RelationshipType.DERIVED_FROM: EdgeType.DERIVED_FROM,
        }
        edge_type = edge_type_map.get(relationship.type, EdgeType.REFERENCES)
        edge = await self._engine.add_edge(
            source_qualified_name=relationship.source_id,
            target_qualified_name=relationship.target_id,
            edge_type=edge_type,
            metadata=relationship.properties,
            weight=relationship.weight,
        )
        if not edge:
            return None
        return {
            "id": str(edge.id),
            "source": relationship.source_id,
            "target": relationship.target_id,
            "type": relationship.type.value,
            "weight": relationship.weight,
        }

    async def build_from_results(
        self,
        patient_id: str,
        results: list[dict[str, Any]],
    ) -> int:
        count = 0
        patient_entity = GraphEntity(
            id=f"patient:{patient_id}",
            type=EntityType.PATIENT,
            name=f"Patient {patient_id}",
        )
        await self.add_entity(patient_entity)
        count += 1

        for result in results:
            test_name = result.get("test_name", "unknown")
            test_entity = GraphEntity(
                id=f"test:{test_name}",
                type=EntityType.TEST,
                name=test_name,
                properties={"category": result.get("category", "")},
            )
            await self.add_entity(test_entity)
            count += 1

            result_entity = GraphEntity(
                id=f"result:{result.get('id', '')}",
                type=EntityType.RESULT,
                name=f"{test_name} result",
                properties=result,
            )
            await self.add_entity(result_entity)
            count += 1

            rel = GraphRelationship(
                source_id=result_entity.id,
                target_id=patient_entity.id,
                type=RelationshipType.ASSOCIATED_WITH,
            )
            await self.add_relationship(rel)

            rel2 = GraphRelationship(
                source_id=result_entity.id,
                target_id=test_entity.id,
                type=RelationshipType.DERIVED_FROM,
            )
            await self.add_relationship(rel2)

        return count

    async def take_snapshot(self) -> dict[str, Any]:
        snap = await self._engine.snapshot()
        return {
            "id": str(snap.id),
            "version": snap.version,
            "node_count": snap.node_count,
            "edge_count": snap.edge_count,
            "graph_hash": snap.graph_hash,
        }


class TraversalStrategy(StrEnum):
    BFS = "bfs"
    DFS = "dfs"
    SHORTEST_PATH = "shortest_path"


class KnowledgeGraphService:
    def __init__(
        self,
        engine: _KGEngine | None = None,
        query: GraphQuery | None = None,
        builder: GraphBuilder | None = None,
    ) -> None:
        self._engine = engine or _KGEngine()
        self._query = query or GraphQuery(self._engine)
        self._builder = builder or GraphBuilder(self._engine)

    @property
    def query(self) -> GraphQuery:
        return self._query

    @property
    def builder(self) -> GraphBuilder:
        return self._builder

    async def traverse(
        self,
        start: str,
        strategy: TraversalStrategy = TraversalStrategy.BFS,
        max_depth: int = 3,
    ) -> list[dict[str, Any]]:
        if strategy == TraversalStrategy.SHORTEST_PATH:
            return []
        return await self._query.find_related(start, max_depth=max_depth)

    async def get_dependency_graph(self, qualified_name: str) -> dict[str, Any]:
        return await self._engine.get_dependency_graph(qualified_name)

    async def scan_project(self) -> int:
        return await self._engine.scan_project()

    async def get_statistics(self) -> dict[str, Any]:
        return await self._engine.get_statistics()
