from app.national.exceptions import NationalDomainError


class RuleNotFoundError(NationalDomainError):
    def __init__(self, rule_id: str) -> None:
        self.rule_id = rule_id
        super().__init__(f"Rule not found: {rule_id}")


class RuleValidationError(NationalDomainError):
    def __init__(self, rule_id: str, reason: str) -> None:
        self.rule_id = rule_id
        self.reason = reason
        super().__init__(f"Rule validation failed: {rule_id}: {reason}")


class RuleEvaluationError(NationalDomainError):
    def __init__(self, rule_id: str, reason: str) -> None:
        self.rule_id = rule_id
        self.reason = reason
        super().__init__(f"Rule evaluation failed: {rule_id}: {reason}")


class RuleConflictError(NationalDomainError):
    def __init__(self, rule_id: str, conflicting_rule_id: str, reason: str) -> None:
        self.rule_id = rule_id
        self.conflicting_rule_id = conflicting_rule_id
        self.reason = reason
        super().__init__(f"Rule conflict between {rule_id} and {conflicting_rule_id}: {reason}")


class RuleVersionError(NationalDomainError):
    def __init__(self, rule_id: str, current_version: int, expected_version: int) -> None:
        self.rule_id = rule_id
        self.current_version = current_version
        self.expected_version = expected_version
        super().__init__(f"Rule version mismatch for {rule_id}: current v{current_version}, expected v{expected_version}")
