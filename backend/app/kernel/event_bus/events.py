from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Event:
    """The canonical event envelope (PROGRAM-EXT-001).

    Everything below `tenant_id` was added by PROGRAM-EXT-001 and is additive
    with a default, so every existing publisher still constructs. What the new
    fields buy is the ability to answer three questions a consumer cannot
    otherwise answer from the envelope alone: who did this (`actor_id`), what
    caused it (`causation_id`), and what it is about (`resource_type` /
    `resource_id`) without reaching into another domain's tables to find out.

    `version` is the event's schema version and is what a consumer pins. It is
    deliberately separate from `provenance`, which records the producing
    capability and release so a malformed event can be traced to a deployment
    rather than only to a name.
    """

    name: str
    data: dict
    version: int = 1
    id: str = ""
    timestamp: float = 0.0
    source: str = ""
    correlation_id: str = ""
    tenant_id: str = ""
    actor_id: str = ""
    actor_type: str = ""
    causation_id: str = ""
    resource_type: str = ""
    resource_id: str = ""
    provenance: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = time.time()

    def caused_by(self, parent: Event) -> Event:
        """Link this event to the one that caused it, keeping the correlation.

        `correlation_id` follows a whole interaction; `causation_id` names the
        single event immediately upstream. Conflating them is how an event
        graph becomes a flat list.
        """
        self.causation_id = parent.id
        if not self.correlation_id:
            self.correlation_id = parent.correlation_id or parent.id
        if not self.tenant_id:
            self.tenant_id = parent.tenant_id
        return self
