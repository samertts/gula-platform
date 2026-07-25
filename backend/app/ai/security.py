from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("gula.ai.security")

_PII_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("national_id", "Iraqi National ID", re.compile(r"\b\d{10,15}\b")),
    ("phone", "Phone number", re.compile(r"(\+?964|0)7[3-9]\d{8}\b")),
    ("email", "Email address", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("ip_address", "IP address", re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")),
    ("credit_card", "Credit card", re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")),
]

_PROMPT_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(
        r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|commands|directions)",
        re.IGNORECASE,
    ),
    re.compile(r"forget\s+(all\s+)?(previous|above)\s+(instructions|context)", re.IGNORECASE),
    re.compile(r"you\s+are\s+(now|free|no\s+longer)", re.IGNORECASE),
    re.compile(r"system\s+(prompt|message|instruction)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if\s+you\s+are|an?\s+AI|a\s+different)", re.IGNORECASE),
    re.compile(r"bypass\s+(the\s+)?(guardrails|safety|restrictions|rules)", re.IGNORECASE),
    re.compile(r"جِه\s+التعليمات\s+السابقة", re.IGNORECASE),
    re.compile(r"تجاهل\s+كل\s+ما\s+سبق", re.IGNORECASE),
]

_UNSAFE_CONTENT = [
    re.compile(
        r"(hack|crack|exploit|vulnerability|0day)\s*(the\s+)?(system|server|database)",
        re.IGNORECASE,
    ),
    re.compile(r"(sql|nosql|ldap|command)\s*injection", re.IGNORECASE),
    re.compile(r"steal|exfiltrat|unauthorized\s*access", re.IGNORECASE),
    re.compile(r"delete\s+(all\s+)?(data|records|tables|database)", re.IGNORECASE),
    re.compile(r"DROP\s+TABLE|DELETE\s+FROM|TRUNCATE\s+", re.IGNORECASE),
]


class AISecurityScanResult:
    def __init__(self):
        self.is_safe: bool = True
        self.issues: list[dict[str, Any]] = []
        self.pii_found: list[dict[str, Any]] = []
        self.injection_score: float = 0.0
        self.safety_score: float = 1.0


def scan_pii(text: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for pii_type, label, pattern in _PII_PATTERNS:
        matches = pattern.findall(text)
        for m in matches:
            found.append(
                {
                    "type": pii_type,
                    "label": label,
                    "value": _mask(m),
                    "position": text.index(m) if m in text else -1,
                },
            )
    return found


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "****"
    return value[:2] + "***" + value[-2:]


def scan_prompt_injection(text: str) -> tuple[float, list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    score = 0.0
    for pattern in _PROMPT_INJECTION_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            score += 0.2 * len(matches)
            issues.append(
                {"pattern": pattern.pattern[:60], "matches": len(matches), "severity": "high"},
            )
    return min(score, 1.0), issues


def scan_unsafe_content(text: str) -> tuple[float, list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    score = 0.0
    for pattern in _UNSAFE_CONTENT:
        matches = pattern.findall(text)
        if matches:
            score += 0.25 * len(matches)
            issues.append(
                {"pattern": pattern.pattern[:60], "matches": len(matches), "severity": "critical"},
            )
    return min(score, 1.0), issues


async def scan_input(text: str) -> AISecurityScanResult:
    result = AISecurityScanResult()

    pii = scan_pii(text)
    if pii:
        result.pii_found = pii
        result.issues.extend(
            {"type": "pii", "detail": p["label"], "severity": "medium"} for p in pii
        )

    inj_score, inj_issues = scan_prompt_injection(text)
    if inj_issues:
        result.injection_score = inj_score
        result.issues.extend(inj_issues)

    unsafe_score, unsafe_issues = scan_unsafe_content(text)
    if unsafe_issues:
        result.issues.extend(unsafe_issues)

    result.safety_score = 1.0 - (result.injection_score * 0.5 + unsafe_score * 0.5)
    result.is_safe = result.injection_score < 0.4 and unsafe_score < 0.4 and len(pii) < 3

    return result


async def sanitize_response(text: str) -> str:
    result = text
    for _pii_type, _label, pattern in _PII_PATTERNS:
        result = pattern.sub(lambda m: _mask(m.group()), result)
    return result
