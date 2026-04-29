"""GULA Edge AI Platform — control plane.

Transforms the system from a traditional client/server architecture into a
"Managed Distributed Edge AI Platform". Modules in this package implement the
control plane (registration, scheduling, trust, policy, model governance,
telemetry); the data plane (the agent itself) lives in `edge_agent/`.

Design tenets (NON-NEGOTIABLE):
  - Opt-in only — no device participates without explicit registration
  - Sandboxed   — agent executes only signed, allowlisted task kinds
  - Tenant-isolated — every record is scoped to a lab_id
  - Zero-trust  — every request reverified via mTLS + signed token + trust score
  - Resource-aware — scheduler honors per-tenant CPU/RAM/battery caps
  - Stateless where possible — server is the source of truth
"""

from .config import EDGE_ENABLED, EDGE_KILL_SWITCH

__all__ = ["EDGE_ENABLED", "EDGE_KILL_SWITCH"]
