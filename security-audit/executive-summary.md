# GULA Platform — Executive Security Assessment Summary

**Assessment Date:** July 24, 2026
**Scope:** Full-stack healthcare platform (FastAPI backend, React frontend, microservices, Docker, K8s, Terraform)
**Classification:** CONFIDENTIAL — Healthcare Data (PHI)

## Overview

GULA Platform is a comprehensive national healthcare laboratory management system designed for the Iraqi healthcare system. The platform handles sensitive patient health information (PHI) and integrates with national identity systems.

## Key Findings Summary

| Severity | Count |
|----------|-------|
| Critical | 12 |
| High | 34 |
| Medium | 28 |
| Low | 47 |
| Informational | 18 |

## Critical Risk Items

1. **Hardcoded Secrets in `.env` file** — Production-grade cryptographic keys and database credentials stored in plaintext in `.env`
2. **Plaintext Secrets in Kubernetes ConfigMap** — `k8s/base/configmap.yaml` stores configuration with sensitive values
3. **Terraform: Plain HTTP ALB Listeners** — Application Load Balancer listeners not using HTTPS
4. **Terraform: Unrestricted Egress Security Groups** — Multiple security groups allow 0.0.0.0/0 egress
5. **No Container Image Signing** — No Docker Content Trust or cosign verification in CI/CD
6. **No Secrets Management Solution** — No Vault, AWS Secrets Manager, or External Secrets Operator integrated
7. **K8s Pods Running as Root** — Multiple deployments lack security context (run as root by default)
8. **CSP Allows `unsafe-inline` and `unsafe-eval`** — Nginx CSP header permits both `'unsafe-inline'` and `'unsafe-eval'`
9. **No MFA Enforcement for Privileged Users** — MFA is optional, not enforced
10. **No Database Encryption at Rest** — No TDE or application-layer encryption for PHI at rest
11. **Hardcoded Test Secrets in Test Files** — Test files use real-looking encryption keys that match production patterns
12. **Supabase Secret Exposure** — `SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_KEY` in environment

## Strengths

- Comprehensive RBAC/ABAC security model with multi-role hierarchy
- Strong password hashing (bcrypt with cost factor 12)
- JWT with blacklisting (Redis-based revocation)
- Rate limiting on auth/public/admin endpoints
- Security headers middleware (HSTS, CSP, X-Frame-Options, etc.)
- Readiness middleware to prevent traffic during startup
- Audit logging throughout the platform
- Break-glass emergency access system
- Consent enforcement engine
- Purpose-of-use enforcement
- VIP protection and minor protection rules
- Container healthcheck configurations
- `no-new-privileges` security option on containers

## Security Score

**Overall Score: 452/1000** (Needs Improvement)

## Immediate Actions Required

1. Remove plaintext secrets from `.env` — use secrets manager
2. Implement secrets management for Kubernetes (ESO + Vault)
3. Add HTTPS listeners to ALB in Terraform
4. Remove `unsafe-inline` and `unsafe-eval` from CSP
5. Enforce MFA for all privileged users
6. Implement database encryption at rest
7. Add Pod Security Standards (PSS) to all K8s deployments
8. Implement container image signing in CI/CD pipeline
9. Add SAST scanning to CI/CD pipeline
10. Set up dependency vulnerability scanning
