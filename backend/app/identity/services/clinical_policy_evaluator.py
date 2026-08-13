from __future__ import annotations


class ClinicalPolicyEvaluator:
    """Pure, deny-by-default policy evaluation shared by sync and async readers."""

    @staticmethod
    def assignment_is_eligible(
        assignment,
        *,
        organization_id: str,
        facility_resource_id: int,
    ) -> bool:
        return (
            assignment.status == "active"
            and assignment.is_active is True
            and str(assignment.clinical_organization_resource_id) == organization_id
            and assignment.clinical_facility_resource_id == facility_resource_id
        )

    @classmethod
    def allows(
        cls,
        *,
        policies,
        assignments,
        person_id: str,
        permission: str,
        organization_id: str | None,
        facility_resource_id: int | None,
    ) -> bool:
        if not organization_id or facility_resource_id is None:
            return False

        eligible = [
            assignment
            for assignment in assignments
            if cls.assignment_is_eligible(
                assignment,
                organization_id=organization_id,
                facility_resource_id=facility_resource_id,
            )
        ]
        if not eligible:
            return False

        decisions = [
            str(policy.effect).lower()
            for policy in policies
            for assignment in eligible
            if cls._policy_applies(
                policy=policy,
                assignment=assignment,
                person_id=person_id,
                permission=permission,
                organization_id=organization_id,
                facility_resource_id=facility_resource_id,
            )
        ]
        return "deny" not in decisions and "allow" in decisions

    @staticmethod
    def _policy_applies(
        *,
        policy,
        assignment,
        person_id: str,
        permission: str,
        organization_id: str,
        facility_resource_id: int,
    ) -> bool:
        resource = permission.rsplit(".", 1)[0]
        subjects = policy.subjects or {}
        conditions = policy.conditions or {}
        role_ids = subjects.get("role_ids", [])
        person_ids = subjects.get("person_ids", [])
        assignment_ids = subjects.get("assignment_ids", [])
        organization_ids = {str(value) for value in conditions.get("clinical_organization_resource_ids", [])}
        try:
            facility_ids = {int(value) for value in conditions.get("clinical_facility_resource_ids", [])}
        except (TypeError, ValueError):
            return False

        return (
            permission in (policy.actions or [])
            and resource in (policy.resources or [])
            and bool(role_ids or person_ids or assignment_ids)
            and bool(organization_ids)
            and bool(facility_ids)
            and (
                assignment.role_id in role_ids
                or person_id in person_ids
                or assignment.id in assignment_ids
            )
            and organization_id in organization_ids
            and facility_resource_id in facility_ids
        )
