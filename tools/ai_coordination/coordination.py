from __future__ import annotations

import json
import sqlite3
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class CoordinationError(RuntimeError):
    """Base error for coordination policy violations."""


class CoordinationConflict(CoordinationError):
    """Raised when an intent overlaps another active agent intent."""


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    provider: str
    model: str
    session_id: str
    branch: str
    commit: str


@dataclass(frozen=True)
class TaskClaim:
    task_id: str
    agent_id: str
    lease_id: str
    expires_at: float


@dataclass(frozen=True)
class ChangeIntent:
    intent_id: str
    task_id: str
    agent_id: str
    paths: tuple[str, ...]
    operation: str
    base_commit: str
    status: str
    created_at: float


_SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
  agent_id TEXT PRIMARY KEY, provider TEXT NOT NULL, model TEXT NOT NULL,
  session_id TEXT NOT NULL, branch TEXT NOT NULL, commit_hash TEXT NOT NULL,
  last_seen REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
  task_id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
  status TEXT NOT NULL, created_by TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS claims (
  task_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, lease_id TEXT UNIQUE NOT NULL,
  expires_at REAL NOT NULL, claimed_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS intents (
  intent_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, agent_id TEXT NOT NULL,
  paths_json TEXT NOT NULL, operation TEXT NOT NULL, base_commit TEXT NOT NULL,
  status TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
  message_id TEXT PRIMARY KEY, sender_id TEXT NOT NULL, recipient_id TEXT,
  kind TEXT NOT NULL, body_json TEXT NOT NULL, created_at REAL NOT NULL,
  read_at REAL
);
CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, actor_id TEXT NOT NULL,
  payload_json TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_recipient_read ON messages(recipient_id, read_at);
CREATE INDEX IF NOT EXISTS idx_intents_status ON intents(status);
"""


class AgentCoordinator:
    """Local, provider-neutral coordination store.

    SQLite transactions make task claims and intent checks atomic. The store is
    deliberately separate from the clinical database: it coordinates code work,
    never clinical data, credentials, or production mutations.
    """

    def __init__(self, database: str | Path = ".gula/coordination.sqlite3") -> None:
        self.database = str(database)
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def _event(self, db: sqlite3.Connection, event_type: str, actor_id: str, payload: dict[str, Any]) -> None:
        db.execute(
            "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), event_type, actor_id, json.dumps(payload, sort_keys=True), time.time()),
        )

    def register_agent(self, identity: AgentIdentity) -> None:
        if identity.branch in {"main", "master"}:
            raise CoordinationError("agents must work on a non-protected branch")
        now = time.time()
        with self._connect() as db:
            db.execute(
                "INSERT INTO agents VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(agent_id) DO UPDATE SET provider=excluded.provider, model=excluded.model, "
                "session_id=excluded.session_id, branch=excluded.branch, commit_hash=excluded.commit_hash, last_seen=excluded.last_seen",
                (identity.agent_id, identity.provider, identity.model, identity.session_id, identity.branch, identity.commit, now),
            )
            self._event(db, "agent_registered", identity.agent_id, {"branch": identity.branch, "commit": identity.commit})

    def create_task(self, title: str, description: str, created_by: str) -> str:
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        with self._connect() as db:
            db.execute("INSERT INTO tasks VALUES (?, ?, ?, 'open', ?, ?)", (task_id, title, description, created_by, time.time()))
            self._event(db, "task_created", created_by, {"task_id": task_id, "title": title})
        return task_id

    def claim_task(self, task_id: str, agent_id: str, lease_seconds: int = 900) -> TaskClaim:
        if lease_seconds < 30 or lease_seconds > 86_400:
            raise CoordinationError("lease_seconds must be between 30 and 86400")
        now = time.time()
        expires = now + lease_seconds
        lease_id = f"lease-{uuid.uuid4().hex}"
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            task = db.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if task is None:
                db.rollback()
                raise CoordinationError("task not found")
            db.execute("DELETE FROM claims WHERE expires_at <= ?", (now,))
            existing = db.execute("SELECT agent_id FROM claims WHERE task_id = ?", (task_id,)).fetchone()
            if existing is not None and existing["agent_id"] != agent_id:
                db.rollback()
                raise CoordinationConflict(f"task already claimed by {existing['agent_id']}")
            db.execute("INSERT OR REPLACE INTO claims VALUES (?, ?, ?, ?, ?)", (task_id, agent_id, lease_id, expires, now))
            db.execute("UPDATE tasks SET status = 'claimed' WHERE task_id = ?", (task_id,))
            self._event(db, "task_claimed", agent_id, {"task_id": task_id, "lease_id": lease_id, "expires_at": expires})
            db.commit()
        return TaskClaim(task_id, agent_id, lease_id, expires)

    def release_task(self, claim: TaskClaim, status: str = "done") -> None:
        if status not in {"open", "done", "blocked", "cancelled"}:
            raise CoordinationError("invalid task status")
        with self._connect() as db:
            row = db.execute("SELECT agent_id FROM claims WHERE task_id = ? AND lease_id = ?", (claim.task_id, claim.lease_id)).fetchone()
            if row is None or row["agent_id"] != claim.agent_id:
                raise CoordinationError("invalid or expired lease")
            db.execute("DELETE FROM claims WHERE task_id = ?", (claim.task_id,))
            db.execute("UPDATE tasks SET status = ? WHERE task_id = ?", (status, claim.task_id))
            self._event(db, "task_released", claim.agent_id, {"task_id": claim.task_id, "status": status})

    @staticmethod
    def _normalise_path(path: str) -> str:
        value = path.replace("\\", "/").lstrip("./")
        if not value or value.startswith("/") or ".." in Path(value).parts:
            raise CoordinationError(f"invalid repository path: {path}")
        return value

    @staticmethod
    def _paths_overlap(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
        for a in left:
            for b in right:
                if a == b or a.startswith(f"{b}/") or b.startswith(f"{a}/"):
                    return True
        return False

    def declare_intent(self, task_id: str, agent_id: str, paths: list[str], operation: str, base_commit: str) -> ChangeIntent:
        if operation not in {"add", "modify", "delete", "rename", "review"}:
            raise CoordinationError("invalid intent operation")
        clean_paths = tuple(sorted({self._normalise_path(path) for path in paths}))
        if not clean_paths:
            raise CoordinationError("at least one repository path is required")
        now = time.time()
        with self._connect() as db:
            active = db.execute("SELECT * FROM intents WHERE status = 'active'").fetchall()
            for row in active:
                other = tuple(json.loads(row["paths_json"]))
                if row["agent_id"] != agent_id and self._paths_overlap(clean_paths, other):
                    raise CoordinationConflict(f"path overlap with intent {row['intent_id']} owned by {row['agent_id']}")
            intent_id = f"intent-{uuid.uuid4().hex[:12]}"
            db.execute("INSERT INTO intents VALUES (?, ?, ?, ?, ?, ?, 'active', ?)", (intent_id, task_id, agent_id, json.dumps(clean_paths), operation, base_commit, now))
            self._event(db, "intent_declared", agent_id, {"intent_id": intent_id, "task_id": task_id, "paths": clean_paths, "operation": operation})
        return ChangeIntent(intent_id, task_id, agent_id, clean_paths, operation, base_commit, "active", now)

    def close_intent(self, intent_id: str, agent_id: str, status: str = "completed") -> None:
        if status not in {"completed", "cancelled", "conflicted"}:
            raise CoordinationError("invalid intent status")
        with self._connect() as db:
            changed = db.execute("UPDATE intents SET status = ? WHERE intent_id = ? AND agent_id = ? AND status = 'active'", (status, intent_id, agent_id)).rowcount
            if not changed:
                raise CoordinationError("intent not found or not owned by agent")
            self._event(db, "intent_closed", agent_id, {"intent_id": intent_id, "status": status})

    def send_message(self, sender_id: str, body: dict[str, Any], recipient_id: str | None = None, kind: str = "status") -> str:
        if kind not in {"status", "question", "answer", "warning", "handoff"}:
            raise CoordinationError("invalid message kind")
        message_id = f"msg-{uuid.uuid4().hex[:12]}"
        with self._connect() as db:
            db.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, NULL)", (message_id, sender_id, recipient_id, kind, json.dumps(body, sort_keys=True), time.time()))
            self._event(db, "message_sent", sender_id, {"message_id": message_id, "recipient_id": recipient_id, "kind": kind})
        return message_id

    def receive_messages(self, agent_id: str, limit: int = 50) -> list[dict[str, Any]]:
        bounded = max(1, min(limit, 200))
        with self._connect() as db:
            rows = db.execute("SELECT * FROM messages WHERE read_at IS NULL AND (recipient_id IS NULL OR recipient_id = ?) ORDER BY created_at LIMIT ?", (agent_id, bounded)).fetchall()
            now = time.time()
            for row in rows:
                db.execute("UPDATE messages SET read_at = ? WHERE message_id = ?", (now, row["message_id"]))
        return [{"message_id": row["message_id"], "sender_id": row["sender_id"], "recipient_id": row["recipient_id"], "kind": row["kind"], "body": json.loads(row["body_json"]), "created_at": row["created_at"]} for row in rows]

    def status(self) -> dict[str, Any]:
        with self._connect() as db:
            db.execute("DELETE FROM claims WHERE expires_at <= ?", (time.time(),))
            counts = {}
            for table in ("agents", "tasks", "claims", "intents", "messages", "events"):
                counts[table] = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            active = db.execute("SELECT intent_id, task_id, agent_id, paths_json, operation, base_commit FROM intents WHERE status = 'active' ORDER BY created_at").fetchall()
        return {"counts": counts, "active_intents": [{"intent_id": r[0], "task_id": r[1], "agent_id": r[2], "paths": json.loads(r[3]), "operation": r[4], "base_commit": r[5]} for r in active]}


def git_context() -> tuple[str, str]:
    def run(*args: str) -> str:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    try:
        branch = run("branch", "--show-current")
        commit = run("rev-parse", "HEAD")
        return branch or "detached", commit
    except (OSError, subprocess.CalledProcessError):
        return "unknown", "unknown"
