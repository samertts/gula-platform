from __future__ import annotations

from typing import Any

from app.national.domain.encounter import Encounter
from app.national.exceptions import EncounterNotFoundError
from app.national.workflows import EncounterWorkflow, WorkflowContext
from shared.events import events


class EncounterService:
    def __init__(self) -> None:
        self.workflow = EncounterWorkflow()

    async def create_encounter(self, data: dict[str, Any]) -> Encounter:
        encounter = Encounter(**{k: v for k, v in data.items() if hasattr(Encounter, k)})
        ctx = WorkflowContext(workflow_id=encounter.id, workflow_type="encounter")
        await self.workflow.execute(ctx, data)
        events.emit("national.encounter.created", {"encounter_id": encounter.id, **data})
        return encounter

    async def complete_encounter(self, encounter_id: str) -> Encounter:
        encounter = Encounter.query.get(encounter_id)
        if not encounter:
            raise EncounterNotFoundError(encounter_id)
        events.emit("national.encounter.completed", {"encounter_id": encounter_id})
        return encounter

    async def cancel_encounter(self, encounter_id: str, reason: str = "") -> Encounter:
        encounter = Encounter.query.get(encounter_id)
        if not encounter:
            raise EncounterNotFoundError(encounter_id)
        events.emit("national.encounter.cancelled", {"encounter_id": encounter_id, "reason": reason})
        return encounter
