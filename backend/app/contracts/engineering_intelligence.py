from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .clinical_core import ContractDefinition, ContractEvidence, ReadinessState

EvidenceName = str
Severity = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class EvidenceFinding:
    evidence: EvidenceName
    severity: Severity
    message: str
    suggested_fix: str


@dataclass(frozen=True)
class ContractHealthReport:
    contract_id: str
    domain: str
    readiness: ReadinessState
    score_percent: int
    present: tuple[EvidenceName, ...]
    missing: tuple[EvidenceName, ...]
    findings: tuple[EvidenceFinding, ...]

    @property
    def can_be_marked_complete(self) -> bool:
        return self.readiness is ReadinessState.READY_FOR_PRODUCTION and not self.missing


_EVIDENCE_LABELS: dict[str, tuple[Severity, str, str]] = {
    "domain_model": ("critical", "لا يوجد Domain/Data Model مثبت.", "ثبّت نموذج المجال وعلاقاته وقواعد عدم التكرار."),
    "state_machine": ("critical", "لا توجد State Machine مثبتة.", "ثبّت الانتقالات المسموحة ورفض الانتقالات غير الصالحة."),
    "backend_contract": ("critical", "لا يوجد Backend API/Error Contract مثبت.", "اكتب request/response/error contract versioned قبل ربط العميل."),
    "authorization": ("critical", "تفويض RBAC غير مثبت.", "أضف authorization policy واختبارات allow/deny."),
    "object_authorization": ("critical", "Object-Level Authorization غير مثبت.", "اختبر الوصول إلى object من خارج العلاقة والنطاق."),
    "tenant_isolation": ("critical", "Tenant isolation غير مثبت.", "أضف اختبارات cross-tenant وتحققاً خادمياً للنطاق."),
    "audit": ("critical", "Audit evidence غير مثبت.", "سجّل before/after وactor/context في سجل append-only."),
    "idempotency": ("high", "Idempotency evidence غير مثبت.", "أضف Idempotency-Key واختبار replay يمنع duplicate side effects."),
    "concurrency": ("high", "Concurrency/If-Match evidence غير مثبت.", "أضف version check واختبار 409 عند stale update."),
    "rate_limits": ("high", "Rate-limit evidence غير مثبت.", "عرّف حدوداً للعملية واختبر 429 بصورة قابلة للتكرار."),
    "error_contract": ("high", "Error contract موحد غير مثبت.", "وحّد error_code/request_id/retryable/field_errors."),
    "frontend_states": ("medium", "Frontend state coverage غير مثبت.", "غطِّ loading/empty/401/403/404/409/422/429/503/offline حيث تنطبق."),
    "rtl_accessibility": ("medium", "RTL/accessibility evidence غير مثبت.", "أضف keyboard/screen-reader/RTL tests ومراجعة ترجمة بشرية."),
    "offline_policy": ("high", "Offline policy غير مثبتة.", "صنّف العملية ONLINE_ONLY/OFFLINE_READ/OFFLINE_DRAFT/OFFLINE_WRITE."),
    "unit_tests": ("medium", "Unit tests غير مثبتة.", "أضف اختبارات منطق المجال والانتقالات."),
    "integration_tests": ("high", "Integration tests غير مثبتة.", "اختبر الخدمة مع التخزين والتفويض والتدقيق."),
    "contract_tests": ("high", "Contract tests غير مثبتة.", "اختبر schema/error compatibility بين العميل والخادم."),
    "security_tests": ("critical", "Security/negative tests غير مثبتة.", "اختبر IDOR وcross-tenant وreplay وprivilege escalation."),
    "e2e_tests": ("high", "Golden E2E غير مثبتة.", "شغّل المسار على Test Backend وSynthetic Database فقط."),
    "performance_tests": ("medium", "Performance evidence غير مثبتة.", "قس latency/query count/bundle/memory قبل وبعد."),
    "remote_ci": ("high", "Remote CI evidence غير مثبتة.", "شغّل CI البعيد ولا تعتبر UNSTABLE نجاحاً."),
    "staging": ("high", "Staging evidence غير مثبتة.", "نفّذ smoke/security checks على staging مع rollback."),
    "rollback": ("high", "Rollback evidence غير مثبتة.", "اكتب runbook واختبر استرجاع migration/deployment."),
    "external_dependencies_ready": ("critical", "تكامل خارجي مطلوب لكنه غير جاهز.", "ثبّت adapter contract وsandbox وcredentials المفوضة قبل التفعيل."),
}


def _required_evidence(contract: ContractDefinition) -> tuple[str, ...]:
    names = [
        "domain_model", "state_machine", "backend_contract", "authorization",
        "object_authorization", "tenant_isolation", "audit", "rate_limits",
        "error_contract", "frontend_states", "rtl_accessibility", "offline_policy",
        "unit_tests", "integration_tests", "contract_tests", "security_tests",
        "e2e_tests", "performance_tests", "remote_ci", "staging", "rollback",
    ]
    safety = contract.write_safety
    if safety.idempotency:
        names.append("idempotency")
    if safety.concurrency:
        names.append("concurrency")
    if contract.external_dependencies:
        names.append("external_dependencies_ready")
    return tuple(names)


def evaluate_contract(contract: ContractDefinition, evidence: ContractEvidence) -> ContractHealthReport:
    required = _required_evidence(contract)
    present = tuple(name for name in required if getattr(evidence, name))
    missing = tuple(name for name in required if not getattr(evidence, name))
    findings = tuple(
        EvidenceFinding(name, _EVIDENCE_LABELS[name][0], _EVIDENCE_LABELS[name][1], _EVIDENCE_LABELS[name][2])
        for name in missing
    )
    score = round((len(present) / len(required)) * 100) if required else 100
    return ContractHealthReport(
        contract_id=contract.contract_id,
        domain=contract.domain,
        readiness=evidence.readiness(contract),
        score_percent=score,
        present=present,
        missing=missing,
        findings=findings,
    )
