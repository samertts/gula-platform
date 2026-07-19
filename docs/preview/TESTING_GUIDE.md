# GULA Preview Environment — Testing Guide

## Demo Accounts

| Role | Email | Password | Permissions |
|------|-------|----------|-------------|
| Super Admin | `admin@demo.gula-platform.org` | (auto-login) | Full system access |
| Ministry Admin | `ministry@demo.gula-platform.org` | (auto-login) | National dashboards, policies |
| Directorate Manager | `directorate@demo.gula-platform.org` | (auto-login) | Regional oversight |
| Hospital Director | `hospital@demo.gula-platform.org` | (auto-login) | Hospital management |
| Lab Manager | `lab.manager@demo.gula-platform.org` | (auto-login) | Lab operations, QC, staff |
| Lab Technician | `lab.tech@demo.gula-platform.org` | (auto-login) | Sample processing, results entry |
| Doctor | `doctor@demo.gula-platform.org` | (auto-login) | Orders, patient records, results |
| Pharmacist | `pharmacist@demo.gula-platform.org` | (auto-login) | Pharmacy, prescriptions |
| Nurse | `nurse@demo.gula-platform.org` | (auto-login) | Patient care, sample collection |
| Reception | `reception@demo.gula-platform.org` | (auto-login) | Registration, appointments |
| Auditor | `auditor@demo.gula-platform.org` | (auto-login) | Audit logs, compliance |
| Citizen | `citizen@demo.gula-platform.org` | (auto-login) | Personal health records |

## Demo Scenarios

### Scenario 1: Patient Registration & Lab Order
1. Login as **Reception**
2. Register a new patient (mock data auto-fills)
3. Create a lab order (select tests)
4. Switch to **Lab Technician** role
5. View the pending order in work queue
6. Process the sample and enter results

### Scenario 2: Result Verification
1. Login as **Lab Manager**
2. Review pending verification queue
3. Verify lab results
4. Flag abnormal results for doctor review

### Scenario 3: Clinical Review
1. Login as **Doctor**
2. View patient list
3. Open patient record with recent lab results
4. Review AI assistant analysis
5. Add clinical notes

### Scenario 4: Ministry Analytics
1. Login as **Ministry Admin**
2. View national health dashboard
3. Explore analytics and KPIs
4. Generate report

### Scenario 5: Document Intelligence
1. Login as any role
2. Navigate to Document Intelligence
3. Upload a sample document (mock processes it)
4. View OCR results, classification, entity extraction
5. Explore knowledge graph connections

### Scenario 6: Feature Flag Testing
1. Login as **Super Admin**
2. Open feature flags panel
3. Disable AI features
4. Verify AI assistant disappears from UI
5. Re-enable and verify restoration

## Data Reset

To reset the synthetic data store:
1. Click the 📊 button (bottom-right)
2. Click **Reset** (clears all data)
3. Click **Regenerate** (creates fresh synthetic data)

## Testing URLs

| Page | URL |
|------|-----|
| Dashboard | `/` |
| Patients | `/patients` |
| Lab Dashboard | `/lab/dashboard` |
| Lab Queue | `/lab/queue` |
| Sample Tracking | `/lab/samples` |
| Quality Control | `/lab/qc` |
| Ministry Dashboard | `/ministry/dashboard` |
| Epidemiology | `/ministry/epidemiology` |
| Citizen Portal | `/citizen/dashboard` |
| Settings | `/settings` |
| Audit Log | `/admin/audit` |
| Infrastructure | `/admin/infrastructure` |
