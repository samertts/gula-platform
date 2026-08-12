"""GULA Shared Library — canonical engineering layer.

Every module in this package is extracted from production code across the
GULA monorepo ecosystem.  Never duplicate code — import from here.

Canonical modules:
  auth          — JWT encode/decode, password hashing
  audit         — hash-chained audit log
  barcode       — barcode generation (Code128, sample barcodes)
  booking       — appointment booking engine
  cache         — caching backends (Redis, in-memory)
  circuit_breaker — circuit breaker pattern
  cli           — CLI utilities
  config        — configuration loading (dataclass-based)
  domain        — domain models (billing, booking, events, healthcare, notifications, security)
  events        — in-process event bus + constants
  health        — health checks (DB, Redis, components)
  licensing     — license management and tiers
  logging       — structured JSON logging (contextvars-based)
  metrics       — metrics collection (counters, gauges, histograms, Prometheus format)
  notifications — push, email, SMS, WhatsApp notification sending
  observability — tracing integration
  pdf           — PDF report generation (ReportLab-based)
  qr            — QR code generation (images and SVG)
  rbac          — role-based access control (enum + extended string API)
  security      — Fernet encryption, HMAC signing
  storage       — storage backends (local, S3, R2)
  subscriptions — subscription plans and management
  payments      — payment processing and gateway
  ai            — AI/LLM client (Gemini, Ollama, Groq)
  sdk           — GULA SDK client
  design_system — UI design tokens, RTL, components
  validators    — common validators
  middleware    — shared middleware components
  domain        — domain models (7 sub-modules)
  generators    — code generators (docs, migrations, modules)
  policies      — policy engine
  workflow      — workflow engine
  schemas       — shared schemas (pagination, response)
  printing      — printer integration
  backup        — backup management
  device        — lab device adapters (ASTM protocol)
  localization  — Arabic-first localization
  search        — search utilities
  scheduler     — scheduler utilities
  feature_flags — feature flag utilities
  messaging     — messaging abstractions
  retry         — retry decorators
  restore       — restore utilities
  architecture  — architecture validation / knowledge graph
  utilities     — helper utilities
  tracing       — distributed tracing
  identity      — identity platform (domain models, service, events)
"""

__version__ = "2.1.0"
