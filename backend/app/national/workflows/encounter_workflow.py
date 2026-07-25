from __future__ import annotations

from app.national.workflows.base import (
    WorkflowContext,
    WorkflowEngine,
    WorkflowState,
    WorkflowStep,
    WorkflowStepStatus,
)


class EncounterWorkflow(WorkflowEngine[dict]):
    async def execute(self, context: WorkflowContext, input_data: dict) -> WorkflowContext:
        context.state = WorkflowState.IN_PROGRESS
        try:
            encounter_type = input_data.get("encounter_type", "outpatient")
            if encounter_type == "emergency":
                await self._handle_emergency_encounter(context, input_data)
            elif encounter_type == "inpatient":
                await self._handle_inpatient_encounter(context, input_data)
            else:
                await self._handle_outpatient_encounter(context, input_data)
            context.state = WorkflowState.COMPLETED
        except Exception as e:
            context.state = WorkflowState.FAILED
            context.errors.append(str(e))
        return context

    async def _handle_outpatient_encounter(self, context: WorkflowContext, data: dict) -> None:
        for step_name in [
            "registration_check",
            "vital_signs",
            "consultation",
            "diagnosis",
            "disposition",
        ]:
            step = WorkflowStep(name=step_name)
            step.status = WorkflowStepStatus.SUCCEEDED
            self.add_step(step)

    async def _handle_emergency_encounter(self, context: WorkflowContext, data: dict) -> None:
        for step_name in ["triage", "emergency_assessment", "immediate_care", "disposition"]:
            step = WorkflowStep(name=step_name)
            step.status = WorkflowStepStatus.SUCCEEDED
            self.add_step(step)

    async def _handle_inpatient_encounter(self, context: WorkflowContext, data: dict) -> None:
        for step_name in [
            "admission",
            "ward_assignment",
            "care_plan",
            "daily_rounds",
            "discharge_planning",
        ]:
            step = WorkflowStep(name=step_name)
            step.status = WorkflowStepStatus.SUCCEEDED
            self.add_step(step)

    async def compensate(self, context: WorkflowContext) -> None:
        context.state = WorkflowState.COMPENSATED

    async def can_transition(self, from_state: WorkflowState, to_state: WorkflowState) -> bool:
        return to_state in self.get_state_flow().get(from_state, [])
