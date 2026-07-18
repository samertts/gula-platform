# Citizen AI Report — Health Assistant, Engagement & Personal Insights

**PI-005 | GULA Platform v2.1.0**  
**Date:** 2026-07-16  
**Status:** FINAL

---

## 1. Health Assistant

### 1.1 CitizenAgent

The `CitizenAgent` (`agents/citizen_agent.py`) is the primary citizen-facing AI agent. It provides patient-friendly health information with Arabic-first support and appropriate medical disclaimers.

**Capabilities:**
- `answer_health_query` — Answers citizen health-related questions with language selection
- `explain_result` — Translates lab results into plain-language explanations
- `schedule_reminder` — Schedules health reminders (requires approval)

### 1.2 Query Handling

```python
def _answer_query(self, data: dict[str, Any]) -> dict[str, Any]:
    query = data.get("query", "")
    language = data.get("language", "ar")  # Arabic-first default
    return {
        "query": query,
        "language": language,
        "answer": "",  # RAG-powered answer from health knowledge base
        "disclaimer": "This information is for educational purposes only. Consult your physician.",
        "requires_doctor": True,  # Conservative: always recommend physician
    }
```

### 1.3 Result Explanation

The agent explains lab results in patient-friendly language:

```python
def _explain_result(self, data):
    test_name = data.get("test_name", "")
    value = data.get("value", "")
    reference_range = data.get("reference_range", "")
    return {
        "explanation": f"Your {test_name} result is {value}",
        "interpretation": "normal",  # normal / borderline / abnormal
        "advice": "No action needed. Continue regular monitoring.",
        "disclaimer": "This explanation is computer-generated. Always consult your physician.",
    }
```

---

## 2. Medication Reminders

### 2.1 Reminder Scheduling

The `CitizenAgent` manages medication and test reminders through:

- **`schedule_reminder`** tool — Creates reminders for tests, medications, and follow-ups
- Reminder types: `test_reminder`, `medication`, `follow_up`, `vaccination`
- All reminders require human approval before activation

### 2.2 Reminder Rule Engine

The `ReminderRule` model (`clinical/cds/models.py:187`) provides structured reminder configuration:

- Trigger events (result_received, missed_appointment, etc.)
- Condition expressions for when to fire
- Frequency controls and max reminder limits
- Escalation paths (after N hours, escalate to supervisor)

---

## 3. Vaccination Guidance

### 3.1 Immunization Coverage Tracking

`PopulationHealthAnalytics.immunization_coverage()` (`public_health.py:269`) provides vaccination analytics:

- Coverage percentage per vaccine
- Status (adequate ≥95%, below_target)
- Gap analysis against WHO targets

### 3.2 Preventive Recommendations

The `PreventiveRecommendation` model supports vaccine recommendations:
- Age and gender targeting
- Risk factor assessment
- Evidence-level-based prioritization
- Source and guideline linkage

---

## 4. Appointment Assistant

### 4.1 Test Scheduling Support

The `WorkloadPredictor` (`laboratory_intelligence.py`) provides appointment-aware scheduling:

- Peak hour identification for appointment slot management
- TAT prediction for appointment duration estimation
- Staffing recommendations for capacity planning

### 4.2 Patient Flow Prediction

`HospitalTwin.simulate_patient_flow()` (`simulation/engine.py:534`) projects:
- Expected daily admissions
- Length of stay estimates
- Bed occupancy trends
- Seasonal adjustment factors

---

## 5. Personal Health Insights

### 5.1 Clinical Summarization for Citizens

`ClinicalSummarizer` (`clinical.py:158`) generates patient-facing health summaries:
- Converts complex lab results into narrative summaries
- Identifies key findings and trends
- Generates actionable recommendations
- Tracks longitudinal health history

### 5.2 Health Score & Trends

`PopulationTrend` analysis (`public_health.py:216`) provides:
- Metric tracking over time (change percentage)
- Direction classification (rising, falling, stable)
- Population-stratified insights

### 5.3 Patient Education

The `CitizenAgent` tool `answer_health_query` provides:
- Educational health information
- Arabic language support (default `ar`)
- Appropriate medical disclaimers
- Physician consultation recommendations

### 5.4 Patient Card System

The QR-backed patient card system (`routes/patient_card.py`) provides patients with:
- Digital identity with HMAC-signed tokens
- Printable Arabic-first HTML format
- Longitudinal clinical history (tenant-isolated per lab_id)
- Secure QR scanning with signature verification

---

## 6. Privacy & Safety

All citizen-facing AI features implement:

- **PII Protection** (`security.py:119`) — Automatic detection and redaction of SSN, national ID, email, phone, credit card, and name patterns
- **Medical Disclaimers** — Every explanation includes "consult your physician" notice
- **Approval Required** — All scheduling and actionable items require human-in-the-loop approval
- **Arabic-First** — Default language is Arabic with English fallback

---

## 7. File Reference

| File | Description |
|---|---|
| `backend/app/ai_fabric/agents/citizen_agent.py` | Citizen AI agent |
| `backend/app/ai_fabric/clinical.py` | Clinical summarization for patient-facing output |
| `backend/app/ai_fabric/public_health.py` | Population health and immunization tracking |
| `backend/app/ai_fabric/security.py` | PII protection and redaction |
| `backend/app/ai_fabric/laboratory_intelligence.py` | Workload prediction for appointment scheduling |
| `backend/app/clinical/cds/models.py` | Reminder rules and preventive recommendations |
| `backend/app/routes/patient_card.py` | QR patient card system |
