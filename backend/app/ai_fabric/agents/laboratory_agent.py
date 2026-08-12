from __future__ import annotations

import logging
from typing import Any

from app.ai_fabric.agents.base import AgentTool, AIAgent

logger = logging.getLogger("gula.ai_fabric.agents.laboratory")


class LaboratoryAgent(AIAgent):
    def __init__(self, agent_id: str = "", name: str = "LaboratoryAgent") -> None:
        super().__init__(agent_id=agent_id, name=name)

    def _register_default_tools(self) -> None:
        self.register_tool(AgentTool(
            name="delta_check",
            description="Perform delta check on patient results",
            fn=self._tool_delta_check,
            parameters={"patient_id": "str", "test_name": "str", "new_value": "float"},
        ))
        self.register_tool(AgentTool(
            name="qc_analysis",
            description="Analyze quality control data",
            fn=self._tool_qc_analysis,
            parameters={"instrument": "str", "control_data": "list"},
        ))
        self.register_tool(AgentTool(
            name="workload_forecast",
            description="Predict laboratory workload and TAT",
            fn=self._tool_workload_forecast,
            parameters={"department": "str", "period": "str"},
        ))

    def can_handle(self, task_type: str) -> bool:
        return task_type in ("laboratory", "lab", "qc", "delta", "workload")

    def _execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = input_data.get("action", "")
        if action == "delta_check":
            return self._run_delta_check(input_data)
        if action == "qc_analysis":
            return self._run_qc_analysis(input_data)
        if action == "workload_forecast":
            return self._forecast_workload(input_data)
        return {"error": f"Unknown action: {action}"}

    def _run_delta_check(self, data: dict[str, Any]) -> dict[str, Any]:
        patient_id = data.get("patient_id", "")
        test_name = data.get("test_name", "")
        new_value = data.get("new_value")
        previous_value = data.get("previous_value")
        delta_pct = 0.0
        significant = False
        if previous_value and new_value:
            if previous_value != 0:
                delta_pct = abs((float(new_value) - float(previous_value)) / float(previous_value)) * 100
            significant = delta_pct > 20.0
        return {
            "patient_id": patient_id,
            "test_name": test_name,
            "previous_value": previous_value,
            "new_value": new_value,
            "delta_pct": round(delta_pct, 2),
            "significant": significant,
            "recommendation": "Flag for review" if significant else "Within expected variation",
        }

    def _run_qc_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        instrument = data.get("instrument", "")
        control_data = data.get("control_data", [])
        rules_violated: list[str] = []
        if control_data:
            values = [float(c.get("value", 0)) for c in control_data]
            mean = sum(values) / len(values) if values else 0
            if len(values) > 1:
                variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
                sd = variance ** 0.5
                for v in values:
                    if abs(v - mean) > 3 * sd:
                        rules_violated.append(f"1:3s (value={v})")
                    elif abs(v - mean) > 2 * sd:
                        rules_violated.append(f"1:2s warning (value={v})")
        return {
            "instrument": instrument,
            "samples_analyzed": len(control_data),
            "rules_violated": rules_violated,
            "status": "out_of_control" if rules_violated else "in_control",
        }

    def _forecast_workload(self, data: dict[str, Any]) -> dict[str, Any]:
        department = data.get("department", "")
        period = data.get("period", "daily")
        return {
            "department": department,
            "period": period,
            "predicted_orders": 0,
            "predicted_tat_minutes": 0,
            "peak_hours": [],
            "staff_required": 0,
        }

    def _tool_delta_check(self, **kwargs: Any) -> dict[str, Any]:
        return self._run_delta_check(kwargs)

    def _tool_qc_analysis(self, **kwargs: Any) -> dict[str, Any]:
        return self._run_qc_analysis(kwargs)

    def _tool_workload_forecast(self, **kwargs: Any) -> dict[str, Any]:
        return self._forecast_workload(kwargs)
