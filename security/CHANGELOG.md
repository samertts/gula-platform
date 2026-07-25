# Changelog

All notable changes to the GULA Security Framework (GSF) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-07-25

### Added

- GSF-001 Identity Module: Multi-tenant identity provider with national ID (NIN) integration
- GSF-002 Secrets Module: Encrypted secret storage with Vault and AWS Secrets Manager backends
- GSF-003 Crypto Module: AEAD encryption, digital signatures, key derivation, key rotation
- GSF-004 Authentication Module: Password, TOTP, WebAuthn, OAuth2, SAML with MFA enforcement
- GSF-005 Authorization Module: RBAC, ABAC, Rego-powered policy engine with fine-grained resource scoping
- GSF-006 Audit Module: Immutable, tamper-evident audit log with SHA-256 hash chains
- GSF-007 Compliance Module: OWASP ASVS Level 3, NIST CSF 2.0, ISO 27001:2022, HIPAA, GDPR, FHIR security
- GSF-008 Headers Module: Zero-Trust HTTP security headers, CSP, HSTS, CORP, COEP, SRI
- GSF-009 Network Module: mTLS mesh, network policies, eBPF-based traffic monitoring
- GSF-010 Database Module: Transparent column-level encryption (CLE), dynamic data masking, SQL audit triggers
- GSF-011 Container Module: Container image signing, vulnerability scanning integration, seccomp/AppArmor profiles
- GSF-012 Kubernetes Module: Pod Security Standards, OPA Gatekeeper, Kyverno policies, network policies
- GSF-013 Terraform Module: Policy-as-Code for infrastructure, sentinel-like Rego checks, drift detection
- GSF-014 GitHub Module: Repository security posture, secret scanning, branch protection, Dependabot configuration
- GSF-015 CI Module: CI/CD pipeline security, SBOM generation, SLSA compliance
- GSF-016 Supply Chain Module: Dependency verification, attestation verification, provenance tracking
- GSF-017 FHIR Module: FHIR R4 security label enforcement, consent directive evaluation, SMART-on-FHIR
- GSF-018 Privacy Module: Data classification engine, anonymization/pseudonymization, consent management
- GSF-019 Threat Detection Module: Real-time threat detection, anomaly detection, SIEM integration
- GSF-020 Integrity Module: File integrity monitoring, configuration drift detection, runtime integrity verification
- Complete threat model following STRIDE methodology
- Risk register with 25+ identified risks across technical, operational, compliance, and healthcare categories
- Attack surface analysis covering network, application, supply chain, physical, and healthcare-specific vectors
- Incident response plan aligned with NIST SP 800-61 Rev 2
- Disaster recovery plan with 4-hour RPO and 1-hour RTO targets
- Business continuity plan for Iraqi governorates with offline-first operations
- Compliance mapping across 15+ security frameworks and regulations
- Security scorecard with quarterly review process
- Architecture documentation with Clean Architecture layers and Zero Trust boundaries
- Development roadmap through Q4 2027 certification milestone
