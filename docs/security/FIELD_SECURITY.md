# GULA Platform — Field-Level Security Model

**Version:** 1.0.0

---

## 1. Field Security Model

Every field in every resource type has an associated security profile that defines how it is displayed and manipulated.

```python
class FieldSecurity:
    field_id: str              # e.g., "patient.national_id"
    resource_type: str         # e.g., "patient"
    field_name: str            # e.g., "national_id"
    default_level: SecurityLevel
    levels_by_role: dict[str, SecurityLevel]   # Role-specific overrides
    levels_by_org_type: dict[str, SecurityLevel]  # Org-specific overrides
    consent_required: bool     # Requires patient consent
    encryption_required: bool  # Encrypted at rest
    masking_pattern: str | None  # e.g., "XXXX-XXXX-XXX{last_4}"
    audit_access: bool         # Log every access to this field
    purpose_restricted: list[str]  # Restricted purposes
```

---

## 2. Security Levels

| Level | Code | Display Behavior | Edit Behavior |
|-------|------|-----------------|---------------|
| Public | `public` | Visible to all authenticated | Editable by authorized |
| Internal | `internal` | Visible within organization | Editable by authorized |
| Restricted | `restricted` | Visible by role + need-to-know | Editable by specific roles |
| Sensitive | `sensitive` | Visible with explicit permission | Editable with justification |
| Protected | `protected` | Hidden by default, shown on request | Editable with consent |
| Confidential | `confidential` | Masked (e.g., XXXX-XX-1234) | Not editable |
| Secret | `secret` | Never displayed, API-only | Not editable |

---

## 3. Field Security by Resource Type

### 3.1 Patient Fields

| Field | Default Level | Sensitive To | Notes |
|-------|-------------|-------------|-------|
| `full_name` | public | — | |
| `date_of_birth` | public | — | |
| `gender` | public | — | |
| `phone` | restricted | patient | Masked for non-clinical |
| `email` | internal | patient | |
| `address` | restricted | patient | |
| `national_id` | protected | patient | Encrypted at rest |
| `passport_number` | protected | patient | Encrypted |
| `health_id` | internal | — | |
| `blood_type` | public | — | |
| `emergency_contact` | restricted | patient | |
| `occupation` | public | — | |
| `marital_status` | public | — | |
| `religion` | internal | patient | |
| `nationality` | public | — | |
| `photo` | internal | patient | |
| `biometric_data` | secret | patient | API only |
| `insurance_policy` | protected | patient | |
| `employer` | internal | patient | |
| `diagnosis` | restricted | patient | |
| `diagnosis.sensitive` | confidential | patient | HIV, cancer, psychiatric |
| `lab_results` | restricted | patient | |
| `lab_results.hiv` | confidential | patient | |
| `lab_results.genetic` | secret | patient | |
| `medication_history` | restricted | patient | |
| `allergies` | restricted | patient | |
| `smoking_status` | internal | patient | |
| `pregnancy_status` | sensitive | patient | |
| `sexual_history` | confidential | patient | |
| `mental_health_history` | confidential | patient | |
| `criminal_record` | confidential | patient | |
| `consent_records` | restricted | — | |
| `advance_directives` | restricted | patient | |
| `organ_donor_status` | internal | patient | |
| `next_of_kin` | restricted | patient | |
| `billing_info` | protected | patient | |
| `payment_history` | protected | patient | |

### 3.2 Employee Fields

| Field | Default Level | Notes |
|-------|-------------|-------|
| `full_name` | public | |
| `employee_id` | internal | |
| `department` | internal | |
| `position` | public | |
| `specialty` | public | |
| `license_number` | restricted | |
| `certifications` | internal | |
| `salary` | confidential | HR + finance only |
| `performance_review` | restricted | Supervisor + HR |
| `disciplinary_record` | confidential | HR + compliance |
| `contact_info` | restricted | |
| `emergency_contact` | restricted | |
| `schedule` | internal | |
| `training_records` | internal | |
| `education` | public | |
| `national_id` | protected | Encrypted |
| `bank_account` | confidential | Finance only |
| `medical_clearance` | restricted | Occupational health |
| `vaccination_status` | internal | |
| `login_activity` | restricted | System admin + self |

### 3.3 Order Fields

| Field | Default Level | Notes |
|-------|-------------|-------|
| `order_id` | public | |
| `patient_name` | restricted | |
| `patient_id` | restricted | |
| `test_name` | internal | |
| `test_code` | internal | |
| `priority` | public | |
| `status` | public | |
| `requesting_doctor` | internal | |
| `requesting_department` | internal | |
| `clinical_notes` | restricted | |
| `diagnosis_code` | restricted | |
| `insurance_info` | protected | |
| `consent_status` | restricted | |
| `collection_date` | internal | |
| `collection_location` | internal | |
| `collected_by` | internal | |
| `verified_by` | internal | |
| `approved_by` | internal | |
| `cancellation_reason` | internal | |
| `order_notes` | internal | |

### 3.4 Result Fields

| Field | Default Level | Notes |
|-------|-------------|-------|
| `result_id` | public | |
| `test_name` | public | |
| `result_value` | restricted | |
| `result_unit` | public | |
| `reference_range` | public | |
| `interpretation` | restricted | |
| `status` | public | |
| `performed_by` | internal | |
| `verified_by` | internal | |
| `validated_by` | internal | |
| `instrument_id` | internal | |
| `result_notes` | internal | |
| `abnormal_flags` | internal | |
| `critical_flags` | internal | |
| `amendment_history` | restricted | |
| `quality_control_ref` | internal | |
| `attachments` | restricted | |

### 3.5 Financial Fields

| Field | Default Level | Notes |
|-------|-------------|-------|
| `invoice_id` | public | |
| `amount` | internal | |
| `discount` | confidential | |
| `tax_amount` | internal | |
| `total` | internal | |
| `paid_amount` | internal | |
| `balance` | internal | |
| `payment_method` | restricted | |
| `insurance_claim_id` | protected | |
| `insurance_coverage` | protected | |
| `patient_responsibility` | internal | |
| `billing_notes` | restricted | |
| `collection_agency` | confidential | |

---

## 4. Mash Strategies

### 4.1 Masking Patterns

| Field Type | Pattern | Example |
|-----------|---------|---------|
| National ID | `XXXX-XXXX-XXX{last_4}` | `XXXX-XXXX-XXX6789` |
| Phone | `{first_3}XXX-{last_4}` | `077XXXX567` |
| Email | `{first_2}***@{domain}` | `mo***@example.com` |
| Credit Card | `XXXX-XXXX-XXXX-{last_4}` | `XXXX-XXXX-XXXX-1234` |
| Name (partial) | `{first_letter}*** {last_name}` | `م*** أحمد` |
| Address | `{first_3_chars}***` | `بع***` |

### 4.2 Encryption

| Field Type | Encryption | Key |
|-----------|-----------|-----|
| National ID | AES-256-GCM | Per-user key |
| Passport | AES-256-GCM | Per-user key |
| Biometric | AES-256-GCM | Hardware-backed key |
| HIV Results | AES-256-GCM | Per-patient key |
| Genetic Data | AES-256-GCM | Per-patient key |
| Financial Data | AES-256-GCM | Per-org key |
| Mental Health | AES-256-GCM | Per-patient key |

---

## 5. Purpose of Use

Access to sensitive fields requires a declared purpose:

| Purpose | Description | Allowed Fields |
|---------|-------------|---------------|
| `treatment` | Direct patient care | Most clinical fields |
| `payment` | Billing and insurance | Financial, insurance |
| `operations` | Healthcare operations | Operational fields |
| `research` | Approved research | De-identified research set |
| `public_health` | Disease surveillance | Epidemiological fields |
| `quality` | Quality improvement | Anonymized subsets |
| `audit` | Compliance audit | Full access (logged) |
| `emergency` | Emergency care | All fields (break-glass) |

---

## 6. Field Security Evaluation

```
Request to view field "patient.national_id"
  → Check user's role
  → Check role's default level for this field
  → Check if any role-specific override exists
  → Check if org-specific override exists
  → Check if consent is required and granted
  → Check purpose of use
  → If emergency mode: apply break-glass policy
  → Apply masking if level requires it
  → Return effective visibility + editability + masking
```

## 7. API Response

```json
{
  "field_id": "patient.national_id",
  "visible": true,
  "editable": false,
  "value": "XXXX-XXXX-XXX6789",
  "masked": true,
  "encrypted": true,
  "consent_required": false,
  "purpose_required": "identity_verification",
  "reason": null
}
```

## 8. Field Security API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/field-security/:resource_type` | Get field security for resource type |
| GET | `/field-security/:resource_type/:field` | Get field security for specific field |
| PUT | `/field-security/:resource_type/:field` | Update field security (admin) |
| GET | `/field-security/evaluate` | Evaluate field access for current user |
