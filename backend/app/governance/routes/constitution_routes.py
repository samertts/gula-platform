from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from governance.catalogs.dependency_registry import DependencyRegistry
from governance.catalogs.technology_catalog import TechnologyCatalog
from governance.compiler.constitution_compiler import ConstitutionCompiler
from governance.constitution_engine import ConstitutionEngine
from governance.engine.architecture_decision_engine import ArchitectureDecisionEngine
from governance.engine.compliance_monitor import ContinuousComplianceMonitor
from governance.engine.dashboards import CostDashboard, SovereigntyDashboard
from governance.engine.procurement_engine import ProcurementEngine
from governance.engine.recommendation_engine import AIRecommendationEngine
from governance.engine.review_engine import AutonomousReviewEngine

router = APIRouter(prefix="/api/v1/governance", tags=["governance"])

compiler = ConstitutionCompiler()
engine = ConstitutionEngine()
catalog = TechnologyCatalog()
registry = DependencyRegistry()
procurement = ProcurementEngine()
arch_engine = ArchitectureDecisionEngine()
recommender = AIRecommendationEngine()
reviewer = AutonomousReviewEngine()
compliance = ContinuousComplianceMonitor()
cost_dashboard = CostDashboard()
sovereignty_dashboard = SovereigntyDashboard()


class RecommendationRequest(BaseModel):
    query: str
    category: str = ""


class ProcurementRequest(BaseModel):
    requirement: str
    cost: float = 0.0


class ADRRequest(BaseModel):
    title: str
    context: str = ""


class EvaluateRequest(BaseModel):
    request_type: str
    context: dict = {}


@router.get("/constitution")
async def get_constitution():
    compiled = compiler.compile_all()
    return compiled.to_dict()


@router.get("/constitution/check")
async def constitution_check():
    return engine.generate_compliance_report()


@router.post("/constitution/evaluate")
async def constitution_evaluate(req: EvaluateRequest):
    return engine.explain_decision(req.request_type, req.context)


@router.get("/technology-catalog")
async def get_technology_catalog(category: str = "", status: str = "", query: str = ""):
    if category:
        results = catalog.get_by_category(category)
    elif status:
        results = catalog.search(status=status)
    elif query:
        results = catalog.search(query=query)
    else:
        results = catalog.technologies
    return {"technologies": [t.to_dict() for t in results], "count": len(results)}


@router.get("/dependency-registry")
async def get_dependency_registry(risk: str = "", type_filter: str = "", query: str = ""):
    if risk:
        results = registry.search(risk=risk)
    elif type_filter:
        results = registry.get_by_type(type_filter)
    elif query:
        results = registry.search(query=query)
    else:
        results = registry.dependencies
    return {"dependencies": [d.to_dict() for d in results], "count": len(results)}


@router.post("/procurement")
async def evaluate_procurement(req: ProcurementRequest):
    ctx = {"cost": req.cost} if req.cost else {}
    decision = procurement.evaluate(req.requirement, ctx)
    return decision.to_dict()


@router.post("/architecture-review")
async def architecture_review(req: ADRRequest):
    adr = arch_engine.generate_adr(req.title, req.context)
    return adr.to_dict()


@router.get("/architecture-review/scan")
async def architecture_scan():
    reviewer.review_all()
    return reviewer.get_report()


@router.post("/recommendation")
async def get_recommendation(req: RecommendationRequest):
    rec = recommender.recommend(req.query, req.category)
    return rec.to_dict()


@router.get("/cost-analysis")
async def cost_analysis():
    return cost_dashboard.get_metrics()


@router.get("/sovereignty")
async def sovereignty_analysis():
    return sovereignty_dashboard.get_metrics()


@router.get("/compliance")
async def compliance_check():
    return compliance.run_check()


@router.get("/compliance/continuous")
async def continuous_compliance():
    return compliance.run_check()
