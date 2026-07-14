from __future__ import annotations


class Provider_managementPolicy:
    def __init__(self):
        self._rules: list[dict] = []

    def evaluate(self, context: dict) -> list[str]:
        violations = []
        for rule in self._rules:
            if not rule.get("condition", lambda c: True)(context):
                violations.append(rule.get("message", "Policy violation"))
        return violations

    def add_rule(self, condition, message: str):
        self._rules.append({"condition": condition, "message": message})
