"""PROGRAM-STABLE-004 — Domain Platform persistence models.

Runtime registrations for the Domain Platform Framework: domain
registrations, instances, versions, contracts, lifecycle events, and
workspace bindings. All tables live in the identity base (``niam_domain_*``)
and are managed by the DomainService.
"""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Text

from app.identity.base import IdentityBaseEntity


class DomainRegistration(IdentityBaseEntity):
    """A Domain installed on the platform (Phase 5 lifecycle owner)."""

    __tablename__ = "niam_domain_registrations"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    domain_code = Column(String(50), unique=True, nullable=False, index=True)
    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(30), nullable=False)
    workspace_type = Column(String(50), nullable=False, index=True)
    lifecycle_state = Column(String(20), default="installed", nullable=False, index=True)
    blueprint = Column(JSON, nullable=False)
    contracts = Column(JSON, nullable=True)
    shared_core_usage = Column(JSON, nullable=True)
    certification = Column(JSON, nullable=True)
    settings = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class DomainInstance(IdentityBaseEntity):
    """A deployed instance of a Domain (independent deployability)."""

    __tablename__ = "niam_domain_instances"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    instance_id = Column(String(100), unique=True, nullable=False, index=True)
    domain_id = Column(
        String(26), ForeignKey("niam_domain_registrations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    environment = Column(String(50), nullable=False)
    version = Column(String(30), nullable=False)
    state = Column(String(20), default="installed", nullable=False)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    health = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class DomainVersionRecord(IdentityBaseEntity):
    """Independent version history for a Domain (Phase 5)."""

    __tablename__ = "niam_domain_versions"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    domain_id = Column(
        String(26), ForeignKey("niam_domain_registrations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version = Column(String(30), nullable=False)
    semver = Column(String(30), nullable=False)
    certified = Column(Boolean, default=False, nullable=False)
    compatibility = Column(JSON, nullable=True)
    changelog = Column(Text, nullable=True)


class DomainContractRecord(IdentityBaseEntity):
    """A versioned cross-domain contract (Phase 4)."""

    __tablename__ = "niam_domain_contracts"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    contract_id = Column(String(100), unique=True, nullable=False, index=True)
    provider_domain_id = Column(
        String(26), ForeignKey("niam_domain_registrations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    consumer_domain_id = Column(
        String(26), ForeignKey("niam_domain_registrations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind = Column(String(20), nullable=False)
    version = Column(String(30), nullable=False)
    endpoint = Column(String(300), nullable=False)
    documentation_url = Column(String(300), nullable=False)
    status = Column(String(20), default="published", nullable=False)
    summary = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class DomainLifecycleEventRecord(IdentityBaseEntity):
    """Immutable audit trail of Domain lifecycle transitions (Phase 5)."""

    __tablename__ = "niam_domain_lifecycle_events"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    domain_id = Column(
        String(26), ForeignKey("niam_domain_registrations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action = Column(String(30), nullable=False)
    from_state = Column(String(20), nullable=False)
    to_state = Column(String(20), nullable=False)
    version = Column(String(30), nullable=True)


class DomainWorkspaceBindingRecord(IdentityBaseEntity):
    """The Domain <-> Workspace binding (Phase 6)."""

    __tablename__ = "niam_domain_workspace_bindings"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    domain_id = Column(
        String(26), ForeignKey("niam_domain_registrations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_type = Column(String(50), nullable=False, index=True)
    ui = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


__all__ = [
    "DomainContractRecord",
    "DomainInstance",
    "DomainLifecycleEventRecord",
    "DomainRegistration",
    "DomainVersionRecord",
    "DomainWorkspaceBindingRecord",
]
