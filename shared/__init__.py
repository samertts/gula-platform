"""GULA Shared Library — canonical engineering layer.

Every module in this package is extracted from production code across the
GULA monorepo ecosystem.  Never duplicate code — import from here.

Canonical modules:
  auth, audit, backup, barcode, booking, cache, circuit_breaker,
  cli, config, design_system, device, documents, domain (7 modules),
  events, feature_flags, generators (3), health, licensing,
  localization, logging, messaging, metrics, middleware, models,
  notifications, observability, payments, pdf, policies, printing,
  qr, rbac, restore, retry, scheduler, schemas, search, sdk (3),
  security, storage, subscriptions, tracing, utilities, validators, workflow
"""

__version__ = "2.1.0"
