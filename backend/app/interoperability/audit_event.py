"""Interop-only audit event shape.

Every adapter operation (success, failure, denial) emits exactly one
``InteropAuditEvent``. This module defines only the shape; chain-row
emission is performed by the audit-chain layer when wiring is approved.

See ``docs/sovereign/phase18-regulatory-governance/04-audit-integrity.md``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class InteropAuditDisposition(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    CAPABILITY_DENIED = "capability_denied"
    CIRCUIT_OPEN = "circuit_open"
    REPLAY_REJECTED = "replay_rejected"
    DEAD_LETTER = "dead_letter"


@dataclass(frozen=True)
class InteropAuditEvent:
    """Interop-call audit shape (inbound or outbound).

    The shape mirrors the existing audit-chain row contract: a stable
    subject + opaque hashes + scope tags. Bodies of inputs/outputs are
    intentionally NOT part of the row; their hashes are.
    """

    direction: str  # "inbound" or "outbound"
    domain_id: str
    operation: str
    request_id: str
    inputs_hash: str
    outputs_hash: str
    disposition: InteropAuditDisposition
    lab_id: str | None = None
    peer_subject: str | None = None
    occurred_at: float = field(default_factory=lambda: time.time())
    error_class: str | None = None
    extra_tags: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    @property
    def subject(self) -> str:
        return f"interop.{self.direction}.{self.operation}"
