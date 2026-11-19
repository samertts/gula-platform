from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text

from app.database import get_db

logger = logging.getLogger("gula.ai.memory")


@dataclass
class Message:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    token_count: int | None = None
    created_at: float = field(default_factory=time.time)


@dataclass
class Conversation:
    session_id: str
    lab_id: int | None = None
    user_id: int | None = None
    title: str | None = None
    messages: list[Message] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryStore:

    def __init__(self):
        self._sessions: dict[str, Conversation] = {}

    async def create_session(
        self,
        lab_id: int | None = None,
        user_id: int | None = None,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        session_id = str(uuid.uuid4())
        conv = Conversation(
            session_id=session_id,
            lab_id=lab_id,
            user_id=user_id,
            title=title,
            metadata=metadata or {},
        )
        self._sessions[session_id] = conv
        try:
            db = next(get_db())
            try:
                meta_json = json.dumps(metadata or {}, ensure_ascii=False)
                db.execute(
                    text("INSERT INTO ai_conversations (lab_id, user_id, session_id, title, metadata) VALUES (:lab, :uid, :sid, :title, CAST(:meta AS jsonb)) RETURNING id"),
                    {"lab": lab_id, "uid": user_id, "sid": session_id, "title": title, "meta": meta_json},
                )
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("[Memory] DB session create failed: %s", exc)
            finally:
                db.close()
        except Exception:
            pass
        return conv

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        token_count: int | None = None,
    ) -> Message:
        conv = self._sessions.get(session_id)
        if conv is None:
            conv = await self.get_session(session_id)
            if conv is None:
                raise ValueError(f"Session {session_id} not found")

        msg = Message(
            role=role,
            content=content,
            metadata=metadata or {},
            token_count=token_count,
        )
        conv.messages.append(msg)

        try:
            db = next(get_db())
            try:
                meta_json = json.dumps(metadata or {}, ensure_ascii=False)
                db.execute(
                    text("INSERT INTO ai_conversation_messages (conversation_id, role, content, metadata, token_count) VALUES ((SELECT id FROM ai_conversations WHERE session_id = :sid), :role, :content, CAST(:meta AS jsonb), :tokens)"),
                    {"sid": session_id, "role": role, "content": content, "meta": meta_json, "tokens": token_count},
                )
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("[Memory] DB message save failed: %s", exc)
            finally:
                db.close()
        except Exception:
            pass
        return msg

    async def get_session(self, session_id: str) -> Conversation | None:
        if session_id in self._sessions:
            return self._sessions[session_id]
        try:
            db = next(get_db())
        except Exception:
            return None
        try:
            row = db.execute(
                text("SELECT id, lab_id, user_id, session_id, title, metadata FROM ai_conversations WHERE session_id = :sid"),
                {"sid": session_id},
            ).fetchone()
            if row is None:
                return None
            meta = row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata or "{}")
            conv = Conversation(
                session_id=row.session_id,
                lab_id=row.lab_id,
                user_id=row.user_id,
                title=row.title,
                metadata=meta,
            )
            msg_rows = db.execute(
                text("SELECT role, content, metadata, token_count, created_at FROM ai_conversation_messages WHERE conversation_id = :cid ORDER BY created_at ASC"),
                {"cid": row.id},
            ).fetchall()
            for m in msg_rows:
                m_meta = m.metadata if isinstance(m.metadata, dict) else json.loads(m.metadata or "{}")
                conv.messages.append(Message(
                    role=m.role, content=m.content, metadata=m_meta,
                    token_count=m.token_count,
                    created_at=m.created_at.timestamp() if hasattr(m.created_at, "timestamp") else time.time(),
                ))
            self._sessions[session_id] = conv
            return conv
        except Exception as exc:
            logger.error("[Memory] get_session failed: %s", exc)
            return None
        finally:
            db.close()

    def get_recent(self, session_id: str, n: int = 10) -> list[Message]:
        conv = self._sessions.get(session_id)
        if not conv:
            return []
        return conv.messages[-n:]

    def get_history(self, session_id: str, max_tokens: int = 2000) -> str:
        conv = self._sessions.get(session_id)
        if not conv:
            return ""
        lines = []
        total = 0
        for msg in conv.messages:
            words = len(msg.content.split())
            if total + words > max_tokens:
                break
            label = "المستخدم" if msg.role == "user" else "المساعد"
            lines.append(f"{label}: {msg.content}")
            total += words
        return "\n\n".join(lines)

    def list_sessions(self, lab_id: int | None = None, limit: int = 50) -> list[dict[str, Any]]:
        sessions = []
        for conv in self._sessions.values():
            if lab_id is not None and conv.lab_id != lab_id:
                continue
            sessions.append({
                "session_id": conv.session_id,
                "lab_id": conv.lab_id,
                "user_id": conv.user_id,
                "title": conv.title,
                "message_count": len(conv.messages),
                "last_message": conv.messages[-1].content[:100] if conv.messages else None,
                "created_at": conv.messages[0].created_at if conv.messages else None,
            })
        return sessions[:limit]

    def delete_session(self, session_id: str) -> bool:
        self._sessions.pop(session_id, None)
        try:
            db = next(get_db())
            try:
                db.execute(text("DELETE FROM ai_conversations WHERE session_id = :sid"), {"sid": session_id})
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
        except Exception:
            pass
        return True


memory_store = MemoryStore()
