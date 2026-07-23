from __future__ import annotations

"""
NIAM — National Identity & Access Management Platform.

This module is the sovereign identity provider for the entire GULA National
Digital Health Platform. It manages:

  - Person Registry (citizens, workforce, external)
  - Identity Types (citizen, government, private, machine, guest, federation)
  - Organization Registry (ministry, hospitals, labs, universities, etc.)
  - Enterprise Accounts (machine identities for organizations)
  - Citizen Accounts (self-registration, OTP, identity verification)
  - Government Workforce (HR-driven employment lifecycle)
  - Private Workforce (enterprise-admin managed)
  - Employment Engine (multi-organization, transfers, termination)
  - Assignment Engine (org/facility/dept/committee assignments)
  - Professional Licensing (medical, lab, pharmacy, certifications)
  - RBAC + ABAC + Context-Based Access Control
  - Policy Engine (ABAC with conditions and obligations)
  - Session Management (single-active-session, device-aware)
  - Device Management (trusted devices, fingerprinting, risk scoring)
  - Authentication (password, passkeys, FIDO2, OTP, OAuth2, OIDC, smart cards)
  - Audit (immutable, hash-chained, every identity event)
  - Security (impossible travel, brute force, credential stuffing detection)

The identity module is COMPLETELY INDEPENDENT from the laboratory module.
It can be used by any current or future GULA sub-system.
"""


def get_router():
    from .api.router import router as _router
    return _router


router = None
__all__ = ["get_router"]
