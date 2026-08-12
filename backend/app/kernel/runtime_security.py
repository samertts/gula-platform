from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

from app._compat import StrEnum
from app.kernel.config.secrets import SecretsManager

logger = logging.getLogger("gula.kernel.runtime_security")


class IsolationLevel(StrEnum):
    NONE = "none"
    PROCESS = "process"
    CONTAINER = "container"
    SANDBOX = "sandbox"


@dataclass
class ResourceLimit:
    cpu_quota: float = 0.5
    memory_limit_mb: int = 256
    max_threads: int = 10
    max_fds: int = 64
    max_network_conn: int = 5
    max_storage_mb: int = 100
    timeout_seconds: int = 30


@dataclass
class SecureExecutionContext:
    id: str = ""
    name: str = ""
    isolation_level: IsolationLevel = IsolationLevel.PROCESS
    resource_limits: ResourceLimit = field(default_factory=ResourceLimit)
    allowed_syscalls: list[str] = field(default_factory=lambda: ["read", "write", "open", "close", "stat", "fstat"])
    blocked_paths: list[str] = field(default_factory=list)
    environment_vars: list[str] = field(default_factory=list)
    started_at: float = 0.0
    is_active: bool = False


class RuntimeSecureIsolation:
    def __init__(self):
        self._contexts: dict[str, SecureExecutionContext] = {}
        self._lock = Lock()
        self._audit_log: list[dict[str, Any]] = []

    def create_context(
        self,
        name: str,
        isolation_level: IsolationLevel = IsolationLevel.PROCESS,
        resource_limits: ResourceLimit | None = None,
    ) -> SecureExecutionContext:
        ctx_id = f"sec-{int(time.time())}-{len(self._contexts)}"
        ctx = SecureExecutionContext(
            id=ctx_id,
            name=name,
            isolation_level=isolation_level,
            resource_limits=resource_limits or ResourceLimit(),
        )
        with self._lock:
            self._contexts[ctx_id] = ctx
        logger.info("Secure context created", extra={"id": ctx_id, "name": name, "isolation": isolation_level.value})
        return ctx

    def start_context(self, ctx_id: str) -> bool:
        ctx = self._contexts.get(ctx_id)
        if not ctx:
            return False
        ctx.started_at = time.time()
        ctx.is_active = True
        self._audit("context_started", {"id": ctx_id, "name": ctx.name})
        return True

    def stop_context(self, ctx_id: str) -> bool:
        ctx = self._contexts.get(ctx_id)
        if not ctx:
            return False
        ctx.is_active = False
        self._audit("context_stopped", {"id": ctx_id, "name": ctx.name})
        return True

    def validate_operation(self, ctx_id: str, operation: str, path: str = "") -> bool:
        ctx = self._contexts.get(ctx_id)
        if not ctx or not ctx.is_active:
            return False
        if path:
            for blocked in ctx.blocked_paths:
                if path.startswith(blocked):
                    self._audit("blocked_path_access", {"ctx": ctx_id, "path": path, "blocked": blocked})
                    return False
        return True

    def get_active_contexts(self) -> list[SecureExecutionContext]:
        return [c for c in self._contexts.values() if c.is_active]

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_contexts": len(self._contexts),
            "active_contexts": len(self.get_active_contexts()),
            "audit_entries": len(self._audit_log),
        }

    def _audit(self, event: str, details: dict[str, Any]) -> None:
        self._audit_log.append({
            "timestamp": time.time(),
            "event": event,
            **details,
        })
        if len(self._audit_log) > 500:
            self._audit_log.pop(0)


class SecretInjector:
    def __init__(self, secrets_manager: SecretsManager | None = None):
        self._secrets_manager = secrets_manager or SecretsManager()
        self._injected: dict[str, dict[str, str]] = {}
        self._lock = Lock()

    def inject(self, target: str, secrets: dict[str, str]) -> int:
        count = 0
        with self._lock:
            if target not in self._injected:
                self._injected[target] = {}
            for key, value in secrets.items():
                env_key = f"{target.upper()}_{key.upper()}"
                os.environ[env_key] = value
                self._injected[target][key] = env_key
                count += 1
        logger.info("Secrets injected", extra={"target": target, "count": count})
        return count

    def inject_from_vault(self, target: str, vault_path: str) -> int:
        try:
            secrets = self._secrets_manager.get_secrets(vault_path)
            return self.inject(target, secrets)
        except Exception as exc:
            logger.error("Vault injection failed", extra={"target": target, "path": vault_path, "error": str(exc)})
            return 0

    def revoke(self, target: str) -> int:
        count = 0
        with self._lock:
            if target in self._injected:
                for _key, env_key in self._injected[target].items():
                    os.environ.pop(env_key, None)
                    count += 1
                del self._injected[target]
        logger.info("Secrets revoked", extra={"target": target, "count": count})
        return count

    def list_injected(self) -> dict[str, list[str]]:
        return {t: list(keys.keys()) for t, keys in self._injected.items()}


class RuntimeAttestation:
    def __init__(self):
        self._known_checksums: dict[str, str] = {}
        self._behavior_baseline: dict[str, dict[str, Any]] = {}
        self._violations: list[dict[str, Any]] = []

    def record_checksum(self, path: str) -> str:
        try:
            content = Path(path).read_bytes()
            checksum = hashlib.sha256(content).hexdigest()
            self._known_checksums[path] = checksum
            return checksum
        except (OSError, FileNotFoundError) as exc:
            logger.error("Checksum failed", extra={"path": path, "error": str(exc)})
            return ""

    def verify_checksum(self, path: str) -> bool:
        known = self._known_checksums.get(path)
        if not known:
            return True
        try:
            content = Path(path).read_bytes()
            current = hashlib.sha256(content).hexdigest()
            return current == known
        except (OSError, FileNotFoundError):
            return False

    def verify_multiple(self, paths: list[str]) -> dict[str, bool]:
        return {p: self.verify_checksum(p) for p in paths}

    def record_behavior_baseline(self, component: str, baseline: dict[str, Any]) -> None:
        self._behavior_baseline[component] = baseline
        logger.info("Behavior baseline recorded", extra={"component": component})

    def detect_anomaly(self, component: str, current: dict[str, Any]) -> bool:
        baseline = self._behavior_baseline.get(component)
        if not baseline:
            return False
        anomalies = []
        for key, expected in baseline.items():
            actual = current.get(key)
            if actual is not None and expected is not None:
                if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                    deviation = abs(actual - expected) / max(abs(expected), 1) * 100
                    if deviation > 50:
                        anomalies.append({"key": key, "expected": expected, "actual": actual, "deviation_pct": round(deviation, 1)})
        if anomalies:
            self._violations.append({"timestamp": time.time(), "component": component, "anomalies": anomalies})
            return True
        return False

    def get_attestation_report(self) -> dict[str, Any]:
        verified = {p: self.verify_checksum(p) for p in self._known_checksums}
        return {
            "integrity": {
                "files_known": len(self._known_checksums),
                "files_verified": sum(1 for v in verified.values() if v),
                "files_tampered": sum(1 for v in verified.values() if not v),
            },
            "behavior": {
                "baselines": len(self._behavior_baseline),
                "violations": len(self._violations),
            },
        }

    def get_stats(self) -> dict[str, Any]:
        return {
            "checksums_recorded": len(self._known_checksums),
            "baselines_recorded": len(self._behavior_baseline),
            "violations_detected": len(self._violations),
        }
