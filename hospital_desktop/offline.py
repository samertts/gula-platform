from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

from api_client import ApiClient, NetworkError

logger = logging.getLogger("nhdw.offline")

LOCAL_SCHEMA = {
    "patients": """
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            mrn TEXT,
            national_id TEXT,
            name_ar TEXT,
            name_en TEXT,
            date_of_birth TEXT,
            gender TEXT,
            phone TEXT,
            address TEXT,
            department TEXT,
            status TEXT DEFAULT 'active',
            data TEXT,
            updated_at TEXT,
            deleted INTEGER DEFAULT 0
        )
    """,
    "admissions": """
        CREATE TABLE IF NOT EXISTS admissions (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            patient_name TEXT,
            department TEXT,
            room TEXT,
            bed TEXT,
            doctor TEXT,
            diagnosis TEXT,
            admission_date TEXT,
            admission_type TEXT,
            status TEXT,
            data TEXT,
            updated_at TEXT,
            deleted INTEGER DEFAULT 0
        )
    """,
    "visits": """
        CREATE TABLE IF NOT EXISTS visits (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            visit_type TEXT,
            department TEXT,
            check_in_time TEXT,
            status TEXT,
            priority TEXT,
            data TEXT,
            updated_at TEXT,
            deleted INTEGER DEFAULT 0
        )
    """,
    "clinical_tasks": """
        CREATE TABLE IF NOT EXISTS clinical_tasks (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            patient_name TEXT,
            task_type TEXT,
            description TEXT,
            assignee TEXT,
            status TEXT,
            priority TEXT,
            due_date TEXT,
            data TEXT,
            updated_at TEXT,
            deleted INTEGER DEFAULT 0
        )
    """,
    "messages": """
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            subject TEXT,
            body TEXT,
            sender_id TEXT,
            sender_name TEXT,
            recipient_id TEXT,
            recipient_name TEXT,
            status TEXT,
            sent_at TEXT,
            data TEXT,
            updated_at TEXT,
            deleted INTEGER DEFAULT 0
        )
    """,
    "alerts": """
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            type TEXT,
            severity TEXT,
            title TEXT,
            message TEXT,
            patient_id TEXT,
            status TEXT,
            created_at TEXT,
            acknowledged_by TEXT,
            resolved_at TEXT,
            data TEXT,
            updated_at TEXT,
            deleted INTEGER DEFAULT 0
        )
    """,
    "sync_log": """
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT,
            entity_id TEXT,
            action TEXT,
            data TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            synced_at TEXT,
            error TEXT
        )
    """,
    "metadata": """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """,
    "department_occupancy": """
        CREATE TABLE IF NOT EXISTS department_occupancy (
            department TEXT PRIMARY KEY,
            total_beds INTEGER DEFAULT 0,
            occupied_beds INTEGER DEFAULT 0,
            available_beds INTEGER DEFAULT 0,
            data TEXT,
            updated_at TEXT
        )
    """,
}

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_patients_mrn ON patients(mrn)",
    "CREATE INDEX IF NOT EXISTS idx_patients_status ON patients(status)",
    "CREATE INDEX IF NOT EXISTS idx_admissions_patient ON admissions(patient_id)",
    "CREATE INDEX IF NOT EXISTS idx_admissions_status ON admissions(status)",
    "CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id)",
    "CREATE INDEX IF NOT EXISTS idx_visits_status ON visits(status)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON clinical_tasks(assignee)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON clinical_tasks(status)",
    "CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)",
    "CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_log(status)",
]


class OfflineDatabase:
    def __init__(self, db_path: str | Path):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self.init_schema()

    def init_schema(self):
        with self._lock:
            for table_ddl in LOCAL_SCHEMA.values():
                self._conn.execute(table_ddl)
            for idx in INDEXES:
                self._conn.execute(idx)
            self._conn.commit()

    def save(self, entity_type: str, data: dict) -> dict:
        table = entity_type
        if table not in LOCAL_SCHEMA:
            raise ValueError(f"Unknown entity type: {entity_type}")

        entity_id = data.get("id", "")
        if not entity_id:
            raise ValueError("Entity must have an 'id' field")

        now = datetime.now(UTC).isoformat()
        data["updated_at"] = now

        with self._lock:
            existing = self._conn.execute(
                f"SELECT id FROM {table} WHERE id = ?", (entity_id,)
            ).fetchone()

            placeholders = ", ".join(f":{k}" for k in data)
            columns = ", ".join(data.keys())
            values = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
                      for k, v in data.items()}

            if existing:
                set_clause = ", ".join(f"{k} = :{k}" for k in data)
                self._conn.execute(
                    f"UPDATE {table} SET {set_clause} WHERE id = :id",
                    values,
                )
            else:
                self._conn.execute(
                    f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                    values,
                )
            self._conn.commit()

        self._log_change(entity_type, entity_id, "upsert", data)
        return data

    def get(self, entity_type: str, entity_id: str) -> dict | None:
        table = entity_type
        with self._lock:
            row = self._conn.execute(
                f"SELECT * FROM {table} WHERE id = ? AND deleted = 0",
                (entity_id,),
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def query(self, entity_type: str, filters: dict | None = None) -> list[dict]:
        table = entity_type
        where_clause = "deleted = 0"
        params = []

        if filters:
            for key, value in filters.items():
                if key == "search":
                    where_clause += " AND (name_ar LIKE ? OR name_en LIKE ? OR mrn LIKE ? OR phone LIKE ?)"
                    term = f"%{value}%"
                    params.extend([term, term, term, term])
                elif key == "department":
                    where_clause += " AND department = ?"
                    params.append(value)
                elif key == "status":
                    where_clause += " AND status = ?"
                    params.append(value)
                elif key == "date_from":
                    where_clause += " AND updated_at >= ?"
                    params.append(value)
                elif key == "date_to":
                    where_clause += " AND updated_at <= ?"
                    params.append(value)
                elif key == "patient_id":
                    where_clause += " AND patient_id = ?"
                    params.append(value)

        with self._lock:
            rows = self._conn.execute(
                f"SELECT * FROM {table} WHERE {where_clause} ORDER BY updated_at DESC",
                params,
            ).fetchall()
        return [dict(r) for r in rows]

    def delete(self, entity_type: str, entity_id: str):
        table = entity_type
        with self._lock:
            self._conn.execute(
                f"UPDATE {table} SET deleted = 1, updated_at = ? WHERE id = ?",
                (datetime.now(UTC).isoformat(), entity_id),
            )
            self._conn.commit()
        self._log_change(entity_type, entity_id, "delete", {})

    def _log_change(self, entity_type: str, entity_id: str, action: str, data: dict):
        now = datetime.now(UTC).isoformat()
        with self._lock:
            self._conn.execute(
                "INSERT INTO sync_log (entity_type, entity_id, action, data, status, created_at) "
                "VALUES (?, ?, ?, ?, 'pending', ?)",
                (entity_type, entity_id, action, json.dumps(data, ensure_ascii=False), now),
            )
            self._conn.commit()

    def get_pending_changes(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM sync_log WHERE status = 'pending' ORDER BY created_at ASC"
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_synced(self, sync_id: int):
        now = datetime.now(UTC).isoformat()
        with self._lock:
            self._conn.execute(
                "UPDATE sync_log SET status = 'synced', synced_at = ? WHERE id = ?",
                (now, sync_id),
            )
            self._conn.commit()

    def mark_failed(self, sync_id: int, error: str):
        with self._lock:
            self._conn.execute(
                "UPDATE sync_log SET status = 'failed', error = ? WHERE id = ?",
                (error, sync_id),
            )
            self._conn.commit()

    def set_metadata(self, key: str, value: str):
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                (key, value),
            )
            self._conn.commit()

    def get_metadata(self, key: str, default: str = "") -> str:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM metadata WHERE key = ?", (key,)
            ).fetchone()
        return row["value"] if row else default

    def close(self):
        self._conn.close()


class SyncEngine:
    def __init__(self, api_client: ApiClient, offline_db: OfflineDatabase):
        self._api = api_client
        self._db = offline_db
        self._timer: threading.Timer | None = None
        self._running = False
        self._sync_interval = 60
        self._listeners: list = []

    def add_listener(self, callback):
        self._listeners.append(callback)

    def _notify(self, status: str, message: str = ""):
        for cb in self._listeners:
            try:
                cb(status, message)
            except Exception:
                pass

    def sync_all(self) -> dict:
        results = {"synced": 0, "failed": 0, "errors": []}
        try:
            self._notify("syncing", "Starting full sync...")

            endpoints = {
                "patients": "patients?limit=1000",
                "admissions": "admissions?limit=1000",
                "visits": "visits?limit=1000",
                "clinical_tasks": "tasks?limit=1000",
                "messages": "messages?limit=1000",
                "alerts": "alerts?limit=1000",
            }

            for entity_type, endpoint in endpoints.items():
                try:
                    data = self._api.get(endpoint)
                    items = data if isinstance(data, list) else data.get("items", data.get("data", []))
                    count = 0
                    for item in items:
                        try:
                            self._db.save(entity_type, item)
                            count += 1
                        except Exception as e:
                            results["failed"] += 1
                            results["errors"].append(str(e))
                    results["synced"] += count
                    logger.info("Synced %d %s", count, entity_type)
                except Exception as e:
                    logger.warning("Failed to sync %s: %s", entity_type, e)
                    results["failed"] += 1
                    results["errors"].append(f"{entity_type}: {e}")

            self._db.set_metadata("last_sync", datetime.now(UTC).isoformat())
            self._notify("success", f"Synced {results['synced']} items")
        except Exception as e:
            self._notify("error", str(e))
            results["errors"].append(str(e))

        self.push_changes()
        return results

    def delta_sync(self, since_timestamp: str | None = None) -> dict:
        if since_timestamp is None:
            since_timestamp = self._db.get_metadata("last_sync", "")
        if not since_timestamp:
            return self.sync_all()

        results = {"synced": 0, "failed": 0, "errors": []}
        try:
            self._notify("syncing", "Incremental sync...")
            endpoints = {
                "patients": f"patients/changes?since={since_timestamp}",
                "admissions": f"admissions/changes?since={since_timestamp}",
            }

            for entity_type, endpoint in endpoints.items():
                try:
                    data = self._api.get(endpoint)
                    items = data if isinstance(data, list) else data.get("items", data.get("data", []))
                    for item in items:
                        try:
                            self._db.save(entity_type, item)
                            results["synced"] += 1
                        except Exception:
                            results["failed"] += 1
                    logger.info("Delta synced %d %s", len(items), entity_type)
                except Exception as e:
                    logger.warning("Delta sync failed for %s: %s", entity_type, e)

            self._db.set_metadata("last_sync", datetime.now(UTC).isoformat())
            self._notify("success", f"Delta sync: {results['synced']} updates")
        except Exception as e:
            self._notify("error", str(e))

        self.push_changes()
        return results

    def push_changes(self) -> dict:
        results = {"pushed": 0, "failed": 0}
        changes = self._db.get_pending_changes()
        if not changes:
            return results

        self._notify("syncing", f"Pushing {len(changes)} changes...")

        for change in changes:
            try:
                data = json.loads(change["data"]) if isinstance(change["data"], str) else {}
                entity_type = change["entity_type"]
                action = change["action"]

                endpoint_map = {
                    "patients": "patients",
                    "admissions": "admissions",
                    "visits": "visits",
                    "clinical_tasks": "tasks",
                    "messages": "messages",
                    "alerts": "alerts",
                }
                endpoint = endpoint_map.get(entity_type)
                if not endpoint:
                    continue

                if action == "delete":
                    self._api.delete(f"{endpoint}/{change['entity_id']}")
                elif action == "upsert":
                    if change.get("id"):
                        self._api.put(f"{endpoint}/{change['entity_id']}", data)
                    else:
                        self._api.post(endpoint, data)

                self._db.mark_synced(change["id"])
                results["pushed"] += 1
            except NetworkError:
                self._db.mark_failed(change["id"], "Network error")
                results["failed"] += 1
                break
            except Exception as e:
                self._db.mark_failed(change["id"], str(e))
                results["failed"] += 1

        return results

    def resolve_conflict(self, local: dict, remote: dict) -> dict:
        local_time = local.get("updated_at", "")
        remote_time = remote.get("updated_at", "")
        if local_time >= remote_time:
            return local
        return remote

    def get_sync_status(self) -> dict:
        pending = len(self._db.get_pending_changes())
        return {
            "last_sync": self._db.get_metadata("last_sync", "Never"),
            "pending_changes": pending,
            "is_syncing": self._running,
            "online": self._api.is_authenticated,
        }

    def start_background_sync(self, interval_seconds: int = 60):
        self._sync_interval = interval_seconds
        self._running = True
        self._schedule_next()

    def _schedule_next(self):
        if not self._running:
            return
        self._timer = threading.Timer(self._sync_interval, self._do_background_sync)
        self._timer.daemon = True
        self._timer.start()

    def _do_background_sync(self):
        if not self._running:
            return
        try:
            if self._api.is_authenticated:
                self.delta_sync()
        except Exception as e:
            logger.warning("Background sync error: %s", e)
        self._schedule_next()

    def stop_background_sync(self):
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None
