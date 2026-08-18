"""AI Platform: vector store, conversations, agents, knowledge graph, governance

Revision ID: 20260719_0001
Revises: 20260716_0016
Create Date: 2026-07-19

"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects import postgresql

revision: str = "20260719_0001"
down_revision: str = "20260716_0016"
branch_labels: str | None = None
depends_on: str | None = None


def _has_table(name: str) -> bool:
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)


def _has_column(table: str, column: str) -> bool:
    if context.is_offline_mode():
        return False
    from sqlalchemy import inspect

    insp = inspect(op.get_bind())
    return any(c["name"] == column for c in insp.get_columns(table))


def _has_index(table: str, index: str) -> bool:
    if context.is_offline_mode():
        return False
    from sqlalchemy import inspect

    insp = inspect(op.get_bind())
    return any(i["name"] == index for i in insp.get_indexes(table))


def _enable_pgvector() -> None:
    if context.is_offline_mode():
        return
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return
    try:
        result = conn.execute(sa.text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchone()
        if result is None:
            from sqlalchemy import create_engine as _ce
            url = str(conn.engine.url)
            _tmp = _ce(url).connect()
            _tmp.execution_options(isolation_level="AUTOCOMMIT")
            _tmp.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
            _tmp.close()
    except Exception:
        pass


def upgrade() -> None:
    _enable_pgvector()

    if not _has_table("ai_embeddings"):
        op.create_table(
            "ai_embeddings",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id"), nullable=False, index=True),
            sa.Column("content_type", sa.String(64), nullable=False, index=True),
            sa.Column("content_id", sa.Integer(), nullable=True),
            sa.Column("content_hash", sa.String(64), nullable=False, index=True),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("embedding", sa.JSON() if op.get_bind().dialect.name != "postgresql" else sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.ARRAY(sa.Float()), nullable=True),
            sa.Column("model", sa.String(128), nullable=False, server_default="gemini-embedding-exp-03-07"),
            sa.Column("dimensions", sa.Integer(), nullable=False, server_default="768"),
            sa.Column("metadata", sa.JSON() if op.get_bind().dialect.name != "postgresql" else sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("content_type", "content_id", "model", name="uq_ai_embedding_content"),
        )

    if not _has_table("ai_conversations"):
        op.create_table(
            "ai_conversations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id"), nullable=False, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("lab_users.id"), nullable=True, index=True),
            sa.Column("session_id", sa.String(128), nullable=False, index=True),
            sa.Column("title", sa.String(256), nullable=True),
            sa.Column("metadata", sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("ai_conversation_messages"):
        op.create_table(
            "ai_conversation_messages",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("ai_conversations.id"), nullable=False, index=True),
            sa.Column("role", sa.String(32), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("metadata", sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("token_count", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("ai_agent_executions"):
        op.create_table(
            "ai_agent_executions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id"), nullable=False, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("lab_users.id"), nullable=True),
            sa.Column("session_id", sa.String(128), nullable=True, index=True),
            sa.Column("agent_name", sa.String(128), nullable=False),
            sa.Column("task", sa.Text(), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
            sa.Column("result", sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.JSONB(), nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("duration_ms", sa.Float(), nullable=True),
            sa.Column("token_count", sa.Integer(), nullable=True),
            sa.Column("cost_usd", sa.Float(), nullable=True),
            sa.Column("approval_id", sa.String(64), nullable=True),
            sa.Column("metadata", sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("ai_knowledge_nodes"):
        op.create_table(
            "ai_knowledge_nodes",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("node_type", sa.String(64), nullable=False, index=True),
            sa.Column("external_id", sa.String(256), nullable=True),
            sa.Column("label", sa.String(512), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("aliases", sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("properties", sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("node_type", "external_id", name="uq_ai_knowledge_node"),
        )

    if not _has_table("ai_knowledge_edges"):
        op.create_table(
            "ai_knowledge_edges",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("source_id", sa.Integer(), sa.ForeignKey("ai_knowledge_nodes.id"), nullable=False, index=True),
            sa.Column("target_id", sa.Integer(), sa.ForeignKey("ai_knowledge_nodes.id"), nullable=False, index=True),
            sa.Column("relationship", sa.String(128), nullable=False, index=True),
            sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
            sa.Column("properties", sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("ai_model_registry"):
        op.create_table(
            "ai_model_registry",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(128), nullable=False, unique=True),
            sa.Column("provider", sa.String(64), nullable=False),
            sa.Column("model_type", sa.String(64), nullable=False),
            sa.Column("version", sa.String(32), nullable=False, server_default="1.0"),
            sa.Column("capabilities", sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("config", sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("max_tokens", sa.Integer(), nullable=True),
            sa.Column("cost_per_1k_input", sa.Float(), nullable=True),
            sa.Column("cost_per_1k_output", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("ai_evaluations"):
        op.create_table(
            "ai_evaluations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id"), nullable=True),
            sa.Column("eval_type", sa.String(64), nullable=False),
            sa.Column("prompt", sa.Text(), nullable=False),
            sa.Column("response", sa.Text(), nullable=False),
            sa.Column("score", sa.Float(), nullable=True),
            sa.Column("metrics", sa.JSON() if op.get_bind().dialect.name != "postgresql" else postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("model", sa.String(128), nullable=False),
            sa.Column("duration_ms", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    tables = [
        "ai_evaluations",
        "ai_model_registry",
        "ai_knowledge_edges",
        "ai_knowledge_nodes",
        "ai_agent_executions",
        "ai_conversation_messages",
        "ai_conversations",
        "ai_embeddings",
    ]
    for table in tables:
        if _has_table(table):
            op.drop_table(table)
