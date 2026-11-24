# GLOSI Domain Taxonomy

**Version:** 1.0.0
**Date:** 2026-11-15
**Purpose:** تصنيف موحد يمنع تكرار المجالات ويجعل البحث قابلاً للقياس.

---

## 1. رموز المجالات الأساسية

| الرمز | المجال | أمثلة على المجالات الفرعية |
|---|---|---|
| `A_health_systems` | الأنظمة الصحية والسجلات الطبية | EHR, HIS, LIS, CIS, MPI, Medical Document Management, CDS |
| `B_laboratory` | المختبرات الطبية | LIS, Workflow Automation, Analyzer Integration, Middleware, Quality, Accreditation, Reference Ranges, Test Catalogues, Specimen Tracking, Exchange |
| `C_public_health` | الصحة العامة والترصد | Disease Surveillance, Event-Based, Indicator-Based, Outbreak, Contact Tracing, Emergency, Real-Time, Epidemiological Intelligence |
| `D_standards_interoperability` | المعايير والتبادل | HL7, FHIR R4, DICOM, ICD, SNOMED CT, LOINC, UCUM, OpenHIE, IHE, Terminology Services |
| `E_identity_security_privacy` | الهوية والأمن والخصوصية | Digital Identity, Healthcare Identity, AuthN, AuthZ, Access Governance, Zero Trust, Encryption, Audit, Consent, Privacy Engineering, Signatures |
| `F_infrastructure_reliability` | البنية والاعتمادية | PostgreSQL, Distributed DB, EDA, Brokers, Offline-First, Sync, Mesh, DTN, DR, HA, Observability, Backup |
| `G_artificial_intelligence` | الذكاء الاصطناعي | Clinical AI, Medical NLP, RAG, Knowledge Graphs, Evaluation, Governance, Explainability, Privacy-Preserving AI, Federated Learning, Safety |
| `H_government_national` | الإدارة الحكومية والوطنية | National HIE, National Platforms, Health Governance, Workforce, Financing, Registries, Gov Digital Infrastructure, Data Governance |

يمكن إضافة مجالات جديدة عند وجود حاجة GULA حقيقية، مع تحديث هذا الملف والسجل.

## 2. رموز فرعية مقترحة

### A — الأنظمة الصحية
`ehr`, `his`, `lis`, `cis`, `patient_identity`, `document_management`, `clinical_decision_support`.

### B — المختبرات
`lis_core`, `workflow_automation`, `analyzer_integration`, `middleware`, `quality_management`,
`accreditation`, `reference_ranges`, `test_catalogue`, `specimen_tracking`, `lab_exchange`.

### C — الصحة العامة
`disease_surveillance`, `event_based`, `indicator_based`, `outbreak`, `contact_tracing`,
`emergency`, `real_time`, `epidemiological_intelligence`.

### D — المعايير
`hl7v2`, `fhir_r4`, `dicom`, `icd`, `snomed_ct`, `loinc`, `ucum`, `openhie`, `ihe`, `terminology`.

### E — الهوية والأمن
`digital_identity`, `healthcare_identity`, `authentication`, `authorization`, `access_governance`,
`zero_trust`, `encryption`, `audit`, `consent`, `privacy_engineering`, `signature`.

### F — البنية
`postgresql`, `distributed_db`, `event_driven`, `message_broker`, `offline_first`, `sync`,
`mesh`, `dtn`, `disaster_recovery`, `high_availability`, `observability`, `backup`.

### G — الذكاء الاصطناعي
`clinical_ai`, `medical_nlp`, `rag`, `knowledge_graph`, `model_evaluation`, `ai_governance`,
`explainability`, `privacy_preserving`, `federated_learning`, `clinical_safety`.

### H — الحكومة والوطن
`national_hie`, `national_platform`, `health_governance`, `workforce`, `financing`,
`national_registry`, `gov_infrastructure`, `data_governance`.

## 3. المجالات الحالية في GULA (مرجعية)

الخريطة التالية مبنية على الوثائق القائمة، وليست ادعاء اكتمال:

| مجال GULA | مرجع |
|---|---|
| LIS / المختبر | `docs/discovery/GLOBAL_HEALTHCARE_ATLAS.md` |
| FHIR R4 / التبادل | `docs/FHIR_R4_NATIONAL_EXPANSION_AR.md` |
| الهوية NIAM / الصلاحيات | `docs/architecture/identity-platform.md` |
| الأمن والتدقيق | `docs/architecture/security-platform.md` |
| الصحة العامة والترصد | `docs/discovery/GLOBAL_HEALTHCARE_GAP_ANALYSIS.md` |
| البنية والاعتمادية | `docs/architecture/CANONICAL_ARCHITECTURE.md` |
| الذكاء الاصطناعي | `docs/architecture/KNOWLEDGE_GRAPH.md` + أدلة AI القائمة |
| الحكومة الوطنية | `docs/architecture/national-platform-program.md` |

## 4. قواعد التصنيف

1. لكل سجل مجال أساسي واحد فقط.
2. يمكن تسجيل مجالات ثانوية في `gula.domain` أو في وصف السجل.
3. لا يُنشأ مجال جديد إذا كان يمكن استخدام رمز قائم.
4. يجب أن يكون التصنيف قابلاً للربط بمكوّن GULA أو بمشكلة وطنية محددة.
5. المشاريع متعددة الوظائف تُصنّف حسب وظيفتها الأساسية، لا حسب حجمها.

## 5. الفجوات المعروفة (للبحث المستقبلي)

- المصطلحات الصحية والترجمات العربية (LOINC/SNOMED/ICD).
- أمن الأجهزة الطبية وتحليل المخاطر السريرية.
- التبادل الوطني مع الجهات الحكومية العراقية.
- العمل دون اتصال والمزامنة في بيئات متقطعة.
- حوكمة الذكاء الاصطناعي السريري والشرح.
- تقييم قابلية التشغيل على أجهزة قديمة.
- إدارة الهوية الوطنية والتحقق الوزاري.
