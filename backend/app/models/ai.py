from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app._compat import UTC
from app.database import Base


class AIEmbedding(Base):
    __tablename__ = "ai_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)
    content_type = Column(String(64), nullable=False, index=True)
    content_id = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=False, index=True)
    text = Column(Text, nullable=False)
    model = Column(String(128), nullable=False, default="gemini-embedding-exp-03-07")
    dimensions = Column(Integer, nullable=False, default=768)
    extra_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("content_type", "content_id", "model", name="uq_ai_embedding_content"),
    )


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("lab_users.id"), nullable=True, index=True)
    session_id = Column(String(128), nullable=False, index=True)
    title = Column(String(256), nullable=True)
    extra_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    messages = relationship(
        "AIConversationMessage", back_populates="conversation", cascade="all, delete-orphan",
    )


class AIConversationMessage(Base):
    __tablename__ = "ai_conversation_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id"), nullable=False, index=True)
    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    extra_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    conversation = relationship("AIConversation", back_populates="messages")


class AIAgentExecution(Base):
    __tablename__ = "ai_agent_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("lab_users.id"), nullable=True)
    session_id = Column(String(128), nullable=True, index=True)
    agent_name = Column(String(128), nullable=False)
    task = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    approval_id = Column(String(64), nullable=True)
    extra_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime(timezone=True), nullable=True)


class AIKnowledgeNode(Base):
    __tablename__ = "ai_knowledge_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_type = Column(String(64), nullable=False, index=True)
    external_id = Column(String(256), nullable=True)
    label = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    aliases = Column(JSONB, nullable=False, default=list)
    properties = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("node_type", "external_id", name="uq_ai_knowledge_node"),)


class AIKnowledgeEdge(Base):
    __tablename__ = "ai_knowledge_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("ai_knowledge_nodes.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("ai_knowledge_nodes.id"), nullable=False, index=True)
    relationship_type = Column(String(128), nullable=False, index=True)
    weight = Column(Float, nullable=False, default=1.0)
    properties = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class AIModelRegistry(Base):
    __tablename__ = "ai_model_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True)
    provider = Column(String(64), nullable=False)
    model_type = Column(String(64), nullable=False)
    version = Column(String(32), nullable=False, default="1.0")
    capabilities = Column(JSONB, nullable=False, default=list)
    config = Column(JSONB, nullable=False, default=dict)
    is_active = Column(Integer, nullable=False, default=1)
    max_tokens = Column(Integer, nullable=True)
    cost_per_1k_input = Column(Float, nullable=True)
    cost_per_1k_output = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class AIEvaluation(Base):
    __tablename__ = "ai_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=True)
    eval_type = Column(String(64), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    score = Column(Float, nullable=True)
    metrics = Column(JSONB, nullable=False, default=dict)
    model = Column(String(128), nullable=False)
    duration_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
