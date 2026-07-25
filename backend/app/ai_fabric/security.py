from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.ai_fabric.security")


@dataclass
class InjectionResult:
    detected: bool = False
    score: float = 0.0
    patterns_matched: list[str] = field(default_factory=list)
    sanitized_text: str = ""


@dataclass
class ValidationResult:
    passed: bool = True
    issues: list[str] = field(default_factory=list)
    score: float = 1.0


@dataclass
class RedactionResult:
    original_text: str = ""
    redacted_text: str = ""
    pii_types_found: list[str] = field(default_factory=list)
    count: int = 0


class PromptInjectionProtector:
    def __init__(self) -> None:
        self._patterns: list[tuple[re.Pattern, str]] = [
            (
                re.compile(
                    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|directions)",
                    re.IGNORECASE,
                ),
                "instruction_override",
            ),
            (re.compile(r"(system|main|base)\s+prompt", re.IGNORECASE), "system_prompt_extraction"),
            (
                re.compile(r"forget\s+(all\s+)?(previous|prior|past)", re.IGNORECASE),
                "memory_manipulation",
            ),
            (re.compile(r"you\s+are\s+(not|now|instead)", re.IGNORECASE), "role_manipulation"),
            (
                re.compile(r"admin(isrator)?\s*(access|bypass|override)", re.IGNORECASE),
                "privilege_escalation",
            ),
            (
                re.compile(r"reveal\s+(your\s+)?(instructions|prompt|system|rules)", re.IGNORECASE),
                "instruction_reveal",
            ),
            (
                re.compile(r"output\s+(raw|original|unmodified|unfiltered)", re.IGNORECASE),
                "filter_bypass",
            ),
            (
                re.compile(r"simulate\s+(jailbreak|bypass|override)", re.IGNORECASE),
                "jailbreak_attempt",
            ),
            (
                re.compile(r"do\s+(not\s+)?(follow|obey|adhere)", re.IGNORECASE),
                "instruction_refusal",
            ),
            (re.compile(r"<[^>]*script[^>]*>", re.IGNORECASE), "xss_attempt"),
            (re.compile(r"DROP\s+(TABLE|DATABASE|INDEX)", re.IGNORECASE), "sql_injection"),
            (
                re.compile(
                    r"(api[_-]?key|secret[_-]?key|password|token)\s*[:=]\s*\S+", re.IGNORECASE,
                ),
                "credential_leak",
            ),
        ]

    def analyze(self, text: str) -> InjectionResult:
        result = InjectionResult(sanitized_text=text)
        for pattern, description in self._patterns:
            if pattern.search(text):
                result.patterns_matched.append(description)
                result.detected = True
        if result.patterns_matched:
            result.score = min(len(result.patterns_matched) * 0.25, 1.0)
            result.sanitized_text = self._sanitize(text)
        return result

    def _sanitize(self, text: str) -> str:
        sanitized = text
        for pattern, _ in self._patterns:
            sanitized = pattern.sub("[REDACTED]", sanitized)
        return sanitized

    async def is_safe(self, text: str) -> bool:
        result = self.analyze(text)
        return not result.detected

    def get_risk_score(self, text: str) -> float:
        return self.analyze(text).score


class OutputValidator:
    def __init__(self) -> None:
        self._blocked_phrases: list[str] = [
            "I cannot generate that",
            "I will not help with",
            "This is not medical advice",
        ]
        self._confidentiality_patterns: list[re.Pattern] = [
            re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            re.compile(r"\b\d{10,}\b"),
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        ]

    def validate(self, text: str) -> ValidationResult:
        issues: list[str] = []

        if len(text) > 100_000:
            issues.append("Output exceeds 100K characters")
        if not text.strip():
            issues.append("Output is empty")

        for phrase in self._blocked_phrases:
            if phrase.lower() in text.lower():
                issues.append(f"Contains blocked phrase: {phrase}")

        for pattern in self._confidentiality_patterns:
            if pattern.search(text):
                issues.append("Potential confidential data in output")

        score = max(0.0, 1.0 - len(issues) * 0.2)
        return ValidationResult(passed=len(issues) == 0, issues=issues, score=round(score, 2))

    def validate_structured(
        self, data: dict[str, Any], schema: dict[str, type] | None = None,
    ) -> ValidationResult:
        issues: list[str] = []
        if schema:
            for field_name, expected_type in schema.items():
                if field_name not in data:
                    issues.append(f"Missing field: {field_name}")
                elif not isinstance(data[field_name], expected_type):
                    issues.append(
                        f"Field {field_name} expected {expected_type.__name__}, got {type(data[field_name]).__name__}",
                    )
        return ValidationResult(passed=len(issues) == 0, issues=issues)


class PIIProtector:
    def __init__(self, redact_mode: str = "replace") -> None:
        self._redact_mode = redact_mode
        self._patterns: list[tuple[re.Pattern, str]] = [
            (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "ssn"),
            (re.compile(r"\b\d{10,}\b"), "national_id"),
            (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "email"),
            (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "phone"),
            (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "credit_card"),
            (re.compile(r"\b\d{5}(?:-\d{4})?\b"), "zip_code"),
            (re.compile(r"\b(?:M[rs]s?\.|Dr\.|Prof\.)\s+[A-Z][a-z]+\b"), "name_with_title"),
            (
                re.compile(
                    r"\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b",
                ),
                "ip_address",
            ),
        ]

    def detect(self, text: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for pattern, pii_type in self._patterns:
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "type": pii_type,
                        "value": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                    },
                )
        return findings

    def redact(self, text: str) -> RedactionResult:
        redacted = text
        types_found: list[str] = []
        count = 0
        for pattern, pii_type in self._patterns:
            replacement = f"[{pii_type.upper()}]" if self._redact_mode == "replace" else "***"
            matches = pattern.findall(text)
            if matches:
                types_found.append(pii_type)
                count += len(matches)
                redacted = pattern.sub(replacement, redacted)
        return RedactionResult(
            original_text=text,
            redacted_text=redacted,
            pii_types_found=list(set(types_found)),
            count=count,
        )

    def mask(self, text: str, keep_last: int = 4) -> str:
        findings = self.detect(text)
        masked = text
        for f in findings:
            value = f["value"]
            if len(value) > keep_last:
                mask_len = len(value) - keep_last
                masked_value = "*" * mask_len + value[-keep_last:]
                masked = masked.replace(value, masked_value, 1)
        return masked

    def is_clean(self, text: str) -> bool:
        return len(self.detect(text)) == 0


class AIFirewall:
    def __init__(
        self,
        injection_protector: PromptInjectionProtector | None = None,
        output_validator: OutputValidator | None = None,
        pii_protector: PIIProtector | None = None,
    ) -> None:
        self._injection = injection_protector or PromptInjectionProtector()
        self._validator = output_validator or OutputValidator()
        self._pii = pii_protector or PIIProtector()

    @property
    def injection(self) -> PromptInjectionProtector:
        return self._injection

    @property
    def validator(self) -> OutputValidator:
        return self._validator

    @property
    def pii(self) -> PIIProtector:
        return self._pii

    def inspect_input(self, text: str) -> dict[str, Any]:
        injection_result = self._injection.analyze(text)
        pii_findings = self._pii.detect(text)
        blocked = injection_result.detected or len(pii_findings) > 0
        return {
            "blocked": blocked,
            "injection": {
                "detected": injection_result.detected,
                "score": injection_result.score,
                "patterns": injection_result.patterns_matched,
            },
            "pii": {
                "detected": len(pii_findings) > 0,
                "count": len(pii_findings),
                "types": list({f["type"] for f in pii_findings}),
            },
            "recommendation": "Block" if blocked else "Allow",
        }

    def inspect_output(self, text: str) -> dict[str, Any]:
        validation = self._validator.validate(text)
        redaction = self._pii.redact(text)
        return {
            "passed": validation.passed,
            "issues": validation.issues,
            "pii_redacted": redaction.count > 0,
            "pii_types": redaction.pii_types_found,
            "safe_output": redaction.redacted_text if redaction.count > 0 else text,
        }

    def process(self, input_text: str, output_text: str) -> dict[str, Any]:
        input_check = self.inspect_input(input_text)
        output_check = self.inspect_output(output_text)
        return {
            "blocked": input_check["blocked"],
            "input": input_check,
            "output": output_check,
        }


ai_firewall = AIFirewall()
