# GULA Platform — Enterprise Role Catalog

**Version:** 1.0.0
**Total Roles:** 156
**Role Hierarchy Levels:** 5 (National → Governorate → Institution → Department → Personal)

---

## Role Hierarchy

```
National (N)
└── Governorate (G)
    └── Institution (I)
        └── Department (D)
            └── Personal (P)
```

**Inheritance**: Each role inherits permissions from all parent roles in its hierarchy.
**Role Groups**: Roles can be grouped for bulk assignment and permissions management.

---

## 1. National Roles (18)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Hierarchy |
|---|---------|---------------|----------------|-------|-----------|
| 1 | `minister_of_health` | Minister of Health | وزير الصحة | N | National |
| 2 | `deputy_minister` | Deputy Minister | نائب وزير الصحة | N | National |
| 3 | `director_general` | Director General | مدير عام | N | National |
| 4 | `national_health_commissioner` | National Health Commissioner | مفوض الصحة الوطني | N | National |
| 5 | `national_epidemiology_director` | National Epidemiology Director | مدير الترصد الوبائي الوطني | N | National |
| 6 | `national_pharmacy_director` | National Pharmacy Director | مدير الصيدلة الوطني | N | National |
| 7 | `national_lab_director` | National Laboratory Director | مدير المختبرات الوطني | N | National |
| 8 | `national_blood_bank_director` | National Blood Bank Director | مدير بنك الدم الوطني | N | National |
| 9 | `national_vaccination_director` | National Vaccination Director | مدير التلقيح الوطني | N | National |
| 10 | `national_emergency_director` | National Emergency Director | مدير الطوارئ الوطني | N | National |
| 11 | `national_insurance_commissioner` | National Insurance Commissioner | مفوض التأمين الصحي | N | National |
| 12 | `national_research_director` | National Research Director | مدير البحوث الوطنية | N | National |
| 13 | `national_quality_director` | National Quality Director | مدير الجودة الوطني | N | National |
| 14 | `national_data_officer` | National Data Officer | مسؤول البيانات الوطني | N | National |
| 15 | `national_security_officer` | National Security Officer | مسؤول الأمن السيبراني | N | National |
| 16 | `national_system_administrator` | National System Administrator | مدير النظام الوطني | N | National |
| 17 | `national_compliance_director` | National Compliance Director | مدير الامتثال الوطني | N | National |
| 18 | `national_auditor` | National Auditor | المراجع الوطني | N | National |

## 2. Governorate Roles (12)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 19 | `governorate_director` | Governorate Health Director | مدير صحة المحافظة | G | `director_general` |
| 20 | `deputy_governorate_director` | Deputy Governorate Director | نائب مدير صحة المحافظة | G | `governorate_director` |
| 21 | `governorate_epidemiology_head` | Governorate Epidemiology Head | رئيس الترصد الوبائي | G | `national_epidemiology_director` |
| 22 | `governorate_lab_director` | Governorate Lab Director | مدير مختبرات المحافظة | G | `national_lab_director` |
| 23 | `governorate_pharmacy_director` | Governorate Pharmacy Director | مدير صيدلة المحافظة | G | `national_pharmacy_director` |
| 24 | `governorate_blood_bank_director` | Governorate Blood Bank Director | مدير بنك دم المحافظة | G | `national_blood_bank_director` |
| 25 | `governorate_vaccination_director` | Governorate Vaccination Director | مدير تلقيح المحافظة | G | `national_vaccination_director` |
| 26 | `governorate_emergency_coordinator` | Governorate Emergency Coordinator | منسق طوارئ المحافظة | G | `national_emergency_director` |
| 27 | `governorate_quality_officer` | Governorate Quality Officer | مسؤول جودة المحافظة | G | `national_quality_director` |
| 28 | `governorate_data_analyst` | Governorate Data Analyst | محلل بيانات المحافظة | G | `national_data_officer` |
| 29 | `governorate_compliance_officer` | Governorate Compliance Officer | مسؤول امتثال المحافظة | G | `national_compliance_director` |
| 30 | `governorate_auditor` | Governorate Auditor | مراجع المحافظة | G | `national_auditor` |

## 3. Institution Leadership Roles (12)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 31 | `hospital_director` | Hospital Director | مدير المستشفى | I | `governorate_director` |
| 32 | `deputy_hospital_director` | Deputy Hospital Director | نائب مدير المستشفى | I | `hospital_director` |
| 33 | `medical_director` | Medical Director | المدير الطبي | I | `hospital_director` |
| 34 | `nursing_director` | Nursing Director | مدير التمريض | I | `hospital_director` |
| 35 | `administrative_director` | Administrative Director | المدير الإداري | I | `hospital_director` |
| 36 | `financial_director` | Financial Director | المدير المالي | I | `hospital_director` |
| 37 | `phc_director` | PHC Center Director | مدير مركز الرعاية الأولية | I | `governorate_director` |
| 38 | `lab_director` | Lab Director | مدير المختبر | I | `governorate_lab_director` |
| 39 | `blood_bank_director` | Blood Bank Director | مدير بنك الدم | I | `governorate_blood_bank_director` |
| 40 | `radiology_director` | Radiology Director | مدير الأشعة | I | `hospital_director` |
| 41 | `pharmacy_director` | Pharmacy Director | مدير الصيدلية | I | `governorate_pharmacy_director` |
| 42 | `emergency_director` | Emergency Department Director | مدير الطوارئ | I | `hospital_director` |

## 4. Department Head Roles (14)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 43 | `internal_medicine_head` | Internal Medicine Head | رئيس الطب الباطني | D | `medical_director` |
| 44 | `surgery_head` | Surgery Department Head | رئيس قسم الجراحة | D | `medical_director` |
| 45 | `pediatrics_head` | Pediatrics Department Head | رئيس قسم الأطفال | D | `medical_director` |
| 46 | `obgyn_head` | OB/GYN Department Head | رئيس قسم النساء والتوليد | D | `medical_director` |
| 47 | `cardiology_head` | Cardiology Department Head | رئيس قسم القلب | D | `medical_director` |
| 48 | `orthopedics_head` | Orthopedics Department Head | رئيس قسم العظام | D | `medical_director` |
| 49 | `neurology_head` | Neurology Department Head | رئيس قسم الأعصاب | D | `medical_director` |
| 50 | `pathology_head` | Pathology Department Head | رئيس قسم الباثولوجيا | D | `lab_director` |
| 51 | `microbiology_head` | Microbiology Department Head | رئيس قسم الأحياء الدقيقة | D | `lab_director` |
| 52 | `hematology_head` | Hematology Department Head | رئيس قسم الدم | D | `lab_director` |
| 53 | `biochemistry_head` | Biochemistry Department Head | رئيس قسم الكيمياء الحيوية | D | `lab_director` |
| 54 | `radiology_department_head` | Radiology Department Head | رئيس قسم الأشعة | D | `radiology_director` |
| 55 | `nursing_supervisor` | Nursing Supervisor | مشرف تمريض | D | `nursing_director` |
| 56 | `quality_management_head` | Quality Management Head | رئيس إدارة الجودة | D | `hospital_director` |

## 5. Clinical Roles (30)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 57 | `general_practitioner` | General Practitioner | طبيب عام | D | `medical_director` |
| 58 | `specialist_physician` | Specialist Physician | طبيب اختصاص | D | `department_head` |
| 59 | `senior_consultant` | Senior Consultant | استشاري أول | D | `department_head` |
| 60 | `surgeon` | Surgeon | جراح | D | `surgery_head` |
| 61 | `cardiology_specialist` | Cardiology Specialist | طبيب قلب اختصاص | D | `cardiology_head` |
| 62 | `neurology_specialist` | Neurology Specialist | طبيب أعصاب اختصاص | D | `neurology_head` |
| 63 | `pediatrician` | Pediatrician | طبيب أطفال | D | `pediatrics_head` |
| 64 | `obgyn_specialist` | OB/GYN Specialist | طبيب نسائية وتوليد | D | `obgyn_head` |
| 65 | `orthopedic_surgeon` | Orthopedic Surgeon | جراح عظام | D | `orthopedics_head` |
| 66 | `anesthesiologist` | Anesthesiologist | طبيب تخدير | D | `surgery_head` |
| 67 | `emergency_physician` | Emergency Physician | طبيب طوارئ | D | `emergency_director` |
| 68 | `intensivist` | Intensivist (ICU) | طبيب عناية مركزة | D | `internal_medicine_head` |
| 69 | `psychiatrist` | Psychiatrist | طبيب نفسي | D | `internal_medicine_head` |
| 70 | `dermatologist` | Dermatologist | طبيب جلدية | D | `internal_medicine_head` |
| 71 | `ophthalmologist` | Ophthalmologist | طبيب عيون | D | `surgery_head` |
| 72 | `ent_specialist` | ENT Specialist | طبيب أنف وأذن وحنجرة | D | `surgery_head` |
| 73 | `urologist` | Urologist | طبيب مسالك بولية | D | `surgery_head` |
| 74 | `nephrologist` | Nephrologist | طبيب كلى | D | `internal_medicine_head` |
| 75 | `endocrinologist` | Endocrinologist | طبيب غدد صماء | D | `internal_medicine_head` |
| 76 | `gastroenterologist` | Gastroenterologist | طبيب جهاز هضمي | D | `internal_medicine_head` |
| 77 | `pulmonologist` | Pulmonologist | طبيب صدرية | D | `internal_medicine_head` |
| 78 | `rheumatologist` | Rheumatologist | طبيب روماتيزم | D | `internal_medicine_head` |
| 79 | `oncologist` | Oncologist | طبيب أورام | D | `internal_medicine_head` |
| 80 | `infectious_disease_specialist` | Infectious Disease Specialist | طبيب أمراض معدية | D | `internal_medicine_head` |
| 81 | `resident_physician` | Resident Physician | طبيب مقيم | D | `department_head` |
| 82 | `intern_physician` | Intern Physician | طبيب متدرب | D | `department_head` |
| 83 | `dentist` | Dentist | طبيب أسنان | D | `hospital_director` |
| 84 | `oral_surgeon` | Oral Surgeon | جراح فم | D | `dentist` |
| 85 | `orthodontist` | Orthodontist | تقويم أسنان | D | `dentist` |
| 86 | `periodontist` | Periodontist | طبيب لثة | D | `dentist` |

## 6. Nursing & Patient Care Roles (8)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 87 | `registered_nurse` | Registered Nurse | ممرض قانوني | D | `nursing_supervisor` |
| 88 | `senior_nurse` | Senior Nurse | ممرض أول | D | `nursing_supervisor` |
| 89 | `critical_care_nurse` | Critical Care Nurse | ممرض عناية مركزة | D | `nursing_supervisor` |
| 90 | `emergency_nurse` | Emergency Nurse | ممرض طوارئ | D | `emergency_director` |
| 91 | `midwife` | Midwife | قابلة قانونية | D | `obgyn_head` |
| 92 | `nurse_educator` | Nurse Educator | مربي تمريض | D | `nursing_director` |
| 93 | `community_health_nurse` | Community Health Nurse | ممرض صحة مجتمع | D | `nursing_director` |
| 94 | `school_nurse` | School Nurse | ممرض مدرسي | D | `nursing_director` |

## 7. Laboratory Roles (12)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 95 | `lab_technician` | Lab Technician | فني مختبر | D | `lab_director` |
| 96 | `senior_lab_technician` | Senior Lab Technician | فني مختبر أول | D | `lab_director` |
| 97 | `lab_supervisor` | Lab Supervisor | مشرف مختبر | D | `lab_director` |
| 98 | `pathologist_doctor` | Pathologist (Doctor) | طبيب باثولوجيا | D | `pathology_head` |
| 99 | `microbiologist_doctor` | Microbiologist (Doctor) | طبيب أحياء دقيقة | D | `microbiology_head` |
| 100 | `clinical_biochemist` | Clinical Biochemist | كيميائي حيوي سريري | D | `biochemistry_head` |
| 101 | `hematology_specialist` | Hematology Specialist | اختصاصي أمراض دم | D | `hematology_head` |
| 102 | `phlebotomist` | Phlebotomist | فني سحب دم | D | `lab_supervisor` |
| 103 | `lab_quality_technician` | Lab Quality Technician | فني جودة مختبر | D | `lab_director` |
| 104 | `lab_instrument_operator` | Lab Instrument Operator | مشغل أجهزة مختبر | D | `lab_supervisor` |
| 105 | `lab_data_entry` | Lab Data Entry | إدخال بيانات مختبر | D | `lab_supervisor` |
| 106 | `lab_courier` | Lab Courier | ساعي مختبر | D | `lab_supervisor` |

## 8. Radiology Roles (6)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 107 | `radiologist_doctor` | Radiologist (Doctor) | طبيب أشعة | D | `radiology_department_head` |
| 108 | `radiology_technician` | Radiology Technician | فني أشعة | D | `radiology_department_head` |
| 109 | `sonographer` | Sonographer | فني موجات فوق صوتية | D | `radiology_department_head` |
| 110 | `mri_technician` | MRI Technician | فني رنين مغناطيسي | D | `radiology_department_head` |
| 111 | `ct_technician` | CT Technician | فني مقطعية | D | `radiology_department_head` |
| 112 | `nuclear_medicine_technician` | Nuclear Medicine Technician | فني طب نووي | D | `radiology_department_head` |

## 9. Blood Bank Roles (6)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 113 | `blood_bank_technician` | Blood Bank Technician | فني بنك دم | D | `blood_bank_director` |
| 114 | `blood_bank_senior_technician` | Blood Bank Senior Technician | فني بنك دم أول | D | `blood_bank_director` |
| 115 | `transfusion_medicine_specialist` | Transfusion Medicine Specialist | اختصاصي طب نقل الدم | D | `blood_bank_director` |
| 116 | `donation_screener` | Donation Screener | فاحص متبرعين | D | `blood_bank_director` |
| 117 | `blood_bank_quality_officer` | Blood Bank Quality Officer | مسؤول جودة بنك دم | D | `blood_bank_director` |
| 118 | `blood_bank_logistics` | Blood Bank Logistics | لوجستي بنك دم | D | `blood_bank_director` |

## 10. Pharmacy Roles (5)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 119 | `pharmacist` | Pharmacist | صيدلي | D | `pharmacy_director` |
| 120 | `senior_pharmacist` | Senior Pharmacist | صيدلي أول | D | `pharmacy_director` |
| 121 | `clinical_pharmacist` | Clinical Pharmacist | صيدلي سريري | D | `pharmacy_director` |
| 122 | `pharmacy_inventory_manager` | Pharmacy Inventory Manager | مدير مخزون الصيدلية | D | `pharmacy_director` |
| 123 | `pharmacy_technician` | Pharmacy Technician | فني صيدلة | D | `pharmacy_director` |

## 11. Emergency Services Roles (6)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 124 | `paramedic` | Paramedic | مسعف | D | `emergency_director` |
| 125 | `senior_paramedic` | Senior Paramedic | مسعف أول | D | `emergency_director` |
| 126 | `emergency_technician` | Emergency Technician | فني طوارئ | D | `emergency_director` |
| 127 | `dispatcher` | Emergency Dispatcher | مرسل طوارئ | D | `emergency_director` |
| 128 | `field_triage_officer` | Field Triage Officer | مسؤول فرز ميداني | D | `emergency_director` |
| 129 | `emergency_logistics` | Emergency Logistics | لوجستي طوارئ | D | `emergency_director` |

## 12. Administrative Roles (14)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 130 | `receptionist` | Receptionist | موظف استقبال | D | `administrative_director` |
| 131 | `admission_officer` | Admission Officer | مسؤول قبول | D | `administrative_director` |
| 132 | `medical_records_officer` | Medical Records Officer | مسؤول سجلات طبية | D | `administrative_director` |
| 133 | `appointment_scheduler` | Appointment Scheduler | منظم مواعيد | D | `administrative_director` |
| 134 | `cashier` | Cashier | صراف | D | `financial_director` |
| 135 | `accountant` | Accountant | محاسب | D | `financial_director` |
| 136 | `senior_accountant` | Senior Accountant | محاسب أول | D | `financial_director` |
| 137 | `billing_specialist` | Billing Specialist | اختصاصي فوترة | D | `financial_director` |
| 138 | `insurance_coordinator` | Insurance Coordinator | منسق تأمين | D | `financial_director` |
| 139 | `procurement_officer` | Procurement Officer | مسؤول مشتريات | D | `administrative_director` |
| 140 | `warehouse_officer` | Warehouse Officer | مسؤول مستودع | D | `administrative_director` |
| 141 | `logistics_officer` | Logistics Officer | مسؤول لوجستي | D | `administrative_director` |
| 142 | `biomedical_engineer` | Biomedical Engineer | مهندس طبي | D | `administrative_director` |
| 143 | `facility_manager` | Facility Manager | مدير منشأة | D | `administrative_director` |

## 13. Public Health Roles (10)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 144 | `epidemiologist` | Epidemiologist | اختصاصي وبائيات | D | `governorate_epidemiology_head` |
| 145 | `public_health_analyst` | Public Health Analyst | محلل صحة عامة | D | `governorate_epidemiology_head` |
| 146 | `vaccination_coordinator` | Vaccination Coordinator | منسق تلقيح | D | `governorate_vaccination_director` |
| 147 | `infection_control_practitioner` | Infection Control Practitioner | ممارس مكافحة عدوى | D | `quality_management_head` |
| 148 | `health_educator` | Health Educator | مثقف صحي | D | `governorate_director` |
| 149 | `community_health_worker` | Community Health Worker | عامل صحة مجتمع | D | `governorate_director` |
| 150 | `environmental_health_officer` | Environmental Health Officer | مسؤول صحة بيئية | D | `governorate_director` |
| 151 | `occupational_health_officer` | Occupational Health Officer | مسؤول صحة مهنية | D | `governorate_director` |
| 152 | `school_health_officer` | School Health Officer | مسؤول صحة مدرسية | D | `governorate_director` |
| 153 | `health_promotion_officer` | Health Promotion Officer | مسؤول تعزيز الصحة | D | `governorate_director` |

## 14. Specialized & Support Roles (12)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 154 | `internal_auditor` | Internal Auditor | مراجع داخلي | D | `governorate_auditor` |
| 155 | `compliance_officer` | Compliance Officer | مسؤول امتثال | D | `governorate_compliance_officer` |
| 156 | `quality_officer` | Quality Officer | مسؤول جودة | D | `quality_management_head` |
| 157 | `patient_safety_officer` | Patient Safety Officer | مسؤول سلامة المرضى | D | `quality_management_head` |
| 158 | `data_protection_officer` | Data Protection Officer | مسؤول حماية البيانات | D | `national_data_officer` |
| 159 | `clinical_trial_coordinator` | Clinical Trial Coordinator | منسق تجارب سريرية | D | `national_research_director` |
| 160 | `research_assistant` | Research Assistant | مساعد باحث | D | `national_research_director` |
| 161 | `medical_educator` | Medical Educator | مربي طبي | D | `national_research_director` |
| 162 | `social_worker` | Social Worker | أخصائي اجتماعي | D | `hospital_director` |
| 163 | `chaplain` | Chaplain (Spiritual Care) | مرشد ديني | D | `hospital_director` |
| 164 | `interpreter` | Medical Interpreter | مترجم طبي | D | `hospital_director` |
| 165 | `volunteer_coordinator` | Volunteer Coordinator | منسق متطوعين | D | `hospital_director` |

## 15. System & Non-Human Roles (6)

| # | Role ID | Role Name (EN) | Role Name (AR) | Level | Parent |
|---|---------|---------------|----------------|-------|--------|
| 166 | `system_administrator` | System Administrator | مدير النظام | N | — |
| 167 | `application_support` | Application Support | دعم التطبيق | N | `system_administrator` |
| 168 | `integration_service` | Integration Service | خدمة تكامل | N | — |
| 169 | `ai_agent` | AI Agent | وكيل ذكاء اصطناعي | N | — |
| 170 | `robot_operator` | Robot Operator | مشغل آلي | N | — |
| 171 | `iot_gateway` | IoT Gateway | بوابة إنترنت الأشياء | N | — |

---

## Role Groups

| Group ID | Group Name | Member Roles | Purpose |
|----------|-----------|-------------|---------|
| `executive` | Executive Leadership | 1-18, 19-30, 31-42 | National & institutional leadership |
| `clinical_core` | Core Clinical | 57-86 | Direct patient care |
| `clinical_support` | Clinical Support | 87-94, 119-123 | Nursing, pharmacy |
| `laboratory` | Laboratory Services | 95-106 | Lab operations |
| `radiology` | Radiology Services | 107-112 | Imaging |
| `blood_bank` | Blood Bank Services | 113-118 | Blood services |
| `emergency` | Emergency Services | 124-129 | Emergency response |
| `public_health` | Public Health | 144-153 | Population health |
| `administrative` | Administration | 130-143 | Facility operations |
| `financial` | Finance | 134-138 | Financial operations |
| `compliance_audit` | Compliance & Audit | 154-158 | Oversight |
| `academic_research` | Academic & Research | 159-161 | Education/research |
| `system` | System Operations | 166-171 | Platform operations |
| `support` | Support Services | 162-165 | Ancillary services |

---

## Role Templates

| Template | Roles Included | Use Case |
|----------|---------------|----------|
| `hospital_leadership` | hospital_director, deputy_hospital_director, medical_director, nursing_director, administrative_director, financial_director | Hospital executive team |
| `lab_team` | lab_director, lab_supervisor, lab_technician, senior_lab_technician, phlebotomist | Full laboratory team |
| `emergency_team` | emergency_director, emergency_physician, emergency_nurse, paramedic, dispatcher | Emergency department |
| `phc_team` | phc_director, general_practitioner, registered_nurse, pharmacist, community_health_worker | Primary health center |
| `icu_team` | intensivist, critical_care_nurse, respiratory_therapist | ICU unit |
| `surgery_team` | surgeon, anesthesiologist, surgical_nurse, scrub_technician | Operating room |
