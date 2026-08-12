from sqlalchemy import JSON, Column, Index, Integer, String, Text

from app.national_data.base import BaseEntity


class KnowledgeGraphNode(BaseEntity):
    __tablename__ = "dp_knowledge_graph_nodes"

    node_type = Column(String(100), nullable=False, index=True)
    node_label = Column(String(200), nullable=False)
    node_label_ar = Column(String(200), nullable=True)
    node_source_id = Column(String(100), nullable=True)
    node_source_system = Column(String(50), nullable=True)

    description = Column(Text, nullable=True)
    properties = Column(JSON, nullable=True)
    external_uri = Column(String(500), nullable=True)

    ontology_class = Column(String(100), nullable=True)
    ontology_code = Column(String(50), nullable=True)

    is_active = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index("ix_dp_kg_node_type", "node_type"),
        Index("ix_dp_kg_node_source", "node_source_system", "node_source_id"),
        {"extend_existing": True},
    )
