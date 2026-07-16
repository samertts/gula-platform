from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app._compat import UTC

from ..enums import (
    ActingRoleStatus,
    AdministrationType,
    DelegationStatus,
    DelegationType,
    GovernanceNodeType,
)
from ..models.hierarchy import (
    ActingAppointment,
    Delegation,
    EmergencyAdministration,
    GovernanceNode,
    GovernanceRole,
    TemporaryAdministration,
)


class GovernanceHierarchyService:
    def __init__(self, db: Session):
        self.db = db

    def create_node(
        self,
        node_type: GovernanceNodeType,
        code: str,
        name_ar: str,
        name_en: str | None = None,
        parent_id: int | None = None,
        governorate: str | None = None,
        district: str | None = None,
        metadata_json: dict | None = None,
    ) -> GovernanceNode:
        node = GovernanceNode(
            node_type=node_type,
            code=code,
            name_ar=name_ar,
            name_en=name_en,
            parent_id=parent_id,
            governorate=governorate,
            district=district,
            metadata_json=metadata_json,
        )
        self.db.add(node)
        self.db.flush()
        if parent_id:
            parent = self.get_node(parent_id)
            node.root_id = parent.root_id if parent else node.id
        else:
            node.root_id = node.id
        return node

    def get_node(self, node_id: int) -> GovernanceNode | None:
        return self.db.query(GovernanceNode).filter(GovernanceNode.id == node_id).first()

    def get_node_by_code(self, code: str) -> GovernanceNode | None:
        return self.db.query(GovernanceNode).filter(GovernanceNode.code == code).first()

    def get_children(self, parent_id: int, active_only: bool = True) -> list[GovernanceNode]:
        q = self.db.query(GovernanceNode).filter(GovernanceNode.parent_id == parent_id)
        if active_only:
            q = q.filter(GovernanceNode.is_active.is_(True))
        return q.all()

    def get_subtree(self, root_id: int) -> list[GovernanceNode]:
        return (
            self.db.query(GovernanceNode)
            .filter(
                or_(
                    GovernanceNode.id == root_id,
                    GovernanceNode.root_id == root_id,
                )
            )
            .order_by(GovernanceNode.node_type, GovernanceNode.code)
            .all()
        )

    def get_ancestors(self, node_id: int) -> list[GovernanceNode]:
        ancestors: list[GovernanceNode] = []
        current = self.get_node(node_id)
        while current and current.parent_id:
            parent = self.get_node(current.parent_id)
            if parent:
                ancestors.insert(0, parent)
                current = parent
            else:
                break
        return ancestors

    def get_path(self, node_id: int) -> list[GovernanceNode]:
        return [*self.get_ancestors(node_id), self.get_node(node_id)]

    def deactivate_node(self, node_id: int) -> GovernanceNode | None:
        node = self.get_node(node_id)
        if node:
            node.is_active = False
        return node

    def create_role(
        self,
        node_id: int,
        name_ar: str,
        name_en: str | None = None,
        permissions: dict | None = None,
    ) -> GovernanceRole:
        role = GovernanceRole(
            node_id=node_id,
            role_name_ar=name_ar,
            role_name_en=name_en,
            permissions=permissions,
        )
        self.db.add(role)
        return role

    def create_delegation(
        self,
        delegator_node_id: int,
        delegate_node_id: int,
        delegation_type: DelegationType,
        scope: dict | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        reason: str | None = None,
        created_by: int | None = None,
    ) -> Delegation:
        delegation = Delegation(
            delegator_node_id=delegator_node_id,
            delegate_node_id=delegate_node_id,
            delegation_type=delegation_type,
            status=DelegationStatus.ACTIVE,
            scope=scope,
            start_date=start_date or datetime.now(UTC),
            end_date=end_date,
            reason=reason,
            created_by=created_by,
        )
        self.db.add(delegation)
        return delegation

    def revoke_delegation(self, delegation_id: int) -> Delegation | None:
        delegation = self.db.query(Delegation).filter(Delegation.id == delegation_id).first()
        if delegation:
            delegation.status = DelegationStatus.REVOKED
        return delegation

    def create_acting_appointment(
        self,
        node_id: int,
        acting_node_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        reason: str | None = None,
        approved_by: int | None = None,
    ) -> ActingAppointment:
        appointment = ActingAppointment(
            node_id=node_id,
            acting_node_id=acting_node_id,
            status=ActingRoleStatus.ACTIVE,
            start_date=start_date or datetime.now(UTC),
            end_date=end_date,
            reason=reason,
            approved_by=approved_by,
        )
        self.db.add(appointment)
        return appointment

    def create_emergency_administration(
        self,
        node_id: int,
        administering_node_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        reason: str | None = None,
        declaration_order: str | None = None,
        declared_by: str | None = None,
    ) -> EmergencyAdministration:
        admin = EmergencyAdministration(
            node_id=node_id,
            administration_type=AdministrationType.EMERGENCY,
            administering_node_id=administering_node_id,
            status="active",
            start_date=start_date or datetime.now(UTC),
            end_date=end_date,
            declaration_reason=reason,
            declaration_order=declaration_order,
            declared_by=declared_by,
        )
        self.db.add(admin)
        return admin

    def create_temporary_administration(
        self,
        original_node_id: int,
        temporary_node_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        reason: str | None = None,
        approved_by: str | None = None,
    ) -> TemporaryAdministration:
        temp_admin = TemporaryAdministration(
            original_node_id=original_node_id,
            temporary_node_id=temporary_node_id,
            status="active",
            start_date=start_date or datetime.now(UTC),
            end_date=end_date,
            reason=reason,
            approved_by=approved_by,
        )
        self.db.add(temp_admin)
        return temp_admin

    def get_active_delegations(self, node_id: int) -> list[Delegation]:
        return (
            self.db.query(Delegation)
            .filter(
                or_(
                    Delegation.delegator_node_id == node_id,
                    Delegation.delegate_node_id == node_id,
                ),
                Delegation.status == DelegationStatus.ACTIVE,
            )
            .all()
        )

    def get_active_acting(self, node_id: int) -> list[ActingAppointment]:
        return (
            self.db.query(ActingAppointment)
            .filter(
                or_(
                    ActingAppointment.node_id == node_id,
                    ActingAppointment.acting_node_id == node_id,
                ),
                ActingAppointment.status == ActingRoleStatus.ACTIVE,
            )
            .all()
        )
