from sqlalchemy import JSON, Column, Float, ForeignKey, Index, Integer, String, Text

from app.national_data.base import BaseEntity


class KnowledgeGraphEdge(BaseEntity):
    __tablename__ = "dp_knowledge_graph_edges"

    source_node_id = Column(
        Integer,
        ForeignKey("dp_knowledge_graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id = Column(
        Integer,
        ForeignKey("dp_knowledge_graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    edge_type = Column(String(100), nullable=False, index=True)
    edge_label = Column(String(200), nullable=True)
    edge_label_ar = Column(String(200), nullable=True)

    weight = Column(Float, default=1.0, nullable=True)
    properties = Column(JSON, nullable=True)
    source_evidence = Column(Text, nullable=True)

    is_active = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index("ix_dp_kg_edge_source", "source_node_id"),
        Index("ix_dp_kg_edge_target", "target_node_id"),
        Index("ix_dp_kg_edge_type", "edge_type"),
        {"extend_existing": True},
    )
