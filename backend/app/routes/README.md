# Routes — API Layer

This module contains all FastAPI route handlers for the GULA Platform. Routes depend on Services only (never on Domain, Models, or Infrastructure directly). Each file maps to a bounded capability: patients, labs, orders, results, samples, auth, stats, EHR/FHIR, compliance, notifications, device integration, and administrative functions.

Key files: `patients.py`, `results.py`, `labs.py`, `orders.py`, `ehr_fhir.py`, `stats.py`, `compliance.py`, `patient_card.py`, `critical_alerts.py`, `samples.py`.
