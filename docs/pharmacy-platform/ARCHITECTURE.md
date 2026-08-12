# National Pharmacy Information Platform (NPIP) — Architecture

**Platform:** NPIP — National Pharmacy Information Platform
**Mission:** 027
**Status:** Planned
**Version:** 0.1.0

---

## 1. Overview

The National Pharmacy Information Platform (NPIP) is a comprehensive pharmacy management system for Iraqi healthcare facilities. It covers the full medication lifecycle: national drug catalog management, prescription processing, dispensing workflows, inventory management, clinical pharmacy services (drug interaction checking, contraindication screening, dose calculation), cold chain monitoring, and controlled substance tracking. NPIP integrates with the EHR medication ordering system and adheres to GS1 barcode standards for medication identification.

### 1.1 Key Objectives

- Establish a national drug catalog as the single source of truth for all medications in Iraq
- Provide end-to-end prescription management (order → verify → dispense → administer → monitor)
- Implement GS1 barcode standards (GTIN + lot + expiry) for all medication tracking
- Deliver clinical pharmacy services: drug-drug interactions, contraindications, dose calculations
- Manage inventory with real-time stock levels, expiry tracking, and automated reordering
- Support cold chain management for temperature-sensitive medications
- Enforce controlled substance workflows with mandatory audit trail (narcotics, psychotropics)
- Classify medications using ATC (Anatomical Therapeutic Chemical) system adapted for Iraq
- Integrate seamlessly with EHR medication orders and nursing BCMA workflows
- Provide clinical decision support at the point of prescribing and dispensing

### 1.2 Scope

| Area | In Scope | Out of Scope |
|------|----------|--------------|
| Drug catalog | National formulary, ATC classification, GS1 barcodes | Drug manufacturing |
| Prescriptions | Create, validate, dispense, track | E-prescribing (handled by EHR) |
| Dispensing | Workflow, verification, labeling | Automated dispensing cabinets |
| Inventory | Stock, expiry, reorder, transfers | Wholesale procurement |
| Clinical pharmacy | Interactions, contraindications, dosing | Therapeutic drug monitoring lab |
| Cold chain | Temperature logging, excursions | Cold storage equipment maintenance |
| Controlled substances | Audit trail, dual signatures, reporting | Regulatory filing |
| Billing | Insurance integration, pricing | Revenue cycle management |

---

## 2. System Context

```
+------------------------------------------------------------------+
|                  National Pharmacy Information Platform            |
|                        (Web + Offline PWA)                        |
+------------------------------------------------------------------+
|                                                                     |
|  +---------------------+  +---------------------+  +-------------+ |
|  | Drug Catalog        |  | Prescriptions       |  | Dispensing  | |
|  | (National Formulary,|  | (Order Entry,       |  | (Workflow,  | |
|  |  ATC, GS1, Pricing) |  |  Validation, Track) |  |  Barcode,   | |
|  +---------------------+  +---------------------+  |  Labeling)  | |
|  +---------------------+  +---------------------+  +-------------+ |
|  | Inventory           |  | Clinical Pharmacy   |                  |
|  | (Stock, Expiry,     |  | (Interactions,      |  +-------------+ |
|  |  Reorder, Cold Chain)|  |  Contraindications, |  | Controlled  | |
|  |                     |  |  Dose Calculation)  |  | Substances  | |
|  +---------------------+  +---------------------+  +-------------+ |
+---------------------------+---------------------------------------+
                            |
+---------------------------+---------------------------------------+
|                      NPIP Service Layer                              |
|                                                                     |
|  +---------------------+  +---------------------+  +--------------+ |
|  | PharmacyService     |  | ClinicalEngine      |  | Dispensing-  | |
|  | (Catalog, Order,    |  | (Interaction,       |  | Workflow     | |
|  |  Inventory)         |  |  Contraindication)  |  |              | |
|  +---------------------+  +---------------------+  +--------------+ |
|                                                                     |
|  +---------------------+  +---------------------+  +--------------+ |
|  | InventoryManagement |  | ColdChainMonitor    |  | Sync Engine  | |
|  | (Stock, Reorder,    |  | (Temp Logging,      |  | (Offline     | |
|  |  Transfer)          |  |  Excursion Alerting) |  |  Support)    | |
|  +---------------------+  +---------------------+  +--------------+ |
+---------------------------+---------------------------------------+
                            |
+---------------------------+---------------------------------------+
|                      GULA Backend API                                |
|                                                                     |
|  +---------------------+  +---------------------+  +--------------+ |
|  | /pharmacy/*         |  | /ehr/medications/*  |  | /nursing/*   | |
|  | (NPIP endpoints)    |  | (EHR medication     |  | (BCMA        | |
|  |                     |  |  ordering)          |  |  integration)| |
|  +---------------------+  +---------------------+  +--------------+ |
+------------------------------------------------------------------+
|                                                                     |
|  +-------------------------------------------------------------+   |
|  |  PostgreSQL 16 (NPIP Tables + EHR Medication Tables)         |   |
|  |  Redis 7 (Cache, Interaction Data, Real-time Stock)          |   |
|  +-------------------------------------------------------------+   |
+------------------------------------------------------------------+
```

---

## 3. Module Structure

### 3.1 Backend Module (`backend/app/pharmacy/`)

```
backend/app/pharmacy/
├── __init__.py
├── base.py                      # PHARMACYBase declarative base
├── models/
│   ├── __init__.py
│   ├── drug_catalog.py           # National drug catalog
│   ├── drug_atc.py               # ATC classification
│   ├── drug_ingredient.py        # Active pharmaceutical ingredients
│   ├── drug_formulation.py       # Formulations (tablet, injection, etc.)
│   ├── drug_package.py           # Package sizes and GS1 barcodes
│   ├── drug_pricing.py           # Price records per package
│   ├── prescription.py           # Prescription header
│   ├── prescription_item.py      # Individual items in a prescription
│   ├── dispensing.py             # Dispensing record
│   ├── dispensing_item.py        # Individual dispensed items
│   ├── pharmacy_inventory.py     # Stock record per location
│   ├── inventory_transaction.py  # Stock movements (receipt, issue, adjustment)
│   ├── inventory_reorder.py      # Reorder rules and pending orders
│   ├── cold_chain_log.py         # Temperature monitoring log
│   ├── cold_chain_excursion.py   # Temperature excursion events
│   ├── controlled_substance.py   # Controlled substance record
│   ├── controlled_substance_log.py # CS usage audit log
│   ├── drug_interaction.py       # Drug-drug interaction knowledge base
│   ├── drug_contraindication.py  # Contraindication knowledge base
│   ├── dose_calculation.py       # Dose calculation rules
│   ├── medication_dispensation.py # Link to EHR medication orders
│   └── pharmacy_location.py      # Pharmacy locations (main, satellite, ward stock)
├── services/
│   ├── __init__.py
│   ├── pharmacy_service.py       # Core pharmacy business logic
│   ├── clinical_engine.py        # Drug interaction and safety engine
│   ├── dispensing_workflow.py    # Dispensing workflow manager
│   ├── inventory_management.py   # Inventory control and reorder
│   └── cold_chain_service.py     # Cold chain monitoring
└── routes/
    ├── __init__.py
    ├── catalog.py                # Drug catalog endpoints
    ├── prescriptions.py          # Prescription endpoints
    ├── dispensing.py             # Dispensing endpoints
    ├── inventory.py              # Inventory endpoints
    ├── clinical.py               # Clinical pharmacy endpoints
    ├── cold_chain.py             # Cold chain endpoints
    ├── controlled.py             # Controlled substance endpoints
    └── interactions.py           # Interaction query endpoints
```

---

## 4. Core Entities (22 Models)

### 4.1 Drug Catalog (6)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `DrugCatalog` | `pharmacy_drug_catalog` | National drug catalog entry | atc_code, generic_name, brand_name, manufacturer, therapeutic_class, active_flag, controlled_substance_flag, cold_chain_flag |
| `DrugATC` | `pharmacy_drug_atc` | ATC classification levels | atc_code, level_1 (anatomical), level_2 (therapeutic), level_3 (pharmacological), level_4 (chemical), level_5 (substance) |
| `DrugIngredient` | `pharmacy_drug_ingredients` | Active pharmaceutical ingredients | name, strength, unit, reference_standard |
| `DrugFormulation` | `pharmacy_drug_formulations` | Drug formulations | drug_id, form_code (tablet, capsule, injection, etc.), administration_route |
| `DrugPackage` | `pharmacy_drug_packages` | Package/sku with GS1 barcode | drug_id, gtin (GS1 GTIN-14), package_size, unit_type, package_type |
| `DrugPricing` | `pharmacy_drug_pricing` | Pricing records | drug_code, package_gtin, unit_price, dispensing_fee, effective_date, price_type (retail/wholesale/insurance) |

### 4.2 Prescriptions (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `Prescription` | `pharmacy_prescriptions` | Prescription document | patient_id, prescriber_id, encounter_id, prescription_date, status (active/completed/cancelled), type (acute/chronic/standing/prn), notes |
| `PrescriptionItem` | `pharmacy_prescription_items` | Individual prescription line | prescription_id, drug_id, formulation_id, dose, dose_unit, frequency, route, duration, quantity, refills, instructions, substitution_allowed |

### 4.3 Dispensing (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `Dispensing` | `pharmacy_dispensing` | Dispensing session | prescription_id, dispensed_by, verified_by, dispensed_at, location_id, status (pending/partial/complete/cancelled) |
| `DispensingItem` | `pharmacy_dispensing_items` | Dispensed item line | dispensing_id, prescription_item_id, drug_id, package_gtin, lot_number, expiry_date, quantity_dispensed, barcode_scanned, price |

### 4.4 Inventory (4)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `PharmacyInventory` | `pharmacy_inventory` | Stock record per location | drug_id, location_id, lot_number, expiry_date, quantity_on_hand, quantity_allocated, quantity_available, reorder_point, reorder_quantity |
| `InventoryTransaction` | `pharmacy_inventory_transactions` | Stock movement audit | inventory_id, transaction_type (receipt/issue/adjustment/transfer/return/destruction), quantity, reference_doc, performed_by, reason_code |
| `InventoryReorder` | `pharmacy_inventory_reorder` | Reorder rules | drug_id, location_id, reorder_point, reorder_quantity, lead_time_days, preferred_supplier, last_reorder_date, active_flag |
| `PharmacyLocation` | `pharmacy_locations` | Inventory locations | hospital_id, name, location_type (main/satellite/ward_floor/unit), is_active |

### 4.5 Clinical Pharmacy (3)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `DrugInteraction` | `pharmacy_drug_interactions` | Drug-drug interaction data | drug_a_id, drug_b_id, severity (contraindicated/major/moderate/minor), mechanism, effect, management, evidence_level |
| `DrugContraindication` | `pharmacy_drug_contraindications` | Contraindication rules | drug_id, condition_id (ICD-10), severity, description, management, evidence_level |
| `DoseCalculation` | `pharmacy_dose_calculations` | Dose calculation rules | drug_id, calculation_type (weight_based/bsa/age_based/fixed), min_dose, max_dose, unit, formula, weight_range_min, weight_range_max, age_range_min, age_range_max, renal_adjustment, hepatic_adjustment |

### 4.6 Cold Chain (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `ColdChainLog` | `pharmacy_cold_chain_logs` | Temperature reading | location_id, device_id, temperature_celsius, humidity_percent, recorded_at, logged_by, sensor_type |
| `ColdChainExcursion` | `pharmacy_cold_chain_excursions` | Temperature excursion event | location_id, device_id, started_at, ended_at, min_temp, max_temp, duration_minutes, affected_items (JSON), action_taken, resolved_by |

### 4.7 Controlled Substances (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `ControlledSubstance` | `pharmacy_controlled_substances` | CS tracking record | drug_id, lot_number, quantity_received, current_balance, last_audit_date, schedule (II/III/IV/V), storage_requirement |
| `ControlledSubstanceLog` | `pharmacy_controlled_substance_logs` | CS usage audit trail | substance_id, transaction_type, quantity, patient_id, prescriber_id, administering_nurse_id, witness_id, timestamp, reason, balance_after |

### 4.8 EHR Link (1)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `MedicationDispensation` | `pharmacy_medication_dispensations` | Link between EHR orders and dispensing | ehr_order_id, dispensing_item_id, patient_id, status (ordered/verified/dispensed/administered), clinical_status |

---

## 5. Service Layer

### 5.1 PharmacyService

Core business logic for catalog management and prescription processing:

| Method | Description |
|--------|-------------|
| `search_catalog` | Search drug catalog by name, ATC, barcode, or ingredient |
| `get_drug_detail` | Get full drug information with pricing, interactions, and stock |
| `get_drug_alternatives` | Find therapeutic alternatives (same ATC level 4) |
| `create_prescription` | Create prescription with clinical validation |
| `validate_prescription` | Validate against interactions, contraindications, dosing |
| `get_prescription_history` | Patient prescription history |
| `get_dispensing_status` | Track dispensing status for a prescription |
| `cancel_prescription` | Cancel prescription with reason |
| `query_pricing` | Get pricing for drug by location and payer |

### 5.2 ClinicalEngine

Drug interaction and clinical safety engine:

| Method | Description |
|--------|-------------|
| `check_drug_interactions` | Check interactions between list of drugs (returns severity-sorted results) |
| `check_contraindications` | Check contraindications for drug + patient conditions |
| `calculate_dose` | Calculate recommended dose based on patient parameters (weight, BSA, age, renal function) |
| `validate_order_safety` | Full safety check: interactions + contraindications + dose |
| `check_duplicate_therapy` | Identify therapeutic duplication |
| `check_allergy` | Cross-reference drug against patient allergies |
| `get_drug_monographs` | Retrieve clinical monographs for education |

**Interaction Severity Levels:**

| Level | Action | Example |
|-------|--------|---------|
| Contraindicated | Cannot dispense, requires overriding physician approval | Warfarin + NSAID in GI bleed patient |
| Major | Warning with pharmacist review required | Simvastatin + Amiodarone |
| Moderate | Inform prescriber, monitor | Metoprolol + Fluoxetine |
| Minor | Document, no action required | Omeprazole + Digoxin |

### 5.3 DispensingWorkflow

End-to-end dispensing process manager:

| Method | Description |
|--------|-------------|
| `start_dispensing` | Begin dispensing session for a prescription |
| `scan_medication` | Scan barcode, validate drug/lot/expiry against prescription |
| `verify_dispensing` | Pharmacist verification of dispensed items |
| `label_dispensing` | Generate patient-specific dispensing label |
| `complete_dispensing` | Finalize dispensing, update inventory |
| `partial_dispense` | Dispense partial quantity, create balance |
| `reverse_dispensing` | Reverse a dispensing in case of error |
| `get_workflow_queue` | Get pending dispensing queue for a pharmacy |

**Dispensing Workflow:**

```
Prescription Received
       ↓
Clinical Check (interactions, contraindications, dose)
       ↓
Inventory Check (stock availability, expiry)
       ↓
Select Items → Scan Barcode (GS1) → Validate Lot/Expiry
       ↓
Pick Items from Shelf
       ↓
Generate Label (patient, drug, dose, instructions, barcode)
       ↓
Pharmacist Verification (independent check)
       ↓
Hand to Patient / Ward
       ↓
Update Inventory → Dispensing Complete
```

### 5.4 InventoryManagement

Inventory control and supply chain management:

| Method | Description |
|--------|-------------|
| `get_stock_level` | Current stock level for drug at location |
| `adjust_stock` | Manual stock adjustment (with reason code) |
| `transfer_stock` | Transfer stock between locations |
| `receive_stock` | Record receipt of stock (purchase order) |
| `check_expiry` | Expiry monitoring and alerting |
| `calculate_reorder` | Calculate reorder quantity based on consumption |
| `generate_reorder` | Generate reorder suggestion |
| `process_returns` | Process returns to supplier |
| `stock_take` | Initiate and reconcile stock take |
| `get_consumption_report` | Drug consumption report by period |

### 5.5 ColdChainService

Temperature monitoring and excursion management:

| Method | Description |
|--------|-------------|
| `log_temperature` | Record temperature reading from sensor/manual |
| `check_excursion` | Check if reading is outside acceptable range |
| `create_excursion` | Create excursion event with affected inventory |
| `resolve_excursion` | Document corrective action and resolve |
| `get_temperature_trend` | Temperature history chart data |
| `get_cold_chain_dashboard` | Cold chain status for pharmacy |

---

## 6. API Endpoints (55+)

### 6.1 Drug Catalog (9)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pharmacy/catalog` | Search drug catalog |
| POST | `/pharmacy/catalog` | Add drug to catalog |
| GET | `/pharmacy/catalog/{id}` | Get drug detail |
| PUT | `/pharmacy/catalog/{id}` | Update drug record |
| GET | `/pharmacy/catalog/{id}/formulations` | Drug formulations |
| GET | `/pharmacy/catalog/{id}/packages` | Drug packages with GS1 barcodes |
| GET | `/pharmacy/catalog/{id}/atc` | ATC classification hierarchy |
| GET | `/pharmacy/catalog/{id}/alternatives` | Therapeutic alternatives |
| GET | `/pharmacy/catalog/{id}/pricing` | Pricing records |

### 6.2 Prescriptions (8)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pharmacy/prescriptions` | List prescriptions |
| POST | `/pharmacy/prescriptions` | Create prescription |
| GET | `/pharmacy/prescriptions/{id}` | Get prescription detail |
| PUT | `/pharmacy/prescriptions/{id}` | Update prescription |
| POST | `/pharmacy/prescriptions/{id}/cancel` | Cancel prescription |
| GET | `/pharmacy/prescriptions/patient/{patient_id}` | Patient prescription history |
| GET | `/pharmacy/prescriptions/pending` | Pending prescriptions |
| GET | `/pharmacy/prescriptions/{id}/validate` | Validate prescription safety |

### 6.3 Dispensing (8)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pharmacy/dispensing` | List dispensing sessions |
| POST | `/pharmacy/dispensing` | Start dispensing |
| GET | `/pharmacy/dispensing/{id}` | Get dispensing detail |
| POST | `/pharmacy/dispensing/{id}/scan` | Scan medication barcode |
| POST | `/pharmacy/dispensing/{id}/verify` | Pharmacist verification |
| POST | `/pharmacy/dispensing/{id}/complete` | Complete dispensing |
| POST | `/pharmacy/dispensing/{id}/partial` | Partial dispense |
| POST | `/pharmacy/dispensing/{id}/reverse` | Reverse dispensing |

### 6.4 Inventory (11)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pharmacy/inventory` | Stock levels with filters |
| GET | `/pharmacy/inventory/{id}` | Stock detail for item |
| PUT | `/pharmacy/inventory/{id}` | Update stock record |
| POST | `/pharmacy/inventory/adjust` | Manual stock adjustment |
| POST | `/pharmacy/inventory/receive` | Receive stock |
| POST | `/pharmacy/inventory/transfer` | Transfer between locations |
| GET | `/pharmacy/inventory/expiry` | Expiry report |
| GET | `/pharmacy/inventory/reorder` | Reorder suggestions |
| POST | `/pharmacy/inventory/reorder/generate` | Generate reorder |
| POST | `/pharmacy/inventory/stock-take` | Initiate stock take |
| GET | `/pharmacy/inventory/consumption` | Consumption report |

### 6.5 Clinical Pharmacy (7)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/pharmacy/clinical/interactions` | Check drug-drug interactions |
| POST | `/pharmacy/clinical/contraindications` | Check contraindications |
| POST | `/pharmacy/clinical/dose-calculate` | Calculate dose |
| POST | `/pharmacy/clinical/validate-order` | Full order safety validation |
| POST | `/pharmacy/clinical/duplicate-check` | Check duplicate therapy |
| GET | `/pharmacy/clinical/monographs/{id}` | Get drug monograph |
| GET | `/pharmacy/clinical/interactions/bulk` | Bulk interaction check (formulary) |

### 6.6 Cold Chain (6)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pharmacy/cold-chain` | Cold chain status |
| POST | `/pharmacy/cold-chain/log` | Record temperature reading |
| GET | `/pharmacy/cold-chain/logs` | Temperature log with filters |
| GET | `/pharmacy/cold-chain/excursions` | Excursion history |
| POST | `/pharmacy/cold-chain/excursions/{id}/resolve` | Resolve excursion |
| GET | `/pharmacy/cold-chain/trend` | Temperature trend data |

### 6.7 Controlled Substances (4)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pharmacy/controlled` | Controlled substance inventory |
| GET | `/pharmacy/controlled/{id}` | CS detail with balance |
| GET | `/pharmacy/controlled/{id}/audit-log` | CS audit trail |
| POST | `/pharmacy/controlled/audit` | Perform CS audit |

### 6.8 Configuration (3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pharmacy/locations` | Pharmacy locations |
| POST | `/pharmacy/locations` | Add pharmacy location |
| GET | `/pharmacy/config` | Pharmacy configuration |

### 6.9 Sync (3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pharmacy/sync/changes` | Changes since timestamp |
| POST | `/pharmacy/sync/push` | Push offline changes |
| GET | `/pharmacy/sync/status` | Sync status |

---

## 7. Clinical Pharmacy

### 7.1 Drug Interaction Engine

The `ClinicalEngine` provides real-time drug interaction checking:

- **Knowledge Base**: DrugBank-derived interaction data with severity classification
- **Query Types**: Single drug pair, multi-drug regimen, full patient medication list
- **Response**: Sorted by severity, with mechanism description, clinical effect, and management recommendation
- **Scope**: Drug-drug, drug-food, drug-condition (contraindications)
- **Integration**: Called automatically during prescription validation and dispensing

### 7.2 Contraindication Screening

Contraindications are checked against the patient's known conditions (ICD-10 coded):

- Condition-based contraindications (e.g., NSAIDs in renal impairment)
- Allergy cross-referencing (e.g., penicillin allergy → avoid all beta-lactams)
- Age-based contraindications (e.g., tetracyclines under 8 years)
- Pregnancy/lactation warnings
- Lab-value-based precautions (e.g., metformin with renal function)

### 7.3 Dose Calculation

Dose calculation supports multiple methods:

| Method | Formula | Parameters |
|--------|---------|------------|
| Weight-based | `dose = weight_kg × mg_per_kg` | Weight, mg/kg factor, max dose |
| BSA-based | `dose = BSA × mg_per_m2` | Height, weight, Mosteller formula |
| Age-based | `dose = age_adjusted_factor × standard_dose` | Age, age group ranges |
| Renal-adjusted | `dose = standard_dose × (CrCl_adjustment)` | CrCl, drug-specific adjustment table |
| Hepatic-adjusted | `dose = standard_dose × hepatic_factor` | Child-Pugh score, drug-specific factor |

---

## 8. Integration with EHR Medication Models

### 8.1 Medication Order Flow

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐
│ EHR MD  │────→│ Pharmacy │────→│ Dispense │────→│ Nursing │
│ Orders  │     │ Receives │     │ Barcode  │     │ BCMA    │
│ Drug X  │     │ Order    │     │ Verify   │     │ Admin   │
└─────────┘     └──────────┘     └──────────┘     └─────────┘
     │               │               │               │
     ↓               ↓               ↓               ↓
┌─────────────────────────────────────────────────────────┐
│               MedicationDispensation Table               │
│  Tracks: ordered → verified → dispensed → administered  │
└─────────────────────────────────────────────────────────┘
```

### 8.2 FHIR MedicationRequest Integration

The `medication_dispensation` model maintains a direct FK to FHIR `MedicationRequest` resources, enabling:

- Bidirectional status updates between EHR and NPIP
- Real-time order visibility for pharmacy
- MAR synchronization with Nursing BCMA
- Clinical validation at order entry (interactions, contraindications)

---

## 9. Reuse Summary

| Component | Reused From | How |
|-----------|-------------|-----|
| Patient model | `models/patient.py` | FK in prescriptions, dispensing |
| LabUser model | `models/lab_user.py` | Pharmacist and prescriber identity |
| EHR medication orders | `ehr_service.py` | `MedicationDispensation.ehr_order_id` |
| AuditService | `services/audit_service.py` | All inventory and dispensing mutations |
| Auth/JWT | `security/auth.py` | API authentication |
| RBAC | `security/rbac.py` | Pharmacy-specific roles (pharmacist, tech, admin) |
| Database session | `database.py` | Shared SQLAlchemy engine |
| Event bus | `core/events.py` | Publish dispensing events to EHR/nursing |
| Notification service | `notifications/` | Inventory alerts, interaction warnings |

---

## 10. GS1 Barcode Support

### 10.1 Barcode Structure

NPIP uses GS1-128 barcodes (GS1 DataMatrix for unit-dose) with Application Identifiers:

| AI | Field | Example |
|----|-------|---------|
| 01 | GTIN (Global Trade Item Number) | 06285910000015 |
| 10 | Lot/Batch Number | A123B4C5 |
| 17 | Expiry Date (YYMMDD) | 271231 |
| 21 | Serial Number | SER123456 |
| 30 | Quantity | 5 |
| 37 | Count of trade items | 20 |

### 10.2 Barcode Workflow

```
Receiving: Scan GTIN → System identifies drug + package
           → Validate against purchase order
           → Record lot number and expiry
           → Update inventory

Dispensing: Scan GTIN → System identifies drug
            → Validate against prescription item
            → Check lot/expiry
            → Record dispensed lot
            → Update inventory

Administration: Scan GTIN on dispensed unit
               → BCMA system validates against medication order
               → Five rights check
               → Record administration
```

---

## 11. Cold Chain Management

### 11.1 Temperature Ranges

| Storage Type | Temperature Range | Monitoring |
|-------------|-------------------|------------|
| Refrigerated (2-8°C) | 2°C to 8°C | Continuous with alerts at 2.5°C and 7.5°C |
| Frozen (-20°C) | -25°C to -15°C | Continuous with alerts at -20°C and -18°C |
| Ultra-frozen (-80°C) | -80°C to -60°C | Continuous with alerts |
| Room temperature | 15°C to 25°C | Periodic logging |

### 11.2 Excursion Protocol

```
Temperature outside range
       ↓
System creates ColdChainExcursion
       ↓
Alert sent to pharmacy manager and quality team
       ↓
Affected items identified and quarantined in inventory
       ↓
Pharmacist assesses impact (duration, severity, product stability data)
       ↓
Decision: Use / Return to Supplier / Destroy
       ↓
Excursion resolved with documented action
       ↓
Inventory updated (released from quarantine / adjusted for loss)
```

---

## 12. Controlled Substance Workflows

### 12.1 Schedules (Iraq MOH Classification)

| Schedule | Description | Examples | Workflow |
|----------|-------------|----------|----------|
| I | Narcotics — highest control | Morphine, Pethidine, Fentanyl | Two-nurse witness, locked storage, daily count |
| II | Psychotropics | Diazepam, Midazolam, Tramadol | Dual signature, locked storage, weekly audit |
| III | Precursors | Pseudoephedrine | Documented dispensing, monthly audit |
| IV | Other controlled | Codeine, Gabapentin | Standard dispensing with reason code |

### 12.2 Audit Trail Requirements

Every controlled substance transaction records:
- Timestamp (with timezone)
- Patient ID and name
- Prescriber ID and name
- Dispensing pharmacist ID and name
- Administering nurse ID and name (if applicable)
- Witness ID and name (for Schedule I-II)
- Quantity before and after
- Transaction reason/type
- Balance after transaction
- Computer-generated transaction ID (sequential, non-repeating)

### 12.3 Mandatory Reconciliation

- **Daily**: Schedule I substances counted and reconciled against log
- **Weekly**: Schedule II substances counted and reconciled
- **Monthly**: Full inventory reconciliation for all controlled substances
- **Quarterly**: Physical audit by independent auditor

---

## 13. ATC Classification System

The NPIP uses the WHO ATC (Anatomical Therapeutic Chemical) classification system with Iraqi Ministry of Health extensions:

| Level | Code | Description | Example |
|-------|------|-------------|---------|
| Anatomical | A | Alimentary tract and metabolism | A |
| Therapeutic | A10 | Drugs used in diabetes | A10 |
| Pharmacological | A10B | Blood glucose lowering drugs | A10B |
| Chemical | A10BA | Biguanides | A10BA |
| Substance | A10BA02 | Metformin | A10BA02 |

The system supports:
- Full ATC hierarchy navigation
- Lookup by any ATC level for formulary management
- Therapeutic alternative identification (same chemical subgroup)
- National reporting by ATC category
- Custom Iraqi extensions for locally approved medications

---

## 14. Offline-First Design

- **Catalog**: Cached locally, updated on sync (daily or on-demand)
- **Prescriptions**: Created offline, synced when online (outbox pattern)
- **Dispensing**: Requires online verification for clinical checks; offline dispensing with deferred validation
- **Inventory**: Stock records cached, updates synced (delta sync)
- **Cold chain**: Temperature readings logged locally, bulk synced
- **Controlled substances**: Limited offline mode (full audit trail required before next online sync)

---

## 15. FHIR Mappings

| NPIP Entity | FHIR Resource | Mapping Notes |
|-------------|---------------|---------------|
| DrugCatalog | `Medication` | code (ATC), form, ingredient, batch |
| DrugPackage | `MedicationKnowledge` (R4/R5) | packaging, cost, regulatory status |
| Prescription | `MedicationRequest` | subject, medication, dosageInstruction, dispenseRequest |
| Dispensing | `MedicationDispense` | medication, subject, quantity, type, whenHandedOver |
| MedicationAdminRecord | `MedicationAdministration` | medication, subject, effectiveDateTime, dose, route |
| DrugInteraction | `DetectedIssue` | code (DRG), mitigation, severity |
| PharmacyInventory | `SupplyDelivery` | suppliedItem, quantity, occurrencePeriod |
| Location | `Location` | physicalType, mode, operationalStatus |
