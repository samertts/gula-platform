from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RuleSeverity(Enum):
    BLOCKER = "blocker"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RuleCategory(Enum):
    FREE_FIRST = "free_first"
    OPEN_SOURCE_FIRST = "open_source_first"
    SELF_HOSTED_FIRST = "self_hosted_first"
    NO_VENDOR_LOCK_IN = "no_vendor_lock_in"
    ZERO_PAID_DEPENDENCY = "zero_paid_dependency"
    REUSE_BEFORE_BUILD = "reuse_before_build"
    LOCAL_AI_FIRST = "local_ai_first"
    FREE_SECURITY_FIRST = "free_security_first"
    COST_GOVERNANCE = "cost_governance"
    PLATFORM_SOVEREIGNTY = "platform_sovereignty"
    SECURITY_BY_DESIGN = "security_by_design"
    PRIVACY_BY_DESIGN = "privacy_by_design"
    ARCHITECTURE_BEFORE_IMPLEMENTATION = "architecture_before_implementation"
    EVIDENCE_BASED_DECISIONS = "evidence_based_decisions"


class TechnologyStatus(Enum):
    APPROVED = "approved"
    CERTIFIED = "certified"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    FORBIDDEN = "forbidden"
    RETIRED = "retired"


class ModuleStatus(Enum):
    CERTIFIED = "certified"
    APPROVED = "approved"
    STABLE = "stable"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass
class ConstitutionalRule:
    id: str
    article: str
    title: str
    description: str
    category: RuleCategory
    severity: RuleSeverity
    source_document: str
    checks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    exceptions: list[str] = field(default_factory=list)
    enforcement: str = ""

    @property
    def is_blocking(self) -> bool:
        return self.severity in (RuleSeverity.BLOCKER, RuleSeverity.HIGH)


@dataclass
class ConstitutionalDocument:
    name: str
    path: str
    version: str
    checksum: str
    rules: list[ConstitutionalRule] = field(default_factory=list)
    articles: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    compiled_at: str = ""


@dataclass
class CompiledConstitution:
    documents: list[ConstitutionalDocument]
    rules: list[ConstitutionalRule]
    checksum: str
    version: str
    compiled_at: str
    rule_count: int
    document_count: int
    conflict_count: int
    dependency_graph: dict[str, list[str]] = field(default_factory=dict)
    inheritance_tree: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "compiled_at": self.compiled_at,
            "checksum": self.checksum,
            "document_count": self.document_count,
            "rule_count": self.rule_count,
            "conflict_count": self.conflict_count,
            "documents": [
                {
                    "name": d.name,
                    "path": d.path,
                    "version": d.version,
                    "checksum": d.checksum,
                    "article_count": len(d.articles),
                    "rule_count": len(d.rules),
                }
                for d in self.documents
            ],
            "rules": [
                {
                    "id": r.id,
                    "article": r.article,
                    "title": r.title,
                    "category": r.category.value,
                    "severity": r.severity.value,
                    "source": r.source_document,
                    "dependencies": r.dependencies,
                }
                for r in self.rules
            ],
            "dependency_graph": self.dependency_graph,
            "inheritance_tree": self.inheritance_tree,
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def to_yaml(self) -> str:
        import yaml
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)


@dataclass
class RuleEvaluationResult:
    rule_id: str
    rule_title: str
    category: RuleCategory
    severity: RuleSeverity
    passed: bool
    details: list[str] = field(default_factory=list)
    score: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_title": self.rule_title,
            "category": self.category.value,
            "severity": self.severity.value,
            "passed": self.passed,
            "score": self.score,
            "details": self.details,
        }


@dataclass
class RuleEvaluationReport:
    evaluated_at: str
    total_rules: int
    passed: int
    failed: int
    score: float
    results: list[RuleEvaluationResult] = field(default_factory=list)
    violations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluated_at": self.evaluated_at,
            "total_rules": self.total_rules,
            "passed": self.passed,
            "failed": self.failed,
            "score": self.score,
            "results": [r.to_dict() for r in self.results],
            "violations": self.violations,
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass
class Technology:
    name: str
    category: str
    license_type: str
    maintainer: str
    maturity: str
    community_size: str
    security_score: int
    cves: int
    documentation_score: int
    cost: float
    tco: float
    vendor: str
    open_source_alternative: str
    commercial_alternative: str
    migration_difficulty: str
    performance_score: int
    architecture_compatibility: int
    sovereignty_score: int
    status: TechnologyStatus
    version: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "license": self.license_type,
            "maintainer": self.maintainer,
            "maturity": self.maturity,
            "community_size": self.community_size,
            "security_score": self.security_score,
            "cves": self.cves,
            "documentation_score": self.documentation_score,
            "cost": self.cost,
            "tco": self.tco,
            "vendor": self.vendor,
            "open_source_alternative": self.open_source_alternative,
            "commercial_alternative": self.commercial_alternative,
            "migration_difficulty": self.migration_difficulty,
            "performance_score": self.performance_score,
            "architecture_compatibility": self.architecture_compatibility,
            "sovereignty_score": self.sovereignty_score,
            "status": self.status.value,
        }


@dataclass
class Dependency:
    name: str
    version: str
    type: str
    purpose: str
    owner: str
    adr: str
    license_type: str
    risk: str
    cves: int
    security_score: int
    upgrade_strategy: str
    rollback_strategy: str
    migration_strategy: str
    replacement: str
    maintenance_status: str
    cost: float
    vendor_lock_in_risk: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "type": self.type,
            "purpose": self.purpose,
            "owner": self.owner,
            "adr": self.adr,
            "license": self.license_type,
            "risk": self.risk,
            "cves": self.cves,
            "security_score": self.security_score,
            "upgrade_strategy": self.upgrade_strategy,
            "rollback_strategy": self.rollback_strategy,
            "migration_strategy": self.migration_strategy,
            "replacement": self.replacement,
            "maintenance_status": self.maintenance_status,
            "cost": self.cost,
            "vendor_lock_in_risk": self.vendor_lock_in_risk,
        }


@dataclass
class ComponentRegistryEntry:
    name: str
    owner: str
    version: str
    dependencies: list[str]
    status: ModuleStatus
    documentation: str
    api_endpoints: list[str]
    reuse_guide: str
    compatibility: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "owner": self.owner,
            "version": self.version,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "documentation": self.documentation,
            "api_endpoints": self.api_endpoints,
            "reuse_guide": self.reuse_guide,
            "compatibility": self.compatibility,
        }


@dataclass
class ProcurementDecision:
    requirement: str
    existing_module: str
    existing_service: str
    existing_library: str
    approved_technology: str
    open_source: str
    community_edition: str
    free_tier: str
    commercial: str
    reject: str
    decision: str
    cost_report: dict[str, Any]
    security_report: dict[str, Any]
    architecture_report: dict[str, Any]
    sovereignty_report: dict[str, Any]
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement": self.requirement,
            "decision": self.decision,
            "recommendation": self.recommendation,
            "cost_report": self.cost_report,
            "security_report": self.security_report,
            "architecture_report": self.architecture_report,
            "sovereignty_report": self.sovereignty_report,
        }


@dataclass
class Recommendation:
    query: str
    results: list[dict[str, Any]]
    ranked: list[dict[str, Any]]
    explanation: str
    total_evaluated: int
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "total_evaluated": self.total_evaluated,
            "ranked": self.ranked,
            "explanation": self.explanation,
            "timestamp": self.timestamp,
        }


@dataclass
class ArchitectureDecision:
    title: str
    context: str
    alternatives: list[dict[str, Any]]
    tradeoffs: list[dict[str, Any]]
    risk_matrix: dict[str, Any]
    cost_matrix: dict[str, Any]
    migration_plan: str
    exit_strategy: str
    compliance_report: dict[str, Any]
    decision: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "context": self.context,
            "decision": self.decision,
            "rationale": self.rationale,
            "alternatives": self.alternatives,
            "tradeoffs": self.tradeoffs,
            "risk_matrix": self.risk_matrix,
            "cost_matrix": self.cost_matrix,
            "migration_plan": self.migration_plan,
            "exit_strategy": self.exit_strategy,
            "compliance_report": self.compliance_report,
        }
