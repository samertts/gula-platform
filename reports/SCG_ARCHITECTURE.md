# SOVEREIGN CONNECTOR GATEWAY (SCG) — ARCHITECTURE

**Design Authority:** Principal Security Architect, Enterprise Integration Architect
**Status:** PROPOSED
**Version:** 1.0.0

---

## EXECUTIVE SUMMARY

The Sovereign Connector Gateway (SCG) is a new core platform subsystem that becomes the **only authorized communication layer** between GULA components and any external system. No AI agent, plugin, module, workflow, or service may communicate directly with external systems. All outbound communication passes through SCG.

**Key Principles:**
- **Zero Trust** — Never trust, always verify
- **Secret Isolation** — AI agents never receive credentials
- **Intent-based** — Agents submit intents, SCG handles execution
- **Offline-first** — Queued requests, conflict resolution
- **Vendor Independent** — No dependency on any single connector framework

---

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                    GULA PLATFORM                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │AI Agents │  │Services  │  │Workflows │  │Modules   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │             │              │         │
│       └──────────────┴─────────────┴──────────────┘         │
│                              │                               │
│                     ┌────────▼────────┐                     │
│                     │   SCG Core      │                     │
│                     │  (Intent API)   │                     │
│                     └────────┬────────┘                     │
│                              │                               │
│          ┌───────────────────┼───────────────────┐          │
│          ▼                   ▼                   ▼          │
│   ┌────────────┐    ┌──────────────┐    ┌──────────────┐   │
│   │ Policy     │    │ Token        │    │ Connector    │   │
│   │ Engine     │◄──►│ Broker       │◄──►│ Registry     │   │
│   └────────────┘    └──────────────┘    └──────┬───────┘   │
│                                                │           │
│          ┌─────────────────────────────────────┼───────┐   │
│          ▼              ▼              ▼       ▼       ▼   │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│   │Connector │  │Connector │  │Connector │  │Connector │ │
│   │Runtime   │  │Sandbox   │  │SDK       │  │Registry  │ │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
  ┌───────────────┐
  │ External      │
  │ Systems       │
  │ (REST/gRPC/   │
  │  MQTT/HL7/    │
  │  FHIR/etc.)   │
  └───────────────┘
```

---

## COMPONENT SPECIFICATIONS

### 1. SCG Core

**Purpose:** Central routing, validation, and orchestration hub.

| Aspect | Specification |
|--------|---------------|
| Protocol | gRPC (internal) + REST (external fallback) |
| Transport | mTLS required for all connections |
| Request format | Intent schema (see below) |
| Response format | ConnectorResult schema |
| Rate limit | Per-tenant, per-connector, per-action |
| Auth | SCG issues time-bound tokens to platform components |

**Intent Schema:**
```json
{
  "intent_id": "uuid",
  "source": "agent_name|service_name|workflow_id",
  "source_type": "ai_agent|service|workflow|module",
  "action": "read|write|delete|admin|stream",
  "target": {
    "connector": "connector_name",
    "operation": "operation_name",
    "params": {}
  },
  "context": {
    "tenant_id": "lab_id|org_id",
    "user_id": "user_id",
    "request_id": "correlation_id",
    "clinical_sensitivity": "standard|sensitive|phi",
    "emergency_override": false
  },
  "constraints": {
    "timeout_s": 30,
    "max_bytes": 1048576,
    "allowed_networks": ["10.0.0.0/8"],
    "requires_approval": false
  }
}
```

### 2. Connector Registry

**Purpose:** Source of truth for all installed connectors, their versions, capabilities, and security posture.

**Registry Entry Schema:**
```json
{
  "connector_id": "uuid",
  "name": "connector_name",
  "version": "semver",
  "type": "official|certified|partner|community|private|commercial",
  "status": "active|deprecated|disabled|sandbox",
  "capabilities": ["read", "write", "stream", "webhook"],
  "protocols": ["rest", "graphql", "grpc", "mqtt", "hl7", "fhir"],
  "auth_methods": ["oauth2", "apikey", "basic", "mtls", "none"],
  "tenant_access": ["tenant_id", "tenant_id", ...],
  "rate_limits": {"global": 100, "per_tenant": 10},
  "security_scan": {"last_pass": "date", "score": "A|B|C|F"},
  "certification": {"level": "bronze|silver|gold|platinum", "expires": "date"},
  "requirements": {
    "min_scg_version": "1.0.0",
    "network_access": ["api.example.com:443"],
    "memory_mb": 64,
    "storage_mb": 10
  }
}
```

### 3. Connector SDK

**Purpose:** Allow third-party developers to build SCG-compatible connectors.

**SDK Components:**
- **Base Connector Class** — Abstract base with lifecycle hooks (init, validate, connect, execute, disconnect, health_check)
- **Schema Generator** — Auto-generates input/output validation schemas from Python type hints
- **Test Harness** — Isolated test environment with mock SCG backend
- **Security Scanner** — Local pre-certification scan for secret leakage, dependency vulnerabilities
- **Documentation Generator** — Auto-generates connector docs from code

**Minimum Connector Implementation:**
```python
from scg_sdk import BaseConnector, operation, schema

class GitHubConnector(BaseConnector):
    @operation(capabilities=["read", "write"])
    @schema(input=ListIssuesInput, output=ListIssuesOutput)
    async def list_issues(self, params):
        # No credentials here — SCG injects them via context
        token = self.context.get_token()
        async with self.http_client() as client:
            client.set_auth(token)
            return await client.get(f"/repos/{params.repo}/issues")
```

### 4. Connector Runtime

**Purpose:** Secure execution environment for connectors.

| Feature | Implementation |
|---------|---------------|
| Isolation | Subprocess per connector (not per request) |
| Resource limits | cgroups v2 (CPU, memory, network, disk) |
| Network filter | eBPF-based outbound allow list |
| Timeout | Hard kill at configured timeout + 5s grace |
| Restart policy | Exponential backoff (1s, 2s, 4s, 8s, 16s, max 60s) |
| Health checks | Every 30s, 3 failures = disable |
| Secrets injection | Via SCG-internal Unix socket (not env vars) |
| Logging | Structured JSON to SCG (not local files) |

### 5. Connector Sandbox

**Purpose:** Pre-production connector testing environment.

- **Scoped network** — Only SCG-internal APIs + mock external services
- **Mock credentials** — Auto-generated, time-limited, no real system access
- **Rate limit bypass** — 10x production limit for testing throughput
- **Failure injection** — Configurable latency, error rates, disconnection
- **Observability** — Full tracing, replay capability

### 6. Policy Engine

**Purpose:** Authorize every SCG operation before execution.

**Policy Types:**
| Policy | Scope | Default |
|--------|-------|---------|
| Allow/Deny | Per connector, per operation | Deny all |
| Read Only | Per connector | Allow for approved |
| Write | Per connector | Deny by default |
| Delete | Per connector | Always deny |
| Admin | Per connector | Always deny |
| Time-based | M-F 8am-6pm | Enforce |
| Location-based | IP CIDR | Enforce |
| Department-based | Lab department | Enforce |
| Clinical override | Critical care path | Requires justification |
| Emergency override | Break glass | Requires audit + notification |

**Policy DSL Example:**
```yaml
policies:
  - name: "github_read_only_for_ai"
    effect: "allow"
    when:
      source_type: "ai_agent"
      connector: "github"
      action: "read"
      tenant: "lab_123"
    constraints:
      rate_limit: 10/minute
      requires_approval: false
      
  - name: "deny_external_writes"
    effect: "deny"
    when:
      action: "write"
      target.network: "!10.0.0.0/8"
```

### 7. Secret Manager

**Purpose:** Store, rotate, and inject secrets without exposing them to agents.

| Feature | Specification |
|---------|---------------|
| Storage | Encrypted at rest (AES-256-GCM) |
| Backend | SCG-internal + optional Vault integration |
| Rotation | Automatic (90 days default, configurable per secret) |
| Access pattern | Agents request by reference, SCG injects |
| Audit | Every secret access logged |
| Breach detection | Unusual access patterns trigger alerts |

**Secret Types:**
- API Keys
- OAuth Tokens (refresh + access)
- JWT Signing Keys
- Database Passwords
- Private Keys (RSA, ECDSA)
- Cloud Provider Credentials
- Service Tokens

### 8. Token Broker

**Purpose:** Issue ephemeral, scope-limited tokens for connector operations.

**Flow:**
1. Agent submits intent with `target.connector` and `target.operation`
2. SCG validates intent against Policy Engine
3. Token Broker checks Secret Manager for stored credentials
4. Broker creates **new** short-lived token (or ephemeral API key) scoped to exact operation
5. Token injected into Connector Runtime for this execution only
6. Token revoked immediately after operation completes (or by TTL)

**Token Characteristics:**
- TTL: 60 seconds (configurable per connector type)
- Scope: Exact operation (not broader)
- Revocation: Automatic on intent completion
- No persistence: Never written to log or database
- One-time use: Token is invalidated after first use

### 9. Audit Engine

**Purpose:** Immutable, tamper-evident record of every SCG operation.

**Audit Record Schema:**
```json
{
  "audit_id": "uuid",
  "intent_id": "uuid",
  "timestamp": "ISO8601",
  "source": "agent_name",
  "source_type": "ai_agent|service|workflow",
  "user_id": "originating_user",
  "tenant_id": "lab_id",
  "connector": "connector_name",
  "operation": "operation_name",
  "action": "read|write|delete|admin",
  "policy_applied": "policy_name",
  "policy_decision": "allow|deny",
  "credential_used": "secret_ref (not value)",
  "execution_time_ms": 1234,
  "response_size_bytes": 5678,
  "risk_score": 0.0-1.0,
  "correlation_id": "request_chain",
  "emergency_override": false,
  "chain_hash": "sha256_of_previous_audit"
}
```

**Chain Anchoring:**
- Every audit record includes SHA-256 hash of previous record
- Periodic anchor to blockchain or transparency log
- Tampering detected by hash chain verification

### 10. Rate Limiter & Quota Manager

**Rate Limiting Dimensions:**
| Dimension | Scope | Method |
|-----------|-------|--------|
| Per tenant | requests/minute | Token bucket |
| Per connector | requests/minute | Token bucket |
| Per operation | requests/minute | Token bucket |
| Per user | requests/minute | Token bucket |
| Global | all requests/minute | Leaky bucket |

**Quota Types:**
| Quota | Units | Reset |
|-------|-------|-------|
| API calls | Count | Monthly |
| Data transfer | MB | Monthly |
| Connector instances | Count | N/A (hard limit) |
| Concurrent executions | Count | Per execution |
| Storage (offline queue) | MB | N/A (hard limit) |

---

## CONNECTOR ADAPTERS

### Tier 1: Infrastructure (SCG Core Team)
- PostgreSQL, MySQL, SQL Server, MongoDB
- Redis, RabbitMQ, Kafka, NATS
- MinIO, S3, Azure Blob
- REST, GraphQL, gRPC

### Tier 2: Communications (Certified Partners)
- Slack, Discord, Microsoft Teams
- Email (SMTP/IMAP), SMS Gateways
- WhatsApp Business, Push Notifications
- Webhook Engine (inbound + outbound)

### Tier 3: Development (Certified Partners)
- GitHub, GitLab, Azure DevOps, Bitbucket
- Jira, Confluence, Notion

### Tier 4: Healthcare (Official + Certified)
- FHIR R4, HL7 v2, HL7 v3
- DICOM, PACS
- LIS, HIS, ERP
- LOINC, SNOMED CT, ICD-10/11

### Tier 5: Identity (Official)
- LDAP, Active Directory
- OIDC Providers, SAML IDP
- OAuth2 Authorization Servers

### Tier 6: Government (Official + Restricted)
- National Identity Gateway
- Government Portal APIs
- National Health Exchanges

### Tier 7: AI (Official)
- OpenAI, Anthropic, Google AI
- xAI, DeepSeek, Qwen
- Ollama, vLLM, Local Models
- MCP Protocol

### Tier 8: Custom (Community + Private)
- OpenConnector Adapter
- Community-built connectors
- Private enterprise connectors

---

## OPENCONNECTOR INTEGRATION (Evaluation)

**Evaluation Result:** OpenConnector is a promising framework for declarative connector definitions. However, we **do not depend on it directly.**

**Integration Strategy:**
1. SCG defines its own Connector SDK (vendor-independent)
2. An **OpenConnector Adapter** is created as a Tier 8 connector
3. If OpenConnector is healthy: SCG routes supported operations through it
4. If OpenConnector is unavailable: SCG provides native implementation
5. The adapter maps OpenConnector specs to SCG's internal schema

**This ensures:** No single point of failure. No vendor lock-in. Graceful degradation.

---

## MCP PROTOCOL INTEGRATION

Model Context Protocol (MCP) is supported as a **connector protocol adapter**:

1. MCP servers register with SCG as connectors
2. AI agents interact with MCP tools/resources through SCG
3. SCG enforces policies, injects secrets, and audits all MCP operations
4. MCP streaming is supported for real-time AI interactions

---

## ZERO TRUST CONNECTIVITY

| Layer | Control | Implementation |
|-------|---------|---------------|
| Network | mTLS | All SCG internal communication |
| Network | Network segmentation | Connectors run in isolated namespaces |
| Identity | JWT + SPIFFE | Every component has identity |
| Device | Device attestation | Connector hosts verified before registration |
| Data | Encryption | All data encrypted in transit (TLS 1.3) |
| Data | Classification | SCG tags data sensitivity per intent |
| Audit | Continuous verification | Every request authenticated, authorized, audited |
| Threat | Behavioral analysis | Anomaly detection on connector traffic patterns |

---

## MULTI-TENANT ISOLATION

| Resource | Isolation Strategy |
|----------|-------------------|
| Connector instances | Separate subprocess per tenant |
| Secrets | Tenant-scoped vault namespace |
| Rate limits | Per-tenant counters |
| Audit logs | Tenant-aware partitioning |
| Data in transit | Tenant-tagged with SPIFFE identity |
| Configuration | Tenant-scoped policy engine |

---

## DATA SOVEREIGNTY

| Feature | Implementation |
|---------|---------------|
| Region restriction | Connectors tagged with allowed regions |
| Data residency | Audit log includes data location |
| Cross-border flow | Policy engine blocks unauthorized transfers |
| Government override | Sovereign override with full audit |
| Offline isolation | No external communication allowed in offline mode |

---

## OFFLINE CONNECTIVITY

| Feature | Implementation |
|---------|---------------|
| Request queuing | Durable queue (local SQLite) when offline |
| Conflict resolution | Last-writer-wins with vector clocks |
| Deferred sync | Prioritized sync when reconnected |
| Priority queuing | Clinical operations queued first |
| Queue limits | Per-tenant queue size limits |
| Retry | Exponential backoff with jitter |
| Circuit breaker | 5 consecutive failures → disable connector |

---

## DISASTER RECOVERY

| Scenario | Recovery |
|----------|----------|
| SCG process crash | Systemd auto-restart, queue replay from checkpoint |
| Node failure | Active-passive SCG pair, shared state in PostgreSQL |
| Region failure | Warm standby in secondary region |
| Data corruption | Point-in-time recovery of audit + queue |
| Connector failure | Circuit breaker, alert, failover to secondary connector |
| Full site failure | Cold standby in independent cloud/region |

---

## CONNECTOR CERTIFICATION

| Level | Requirements | Benefits |
|-------|--------------|----------|
| **Bronze** | SDK compliance, security scan, basic tests | Listed in marketplace, community badge |
| **Silver** | + Integration tests, documentation, 80% coverage | Certified badge, priority support |
| **Gold** | + Penetration test, load test, 95% coverage | Featured listing, SCG team review |
| **Platinum** | + Source code audit, SLA commitment | Official partner, joint roadmap |

---

## IMPLEMENTATION PRIORITY

| Phase | Components | Timeline |
|-------|------------|----------|
| **Phase 1** | SCG Core, Connector Registry, Policy Engine, Audit Engine, Token Broker, Secret Manager | Month 1-3 |
| **Phase 2** | Connector SDK, Connector Runtime, Sandbox, Tier 1 connectors (REST, gRPC, PostgreSQL, Redis, S3) | Month 4-6 |
| **Phase 3** | Tier 2-3 connectors, OpenConnector Adapter, MCP integration | Month 7-9 |
| **Phase 4** | Tier 4-6 connectors, Marketplace, Certification program | Month 10-12 |
| **Phase 5** | Tier 7-8 connectors, Multi-region DR, Zero Trust hardening | Month 13-18 |
| **Phase 6** | AI-native connector discovery, predictive routing, self-healing marketplace | Month 19-24 |

---

## RISK REGISTER (SCG-specific)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Connector supply chain attack | Medium | Critical | Signed connector manifests, reproducible builds |
| Policy engine bypass | Low | Critical | Defense-in-depth, multiple policy enforcement points |
| Secret leakage via connector | Medium | Critical | Sandboxed runtime, network filtering, no direct secret access |
| Connector incompatibility on upgrade | Medium | High | Version pinning, canary testing, rollback capability |
| Performance bottleneck | Medium | Medium | Horizontal scaling, connection pooling, async I/O |
| OpenConnector dependency | Low | Medium | Adapter pattern, no direct dependency |
| Developer experience friction | Medium | Medium | SDK, templates, generator, certification guide |
| Marketplace quality control | Medium | Medium | Certification tiers, automated scanning, user ratings |
