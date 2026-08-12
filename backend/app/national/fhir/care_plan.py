from __future__ import annotations

from typing import Any

from app.ehr.models.care_plan import CarePlan, CarePlanActivity, CarePlanGoal


class FHIRCarePlanMapper:
    RESOURCE_TYPE = "CarePlan"

    @classmethod
    def from_model(cls, care_plan: CarePlan, goals: list[CarePlanGoal] | None = None, activities: list[CarePlanActivity] | None = None) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": care_plan.fhir_id or care_plan.id,
            "status": cls._build_status(care_plan.status.value if care_plan.status else "draft"),
            "intent": care_plan.intent or "plan",
            "category": [{"coding": [{"code": care_plan.category}]}] if care_plan.category else [],
            "title": care_plan.title_ar or care_plan.title,
            "description": care_plan.description,
            "subject": {"reference": f"Patient/{care_plan.patient_id}"},
            "encounter": {"reference": f"Encounter/{care_plan.encounter_id}"} if care_plan.encounter_id else None,
            "author": {"reference": f"Practitioner/{care_plan.practitioner_id}"} if care_plan.practitioner_id else None,
            "period": cls._build_period(care_plan),
            "goal": cls._build_goal_refs(goals),
            "activity": cls._build_activities(activities, goals),
            "supportingInfo": cls._build_supporting_info(care_plan),
            "note": [{"text": care_plan.notes}] if care_plan.notes else [],
        }
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def from_goal(cls, goal: CarePlanGoal) -> dict[str, Any]:
        resource = {
            "resourceType": "Goal",
            "id": goal.fhir_id or goal.id,
            "lifecycleStatus": goal.status or "in-progress",
            "description": {"text": goal.description_ar or goal.description},
            "priority": {"coding": [{"code": str(goal.priority)}]} if goal.priority else None,
            "target": cls._build_goal_target(goal),
            "achievementStatus": {"coding": [{"code": goal.outcome}]} if goal.outcome else None,
            "note": [{"text": goal.notes}] if goal.notes else [],
        }
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _build_status(cls, status: str) -> str:
        mapping = {"draft": "draft", "active": "active", "completed": "completed", "revised": "revised", "cancelled": "cancelled", "entered_in_error": "entered-in-error"}
        return mapping.get(status, "unknown")

    @classmethod
    def _build_period(cls, care_plan: CarePlan) -> dict | None:
        if not care_plan.period_start and not care_plan.period_end:
            return None
        period = {}
        if care_plan.period_start:
            period["start"] = care_plan.period_start.isoformat()
        if care_plan.period_end:
            period["end"] = care_plan.period_end.isoformat()
        return period

    @classmethod
    def _build_goal_refs(cls, goals: list[CarePlanGoal] | None) -> list[dict]:
        if not goals:
            return []
        return [{"reference": f"Goal/{g.fhir_id or g.id}"} for g in goals if g.id]

    @classmethod
    def _build_activities(cls, activities: list[CarePlanActivity] | None, goals: list[CarePlanGoal] | None) -> list[dict]:
        if not activities:
            return []
        goal_map = {g.id: g for g in (goals or [])}
        return [cls._build_activity(a, goal_map.get(a.goal_id)) for a in activities]

    @classmethod
    def _build_activity(cls, activity: CarePlanActivity, goal: CarePlanGoal | None) -> dict:
        ref: dict[str, Any] = {
            "id": activity.fhir_id or activity.id,
            "extension": [],
        }
        detail: dict[str, Any] = {
            "status": activity.status or "not-started",
            "description": activity.description_ar or activity.description,
            "scheduledPeriod": cls._build_activity_schedule(activity),
            "performer": [{"actor": {"reference": f"Practitioner/{activity.performer_id}"}, "display": activity.performer or ""}] if activity.performer_id else [],
            "location": {"display": activity.location} if activity.location else None,
            "outcomeCodeableConcept": [{"text": activity.outcome}] if activity.outcome else [],
            "progress": [{"text": activity.progress_notes}] if activity.progress_notes else [],
        }
        if activity.activity_code and activity.activity_code_system:
            detail["code"] = {"coding": [{"system": activity.activity_code_system, "code": activity.activity_code}]}
        if goal:
            detail["goal"] = [{"reference": f"Goal/{goal.fhir_id or goal.id}"}]
        ref["detail"] = {k: v for k, v in detail.items() if v is not None and v != []}
        return ref

    @classmethod
    def _build_activity_schedule(cls, activity: CarePlanActivity) -> dict | None:
        if not activity.scheduled_start and not activity.scheduled_end:
            return None
        period = {}
        if activity.scheduled_start:
            period["start"] = activity.scheduled_start.isoformat()
        if activity.scheduled_end:
            period["end"] = activity.scheduled_end.isoformat()
        return period

    @classmethod
    def _build_goal_target(cls, goal: CarePlanGoal) -> list[dict] | None:
        if not goal.target_date and not goal.achievement_date:
            return None
        target: dict[str, Any] = {}
        if goal.target_date:
            target["dueDate"] = goal.target_date.isoformat()
        if goal.achievement_date:
            target["detailBoolean"] = True
        if goal.measured_by:
            target["measure"] = {"coding": [{"code": goal.measured_by}]}
        return [target]

    @classmethod
    def _build_supporting_info(cls, care_plan: CarePlan) -> list[dict] | None:
        if not care_plan.supporting_info:
            return None
        if isinstance(care_plan.supporting_info, list):
            return [{"reference": item} if isinstance(item, str) else item for item in care_plan.supporting_info]
        return [care_plan.supporting_info]
