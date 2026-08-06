"""GULA User Communication Experience Layer (PROGRAM-COMM-003).

Provider-independent user experience on top of the Communication Core
(``shared.communication``) and the provider layer
(``shared.communication_providers``). Neither is modified: the experience
layer composes them — durable in-app inbox, user preferences, channel
selection, categories, history, and the HTTP API every GULA application
gains automatically.

Modules:
  - domain: pure enums, value objects, quiet-hours/weekend/holiday rules
  - models: ORM rows for the inbox, history events and preferences
  - sinks: durable in-app sink + audit-history sink (bound at composition root)
  - preferences_service: per-user preference CRUD + channel catalog
  - inbox_service: query/filter/search/actions/history + retry
  - routes: FastAPI router mounted by the platform factory
"""

from __future__ import annotations

__all__: list[str] = []
