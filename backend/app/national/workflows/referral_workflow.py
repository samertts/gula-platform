from __future__ import annotations

from app.national.workflows.base import WorkflowContext, WorkflowEngine, WorkflowState, WorkflowStep, WorkflowStepStatus


class ReferralWorkflow(WorkflowEngine[dict]):
    async def execute(self, context: WorkflowContext, input_data: dict) -> WorkflowContext:
        context.state = WorkflowState.IN_PROGRESS
        try:
            for step_name in ["referral_initiation", "clinical_review", "facility_selection", "notification", "acceptance"]:
                step = WorkflowStep(name=step_name)
                step.status = WorkflowStepStatus.SUCCEEDED
                self.add_step(step)
            context.state = WorkflowState.COMPLETED
        except Exception as e:
            context.state = WorkflowState.FAILED
            context.errors.append(str(e))
        return context

    async def compensate(self, context: WorkflowContext) -> None:
        context.state = WorkflowState.COMPENSATED

    async def can_transition(self, from_state: WorkflowState, to_state: WorkflowState) -> bool:
        return to_state in self.get_state_flow().get(from_state, [])
