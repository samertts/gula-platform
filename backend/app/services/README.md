# Services — Business Logic Layer

This module contains all business logic service classes for the GULA Platform. Services depend on Domain only (never on Routes, other Services directly, or Infrastructure). Includes: `patient_service.py`, `order_service.py`, `outbox_service.py`, `clinical_service.py`, `ehr_service.py`, `identity_service.py`, `audit_service.py`, `pdf_report.py`, and sub-packages for MPI (`mpi/`) and reference data (`reference/`).
