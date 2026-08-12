from __future__ import annotations

from pathlib import Path

from . import DimensionEvaluator, DimensionResult


class OfflineEvaluator(DimensionEvaluator):
    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        sync_mechanism = self._check_sync_mechanism(target)
        self._add_evidence(
            "sync_mechanism",
            value=sync_mechanism,
            source="AST scan",
            passed=sync_mechanism,
        )
        if not sync_mechanism:
            self._add_remediation(
                "Implement offline sync mechanism (Service Worker / background sync)",
                severity="high",
                effort="12h",
            )

        conflict_resolution = self._check_conflict_resolution(target)
        self._add_evidence(
            "conflict_resolution",
            value=conflict_resolution,
            source="AST scan",
            passed=conflict_resolution,
        )
        if not conflict_resolution:
            self._add_remediation(
                "Add conflict resolution strategy (last-write-wins / CRDT / operational transform)",
                severity="high",
                effort="8h",
            )

        indexed_db = self._check_indexed_db(target)
        self._add_evidence(
            "indexed_db_usage",
            value=indexed_db,
            source="Frontend files",
            passed=indexed_db,
        )
        if not indexed_db:
            self._add_remediation(
                "Use IndexedDB or localStorage for client-side data persistence",
                severity="medium",
                effort="4h",
            )

        service_worker = self._check_service_worker(target)
        self._add_evidence(
            "service_worker",
            value=service_worker,
            source="Frontend files",
            passed=service_worker,
        )
        if not service_worker:
            self._add_remediation(
                "Register a Service Worker for offline caching and background sync",
                severity="medium",
                effort="6h",
            )

        delta_sync = self._check_delta_sync(target)
        self._add_evidence(
            "delta_sync",
            value=delta_sync,
            source="AST scan",
            passed=delta_sync,
        )
        if not delta_sync:
            self._add_remediation(
                "Implement delta sync to transfer only changed records",
                severity="medium",
                effort="6h",
            )

        queue_mechanism = self._check_queue_mechanism(target)
        self._add_evidence(
            "offline_queue",
            value=queue_mechanism,
            source="AST scan",
            passed=queue_mechanism,
        )
        if not queue_mechanism:
            self._add_remediation(
                "Add offline mutation queue that replays on reconnection",
                severity="medium",
                effort="5h",
            )

        retry_logic = self._check_retry_logic(target)
        self._add_evidence(
            "sync_retry_logic",
            value=retry_logic,
            source="AST scan",
            passed=retry_logic,
        )
        if not retry_logic:
            self._add_remediation(
                "Add exponential backoff retry logic for failed sync attempts",
                severity="low",
                effort="2h",
            )

        score = 1.0
        checks = [
            (sync_mechanism, 0.2),
            (conflict_resolution, 0.15),
            (indexed_db, 0.1),
            (service_worker, 0.15),
            (delta_sync, 0.1),
            (queue_mechanism, 0.1),
            (retry_logic, 0.05),
        ]
        for passed, penalty in checks:
            if not passed:
                score -= penalty

        return self._result(score)

    def _check_sync_mechanism(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "sync" in content.lower() and ("data" in content.lower() or "pull" in content.lower()):
                    return True
            except Exception:
                continue
        return False

    def _check_conflict_resolution(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "conflict" in content.lower() or "merge" in content.lower():
                    return True
            except Exception:
                continue
        return False

    def _check_indexed_db(self, target: Path) -> bool:
        for pattern in ["*.js", "*.ts", "*.tsx", "*.jsx"]:
            for f in target.rglob(pattern):
                try:
                    content = f.read_text()
                    if "indexedDB" in content or "localStorage" in content:
                        return True
                except Exception:
                    continue
        return False

    def _check_service_worker(self, target: Path) -> bool:
        for _f in target.rglob("service-worker.*"):
            return True
        for pattern in ["*.js", "*.ts"]:
            for f in target.rglob(pattern):
                try:
                    content = f.read_text()
                    if "serviceWorker" in content or "Service-Worker" in content:
                        return True
                except Exception:
                    continue
        return False

    def _check_delta_sync(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "delta" in content.lower() or "incremental" in content.lower():
                    if "sync" in content.lower() or "update" in content.lower():
                        return True
            except Exception:
                continue
        return False

    def _check_queue_mechanism(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "queue" in content.lower() and "outbox" not in content.lower():
                    if "offline" in content.lower() or "sync" in content.lower():
                        return True
                if "outbox" in content.lower() and "event" in content.lower():
                    return True
            except Exception:
                continue
        return False

    def _check_retry_logic(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if ("retry" in content.lower() or "backoff" in content.lower()) and (
                    "exponential" in content.lower() or "attempt" in content.lower()
                ):
                    return True
            except Exception:
                continue
        return False
