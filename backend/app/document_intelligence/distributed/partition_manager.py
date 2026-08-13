from __future__ import annotations

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


class PartitionManager:
    def __init__(self, num_partitions: int = 16):
        self._num_partitions = num_partitions
        self._partition_assignments: dict[int, str] = {}

    def get_partition(self, document_id: str) -> int:
        # Stable partitioning only; this digest is never used for security.
        hash_val = int(hashlib.sha256(str(document_id).encode()).hexdigest(), 16)
        return hash_val % self._num_partitions

    def assign_worker(self, partition: int, worker_id: str):
        self._partition_assignments[partition] = worker_id

    def get_worker(self, document_id: str) -> str | None:
        partition = self.get_partition(document_id)
        return self._partition_assignments.get(partition)

    def rebalance(self, active_workers: list[str]):
        if not active_workers:
            return
        per_worker = self._num_partitions // len(active_workers)
        remainder = self._num_partitions % len(active_workers)
        idx = 0
        for partition in range(self._num_partitions):
            if idx < remainder:
                self._partition_assignments[partition] = active_workers[idx]
            else:
                worker_idx = idx // per_worker
                self._partition_assignments[partition] = active_workers[
                    min(worker_idx, len(active_workers) - 1)
                ]
            idx += 1

    @property
    def num_partitions(self) -> int:
        return self._num_partitions

    def get_stats(self) -> dict[str, Any]:
        worker_counts: dict[str, int] = {}
        for w in self._partition_assignments.values():
            worker_counts[w] = worker_counts.get(w, 0) + 1
        return {
            "total_partitions": self._num_partitions,
            "active_workers": len(set(self._partition_assignments.values())),
            "partitions_per_worker": worker_counts,
        }
