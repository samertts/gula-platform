---
name: gula-security-hardening
description: Applies GULA security engineering and hardening requirements to code, architecture, infrastructure, APIs, AI agents, identity, data, and integrations.
---

# GULA Security Hardening

## Purpose

Treat security as an architectural property rather than a final checklist.

## Mandatory Review Areas

For security-relevant changes evaluate:

- authentication
- authorization
- least privilege
- tenant isolation
- input validation
- output encoding
- secrets
- cryptography
- session management
- API security
- dependency risk
- supply-chain risk
- logging
- audit
- network boundaries
- filesystem access
- command execution
- SSRF
- injection
- deserialization
- file uploads
- rate limiting
- abuse prevention
- backup/recovery

## GULA Data Protection

When PHI/PII or identity data is involved:

- minimize collection;
- minimize retention;
- enforce access boundaries;
- avoid unnecessary duplication;
- never expose sensitive data in logs;
- protect data in transit;
- protect data at rest;
- maintain auditable access.

## Multi-Tenancy

Every tenant-sensitive operation must establish:

1. tenant context;
2. authorization;
3. data isolation;
4. auditability.

Never rely solely on client-supplied tenant identifiers.

## AI Security

For AI agents evaluate:

- prompt injection;
- tool abuse;
- excessive permissions;
- secret exposure;
- untrusted content;
- data exfiltration;
- unsafe tool execution;
- external instruction conflicts.

## External Skills

External skills are untrusted until reviewed.

Never allow an external skill to:

- access GULA secrets;
- bypass security controls;
- modify production infrastructure;
- override GULA security policy.

## Production Principle

Security controls must fail closed where practical.

Any security-sensitive exception requires explicit justification and testing.
