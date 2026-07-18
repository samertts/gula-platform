# Operational AI Report — Predictive Analytics, Resource Optimization & Engineering AI

**PI-005 | GULA Platform v2.1.0**  
**Date:** 2026-07-16  
**Status:** FINAL

---

## 1. Predictive Analytics

### 1.1 Workload Prediction

`WorkloadPredictor` (`laboratory_intelligence.py:236`) forecasts laboratory operations:

- **`predict_daily()`** — Average daily order volume from 90-day history
- **`predict_tat()`** — Turnaround time estimation by order type (routine/stat) and backlog
- **`peak_hour_analysis()`** — Identifies peak hours and staffing recommendations

**Model:** Historical average with backlog-adjusted TAT = `base_TAT × (1 + backlog × 0.01)`

### 1.2 Demand Prediction (Legacy)

`ai/lab_business_ai/demand_prediction.py` — Predicts next most likely test based on historical frequency (simple mode-of-historical-data approach).

### 1.3 Laboratory Business AI

The `ai/lab_business_ai/` directory provides:
- `lab_activity.py` — Lab activity analysis
- `lab_dashboard.py` — Operational dashboards
- `top_tests.py` — Most frequent tests analysis
- `data_loader.py` — Data loading utilities

---

## 2. Resource Optimization

### 2.1 Digital Twin Capacity Planning

The `DigitalTwinEngine` (`simulation/engine.py`) provides predictive capacity planning:

**CapacityPlan generation** (`_create_capacity_plan`):
- Compares current capacity vs. predicted peak demand
- Priority-based recommendations (high/medium/low)
- Recommended capacity = peak × 1.15 (high priority) / peak × 1.05 (medium) / current × 1.02 (low)

**Forecast methodology:**
1. Extract historical metric series from twin metrics
2. Apply linear trend projection
3. Apply EMA smoothing
4. Calculate volatility-based confidence
5. Generate capacity plan with priority scoring

### 2.2 Laboratory Twin Utilization

`LaboratoryTwin.calculate_utilization()` computes:
- Equipment uptime (historical, stochastic)
- Error rate tracking
- Throughput per hour
- Capacity utilization percentage with seasonal adjustment
- Operational status (operational / at_capacity)

### 2.3 Hospital Twin Resource Management

`HospitalTwin` simulates:
- Bed occupancy forecasting (7–14 day horizon)
- Staff utilization assessment
- Seasonal factor integration
- Admission/discharge modeling with random walk

---

## 3. Infrastructure Prediction and Failure Prediction

### 3.1 Preventive Engine

The `ai/preventive_engine.py` and `ai/preventive/preventive_ai/` modules provide:

- Age/gender-based preventive screening recommendations
- Structured rule definitions for test suggestions
- Coverage gap analysis

### 3.2 Simulation-Based Failure Prediction

The `DigitalTwinEngine.get_twin_health()` method evaluates twin health:
- Data freshness (staleness check — 24h / 48h thresholds)
- Simulation failure rate
- Prediction accuracy (MAPE-based)
- Composite health score (0–100) with status: healthy / degraded / unhealthy

### 3.3 Performance Analysis

`ai/performance_analysis.py` — Error rate classification:
- < 2% → Good performance
- 2–5% → Moderate error rate
- > 5% → High error rate

---

## 4. Self-Healing Suggestions

### 4.1 Engineering Agent

`EngineeringAgent` (`agents/engineering_agent.py`) provides autonomous infrastructure analysis:

| Tool | Description |
|---|---|
| `audit_architecture` | Code architecture compliance audit |
| `check_dependency` | Dependency health and security check |
| `suggest_refactor` | Code refactoring suggestions |
| `validate_config` | Configuration best-practices validation |

### 4.2 Architecture Audit Findings

The engineering agent audits modules and produces:
- Severity-graded findings (info / ok / warning / error)
- Specific recommendations (e.g., "Add circuit breakers to external AI calls")
- Maintainability scores

### 4.3 Self-Healing Context

The AI fabric integrates with the platform's self-healing infrastructure:
- Circuit breaker (`core/self_healing.py`) — isolates failing DB/Redis
- Auto-Repair Engine (`core/auto_repair.py`) — GC, pool recycle, reconnects
- Adaptive concurrency — halves max concurrent on slow DB readings

---

## 5. Engineering AI

### 5.1 Architecture Review

The `EngineeringAgent` audits:
- Module structure and layering
- Security posture
- Dependency health
- Configuration validity

### 5.2 Code Review

Tools available:
- `suggest_refactor(file_path)` — Analyzes file complexity and maintainability
- `check_dependency(package)` — Vulnerability scanning
- `validate_config(section)` — Configuration best-practice validation

### 5.3 Test Generation

The engineering agent can analyze code patterns and suggest test cases, though test generation is primarily handled by the CI pipeline and manual pytest coverage.

### 5.4 Self-Audit Workflow

The platform includes a self-audit agent (`scripts/self_audit_agent.py`) that:
- Scans the codebase for issues
- Optionally applies safe fixes
- Can run on a watch loop (hourly)

---

## 6. Disease Forecasting

### 6.1 Directorate Twin Disease Scenarios

`DirectorateTwin.simulate_disease_scenario()` models:
- SIR compartmental model with configurable R0
- Disease profiles (influenza, COVID-19, measles, cholera, dengue)
- Mitigation scenarios (moderate/strong/lockdown interventions)
- Healthcare impact estimation (hospitalizations, severe cases, fatalities)

### 6.2 National Health Twin Outbreak Modeling

`NationalHealthTwin.simulate_outbreak_scenario()` provides:
- Population-scale SIR modeling (Iraq ~40M default)
- No-intervention vs. intervention comparisons
- Fatality estimation with intervention effectiveness
- Healthcare system impact (hospitalization rate, ICU admissions)

### 6.3 Population Health Trends

`PopulationHealthAnalytics` (`public_health.py:216`) tracks:
- Trend direction analysis (rising >5%, falling <-5%, stable)
- Disease prevalence rate per 100k population
- Immunization coverage with WHO target gaps
- Metrics: life expectancy, infant mortality, chronic disease prevalence, vaccination coverage, healthcare access, bed-to-population ratio

---

## 7. File Reference

| File | Description |
|---|---|
| `backend/app/ai_fabric/laboratory_intelligence.py` | Workload prediction, peak hour analysis |
| `backend/app/ai_fabric/public_health.py` | Population health analytics |
| `backend/app/ai_fabric/agents/engineering_agent.py` | Engineering AI agent |
| `backend/app/simulation/engine.py` | Digital twin engine (all 4 twin types) |
| `backend/app/simulation/models.py` | Simulation ORM models |
| `backend/app/simulation/routes.py` | Simulation API |
| `ai/lab_business_ai/demand_prediction.py` | Legacy demand prediction |
| `ai/lab_business_ai/lab_activity.py` | Lab activity analysis |
| `ai/lab_business_ai/lab_dashboard.py` | Lab operational dashboards |
| `ai/preventive_engine.py` | Legacy preventive screening |
| `ai/preventive/preventive_ai/preventive_engine.py` | Structured preventive engine |
| `ai/performance_analysis.py` | Performance analysis |
| `ai/population_health.py` | Population health statistics |
| `ai/population/population_ai/trend_analysis.py` | Trend analysis |
| `ai/population/population_ai/prevalence_analysis.py` | Prevalence analysis |
| `scripts/self_audit_agent.py` | Claude-powered self-audit |
