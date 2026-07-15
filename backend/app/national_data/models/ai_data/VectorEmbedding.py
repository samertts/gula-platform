from datetime import datetime

from app._compat import UTC
from app.national_data.base import BaseEntity
from sqlalchemy import JSON, Column, DateTime, Index, Integer, String, Text


class VectorEmbedding(BaseEntity):
    __tablename__ = "dp_vector_embeddings"

    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    embedding_model = Column(String(100), nullable=False)
    embedding_dimension = Column(Integer, nullable=False)

    embedding_text = Column(Text, nullable=True)
    embedding_source = Column(String(100), nullable=True)

    chunk_index = Column(Integer, default=0, nullable=False)
    chunk_text = Column(Text, nullable=True)

    metadata_ = Column("metadata", JSON, nullable=True)
    lab_id = Column(Integer, nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_dp_vector_entity", "entity_type", "entity_id"),
        Index("ix_dp_vector_model", "embedding_model"),
        Index("ix_dp_vector_lab", "lab_id"),
        {"extend_existing": True},
    )
