# GULA National Health Ecosystem — Architecture & Scope

## 1. Vision & Scope

GULA is not limited to a single laboratory information system; it is a **comprehensive national healthcare platform** designed to serve the entire health sector in Iraq—spanning the **public sector (Ministry of Health and public hospitals/clinics)**, the **private sector (private hospitals, labs, pharmacies, radiology centers)**, and the **mixed/institutional sector**.

The platform unifies patient records, clinical workflows, administrative management, and ancillary support services into a single integrated architecture with strict role-based access control, multi-tenant institutional isolation, and immutable audit logging.

## 2. Core Health Services & Workspaces

The platform is organized into adaptive workspaces accessible through a unified account:

| Workspace ID | Domain | Primary Scope |
|---|---|---|
| `laboratory` | Laboratory Information System (LIS) | Specimen tracking, order entry, CPOE, test execution, review, and release |
| `hospital` | Hospital & Inpatient Operations | ADT (Admission, Discharge, Transfer), ward rounds, bed management, and nursing care |
| `clinical` | Outpatient & Clinic Management | Appointments, consultations, SOAP notes, electronic prescriptions, and referrals |
| `pharmacy` | Pharmacy & Medication Supply | Drug catalogs, inventory, prescription dispensing, and stock tracking |
| `radiology` | Radiology & PACS Integration | Imaging orders, DICOM metadata storage, reports, and diagnostic reviews |
| `emergency` | Emergency & Triage | Fast-track intake, trauma triage, critical alerts, and emergency medication |
| `public_health` | Public Health & Epidemiology | Outbreak surveillance, population health metrics, and mandatory reporting |
| `facility` | Institution Administration | Staff management, role assignments, billing, resource allocation, and audit reviews |
| `governance` | National Health Governance | Cross-institution compliance, policy enforcement, and regulatory oversight |

## 3. Sector Integration (Public, Private, Mixed)

GULA provides standardized APIs and data adapters to integrate with existing legacy systems across all three sectors:
- **Public Sector**: Direct alignment with Ministry of Health standards, district health offices, and public hospital networks.
- **Private Sector**: Secure tenant boundaries for private hospitals, independent laboratories, and specialized clinics.
- **Mixed/Institutional Sector**: Corporate health programs, university medical centers, and insurance-linked providers.

## 4. Google Play Console & Mobile Distribution

To support mobile deployment across Android and iOS:
- **Android (`io.gula.android`)**: Configured with production signing, ProGuard rules, adaptive icons, and App Bundle (`.aab`) output ready for Google Play Console publishing.
- **iOS (`io.gula.ios`)**: Native Swift wrapper and PWA fallback configured with secure cookie handling and keychain persistence for App Store submission.
