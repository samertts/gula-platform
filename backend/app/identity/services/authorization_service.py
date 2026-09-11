from __future__ import annotations

from sqlalchemy.orm import Session

from app.identity.repositories.assignment_repository import AssignmentRepository
from app.identity.repositories.organization_repository import OrganizationRepository
from app.identity.repositories.policy_repository import PolicyRepository
from app.identity.services.clinical_policy_evaluator import ClinicalPolicyEvaluator


class AuthorizationService:

    def __init__(self, session: Session) -> None:
        self.session = session
        self.assignment_repo = AssignmentRepository(session)
        self.organization_repo = OrganizationRepository(session)
        self.policy_repo = PolicyRepository(session)

    def has_permission(
        self,
        person_id: str,
        permission: str,
        organization_id: str | None = None,
        facility_resource_id: int | None = None,
    ) -> bool:
        """Evaluate a precise policy within an explicitly resolved clinical scope."""

        assignments = self.assignment_repo.find_by_person_id(person_id)
        policies = self.policy_repo.find_enabled_for_action(permission)
        return ClinicalPolicyEvaluator.allows(
            policies=policies,
            assignments=assignments,
            person_id=person_id,
            permission=permission,
            organization_id=organization_id,
            facility_resource_id=facility_resource_id,
        )

    def get_assignments_for_person(self, person_id: str) -> list:
        return self.assignment_repo.find_by_person_id(person_id)

    def get_assignments_for_organization(self, org_id: str) -> list:
        return self.assignment_repo.find_by_organization_id(org_id)
