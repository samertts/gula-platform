from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app._compat import UTC, StrEnum

from ..database import Base


class NodeType(StrEnum):
    PROJECT = "PROJECT"
    MODULE = "MODULE"
    SERVICE = "SERVICE"
    PACKAGE = "PACKAGE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    ENDPOINT = "ENDPOINT"
    DATABASE_TABLE = "DATABASE_TABLE"
    DATABASE_COLUMN = "DATABASE_COLUMN"
    EVENT = "EVENT"
    WORKFLOW = "WORKFLOW"
    FHIR_RESOURCE = "FHIR_RESOURCE"
    PERMISSION = "PERMISSION"
    POLICY = "POLICY"
    DOCUMENTATION = "DOCUMENTATION"
    ADR = "ADR"
    TEST = "TEST"
    SECURITY_CONTROL = "SECURITY_CONTROL"
    MODEL = "MODEL"
    ROUTE = "ROUTE"
    CONFIG = "CONFIG"
    INTEGRATION = "INTEGRATION"


class EdgeType(StrEnum):
    DEPENDS_ON = "DEPENDS_ON"
    CONTAINS = "CONTAINS"
    IMPLEMENTS = "IMPLEMENTS"
    EXTENDS = "EXTENDS"
    CALLS = "CALLS"
    PUBLISHES = "PUBLISHES"
    SUBSCRIBES_TO = "SUBSCRIBES_TO"
    REFERENCES = "REFERENCES"
    DOCUMENTS = "DOCUMENTS"
    TESTS = "TESTS"
    DEPLOYS = "DEPLOYS"
    CONFIGURES = "CONFIGURES"
    AUTHENTICATES = "AUTHENTICATES"
    AUTHORIZES = "AUTHORIZES"
    ENCRYPTS = "ENCRYPTS"
    VALIDATES = "VALIDATES"
    TRANSFORMS = "TRANSFORMS"
    MIGRATES = "MIGRATES"


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    qualified_name = Column(String(512), nullable=False, unique=True, index=True)
    description = Column(Text, default="")
    metadata = Column(JSON, default=dict)
    source_path = Column(String(512), default="")
    tags = Column(JSON, default=list)
    version = Column(String(20), default="1.0.0")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    outgoing_edges = relationship(
        "KnowledgeEdge",
        foreign_keys="KnowledgeEdge.source_node_id",
        back_populates="source_node",
        lazy="dynamic",
    )
    incoming_edges = relationship(
        "KnowledgeEdge",
        foreign_keys="KnowledgeEdge.target_node_id",
        back_populates="target_node",
        lazy="dynamic",
    )


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_node_id = Column(
        Integer, ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_node_id = Column(
        Integer, ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    edge_type = Column(String(50), nullable=False, index=True)
    metadata = Column(JSON, default=dict)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    source_node = relationship(
        "KnowledgeNode",
        foreign_keys=[source_node_id],
        back_populates="outgoing_edges",
    )
    target_node = relationship(
        "KnowledgeNode",
        foreign_keys=[target_node_id],
        back_populates="incoming_edges",
    )


class KnowledgeGraphSnapshot(Base):
    __tablename__ = "knowledge_graph_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(20), nullable=False, index=True)
    node_count = Column(Integer, nullable=False, default=0)
    edge_count = Column(Integer, nullable=False, default=0)
    graph_hash = Column(String(64), nullable=False)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
