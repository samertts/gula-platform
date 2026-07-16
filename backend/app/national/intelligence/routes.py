from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query

from app.national.intelligence.ai_platform.llm import (
    AIAuditEngine,
    AIHumanApproval,
    ExplainabilityEngine,
    InferenceEngine,
    KnowledgeGraph,
    LLMGateway,
    ModelRegistry,
    ModelRouter,
    PromptRegistry,
    RAGEngine,
    SafetyFilter,
    VectorStore,
)
from app.national.intelligence.automation.engine import (
    CompensationEngine,
    EscalationEngine,
    JobOrchestrator,
    NotificationAutomationEngine,
    RuleAutomationEngine,
    ScheduleAutomationEngine,
    TaskAutomationEngine,
)
from app.national.intelligence.clinical.recommendations import (
    CareGapDetector,
    ClinicalAlertEngine,
    ClinicalRecommendationEngine,
    CriticalResultEscalation,
    DrugInteractionEngine,
    DuplicateTherapyDetector,
    PreventiveCareEngine,
    RiskStratificationEngine,
)
from app.national.intelligence.hospital.analytics import (
    AdmissionForecaster,
    BedPredictor,
    DischargePredictor,
    EmergencyLoadPredictor,
    ICUCapacityPredictor,
    QueuePredictor,
    ResourceUtilizationEngine,
)
from app.national.intelligence.laboratory.analytics import (
    AnalyzerHealthPredictor,
    DeltaCheckEngine,
    QCPredictor,
    ReagentPredictor,
    TurnaroundOptimizer,
    WorkloadDistributor,
)
from app.national.intelligence.public_health.surveillance import (
    ChildHealthEngine,
    DiseaseSurveillanceEngine,
    MaternalHealthEngine,
    MortalityAnalyzer,
    OutbreakDetectionEngine,
    PopulationRiskEngine,
    VaccinationCoverageEngine,
)
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/intelligence", tags=["National Intelligence Platform"])

task_engine = TaskAutomationEngine()
rule_engine = RuleAutomationEngine()
schedule_engine = ScheduleAutomationEngine()
notification_engine = NotificationAutomationEngine()
escalation_engine = EscalationEngine()
compensation_engine = CompensationEngine()
job_orchestrator = JobOrchestrator()
clinical_rec_engine = ClinicalRecommendationEngine()
drug_interaction_engine = DrugInteractionEngine()
duplicate_therapy_detector = DuplicateTherapyDetector()
preventive_care_engine = PreventiveCareEngine()
care_gap_detector = CareGapDetector()
risk_engine = RiskStratificationEngine()
alert_engine = ClinicalAlertEngine()
critical_escalation = CriticalResultEscalation()
analyzer_health = AnalyzerHealthPredictor()
qc_predictor = QCPredictor()
reagent_predictor = ReagentPredictor()
tat_optimizer = TurnaroundOptimizer()
workload_distributor = WorkloadDistributor()
delta_check_engine = DeltaCheckEngine()
bed_predictor = BedPredictor()
queue_predictor = QueuePredictor()
icu_predictor = ICUCapacityPredictor()
emergency_predictor = EmergencyLoadPredictor()
admission_forecaster = AdmissionForecaster()
discharge_predictor = DischargePredictor()
resource_utilization = ResourceUtilizationEngine()
disease_surveillance = DiseaseSurveillanceEngine()
outbreak_detection = OutbreakDetectionEngine()
vaccination_coverage = VaccinationCoverageEngine()
population_risk = PopulationRiskEngine()
mortality_analyzer = MortalityAnalyzer()
maternal_health = MaternalHealthEngine()
child_health = ChildHealthEngine()
llm_gateway = LLMGateway()
prompt_registry = PromptRegistry()
model_registry = ModelRegistry()
model_router = ModelRouter()
inference_engine = InferenceEngine()
vector_store = VectorStore()
knowledge_graph = KnowledgeGraph()
rag_engine = RAGEngine()
explainability_engine = ExplainabilityEngine()
safety_filter = SafetyFilter()
ai_human_approval = AIHumanApproval()
ai_audit_engine = AIAuditEngine()


@router.post("/automation/tasks", summary="Create automation task")
def create_automation_task(
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    task = task_engine.schedule_task(
        name=body.get("name", ""),
        action=body.get("action", ""),
        params=body.get("params"),
        priority=body.get("priority", 0),
        max_retries=body.get("max_retries", 3),
    )
    return {
        "task_id": task.id,
        "name": task.name,
        "action": task.action,
        "status": task.status.value,
    }


@router.get("/automation/tasks", summary="List automation tasks")
def list_automation_tasks(
    status: str | None = Query(None, description="Filter by status"),
    current_user=Depends(get_current_user),
):
    return {"tasks": task_engine.list_tasks()}


@router.post("/automation/rules/evaluate", summary="Evaluate automation rules")
def evaluate_automation_rules(
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    context = body.get("context", {})
    triggered = rule_engine.evaluate_rules(context)
    return {
        "rules_evaluated": len(rule_engine._rules),
        "triggered": triggered,
    }


@router.post("/clinical/recommendations", summary="Get clinical recommendations")
def get_clinical_recommendations(
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    patient_id = body.get("patient_id", "")
    context = body.get("context", {})
    recommendations = clinical_rec_engine.generate_recommendations(patient_id, context)
    return {
        "patient_id": patient_id,
        "recommendations": [
            {
                "id": r.id,
                "type": r.recommendation_type,
                "title": r.title,
                "description": r.description,
                "evidence_level": r.evidence_level,
                "priority": r.priority,
            }
            for r in recommendations
        ],
    }


@router.get("/clinical/drug-interaction/{medication_a}/{medication_b}", summary="Check drug interaction")
def check_drug_interaction(
    medication_a: str = Path(..., description="First medication"),
    medication_b: str = Path(..., description="Second medication"),
    current_user=Depends(get_current_user),
):
    interactions = drug_interaction_engine.check_interactions([medication_a, medication_b])
    return {
        "medications": [medication_a, medication_b],
        "interactions": [
            {
                "medications": list(i.medications),
                "severity": i.severity,
                "description": i.description,
                "mechanism": i.mechanism,
                "recommendation": i.recommendation,
            }
            for i in interactions
        ],
    }


@router.get("/clinical/care-gaps/{patient_id}", summary="Detect care gaps")
def detect_care_gaps(
    patient_id: str = Path(..., description="Patient ID"),
    current_user=Depends(get_current_user),
):
    gaps = care_gap_detector.detect_care_gaps(patient_id)
    return {
        "patient_id": patient_id,
        "care_gaps": [
            {
                "id": g.id,
                "guideline_id": g.guideline_id,
                "description": g.description,
                "severity": g.severity,
                "due_date": g.due_date,
            }
            for g in gaps
        ],
    }


@router.get("/clinical/risk-score/{patient_id}", summary="Calculate risk score")
def calculate_risk_score(
    patient_id: str = Path(..., description="Patient ID"),
    age: int = Query(30, description="Patient age"),
    gender: str = Query("M", description="Patient gender"),
    current_user=Depends(get_current_user),
):
    patient = {"age": age, "gender": gender, "conditions": [], "lifestyle": []}
    risk = risk_engine.stratify_risk(patient_id, patient)
    return {
        "patient_id": patient_id,
        "risk_score": risk.score,
        "risk_category": risk.category,
        "risk_factors": risk.factors,
        "percentile": risk.percentile,
    }


@router.post("/clinical/alerts/evaluate", summary="Evaluate clinical alerts")
def evaluate_clinical_alerts(
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    patient_id = body.get("patient_id", "")
    context = body.get("context", {})
    alerts = alert_engine.evaluate_alerts(patient_id, context)
    prioritized = alert_engine.prioritize_alerts(alerts)
    return {
        "patient_id": patient_id,
        "alerts": [
            {
                "id": a.id,
                "type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "created_at": a.created_at,
            }
            for a in prioritized
        ],
    }


@router.get("/laboratory/analyzer/{analyzer_id}/health", summary="Analyzer health status")
def get_analyzer_health(
    analyzer_id: str = Path(..., description="Analyzer ID"),
    error_rate: float = Query(0.0, description="Error rate"),
    calibration_deviation: float = Query(0.0, description="Calibration deviation"),
    temperature_deviation: float = Query(0.0, description="Temperature deviation"),
    current_user=Depends(get_current_user),
):
    metrics = {
        "error_rate": error_rate,
        "calibration_deviation": calibration_deviation,
        "temperature_deviation": temperature_deviation,
        "vibration_level": 0.0,
    }
    health = analyzer_health.predict_failure(analyzer_id, metrics)
    return {
        "analyzer_id": analyzer_id,
        **health,
    }


@router.post("/laboratory/turnaround/analyze", summary="TAT analysis")
def analyze_turnaround(
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    lab_id = body.get("lab_id", "")
    test_code = body.get("test_code", "")
    period = body.get("period", 30)
    tat_data = tat_optimizer.analyze_tat(lab_id, test_code, period)
    bottlenecks = tat_optimizer.identify_bottlenecks({
        "avg_tat_minutes": tat_data.avg_tat_minutes,
        "p50_tat_minutes": tat_data.p50_tat_minutes,
        "p95_tat_minutes": tat_data.p95_tat_minutes,
        "sample_count": 0,
    })
    recommendations = tat_optimizer.recommend_optimizations(bottlenecks)
    return {
        "lab_id": lab_id,
        "test_code": test_code,
        "avg_tat_minutes": tat_data.avg_tat_minutes,
        "p50_tat_minutes": tat_data.p50_tat_minutes,
        "p95_tat_minutes": tat_data.p95_tat_minutes,
        "bottlenecks": bottlenecks,
        "recommendations": recommendations,
    }


@router.get("/hospital/bed-forecast", summary="Bed occupancy forecast")
def get_bed_forecast(
    hospital_id: str = Query("", description="Hospital ID"),
    days: int = Query(7, description="Forecast days"),
    current_user=Depends(get_current_user),
):
    forecast = bed_predictor.get_bed_forecast(hospital_id, days)
    recommendations = bed_predictor.recommend_capacity_adjustment(forecast)
    return {
        "hospital_id": hospital_id,
        "forecast": forecast,
        "capacity_recommendations": recommendations,
    }


@router.get("/hospital/queue-prediction", summary="Queue length prediction")
def get_queue_prediction(
    department_id: str = Query("", description="Department ID"),
    day: int = Query(0, description="Day of week (0=Mon)"),
    hour: int = Query(9, description="Hour of day"),
    current_user=Depends(get_current_user),
):
    queue_length = queue_predictor.predict_queue_length(department_id, day, hour)
    wait_time = queue_predictor.get_estimated_wait_time(department_id)
    staffing = queue_predictor.recommend_staffing({
        "predicted_queue_length": queue_length,
    })
    return {
        "department_id": department_id,
        "predicted_queue_length": queue_length,
        "estimated_wait_minutes": wait_time,
        "recommended_staffing": staffing,
    }


@router.get("/public-health/surveillance/{disease}", summary="Disease surveillance")
def get_disease_surveillance(
    disease: str = Path(..., description="Disease code"),
    region: str = Query("", description="Region"),
    period: int = Query(30, description="Period in days"),
    current_user=Depends(get_current_user),
):
    return disease_surveillance.generate_surveillance_report(disease, region)


@router.post("/public-health/outbreak/detect", summary="Detect disease outbreak")
def detect_outbreak(
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    cases = body.get("cases", [])
    baseline = body.get("baseline", 0)
    threshold = body.get("threshold", 2.0)
    result = outbreak_detection.detect_outbreak(cases, baseline, threshold)
    if cases:
        r0 = outbreak_detection.calculate_r0(cases)
        result["r0_estimate"] = r0
        severity = outbreak_detection.assess_outbreak_severity({**result, "r0_estimate": r0})
        result["severity_assessment"] = severity
    return result


@router.post("/ai/llm/query", summary="Query LLM")
async def query_llm(
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    prompt = body.get("prompt", "")
    model = body.get("model", "gpt-3.5-turbo")
    parameters = body.get("parameters", {})
    return await llm_gateway.query_llm(prompt, model, parameters)


@router.post("/ai/embeddings/store", summary="Store embedding")
def store_embedding(
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    entity_id = body.get("entity_id", "")
    embedding = body.get("embedding", [])
    metadata = body.get("metadata", {})
    vector_store.store_embedding(entity_id, embedding, metadata)
    return {"entity_id": entity_id, "stored": True}


@router.post("/ai/embeddings/search", summary="Search embeddings")
def search_embeddings(
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    query_embedding = body.get("query_embedding", [])
    k = body.get("k", 10)
    results = vector_store.search_similar(query_embedding, k)
    return {"results": results, "count": len(results)}


@router.post("/ai/rag/query", summary="RAG query")
async def rag_query(
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    query = body.get("query", "")
    k = body.get("k", 5)
    context = rag_engine.retrieve_context(query, vector_store, k)
    result = await rag_engine.generate_with_context(query, context, llm_gateway)
    return {
        "query": query,
        "context_used": context,
        "response": result,
    }


@router.get("/ai/models", summary="List AI models")
def list_ai_models(
    capability: str | None = Query(None, description="Filter by capability"),
    current_user=Depends(get_current_user),
):
    models = model_registry.list_models(capability)
    return {
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "version": m.version,
                "capabilities": m.capabilities,
                "status": m.status,
            }
            for m in models
        ],
    }


@router.post("/ai/approval/request", summary="Request human approval")
def request_ai_approval(
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    action = body.get("action", "")
    context = body.get("context", {})
    risk_level = body.get("risk_level", "medium")
    return ai_human_approval.request_approval(action, context, risk_level)


@router.post("/ai/approval/{approval_id}/respond", summary="Approve or reject AI action")
def respond_to_approval(
    approval_id: str = Path(..., description="Approval ID"),
    body: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    decision = body.get("decision", "approve")
    reason = body.get("reason", "")
    try:
        if decision == "approve":
            result = ai_human_approval.approve_action(approval_id, reviewer=current_user.email)
        elif decision == "reject":
            result = ai_human_approval.reject_action(approval_id, reason=reason, reviewer=current_user.email)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid decision: {decision}")
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
