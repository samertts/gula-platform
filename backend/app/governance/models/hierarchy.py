from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app._compat import UTC

from ..base import GovernanceBaseEntity
from ..enums import (
    ActingRoleStatus,
    AdministrationType,
    DelegationStatus,
    DelegationType,
    GovernanceNodeType,
)


class GovernanceNode(GovernanceBaseEntity):
    __tablename__ = "gov_hierarchy_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_type = Column(Enum(GovernanceNodeType), nullable=False, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    parent_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=True, index=True)
    root_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=True, index=True)
    governorate = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("code", name="uq_gov_hierarchy_node_code"),
        {"extend_existing": True},
    )


class GovernanceRole(GovernanceBaseEntity):
    __tablename__ = "gov_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=False, index=True)
    role_name_ar = Column(String(200), nullable=False)
    role_name_en = Column(String(200), nullable=True)
    permissions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class Delegation(GovernanceBaseEntity):
    __tablename__ = "gov_delegations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    delegator_node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=False, index=True)
    delegate_node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=False, index=True)
    delegation_type = Column(Enum(DelegationType), nullable=False)
    status = Column(Enum(DelegationStatus), nullable=False, default=DelegationStatus.ACTIVE, index=True)
    scope = Column(JSON, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class ActingAppointment(GovernanceBaseEntity):
    __tablename__ = "gov_acting_appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=False, index=True)
    acting_node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=False, index=True)
    status = Column(Enum(ActingRoleStatus), nullable=False, default=ActingRoleStatus.ACTIVE, index=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=True)
    approved_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class EmergencyAdministration(GovernanceBaseEntity):
    __tablename__ = "gov_emergency_admin"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=False, index=True)
    administration_type = Column(Enum(AdministrationType), nullable=False, default=AdministrationType.EMERGENCY)
    administering_node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=True)
    status = Column(String(20), default="active", index=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    declaration_reason = Column(Text, nullable=True)
    declaration_order = Column(String(200), nullable=True)
    declared_by = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class TemporaryAdministration(GovernanceBaseEntity):
    __tablename__ = "gov_temporary_admin"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=False, index=True)
    temporary_node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=False, index=True)
    status = Column(String(20), default="active", index=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=True)
    approved_by = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
