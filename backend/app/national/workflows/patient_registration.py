from __future__ import annotations

from app.national.workflows.base import WorkflowContext, WorkflowEngine, WorkflowState, WorkflowStep, WorkflowStepStatus


class PatientRegistrationWorkflow(WorkflowEngine[dict]):
    STATES = {
        "initiated": ["identity_verification", "demographics_collection", "contact_info", "guardian_assignment", "consent_obtained", "completed"],
        "identity_verification": ["demographics_collection", "failed"],
        "demographics_collection": ["contact_info", "failed"],
        "contact_info": ["guardian_assignment", "failed"],
        "guardian_assignment": ["consent_obtained", "skipped", "completed"],
        "consent_obtained": ["completed", "failed"],
        "completed": [],
        "failed": ["rollback"],
        "rollback": ["initiated", "cancelled"],
        "cancelled": [],
    }

    async def execute(self, context: WorkflowContext, input_data: dict) -> WorkflowContext:
        context.state = WorkflowState.IN_PROGRESS
        try:
            if input_data.get("identity_type") == "newborn":
                await self._handle_newborn_registration(context, input_data)
            elif input_data.get("identity_type") == "foreigner":
                await self._handle_foreigner_registration(context, input_data)
            else:
                await self._handle_standard_registration(context, input_data)
            context.state = WorkflowState.COMPLETED
        except Exception as e:
            context.state = WorkflowState.FAILED
            context.errors.append(str(e))
        return context

    async def _handle_standard_registration(self, context: WorkflowContext, data: dict) -> None:
        step1 = WorkflowStep(name="identity_verification")
        step1.status = WorkflowStepStatus.SUCCEEDED
        self.add_step(step1)
        step2 = WorkflowStep(name="demographics_collection")
        step2.status = WorkflowStepStatus.SUCCEEDED
        self.add_step(step2)
        step3 = WorkflowStep(name="completed")
        step3.status = WorkflowStepStatus.SUCCEEDED
        self.add_step(step3)

    async def _handle_newborn_registration(self, context: WorkflowContext, data: dict) -> None:
        step1 = WorkflowStep(name="birth_certificate_verification")
        step1.status = WorkflowStepStatus.SUCCEEDED
        self.add_step(step1)
        step2 = WorkflowStep(name="guardian_assignment")
        step2.status = WorkflowStepStatus.SUCCEEDED
        self.add_step(step2)
        step3 = WorkflowStep(name="temporary_health_number")
        step3.status = WorkflowStepStatus.SUCCEEDED
        self.add_step(step3)

    async def _handle_foreigner_registration(self, context: WorkflowContext, data: dict) -> None:
        step1 = WorkflowStep(name="passport_verification")
        step1.status = WorkflowStepStatus.SUCCEEDED
        self.add_step(step1)
        step2 = WorkflowStep(name="visa_verification")
        step2.status = WorkflowStepStatus.SUCCEEDED
        self.add_step(step2)
        step3 = WorkflowStep(name="biometric_enrollment")
        step3.status = WorkflowStepStatus.SUCCEEDED
        self.add_step(step3)

    async def compensate(self, context: WorkflowContext) -> None:
        context.state = WorkflowState.COMPENSATED
        for step in reversed(self._steps):
            if step.status == WorkflowStepStatus.SUCCEEDED:
                step.status = WorkflowStepStatus.COMPENSATED

    async def can_transition(self, from_state: WorkflowState, to_state: WorkflowState) -> bool:
        valid = self.get_state_flow().get(from_state, [])
        return to_state in valid
