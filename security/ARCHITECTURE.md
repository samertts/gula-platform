# GSF Architecture — Clean Architecture, Zero Trust, and Integration Design

**Document ID**: GSF-ARCH-001  
**Version**: 1.0.0  
**Effective Date**: 2026-07-25  

---

## 1. Architecture Philosophy

GSF follows **Clean Architecture** (Robert C. Martin) with **Domain-Driven Design**
principles adapted for a national-scale healthcare security subsystem. The
architecture prioritizes:

- **Independence** — Each module can be developed, tested, and deployed independently
- **Testability** — Business logic is framework-agnostic and fully testable
- **Security** — Security controls are architected-in, not bolted-on
- **Replaceability** — Every component can be swapped without affecting others
- **Healthcare-specific** — FHIR R4, HL7, and Iraqi health domain models are first-class

---

## 2. Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FRAMEWORKS & DRIVERS                           │
│                                                                     │
│  FastAPI │ Flask │ Django │ Kubernetes │ Terraform │ Vault │ AWS    │
│  PostgreSQL │ Redis │ Kafka │ ELK │ Splunk │ Wazuh │ OPA │ Kyverno │
└─────────────────────────────────────────────────────────────────────│
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                      INTERFACE ADAPTERS                             │
│                                                                     │
│  ┌────────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ API Controllers    │  │ CLI Handlers     │  │ Event Handlers │  │
│  │ ─ FastAPI routes   │  │ ─ gsfctl         │  │ ─ Kafka        │  │
│  │ ─ Middleware       │  │ ─ management     │  │ ─ RabbitMQ     │  │
│  │ ─ Request/Response │  │ ─ audit queries  │  │ ─ webhooks     │  │
│  └────────────────────┘  └──────────────────┘  └────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Module Adapters / Presenters                                  │   │
│  │ ─ IdentityController    ─ SecretsController                  │   │
│  │ ─ AuthController        ─ AuditController                    │   │
│  │ ─ CompliancePresenter   ─ FhirSecurityAdapter                │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────│
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                          USE CASES                                  │
│                                                                     │
│  ┌────────────┐ ┌────────────┐ ┌───────────┐ ┌────────────────┐   │
│  │ Authenticate│ │ Authorize  │ │ AuditLog  │ │ EncryptData    │   │
│  │ User       │ │ Request    │ │ Event     │ │ /DecryptData   │   │
│  └────────────┘ └────────────┘ └───────────┘ └────────────────┘   │
│                                                                     │
│  ┌────────────┐ ┌────────────┐ ┌───────────┐ ┌────────────────┐   │
│  │ Manage     │ │ Rotate     │ │ Evaluate  │ │ Generate       │   │
│  │ Identity   │ │ Secret     │ │ Consent   │ │ ComplianceRpt  │   │
│  └────────────┘ └────────────┘ └───────────┘ └────────────────┘   │
│                                                                     │
│  ┌────────────┐ ┌────────────┐ ┌───────────┐ ┌────────────────┐   │
│  │ Verify     │ │ Detect     │ │ Validate  │ │ Enforce        │   │
│  │ Integrity  │ │ Anomaly    │ │ SBOM      │ │ NetworkPolicy  │   │
│  └────────────┘ └────────────┘ └───────────┘ └────────────────┘   │
└─────────────────────────────────────────────────────────────────────│
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                          ENTITIES                                   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Core Domain Models                                          │    │
│  │                                                             │    │
│  │ ├── Identity {id, tenant_id, nin, roles, attributes}        │    │
│  │ ├── Credential {type, hash, salt, metadata}                 │    │
│  │ ├── Policy {id, effect, action, resource, condition}        │    │
│  │ ├── Certificate {subject, issuer, pubkey, validity}         │    │
│  │ ├── Secret {id, version, encrypted_value, metadata}         │    │
│  │ ├── Consent {patient_id, directive, scope, expiry}          │    │
│  │ ├── AuditEvent {timestamp, actor, action, resource, hash}   │    │
│  │ ├── ComplianceControl {id, framework, requirement, status}  │    │
│  │ ├── SecurityLabel {classification, compartment, category}   │    │
│  │ └── ThreatAlert {type, severity, indicator, timestamp}      │    │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 Dependency Rule

Source code dependencies **only point inward**. Entities know nothing about
Use Cases. Use Cases know nothing about Adapters. Adapters know nothing about
Frameworks. This ensures business logic remains framework-agnostic.

---

## 3. Module Dependency Graph

```
                        ┌──────────────┐
                        │  GSF-003     │
                        │  Crypto      │
                        └──────┬───────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                   ▼
     ┌──────────┐      ┌──────────────┐    ┌────────────┐
     │ GSF-002  │      │  GSF-004     │    │ GSF-006    │
     │ Secrets  │◄────►│  Auth        │◄──►│ Audit      │
     └────┬─────┘      └──────┬───────┘    └────────────┘
          │                   │
          ▼                   ▼
     ┌──────────┐      ┌──────────────┐    ┌────────────┐
     │ GSF-001  │◄────►│  GSF-005     │    │ GSF-007    │
     │ Identity │      │  Authorization│◄──►│ Compliance │
     └──────────┘      └──────────────┘    └────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                     ▼
     ┌──────────┐      ┌──────────────┐    ┌────────────┐
     │ GSF-017  │      │  GSF-008     │    │ GSF-018    │
     │ FHIR     │      │  Headers     │    │ Privacy    │
     └──────────┘      └──────────────┘    └────────────┘
                               │
     ┌─────────────────────────┼─────────────────────────┐
     ▼                         ▼                         ▼
┌────────────┐         ┌──────────────┐          ┌────────────┐
│ GSF-009    │         │  GSF-010     │          │ GSF-019    │
│ Network    │◄───────►│  Database    │◄────────►│ Threat     │
└────────────┘         └──────────────┘          │ Detection  │
     │                                           └────────────┘
     ▼
┌────────────┐         ┌──────────────┐          ┌────────────┐
│ GSF-011    │◄───────►│  GSF-012     │◄────────►│ GSF-013    │
│ Container  │         │  Kubernetes  │          │ Terraform  │
└────────────┘         └──────────────┘          └────────────┘
     │                      │
     ▼                      ▼
┌────────────┐         ┌──────────────┐
│ GSF-014    │◄───────►│  GSF-015     │
│ GitHub     │         │  CI/CD       │
└────────────┘         └──────┬───────┘
                              │
                              ▼
                         ┌──────────────┐
                         │  GSF-016     │
                         │ Supply Chain │
                         └──────────────┘
```

### Dependency Rules

1. Core modules (GSF-001 through GSF-007) have no external framework dependencies
2. Infrastructure modules (GSF-009 through GSF-016) depend on core modules
3. No module depends on a higher-numbered module
4. Crypto (GSF-003) is the foundational dependency; all other modules may use it
5. Circular dependencies are prohibited

---

## 4. Data Flow Diagrams

### 4.1 Authentication Flow

```
                ┌──────────┐
                │  Client  │
                └────┬─────┘
                     │ POST /auth/login
                     ▼
             ┌───────────────┐
             │  API Gateway  │
             │  (GSF-008)    │
             │  Headers/CORS │
             └───────┬───────┘
                     │
                     ▼
             ┌───────────────┐
             │  Identity P.  │
             │  (GSF-001)    │
             │  Resolve Tenn │
             └───────┬───────┘
                     │
                     ▼
             ┌───────────────┐
             │  Auth Module  │
             │  (GSF-004)    │
             │  Verify Pass  │
             └───────┬───────┘
                     │
              ┌──────┴──────┐
              │             │
              ▼             ▼
       ┌──────────┐  ┌──────────┐
       │ MFA      │  │ No MFA   │
       │ Required │  │ Needed   │
       └────┬─────┘  └────┬─────┘
            │             │
            ▼             ▼
     ┌────────────┐ ┌──────────────┐
     │ TOTP / WA  │ │ Issue Token │
     │ Verify     │ │ (JWT)       │
     └──────┬─────┘ └──────┬───────┘
            │              │
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │ Audit Log    │
            │ (GSF-006)    │
            │ Event Record │
            └──────────────┘
```

### 4.2 Authorization Flow

```
          ┌──────────┐
          │ Request  │
          │ w/ Token │
          └────┬─────┘
               │
               ▼
       ┌──────────────┐
       │ AuthZ Engine │
       │ (GSF-005)    │
       └──────┬───────┘
              │
        ┌─────┴─────┐
        │           │
        ▼           ▼
  ┌─────────┐ ┌─────────┐
  │ RBAC    │ │ ABAC    │
  │ Check   │ │ Check   │
  │ Roles   │ │ Attrs   │
  └────┬────┘ └────┬────┘
       │           │
       └─────┬─────┘
             │
             ▼
      ┌──────────────┐
      │ Policy Engine│
      │ (OPA/Rego)   │
      └──────┬───────┘
             │
       ┌─────┴─────┐
       │ ALLOW     │
       │ or DENY   │
       └───────────┘
```

### 4.3 Audit Log Flow

```
  ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ Service  │    │ Service  │    │ Service  │
  │ A        │    │ B        │    │ C        │
  └────┬─────┘    └────┬─────┘    └────┬─────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
                       ▼
                ┌──────────────┐
                │ Audit Logger │
                │ (GSF-006)    │
                │ ─ Structured │
                │ ─ Hash Chain │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │  Audit Store  │
                │  ┌─────────┐  │
                │  │ Write   │  │
                │  │ Ahead   │  │
                │  │ Log     │  │
                │  └─────────┘  │
                │  ┌─────────┐  │
                │  │ Object  │  │
                │  │ Store   │  │
                │  └─────────┘  │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │ SIEM Export  │
                │ (ELK/Splunk) │
                └──────────────┘
```

### 4.4 FHIR Security Flow

```
  ┌──────────┐
  │ FHIR     │
  │ Client   │
  └────┬─────┘
       │ GET /fhir/Patient/{id}
       ▼
  ┌──────────────┐
  │ SMART-on-    │
  │ FHIR Auth    │
  │ (GSF-017.3)  │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Security     │
  │ Label Check  │
  │ (GSF-017.1)  │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Consent      │
  │ Evaluation   │
  │ (GSF-017.2)  │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Authorization│
  │ (GSF-005)    │
  └──────┬───────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
  ┌────┐  ┌──────┐
  │200 │  │ 403  │
  │ OK │  │Denied│
  └────┘  └──────┘
```

---

## 5. Zero Trust Architecture

### 5.1 Zero Trust Pillars

```
┌────────────────────────────────────────────────────────────────────┐
│                    ZERO TRUST ARCHITECTURE                          │
│                                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Identity │  │ Devices  │  │ Network  │  │ Data     │          │
│  │ ─ Every  │  │ ─ Device │  │ ─ mTLS   │  │ ─ CLE    │          │
│  │   request│  │   posture│  │ ─ Network│  │ ─ Masking│          │
│  │ ─ MFA    │  │ ─ MDM    │  │   Policy │  │ ─ DLP    │          │
│  │ ─ JIT    │  │ ─ Compliance│ ─ Microseg│  │ ─ Labels │          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │
│                                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Workloads│  │ Analytics│  │ Automation│  │ Orchest. │          │
│  │ ─ Pod    │  │ ─ UEBA   │  │ ─ Policy  │  │ ─ K8s    │          │
│  │   Security│ │ ─ Threat │  │   as Code │  │ ─ Terra  │          │
│  │ ─ Service│  │   Intel  │  │ ─ IR Auto │  │   form   │          │
│  │   Mesh   │  │ ─ SIEM   │  │   mation  │  │ ─ GitOps │          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │
└────────────────────────────────────────────────────────────────────┘
```

### 5.2 Trust Boundaries

```
                          INTERNET
                             │
                     [WAF / DDoS Protection]
                             │
                    ┌────────┴────────┐
                    │   DMZ / Public  │  ─ Trust Boundary 1
                    │   ┌──────────┐  │
                    │   │ API Gw   │  │
                    │   └──────────┘  │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  Application    │  ─ Trust Boundary 2
                    │  ┌──────────┐   │
                    │  │ Services │   │
                    │  └──────────┘   │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  Data Layer     │  ─ Trust Boundary 3
                    │  ┌──────────┐   │
                    │  │ Database │   │
                    │  │ Storage  │   │
                    │  └──────────┘   │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  Backup/DR      │  ─ Trust Boundary 4
                    │  ┌──────────┐   │
                    │  │ Off-site │   │
                    │  │ Backups  │   │
                    │  └──────────┘   │
                    └─────────────────┘
```

---

## 6. Integration Points

### 6.1 With GULA Backend (FastAPI)

```
┌────────────────────────────────────────────────────────────┐
│                    GULA Platform Backend                    │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐ │
│  │FastAPI   │   │FHIR      │   │Device    │   │Admin   │ │
│  │Routes    │   │Gateway   │   │Bridge    │   │Panel   │ │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └───┬────┘ │
│       │              │              │              │       │
│       └──────────────┼──────────────┼──────────────┘       │
│                      ▼              ▼                       │
│              ┌──────────────────────────────┐               │
│              │       GSF Integration        │               │
│              │  ┌──────────┐ ┌───────────┐  │               │
│              │  │Auth MW   │ │Audit MW   │  │               │
│              │  ├──────────┤ ├───────────┤  │               │
│              │  │Header MW │ │Compliance │  │               │
│              │  └──────────┘ └───────────┘  │               │
│              └──────────────┬───────────────┘               │
│                             │                                │
└─────────────────────────────┼────────────────────────────────┘
                              │
                     ┌────────┴────────┐
                     │   GSF Modules   │
                     └─────────────────┘
```

### 6.2 With Kubernetes

```
┌──────────────────────────────────────────────────────┐
│                GULA Kubernetes Cluster                │
│                                                       │
│  ┌────────────────────────────────────────────────┐  │
│  │         GSF Operator (GSF-012)                 │  │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │  │
│  │  │Gatekeeper │  │ Kyverno  │  │ Pod Security│  │  │
│  │  │Constraints│  │ Policies │  │ Standards   │  │  │
│  │  └──────────┘  └──────────┘  └─────────────┘  │  │
│  └────────────────────────────────────────────────┘  │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ mTLS     │  │ Network  │  │ Secrets  │           │
│  │ Sidecar  │  │ Policies │  │ (Vault)  │           │
│  └──────────┘  └──────────┘  └──────────┘           │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ HPA      │  │ PDB      │  │ Pod      │           │
│  │ Scaling  │  │ (DR)     │  │Topology  │           │
│  └──────────┘  └──────────┘  └──────────┘           │
└──────────────────────────────────────────────────────┘
```

---

## 7. Security Domain Boundaries

```
                     ┌─────────────────────────────────────┐
                     │       Security Domain Boundary       │
                     │         ────────────────             │
                     │  ┌───┐  ┌───┐  ┌───┐  ┌───┐       │
                     │  │Id │  │Sec│  │Cry│  │AuN│       │
                     │  │ t │  │ r │  │ p │  │ t │       │
                     │  │(1)│  │(2)│  │(3)│  │(4)│       │
                     │  └───┘  └───┘  └───┘  └───┘       │
                     │                                    │
                     │  ┌───┐  ┌───┐  ┌───┐  ┌───┐       │
                     │  │AuZ│  │Aud│  │Cmp│  │Hdr│       │
                     │  │(5)│  │(6)│  │(7)│  │(8)│       │
                     │  └───┘  └───┘  └───┘  └───┘       │
                     │                                    │
                     │  ┌───┐  ┌───┐  ┌───┐  ┌───┐       │
                     │  │Net│  │DB │  │FH │  │Pri│       │
                     │  │(9)│  │(10)│  │(17)│  │(18)│       │
                     │  └───┘  └───┘  └───┘  └───┘       │
                     │                                    │
                     │  ┌───┐  ┌───┐  ┌───┐  ┌───┐       │
                     │  │TD │  │Int│  │Thr│  │K8s│       │
                     │  │(19)│  │(20)│  │(13)│  │(12)│       │
                     │  └───┘  └───┘  └───┘  └───┘       │
                     └─────────────────────────────────────┘
```

---

## 8. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Clean Architecture over layered | Prevents framework lock-in, enables independent testing |
| Rego/OPA for policies | Declarative, testable, portable across cloud/on-prem |
| Hash chain for audit | Tamper-evident without requiring blockchain complexity |
| Argon2id for passwords | Memory-hard, resistant to GPU/ASIC attacks |
| mTLS for service mesh | Zero-trust networking, no VPN required |
| AES-256-GCM for encryption | Authenticated encryption, NIST-approved |
| Column-level encryption | Granular PHI protection without DB-level encryption overhead |

---

## 9. Performance Considerations

| Module | Expected Latency | Optimization |
|--------|-----------------|--------------|
| Crypto (GSF-003) | < 5ms (AES), < 50ms (sign) | Native bindings, key caching |
| Auth (GSF-004) | < 20ms (password), < 100ms (TOTP) | Session caching, connection pooling |
| AuthZ (GSF-005) | < 10ms (RBAC), < 50ms (ABAC) | Policy caching, partial evaluation |
| Audit (GSF-006) | < 5ms (write), async | Write-ahead log, batch export |
| Network (GSF-009) | < 1ms (policy check) | eBPF/XDP for packet filtering |

---

## 10. References

- Clean Architecture: Martin, R. (2017). *Clean Architecture: A Craftsman's Guide*
- Zero Trust: NIST SP 800-207 *Zero Trust Architecture*
- FHIR Security: HL7 FHIR Security Implementation Guide v3.0
- OPA/Rego: Open Policy Agent Documentation
- NIST CSF 2.0: *Cybersecurity Framework* (2024)

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-25 | GULA Security Team | Initial architecture document |
