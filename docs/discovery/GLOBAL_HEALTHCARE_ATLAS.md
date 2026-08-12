# GLOBAL HEALTHCARE ATLAS

> **GULA Platform — Domain Discovery & Coverage Assessment**
>
> Classification Framework: WHO Family of International Classifications (FIC), HIMSS Analytics,
> HL7 FHIR R4, ISO/TC 215 Health Informatics, CAP Laboratory Accreditation, CLSI Guidelines,
> Joint Commission International (JCI), ACGME Specialties, WMA Statements, ICN Nursing Taxonomy.
>
> **Document Authority:** This document is structured as an international discovery committee report
> representing the WHO, HIMSS, HL7, ISO, CAP, CLSI, Joint Commission, Hospital CEOs, Medical
> Universities, Public Health Experts, Enterprise Architects, and AI Researchers. It inventories
> every recognized healthcare domain, medical specialty, laboratory science, nursing specialty,
> pharmacy specialty, radiology/imaging modality, dentistry specialty, and allied health profession
> for the GULA Platform — an Iraqi-first but globally-deployable healthcare information system.
>
> **Coverage Scale:** None (missing) / Partial (some components exist) / Present (module exists
> but may be partial) / Complete (production-grade, audited)
>
> **Version:** 2.1.0 — Last Updated: July 2026

---

## TABLE OF CONTENTS

1. [PHASE 1: Healthcare Domains (Complete Worldwide Catalog)](#phase-1-healthcare-domains)
2. [PHASE 2: Medical Specialties (Complete Catalog)](#phase-2-medical-specialties)
3. [PHASE 3: Laboratory Sciences (Complete Catalog)](#phase-3-laboratory-sciences)
4. [PHASE 4: Nursing Specialties (Complete Catalog)](#phase-4-nursing-specialties)
5. [PHASE 5: Pharmacy Specialties](#phase-5-pharmacy-specialties)
6. [PHASE 6: Radiology/Imaging Specialties](#phase-6-radiologyimaging-specialties)
7. [PHASE 7: Dentistry Specialties](#phase-7-dentistry-specialties)
8. [PHASE 8: Allied Health Professions](#phase-8-allied-health-professions)

---

# PHASE 1: Healthcare Domains

## 1.1 Primary Care

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | First-contact, continuous, comprehensive, and coordinated care provided to individuals and families without referral |
| **Key Services** | Health promotion, disease prevention, health education, diagnosis & treatment of common illnesses, chronic disease management, referral coordination |
| **Technology Requirements** | EMR/EHR, appointment scheduling, clinical decision support (CDS), patient portals, referral management, population health analytics, immunization registries |
| **HL7 FHIR Coverage** | Patient, Encounter, Condition, Observation, MedicationRequest, CarePlan, CareTeam |
| **GULA Coverage** | **Present** — `routes/care_continuum.py` (primary care encounters, health assessments, family medicine records), `routes/ehr.py` (clinical notes, medications, problems, care plans), `services/care_continuum_service.py` |

## 1.2 Secondary Care

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Medical care provided by a specialist or facility upon referral from a primary care physician; typically hospital-based |
| **Key Services** | Inpatient hospitalization, specialist consultations, surgical services, diagnostic imaging, emergency care |
| **Technology Requirements** | Hospital information system (HIS), departmental systems (OR, ICU, radiology, lab), bed management, scheduling |
| **GULA Coverage** | **Present** — `routes/hospital.py` (complete facility hierarchy: hospital > campus > building > floor > department > clinic > room > bed), bed assignment engine, operation theater management, medical equipment tracking |

## 1.3 Tertiary Care

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Highly specialized medical care, usually provided in major teaching hospitals with advanced diagnostic and treatment capabilities |
| **Key Services** | Complex surgery (neurosurgery, cardiothoracic), oncology centers, transplant units, advanced diagnostic services, intensive care |
| **Technology Requirements** | Specialized clinical information systems, PACS, critical care documentation, transplant registries |
| **GULA Coverage** | **Partial** — Hospital infrastructure supports tertiary facility types (`teaching`, `specialized` hospital types), general order management, but no transplant-specific or advanced oncology-specific modules |

## 1.4 Quaternary Care

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Extension of tertiary care with even more specialized and uncommon procedures; often experimental or highly complex |
| **Key Services** | Experimental treatments, gene therapy, advanced neurosurgery, rare disease management |
| **Technology Requirements** | Research registries, genomic data integration, clinical trial management |
| **GULA Coverage** | **Partial** — `routes/clinical.py` has research registries and cohorts, but no clinical trial management or gene therapy tracking |

## 1.5 Preventive Medicine

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Proactive healthcare focused on disease prevention at primary, secondary, and tertiary levels |
| **Key Services** | Health screenings, vaccination programs, health risk assessments, lifestyle counseling, chemoprophylaxis |
| **Technology Requirements** | Population health platforms, screening campaign management, risk stratification, reminder/recall systems |
| **GULA Coverage** | **Present** — `routes/care_continuum.py` (preventive care records, screening campaigns, health promotion activities, risk stratifications, reminder schedules), `services/clinical_intelligence.py` (care gap detection) |

## 1.6 Public Health

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Organized measures to prevent disease, promote health, and prolong life among populations |
| **Key Services** | Disease surveillance, epidemic response, health statistics, environmental health monitoring, health education, policy development |
| **Technology Requirements** | Disease registries, surveillance systems, GIS mapping, outbreak detection algorithms, reporting dashboards |
| **GULA Coverage** | **Present** — `routes/care_continuum.py` (health programs, program enrollments, screening campaigns, community visits, occupational health records), `routes/national_data.py`, `routes/compliance.py`, `services/epidemiology.py` |

## 1.7 Emergency Medicine

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Medical specialty concerned with the immediate diagnosis and treatment of acute illness and injury |
| **Key Services** | Triage, resuscitation, trauma care, acute medical management, disaster response |
| **Technology Requirements** | Emergency department information system (EDIS), triage algorithms, trauma registry, mass casualty incident management |
| **GULA Coverage** | **Partial** — `routes/clinical_documentation.py` includes emergency notes (`emergency_note`), `routes/hospital.py` supports emergency room types, but no dedicated EDIS, triage engine, or trauma registry |

## 1.8 Military Medicine

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Medical practices specific to military personnel and operations, including combat casualty care |
| **Key Services** | Combat casualty care, tactical evacuation, field hospital operations, military occupational health, chemical/bio defense |
| **Technology Requirements** | Deployed EMR, tactical health records, evacuation tracking, NBC (nuclear/biological/chemical) exposure documentation |
| **GULA Coverage** | **Missing** — Not yet implemented. Edge platform (`routes/edge.py`, `app/edge/`) provides offline-capable infrastructure that could support field operations |

## 1.9 Disaster Medicine

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Medical specialty focused on preparation, response, and recovery from natural and man-made disasters |
| **Key Services** | Mass casualty triage, field medical response, shelter medicine, disaster mental health, recovery planning |
| **Technology Requirements** | Mass casualty tracking, patient distribution management, resource tracking, interoperable emergency systems |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.10 Space Medicine

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Medical specialty concerned with the health of astronauts and spaceflight participants |
| **Key Services** | Pre-flight screening, in-flight health monitoring, radiation exposure tracking, countermeasure protocols, post-flight rehabilitation |
| **Technology Requirements** | Telemetry-based health monitoring, microgravity-adapted clinical protocols, radiation dosimetry |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.11 Occupational Health

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Promotion and maintenance of the highest degree of physical, mental, and social well-being of workers |
| **Key Services** | Pre-employment screening, periodic health exams, workplace hazard assessment, injury management, return-to-work programs |
| **Technology Requirements** | Occupational health records, exposure tracking, fit-for-duty assessments, workers' compensation integration |
| **GULA Coverage** | **Present** — `routes/care_continuum.py` (`/occupational-health-records` endpoint), worker health tracking within facility management |

## 1.12 Sports Medicine

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Medical specialty dealing with physical fitness, treatment, and prevention of sports- and exercise-related injuries |
| **Key Services** | Athletic injury diagnosis/treatment, performance optimization, concussion management, rehabilitation, doping control |
| **Technology Requirements** | Musculoskeletal imaging integration, rehabilitation tracking, concussion protocol CDS, performance analytics |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.13 Travel Medicine

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Medical specialty focused on prevention and management of health issues related to international travel |
| **Key Services** | Pre-travel consultation, vaccinations, malaria prophylaxis, altitude illness prevention, post-travel illness evaluation |
| **Technology Requirements** | Travel health record, vaccine registry, geographic risk databases |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.14 Digital Health

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Use of digital technologies for health; includes mHealth, telehealth, health IT, wearable devices, AI |
| **Key Services** | Electronic health records, mobile health apps, telemedicine platforms, remote monitoring, AI diagnostics |
| **Technology Requirements** | FHIR APIs, interoperability gateways, cloud infrastructure, cybersecurity frameworks, AI/ML pipelines |
| **GULA Coverage** | **Complete** — FHIR-compliant EHR (`routes/ehr_fhir.py`), mobile routes (`routes/mobile.py`), citizen portal (`routes/citizen_portal.py`), AI platform (`routes/ai.py`, `app/ai/`), edge computing (`app/edge/`), lab device integration (`gateways/lab_device_gateway.py`) |

## 1.15 Precision Medicine

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | An approach to patient care that uses genetic, environmental, and lifestyle factors to tailor treatments |
| **Key Services** | Genomic sequencing analysis, pharmacogenomics, targeted therapy selection, biomarker testing |
| **Technology Requirements** | Genomic data storage (GA4GH standards), bioinformatics pipelines, variant interpretation, clinical decision support for targeted therapies |
| **GULA Coverage** | **Missing** — Not yet implemented. Platform has extensible lab results and clinical data models that could support biomarker/ genomic data storage |

## 1.16 Genomic Medicine

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Use of genomic information in clinical care for diagnosis, treatment, and prevention |
| **Key Services** | Whole genome/exome sequencing, carrier screening, prenatal genetic testing, tumor genomics, pharmacogenomics |
| **Technology Requirements** | VCF/BCR file storage, GA4GH htsget API, ClinVar/OMIM integration, variant classification (ACMG/AMP) |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.17 Telemedicine

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Remote delivery of healthcare services using telecommunications technology |
| **Key Services** | Virtual consultations, remote patient monitoring, store-and-forward dermatology/radiology, tele-ICU, tele-stroke |
| **Technology Requirements** | Video conferencing, secure messaging, remote monitoring devices, e-prescribing, telehealth-specific documentation templates |
| **GULA Coverage** | **Partial** — Platform supports mobile health, secure messaging, e-prescribing via EHR, but lacks dedicated video consultation infrastructure and telemedicine-specific workflows |

## 1.18 Home Care

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Healthcare services provided in a patient's home rather than in a clinical setting |
| **Key Services** | Skilled nursing, physical therapy, wound care, medication management, home health aide, hospice support |
| **Technology Requirements** | Home care documentation, visit scheduling, remote monitoring integration, caregiver portals |
| **GULA Coverage** | **Present** — `routes/care_continuum.py` (`/home-care-plans` endpoint CRUD), home care plan management |

## 1.19 Long-Term Care

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | A range of services addressing the health, personal care, and social needs of individuals who lack capacity for self-care |
| **Key Services** | Nursing home care, assisted living, skilled nursing facility, memory care, rehabilitation services |
| **Technology Requirements** | Long-term care documentation, ADL/IADL tracking, MDS (Minimum Data Set), care plan management |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.20 Palliative Care

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | An approach that improves quality of life of patients and families facing life-threatening illness |
| **Key Services** | Symptom management, pain control, psychosocial support, advance care planning, family support |
| **Technology Requirements** | Palliative care assessment tools (ESAS, PPS), advance directive documentation, pain management protocols |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.21 Hospice Care

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | A model of care for terminally ill patients focused on comfort and quality of life rather than curative treatment |
| **Key Services** | End-of-life care, bereavement support, respite care, spiritual care, symptom management |
| **Technology Requirements** | Hospice documentation, medication management (scheduled PRN), bereavement tracking |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.22 Mental Health

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | A state of well-being enabling individuals to cope with life stresses, realize abilities, and contribute to community |
| **Key Services** | Psychiatric evaluation, psychotherapy, medication management, crisis intervention, substance abuse treatment, rehabilitation |
| **Technology Requirements** | Behavioral health EHR, DSM-5/ICD-11 coding, standardized assessment tools (PHQ-9, GAD-7), suicide risk assessment, substance use tracking |
| **GULA Coverage** | **Partial** — `routes/clinical_documentation.py` supports SOAP/progress notes that can document mental health encounters. No dedicated MH-specific assessment tools or suicide risk engine |

## 1.23 Community Health

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Health services delivered at the community level, emphasizing prevention and health equity |
| **Key Services** | Community health worker programs, outreach clinics, health education, home visiting, community needs assessment |
| **Technology Requirements** | Community health worker mobile tools, social determinants of health (SDOH) screening, community resource referral |
| **GULA Coverage** | **Present** — `routes/care_continuum.py` (community care records, community clinic records, community visits, health promotion activities), comprehensive community health infrastructure |

## 1.24 School Health

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Healthcare services provided within educational settings to promote student health and well-being |
| **Key Services** | School nursing, immunization compliance, vision/hearing screening, health education, mental health services |
| **Technology Requirements** | School health records, immunization registries, mandatory screening tracking, parent portals |
| **GULA Coverage** | **Present** — `routes/care_continuum.py` (`/school-health-visits` endpoint), immunization scheduling and tracking, screening campaign management |

## 1.25 Environmental Health

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Aspects of human health determined by physical, chemical, biological, social, and psychosocial factors in the environment |
| **Key Services** | Air/water quality monitoring, toxicology, food safety, climate change health impacts, occupational exposure management |
| **Technology Requirements** | Environmental monitoring data integration, GIS exposure mapping, exposure registries |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.26 Veterinary Public Health / One Health

| Attribute | Description |
|-----------|-------------|
| **WHO/OIE Definition** | An integrated approach recognizing the interconnection between human, animal, and environmental health |
| **Key Services** | Zoonotic disease surveillance, food safety, antimicrobial resistance monitoring, comparative medicine |
| **Technology Requirements** | Cross-species disease registries, zoonotic outbreak detection, AMR surveillance |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.27 Concierge Medicine / Direct Primary Care (DPC)

| Attribute | Description |
|-----------|-------------|
| **Definition** | A practice model where patients pay a retainer/membership fee for enhanced access and comprehensive primary care |
| **Key Services** | Extended appointments, 24/7 access, same-day scheduling, comprehensive care coordination |
| **Technology Requirements** | Membership management, subscription billing, extended scheduling, patient communication platform |
| **GULA Coverage** | **Partial** — Subscription/tier management exists (`routes/tiers.py`, `models/subscription.py`), but no DPC-specific workflow |

## 1.28 Population Health

| Attribute | Description |
|-----------|-------------|
| **IHI Definition** | Health outcomes of a defined group, including distribution of outcomes within the group |
| **Key Services** | Risk stratification, care gap analysis, chronic disease management, social determinant interventions, quality measurement |
| **Technology Requirements** | Analytics dashboards, risk models (ACG/HCC), registries, care management platforms, SDOH data |
| **GULA Coverage** | **Present** — `routes/clinical.py` (quality indicators, registries, cohorts), `routes/care_continuum.py` (risk stratification, chronic disease registry, care gap detection), `routes/stats.py`, `services/clinical_intelligence.py` |

## 1.29 Regenerative Medicine

| Attribute | Description |
|-----------|-------------|
| **Definition** | Medical approaches that repair or replace damaged tissues using stem cells, tissue engineering, and biomaterials |
| **Key Services** | Stem cell therapy, tissue engineering, gene editing, platelet-rich plasma (PRP) therapy |
| **Technology Requirements** | Cell therapy tracking, stem cell registry, GMP compliance documentation |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.30 Functional Medicine

| Attribute | Description |
|-----------|-------------|
| **IFM Definition** | A systems biology-based approach that identifies and addresses root causes of disease |
| **Key Services** | Comprehensive functional assessment, nutritional therapy, environmental toxin assessment, gut health, hormone optimization |
| **Technology Requirements** | Extended lab panel integration, lifestyle tracking, nutritional supplement management |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.31 Integrative Medicine

| Attribute | Description |
|-----------|-------------|
| **Definition** | Combines conventional and evidence-based complementary therapies for whole-person care |
| **Key Services** | Acupuncture, herbal medicine, mind-body therapy, manual therapy, nutritional counseling |
| **Technology Requirements** | CAM therapy documentation, supplement interaction checks, outcome tracking |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.32 Hyperbaric Medicine

| Attribute | Description |
|-----------|-------------|
| **Definition** | Medical treatment using 100% oxygen at increased atmospheric pressure for specific conditions |
| **Key Services** | Wound care (diabetic ulcers, radiation injuries), decompression sickness, carbon monoxide poisoning, gas gangrene |
| **Technology Requirements** | Hyperbaric chamber documentation, treatment protocols, pressure/time recording |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.33 Tropical Medicine

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Branch of medicine dealing with diseases that occur in tropical and subtropical regions |
| **Key Services** | Malaria diagnosis/treatment, neglected tropical disease (NTD) management, vector-borne disease surveillance, parasitology |
| **Technology Requirements** | Tropical disease registries, NTD-specific diagnostic algorithms, vector surveillance data |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.34 Adolescent Medicine

| Attribute | Description |
|-----------|-------------|
| **Definition** | Medical specialty focused on the physical, psychological, and social health of adolescents |
| **Key Services** | Adolescent well-visits, immunizations (HPV, meningitis), mental health screening, reproductive health, substance use counseling |
| **Technology Requirements** | Adolescent-specific screening tools, confidentiality management, transition-to-adult-care coordination |
| **GULA Coverage** | **Partial** — General clinical documentation supports adolescent encounters; immunization tracking exists; no dedicated adolescent-specific workflow |

## 1.35 Transitional Care

| Attribute | Description |
|-----------|-------------|
| **Definition** | Services ensuring coordination and continuity as patients transfer between care settings |
| **Key Services** | Hospital-to-home transitions, discharge planning, medication reconciliation, follow-up coordination |
| **Technology Requirements** | Discharge summaries (CCD-A), medication reconciliation tools, follow-up scheduling, home care coordination |
| **GULA Coverage** | **Present** — `routes/care_continuum.py` (`/transitions-of-care`, `/clinical-handovers` endpoints) |

## 1.36 Urgent Care

| Attribute | Description |
|-----------|-------------|
| **Definition** | Walk-in medical care for conditions requiring prompt attention but not life-threatening |
| **Key Services** | Acute illness treatment, minor injury care, diagnostic testing, occupational health services |
| **Technology Requirements** | Walk-in scheduling, fast-track documentation, limited formulary management |
| **GULA Coverage** | **Partial** — `routes/hospital.py` supports clinic types including urgent care; general clinical orders and documentation available; no dedicated urgent care workflow |

## 1.37 Retail Health

| Attribute | Description |
|-----------|-------------|
| **Definition** | Basic healthcare services delivered in retail settings such as pharmacies or grocery stores |
| **Key Services** | Minor illness treatment, vaccinations, health screenings, prescription services |
| **Technology Requirements** | Point-of-care testing integration, retail EMR, vaccination registry connectivity |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.38 Lifestyle Medicine

| Attribute | Description |
|-----------|-------------|
| **ACLM Definition** | Evidence-based therapeutic approach using lifestyle interventions to prevent, treat, and reverse chronic disease |
| **Key Services** | Nutrition counseling, physical activity prescription, sleep optimization, stress management, substance cessation |
| **Technology Requirements** | Lifestyle tracking, exercise prescription tools, dietary assessment, sleep tracking integration |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.39 Gender-Affirming Care

| Attribute | Description |
|-----------|-------------|
| **WPATH Definition** | Medical and mental health care supporting transgender and gender-diverse individuals |
| **Key Services** | Hormone therapy, gender-affirming surgery, mental health support, voice therapy, legal documentation support |
| **Technology Requirements** | Gender-inclusive EHR, hormone protocol CDS, surgical care pathways, preferred name/pronoun infrastructure |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.40 Global Health

| Attribute | Description |
|-----------|-------------|
| **WHO Definition** | Health issues transcending national boundaries requiring international cooperation |
| **Key Services** | International health regulations, global disease surveillance, health systems strengthening, cross-border health initiatives |
| **Technology Requirements** | Multi-language support, cross-jurisdictional data exchange, WHO reporting frameworks |
| **GULA Coverage** | **Partial** — Arabic-first platform with multi-language capability; SNDHS integration (Iraqi national); could be extended for multi-country deployment |

## 1.41 Planetary Health

| Attribute | Description |
|-----------|-------------|
| **Lancet Definition** | Health of human civilization and the natural systems on which it depends |
| **Key Services** | Climate change health impact monitoring, biodiversity health connections, sustainable healthcare delivery |
| **Technology Requirements** | Climate-health analytics, sustainable supply chain tracking, carbon footprint reporting |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.42 Evolutionary Medicine

| Attribute | Description |
|-----------|-------------|
| **Definition** | Application of evolutionary theory to understand health and disease |
| **Key Services** | Evolutionary analysis of disease patterns, antibiotic stewardship (evolutionary basis), mismatch disease identification |
| **Technology Requirements** | Phylogenetic analysis tools, antimicrobial resistance evolutionary tracking |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.43 Nanomedicine

| Attribute | Description |
|-----------|-------------|
| **Definition** | Medical application of nanotechnology for diagnosis, treatment, and prevention |
| **Key Services** | Nanoparticle drug delivery, nanosensors for diagnostics, nanorobotics for surgery, molecular imaging |
| **Technology Requirements** | Nanomaterial tracking, nanoparticle pharmacokinetics modeling, molecular imaging data management |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.44 Systems Medicine

| Attribute | Description |
|-----------|-------------|
| **Definition** | Integrative approach combining multi-omics, clinical data, and computational modeling for personalized healthcare |
| **Key Services** | Multi-omics data integration, biomarker discovery, disease modeling, network pharmacology |
| **Technology Requirements** | Omics data storage, pathway analysis tools, computational modeling platforms, AI/ML pipelines |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.45 Network Medicine

| Attribute | Description |
|-----------|-------------|
| **Definition** | Application of network theory to understand disease mechanisms and drug targets |
| **Key Services** | Protein-protein interaction analysis, gene regulatory network modeling, drug-target identification |
| **Technology Requirements** | Bioinformatics tools, graph databases, high-performance computing |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.46 Exposome Medicine

| Attribute | Description |
|-----------|-------------|
| **Definition** | Study of the totality of environmental exposures from conception onward and their health impacts |
| **Key Services** | Environmental exposure assessment, occupational history, lifestyle factor tracking, cumulative risk assessment |
| **Technology Requirements** | Exposure data capture, environmental database integration, geospatial analysis |
| **GULA Coverage** | **Missing** — Not yet implemented |

## 1.47 P4 Medicine (Predictive, Preventive, Personalized, Participatory)

| Attribute | Description |
|-----------|-------------|
| **Leroy Hood Definition** | A systems approach to medicine that is predictive, preventive, personalized, and participatory |
| **Key Services** | Wellness-focused care, risk prediction, patient activation, personalized prevention plans |
| **Technology Requirements** | Risk prediction models, patient engagement platforms, wellness tracking, biomarker monitoring |
| **GULA Coverage** | **Partial** — AI risk prediction (`routes/ai.py`), care gap detection, preventive care records; missing deep patient activation/participatory infrastructure |

## 1.48 Emerging Healthcare Domains (Future)

| Domain | Description | GULA Coverage |
|--------|-------------|---------------|
| **Digital Twin Medicine** | Virtual patient replicas for treatment simulation | Missing |
| **Psychedelic-Assisted Therapy** | MDMA/psilocybin therapy for PTSD/depression | Missing |
| **Long COVID / Post-Acute Sequelae** | Chronic management of post-viral syndromes | Missing |
| **Metabolic Psychiatry** | Diet/nutrition intervention for mental health | Missing |
| **Social Prescribing** | Non-medical referral to community services | Missing |
| **Microbiome Medicine** | Gut microbiome analysis and therapeutics | Missing |
| **Epigenetic Medicine** | Epigenetic modification for disease prevention | Missing |
| **Mitochondrial Medicine** | Mitochondrial dysfunction diagnostics/treatment | Missing |
| **Senolytic Medicine** | Cellular senescence clearance for aging | Missing |
| **Computational Psychiatry** | AI-driven mental health assessment | Missing |
| **Digital Therapeutics (DTx)** | Evidence-based software as medical device | Missing |
| **Quantum Medicine** | Quantum computing for molecular simulation | Missing |
| **Immunometabolism** | Intersection of immune function and metabolism | Missing |
| **Space Health** | Off-planet healthcare delivery systems | Missing |
| **4P Medicine Expansion** | Participatory + Pervasive health monitoring | Missing |

---

# PHASE 2: Medical Specialties

## 2.1 Internal Medicine & Subspecialties

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **Internal Medicine (General)** | Diagnosis and non-surgical treatment of adult diseases | Comprehensive history/physical, diagnostic test interpretation | **Present** — Clinical orders, documentation, lab results, EHR |
| **Cardiology** | Heart and cardiovascular system diseases | ECG interpretation, echocardiography, stress testing, cardiac catheterization, pacemaker management | **Partial** — Lab orders for cardiac markers, clinical documentation; no dedicated cardiology module or ECG integration |
| **Gastroenterology** | Digestive system diseases | Endoscopy, colonoscopy, liver biopsy, pH monitoring | **Partial** — Lab orders for GI markers, pathology results; no endoscopy documentation module |
| **Pulmonology (Respiratory Medicine)** | Lung and respiratory tract diseases | Pulmonary function tests, bronchoscopy, thoracentesis, sleep studies | **Partial** — Lab orders, clinical documentation; no PFT integration |
| **Nephrology** | Kidney diseases | Dialysis management, kidney biopsy, electrolyte management | **Partial** — Lab orders (creatinine, eGFR, electrolytes), dialysis units in hospital model (`dialysis` unit type); no dialysis-specific EMR |
| **Endocrinology** | Hormone and metabolic disorders | Diabetes management, thyroid ultrasound, dynamic endocrine testing | **Partial** — Lab orders (HbA1c, thyroid panel, hormones), clinical documentation; no endocrine-specific CDS |
| **Rheumatology** | Autoimmune and inflammatory disorders | Joint aspiration, autoimmune serology interpretation, DMARD management | **Partial** — Lab orders (autoimmune panels, inflammatory markers), clinical documentation |
| **Hematology** | Blood disorders | Bone marrow biopsy, chemotherapy administration, apheresis, coagulation management | **Partial** — Lab orders (CBC, coagulation, hematopathology), clinical documentation; no dedicated hematology EMR |
| **Infectious Disease** | Bacterial, viral, fungal, parasitic infections | Antibiotic stewardship, infection control consultation, travel medicine | **Present** — Microbiology lab integration, antibiotic stewardship potential, epidemiology service |
| **Medical Oncology** | Cancer diagnosis and treatment | Chemotherapy planning, immunotherapy, targeted therapy, tumor board documentation | **Partial** — Lab orders (tumor markers), clinical documentation, research registries; no dedicated oncology EMR workflow |
| **Clinical Immunology/Allergy** | Immune system disorders | Allergy skin testing, immunotherapy administration, immunology lab interpretation | **Partial** — Lab orders, clinical documentation |
| **Hepatology** | Liver diseases (GI subspecialty) | Liver biopsy, fibroscan interpretation, viral hepatitis management | **Partial** — Lab orders (LFTs, viral serologies), clinical documentation |
| **Critical Care Medicine (Intensivist)** | Life-threatening conditions in ICU | Mechanical ventilation management, central line placement, hemodynamic monitoring, code management | **Partial** — ICU unit model in hospital module, clinical documentation; no ventilator/hemodynamic integration |
| **Geriatric Medicine** | Elderly patient care | Comprehensive geriatric assessment, falls risk evaluation, polypharmacy review | **Missing** — No dedicated geriatric module |
| **Sports Medicine (Internal Med)** | Exercise and athletic injuries | MSK ultrasound, joint injection, concussion assessment | **Missing** |
| **Sleep Medicine** | Sleep disorders | Polysomnography interpretation, CPAP management | **Missing** |
| **Palliative Medicine (Internal Med)** | End-of-life symptom management | Symptom assessment, advance care planning | **Missing** |

## 2.2 Surgical Specialties

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **General Surgery** | Abdominal organs, breast, endocrine surgery | Laparoscopic cholecystectomy, hernia repair, appendectomy, breast surgery | **Present** — Operation theater management (`routes/hospital.py`), clinical orders for surgery, documentation |
| **Cardiothoracic Surgery** | Heart, lungs, esophagus, chest wall | CABG, valve repair/replacement, lung resection, heart transplant | **Partial** — OT management supports `cardiac` theater type; no specialized cardiac surgery workflow |
| **Neurosurgery** | Brain, spinal cord, peripheral nerves | Craniotomy, spinal decompression, deep brain stimulation, aneurysm clipping | **Partial** — OT management supports `neuro` theater type |
| **Orthopedic Surgery** | Musculoskeletal system | Joint replacement (hip/knee), fracture fixation, arthroscopy, spine surgery | **Partial** — OT management supports `ortho` theater type |
| **Pediatric Surgery** | Surgical care for children | Congenital anomaly repair, pediatric tumor resection, hernia repair in children | **Partial** — General surgery infrastructure |
| **Plastic & Reconstructive Surgery** | Aesthetic and functional reconstruction | Facelift, rhinoplasty, breast reconstruction, microsurgery, burn reconstruction | **Partial** — OT infrastructure, no aesthetic-specific module |
| **Vascular Surgery** | Blood vessels (except heart/brain) | Carotid endarterectomy, AAA repair, peripheral bypass, varicose vein treatment, dialysis access | **Partial** — OT infrastructure |
| **Urological Surgery** | Male and female urinary tract, male reproductive | TURP, nephrectomy, cystectomy, vasectomy, prostatectomy | **Partial** — OT infrastructure, lab orders |
| **Colorectal Surgery** | Colon, rectum, anus | Colectomy, low anterior resection, ostomy creation | **Partial** — OT infrastructure |
| **Transplant Surgery** | Organ transplantation | Kidney, liver, pancreas, heart, lung transplant | **Partial** — OT infrastructure; no transplant registry |
| **Surgical Oncology** | Cancer surgery | Tumor resection, lymph node dissection, HIPEC | **Partial** — OT infrastructure, research registries |
| **Trauma Surgery / Acute Care Surgery** | Emergency surgical care | Damage control laparotomy, fracture fixation, thoracotomy | **Partial** — OT infrastructure, emergency room types |
| **Ophthalmic Surgery** | Eye surgery (see also Ophthalmology) | Cataract extraction, LASIK, vitrectomy, retinal detachment repair | **Partial** — OT supports `ophthalmic` theater type |

## 2.3 Pediatrics & Subspecialties

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **General Pediatrics** | Child health from birth to adolescence | Well-child visits, immunization administration, growth monitoring | **Present** — Immunization tracking, growth monitoring, primary care encounters |
| **Neonatal-Perinatal Medicine** | Care of newborn infants (especially premature/sick) | NICU management, neonatal resuscitation, therapeutic hypothermia | **Present** — Room type supports `nicu`, bed type supports `nicu` |
| **Pediatric Cardiology** | Heart conditions in children | Echocardiogram, cardiac catheterization |
| **Pediatric Critical Care** | Critically ill children | PICU management, mechanical ventilation |
| **Pediatric Emergency Medicine** | Acute pediatric care | Pediatric resuscitation, trauma stabilization |
| **Pediatric Endocrinology** | Hormonal disorders in children | Growth hormone therapy, diabetes management |
| **Pediatric Gastroenterology** | Digestive disorders in children | Endoscopy, feeding tube management |
| **Pediatric Hematology-Oncology** | Blood disorders/cancer in children | Chemotherapy, bone marrow transplant |
| **Pediatric Infectious Disease** | Infections in children | Antimicrobial management, congenital infection |
| **Pediatric Nephrology** | Kidney disorders in children | Dialysis, kidney biopsy |
| **Pediatric Pulmonology** | Lung disorders in children | Bronchoscopy, asthma management, CF care |
| **Pediatric Rheumatology** | Autoimmune disorders in children | Juvenile arthritis management |
| **Developmental-Behavioral Pediatrics** | Development and behavior | Autism assessment, ADHD management, developmental screening |
| **Pediatric Hospital Medicine** | Inpatient pediatric care | Comprehensive hospital care for children |
| **Adolescent Medicine** | Ages 10-25 health | Confidential care, reproductive health, substance use |

**GULA Coverage Summary for Pediatrics:** **Present** — Growth monitoring, immunization records/scheduling, primary care encounters supporting pediatric well-visits, NICU unit/bed types, pediatric hospital infrastructure. Missing dedicated subspecialty workflows.

## 2.4 Obstetrics & Gynecology

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **General Obstetrics & Gynecology** | Women's reproductive health | Prenatal care, delivery, gynecologic exams, contraception | **Present** — Pregnancy records, antenatal care visits, delivery records, postnatal care visits |
| **Maternal-Fetal Medicine** | High-risk pregnancy | Ultrasound, amniocentesis, fetal monitoring, multiple gestation management | **Present** — High-risk pregnancy documentation |
| **Gynecologic Oncology** | Female reproductive cancers | Radical hysterectomy, chemotherapy, pelvic exenteration | **Partial** — OT infrastructure, clinical documentation |
| **Reproductive Endocrinology & Infertility** | Fertility and hormone disorders | IVF, egg retrieval, hormone therapy, reproductive surgery | **Partial** — Lab orders for reproductive hormones |
| **Female Pelvic Medicine & Reconstructive Surgery** | Pelvic floor disorders | Sling procedures, pelvic organ prolapse repair | **Partial** — OT infrastructure |
| **Family Planning** | Contraceptive management | IUD placement/removal, sterilization, abortion care | **Missing** |
| **Pediatric & Adolescent Gynecology** | Gynecological care for youth | Exam under anesthesia, congenital anomaly management | **Missing** |

## 2.5 Psychiatry

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **General Psychiatry** | Mental health diagnosis and treatment | Psychiatric evaluation, medication management, psychotherapy | **Partial** — Clinical documentation supports MH notes, no dedicated psychiatry module |
| **Child & Adolescent Psychiatry** | Youth mental health | Family therapy, behavioral intervention, school consultation | **Missing** |
| **Consultation-Liaison Psychiatry** | Psychiatry in medical settings | Hospital-based psychiatric consultation | **Missing** |
| **Forensic Psychiatry** | Legal aspects of mental health | Competency evaluation, criminal responsibility assessment | **Missing** |
| **Geriatric Psychiatry** | Elderly mental health | Dementia evaluation, late-life depression treatment | **Missing** |
| **Addiction Psychiatry** | Substance use disorders | Detoxification management, MAT (medication-assisted treatment), relapse prevention | **Missing** |
| **Psychosomatic Medicine** | Mind-body interaction | Treatment of somatic symptom disorders | **Missing** |
| **Clinical Neurophysiology (Psych)** | Brain function assessment | EEG, quantitative EEG, evoked potentials | **Missing** |
| **Sleep Medicine (Psychiatry)** | Sleep disorders | Sleep study interpretation, CBT-I | **Missing** |

## 2.6 Neurology

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **General Neurology** | Nervous system disorders | Neurological exam, diagnostic test interpretation | **Partial** — Clinical documentation, lab orders (CSF analysis) |
| **Vascular Neurology (Stroke)** | Cerebrovascular disease | Thrombolysis administration, stroke protocol management | **Missing** |
| **Epilepsy & Clinical Neurophysiology** | Seizure disorders | EEG interpretation, video-EEG monitoring, epilepsy surgery evaluation | **Missing** |
| **Neuromuscular Medicine** | Muscle and nerve disorders | EMG/NCS interpretation, muscle biopsy | **Missing** |
| **Movement Disorders** | Parkinson's, dystonia, tremor | Deep brain stimulation management, botulinum toxin injection | **Missing** |
| **Neurocritical Care** | Neurologic emergencies | ICP monitoring, post-stroke care, status epilepticus management | **Missing** |
| **Neuroimmunology** | Immune-mediated neurological disorders | MS management, immunotherapy for neurologic conditions | **Missing** |
| **Headache Medicine** | Complex headache disorders | Migraine management, nerve blocks, Botox for migraine | **Missing** |
| **Neuro-oncology** | Brain/spinal cord tumors | Chemotherapy planning, pseudoprogression assessment | **Missing** |
| **Cognitive & Behavioral Neurology** | Dementia, memory disorders | Cognitive assessment, dementia management | **Missing** |
| **Autonomic Disorders** | Autonomic nervous system | Tilt-table testing, autonomic reflex screen | **Missing** |
| **Neurogenetics** | Genetic neurological disorders | Genetic testing interpretation, genetic counseling | **Missing** |

## 2.7 Radiology

*(Detailed in Phase 6 — Radiology/Imaging Specialties)*

## 2.8 Emergency Medicine

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **General Emergency Medicine** | Acute care for all ages | Resuscitation, wound repair, fracture reduction, emergency ultrasound | **Partial** — Emergency room types, emergency notes |
| **Pediatric Emergency Medicine** | Acute pediatric care | Pediatric resuscitation, foreign body removal | **Partial** |
| **Emergency Medical Services (EMS)** | Pre-hospital care | Field triage, disaster response coordination | **Missing** |
| **Medical Toxicology** | Poisoning and overdose | Toxidrome management, antidote administration, venomous bite treatment | **Missing** |
| **Disaster Medicine** | Mass casualty events | MCI triage, field hospital setup, resource allocation | **Missing** |
| **Wilderness & Environmental Medicine** | Outdoor emergencies | Altitude illness, hypothermia, envenomation | **Missing** |
| **Ultrasound in Emergency Medicine** | Point-of-care ultrasound | eFAST, cardiac ultrasound, procedural guidance | **Missing** |
| **Critical Care (Emergency)** | ED-based critical care | ED ICU management, prolonged resuscitation | **Missing** |

## 2.9 Anesthesiology

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **General Anesthesiology** | Perioperative care | General anesthesia, regional anesthesia, sedation | **Partial** — Operation theater management; no anesthesia information management system (AIMS) |
| **Critical Care Anesthesiology** | ICU management | Ventilator management, hemodynamic optimization | **Missing** |
| **Pain Medicine** | Acute and chronic pain | Epidural steroid injections, nerve blocks, implantable pump management | **Missing** |
| **Pediatric Anesthesiology** | Anesthesia for children | Neonatal anesthesia, congenital heart anesthesia | **Missing** |
| **Cardiothoracic Anesthesiology** | Cardiac surgery anesthesia | Transesophageal echocardiography (TEE), CPB management | **Missing** |
| **Neuroanesthesiology** | Neurosurgery anesthesia | Awake craniotomy, spinal cord monitoring | **Missing** |
| **Obstetric Anesthesiology** | Labor and delivery anesthesia | Epidural analgesia for labor, C-section anesthesia | **Missing** |
| **Regional Anesthesiology & Acute Pain** | Peripheral nerve blocks | Ultrasound-guided regional anesthesia, catheter techniques | **Missing** |
| **Palliative Medicine (Anesthesia)** | End-of-life pain | Advanced pain management for terminal illness | **Missing** |

## 2.10 Pathology

*(Detailed in Phase 3 — Laboratory Sciences)*

## 2.11 Ophthalmology

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **General Ophthalmology** | Eye diseases and surgery | Comprehensive eye exam, refraction, cataract surgery | **Partial** — OT supports `ophthalmic` theater type, clinical documentation |
| **Retina & Vitreous** | Retinal disorders | Retinal detachment repair, intravitreal injections, laser photocoagulation | **Partial** |
| **Glaucoma** | Optic nerve disease | Trabeculectomy, tube shunt, laser trabeculoplasty | **Partial** |
| **Cornea & External Disease** | Corneal disorders | Corneal transplant, cross-linking, pterygium excision | **Partial** |
| **Pediatric Ophthalmology** | Children's eye disorders | Strabismus surgery, amblyopia management | **Partial** |
| **Oculoplastics & Orbital Surgery** | Eyelid and orbit | Blepharoplasty, ptosis repair, orbital decompression | **Partial** |
| **Neuro-Ophthalmology** | Visual system neurologic disorders | Visual field testing, optic neuritis management | **Partial** |
| **Uveitis** | Intraocular inflammation | Immunosuppressive therapy management | **Missing** |
| **Refractive Surgery** | Vision correction | LASIK, PRK, SMILE, ICL | **Partial** |

## 2.12 Dermatology

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **General Dermatology** | Skin diseases | Skin exam, biopsy, cryotherapy, excisions | **Partial** — Clinical documentation, lab orders (dermatopathology) |
| **Dermatopathology** | Skin pathology | Microscopic examination of skin specimens | **Partial** — Pathology lab infrastructure |
| **Pediatric Dermatology** | Children's skin disorders | Hemangioma management, atopic dermatitis | **Missing** |
| **Procedural Dermatology** | Advanced dermatologic surgery | Mohs micrographic surgery, laser surgery, skin grafting | **Missing** |
| **Cosmetic Dermatology** | Aesthetic treatments | Botox, fillers, chemical peels, laser resurfacing | **Missing** |
| **Dermatoimmunology** | Immune-mediated skin disease | Psoriasis/eczema biologic therapy | **Missing** |
| **Teledermatology** | Remote skin diagnosis | Store-and-forward image-based consultation | **Missing** |
| **Oncologic Dermatology** | Skin cancer | Melanoma management, wide local excision, sentinel node | **Partial** — Clinical documentation |

### Dermatology Common Procedures (Detailed)

| Procedure Category | Specific Procedures | Documentation Required | GULA Status |
|--------------------|--------------------|----------------------|-------------|
| **Diagnostic** | Skin biopsy (punch, shave, excisional, incisional), curettage for histology, KOH preparation, scabies preparation, Tzanck smear, skin scraping, Wood's lamp examination, diascopy, dermatoscopy (dermoscopy), patch testing (TRUE Test, Finn Chamber), phototesting, biopsy for immunofluorescence (lupus, pemphigus), bacterial/fungal/viral culture | Procedure notes, lab order for histopathology/microbiology, specimen tracking, coded diagnosis (ICD-10 L00-L99) | **Partial** — Biopsy orders, pathology results |
| **Therapeutic Surgical** | Excision (simple, complex, layered), Mohs micrographic surgery (fresh tissue technique), cryosurgery (liquid nitrogen spray, cryoprobe, curettage and electrodesiccation), curettage and electrodesiccation (C&E), electrosurgery (electrodessication, electrofulguration, electrocoagulation, electrosection), laser surgery (CO2, pulsed dye, Nd:YAG, alexandrite, diode, erbium:YAG, IPL, fractional resurfacing, Q-switched ruby), photodynamic therapy (ALA/PDT: 5-aminolevulinic acid, methyl aminolevulinate), dermabrasion (motorized, manual), microdermabrasion, sclerotherapy for leg veins, nail avulsion (partial, total), nail surgery (nail bed biopsy, matrixectomy, nail fold surgery), hair transplantation (FUT, FUE), scar revision, skin grafting (split-thickness, full-thickness, composite), flap reconstruction (local, regional, advancement, rotation, transposition, interpolation, island pedicle flap, bilobed flap, rhomboid flap, random pattern flap, staged interpolation flap), liposuction (tumescent, laser-assisted, ultrasound-assisted, power-assisted, water-assisted, VASER, SmartLipo, CoolLipo, ProLipo, SlimLipo, LipoSonix, LipoSelection, LipoDissolve, Mesotherapy), tumescent liposuction | Surgical note (pre-op diagnosis, procedure, findings, margins, closure method, complications, post-op plan), specimen tracking for pathology (Mohs map, orientation, margins, debulk, permanent sections, Tissue mapping diagram), pathology requisition (tissue type, site, clinical diagnosis, special stains requested), photography (pre-op, intra-op, post-op), follow-up appointment, wound care instructions | **Missing** — No Mohs mapping, photography management, or dermatologic-specific surgical documentation |
| **Aesthetic/Cosmetic** | Botulinum toxin type A (Botox Cosmetic, Dysport, Xeomin, Jeuveau, Daxxify): glabellar lines, forehead lines, crow's feet, bunny lines, perioral lines, platysmal bands, masseter hypertrophy, axillary hyperhidrosis, palmar hyperhidrosis, chin dimpling, gummy smile, eyebrow lift, DAO depressor anguli oris, mentalis, nasalis, procerus, corrugator, frontalis, orbicularis oculi, orbicularis oris, depressor supercilii, levator labii superioris alaeque nasi, risorius, zygomaticus, buccinator, platysma, sternocleidomastoid, trapezius | Injectable log (product, lot number, dilution, dose, injection sites, volumes, adverse events), photographic documentation (standardized views, lighting), consent form, patient-reported outcome | **Missing** |
| **Medical Dermatology Therapies** | Systemic therapy for psoriasis/acne/hidradenitis suppurativa (biologic registry: adalimumab/Humira, ustekinumab/Stelara, secukinumab/Cosentyx, ixekizumab/Taltz, brodalumab/Siliq, guselkumab/Tremfya, tildrakizumab/Ilumya, risankizumab/Skyrizi, bimekizumab/Bimzelx, certolizumab pegol/Cimzia, etanercept/Enbrel, infliximab/Remicade, apremilast/Otezla, deucravacitinib/Sotyktu, tofacitinib/Xeljanz, ritlecitinib/Litfulo, abrocitinib/Cibinqo, upadacitinib/Rinvoq), isotretinoin/Accutane for acne (iPLEDGE monitoring), PUVA (psoralen + UVA) phototherapy, narrowband UVB (311-313 nm), excimer laser/light (308 nm) for localized psoriasis/vitiligo, UVA1 for scleroderma/atopic dermatitis, extracorporeal photopheresis (ECP) for cutaneous T-cell lymphoma/scleroderma/GVHD, topical immunotherapy (imiquimod/Aldara/Zyclara, ingenol mebutate/Picato - withdrawn, 5-fluorouracil/Efudex/Carac/Tolak, topical retinoids, corticosteroids, calcineurin inhibitors, PDE4 inhibitor (crisaborole/Eucrisa), JAK inhibitor (ruxolitinib/Opzelura), vitamin D analogs, coal tar, anthralin/dithranol, topical antibiotics, antifungals, antivirals, steroids, immunomodulators, NSAIDs (diclofenac 3% gel/Solaraze), T-cell inhibitors (pimecrolimus/Elidel), tacrolimus/Protopic, sirolimus/Rapamune | Biologic therapy registry, disease activity scores (PASI, DLQI, BSA, PGA, NAPSI, SALT, mN, mSWAT, SCORAD, EASI, POEM, CDLQI, Itch NRS, Pain NRS, fatigue assessment, patient global assessment, physician global assessment, dermatology life quality index), treatment response monitoring, laboratory monitoring protocol, adverse event tracking, safety laboratories (CBC, CMP, LFTs, lipids, TB screening, hepatitis panel, pregnancy test) | **Missing** — Biologic registries, disease activity scoring |
| **Dermatologic Photography** | Clinical photography: standardized views (front, left, right oblique, left lateral, right lateral, back, close-up), dermatoscopic photography (polarized, non-polarized, immersion fluid), total body photography/mole mapping (sequential digital dermoscopy, FotoFinder, DermoGenius, MoleMax, DermLite, Canfield, Vectra, Arista, Clarius, Visia, VivoSight, OCT, RCM reflectance confocal microscopy, multiphoton microscopy, high-definition OCT, line-field confocal OCT, dynamic optical coherence tomography, MSI multispectral imaging, thermal imaging, fluorescence imaging), serial photography for monitoring lesions over time | Image storage (DICOM, JPEG, PNG), lesion mapping and tracking (ABCDE rule, Glasgow 7-point checklist, ugly duckling sign, dermoscopic patterns, 2-step dermoscopy algorithm, revised pattern analysis, chaos and clues algorithm, TADA triage amalgamated dermoscopic algorithm, IDS dermoscopy, Menzies method, 7-point checklist, 3-point checklist, CASH algorithm, BLINCK algorithm), AI integration for image analysis | **Missing** |
| **Teledermatology** | Store-and-forward (asynchronous): digital images + clinical history submitted for specialist review. Real-time (synchronous): live video consultation with dermatologist. Hybrid: combined approaches. | Image upload (standardized photography, dermoscopic images), clinical history and questionnaire, structured teledermatology consult template (history, medications, prior treatments, review of systems, skin exam findings, differential diagnosis, assessment and plan, follow-up interval, biopsy recommendation, medication prescription), billing modifiers (store-and-forward (CPT 99241-99245, GQ, GT, 95), real-time telemedicine (CPT 99201-99215 with modifier 95/GT/GQ), asynchronous telemedicine store-and-forward (CPT 99241-99245), synchronous telemedicine (CPT 99201-99215), audio-only (99441-99443), virtual check-in (G2012, G2010, G2061-G2063, G2250-G2252), e-consult (99446-99452, G2010, G2012) | **Missing** |

## 2.13 Physical Medicine & Rehabilitation (PM&R)

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **General PM&R** | Functional restoration | Rehabilitation assessment, therapy prescription | **Missing** |
| **Spinal Cord Injury Medicine** | SCI care | Functional assessment, spasticity management, bowel/bladder program | **Missing** |
| **Traumatic Brain Injury Medicine** | TBI rehabilitation | Cognitive rehabilitation, behavioral management | **Missing** |
| **Stroke Rehabilitation** | Post-stroke recovery | Motor recovery, speech therapy coordination | **Missing** |
| **Pediatric Rehabilitation** | Children with disabilities | CP management, developmental therapy | **Missing** |
| **Sports Medicine (PM&R)** | Athletic injuries | MSK ultrasound, PRP injections, rehabilitation | **Missing** |
| **Pain Medicine (PM&R)** | Chronic pain | Trigger point injections, nerve blocks, TENS | **Missing** |
| **Neuromuscular Medicine (PM&R)** | Muscle/nerve disorders | EMG, muscle biopsy, ALS management | **Missing** |
| **Amputee Rehabilitation** | Prosthetic training | Prosthetic fitting, gait training | **Missing** |
| **Cardiac Rehabilitation** | Post-cardiac event | Exercise prescription, risk factor modification | **Missing** |
| **Pulmonary Rehabilitation** | Chronic lung disease | Breathing exercises, oxygen assessment | **Missing** |
| **Musculoskeletal Rehabilitation** | Orthopedic conditions | Therapeutic exercise, manual therapy | **Missing** |

## 2.14 Preventive Medicine

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **General Preventive Medicine** | Population and individual prevention | Health risk assessment, screening recommendations | **Present** — Preventive care records, screening campaigns, risk stratification |
| **Aerospace Medicine** | Aviation and space health | Flight crew medical certification | **Missing** |
| **Occupational Medicine** | Workplace health | Work-related illness evaluation, fit-for-duty exams | **Present** — Occupational health records |
| **Public Health & General Preventive Medicine** | Community health | Epidemiology investigation, program planning | **Present** — Epidemiology service, health programs |
| **Undersea & Hyperbaric Medicine** | Dive medicine | Recompression therapy, fitness-to-dive evaluation | **Missing** |

## 2.15 Family Medicine

| Attribute | Description |
|-----------|-------------|
| **Scope** | Comprehensive healthcare for all ages, sexes, and organ systems |
| **Common Procedures** | Well-child exams, adult physicals, gynecologic care (Pap smear), minor surgery (skin biopsies, abscess drainage), joint injections, ECGs, spirometry, Point-of-care ultrasound |
| **GULA Coverage** | **Present** — Primary care encounters, family medicine records, health assessments, immunization tracking, clinical documentation, lab orders |

## 2.16 Medical Genetics & Genomics

| Specialty | Description | Common Procedures | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **Clinical Genetics** | Genetic disorder diagnosis | Dysmorphology exam, pedigree analysis, genetic counseling | **Missing** |
| **Medical Biochemical Genetics** | Inborn errors of metabolism | Metabolic screening, dietary management | **Missing** |
| **Molecular Genetic Pathology** | DNA/RNA testing | NGS interpretation, variant classification | **Missing** |
| **Cytogenetics** | Chromosomal analysis | Karyotype interpretation, FISH analysis | **Missing** |
| **Genetic Counseling** | Risk communication | Pre-test counseling, result disclosure | **Missing** |

## 2.17 Other Recognized Specialties

| Specialty | Description | GULA Coverage |
|-----------|-------------|---------------|
| **Nuclear Medicine** | Radioactive tracers for diagnosis and therapy | **Partial** — Clinical orders for nuclear studies |
| **Radiation Oncology** | Radiation therapy for cancer | **Missing** |
| **Medical Microbiology** | Pathogen identification (see Phase 3) | **Present** — Microbiology lab integration |
| **Clinical Neurophysiology** | Nervous system functional assessment | **Missing** |
| **Oral & Maxillofacial Surgery** | Face, mouth, jaw surgery | **Partial** — OT infrastructure |
| **Pain Medicine (Multidisciplinary)** | Comprehensive pain management | **Missing** |
| **Clinical Informatics** | Health IT, data analytics | **Complete** — Platform core competency |
| **Neurodevelopmental Disabilities** | Developmental disorders in children | **Missing** |
| **Vascular Neurology** | Stroke care | **Missing** |
| **Hospice & Palliative Medicine** | End-of-life care | **Missing** |
| **Sleep Medicine** | Sleep disorders | **Missing** |
| **Transplant Hepatology** | Liver transplant medicine | **Missing** |
| **Medical Toxicology** | Poisonings | **Missing** |
| **Sports Medicine** | Athletic medicine | **Missing** |
| **Clinical Cardiac Electrophysiology** | Heart rhythm disorders | **Missing** |
| **Advanced Heart Failure & Transplant Cardiology** | End-stage heart disease | **Missing** |
| **Adult Congenital Heart Disease** | Grown-up congenital heart | **Missing** |
| **Interventional Cardiology** | Catheter-based heart procedures | **Missing** |
| **Interventional Radiology** | Image-guided procedures | **Missing** |
| **Vascular & Interventional Neurology** | Catheter-based stroke therapy | **Missing** |

---

# PHASE 3: Laboratory Sciences (Complete Catalog)

## 3.1 Clinical Chemistry

| Sub-discipline | Description | Key Assays/Tests | GULA Coverage |
|----------------|-------------|-------------------|---------------|
| **General Chemistry** | Routine biochemical analysis | Glucose, BUN, creatinine, electrolytes (Na, K, Cl, HCO3), calcium, phosphorus, magnesium | **Complete** — Comprehensive lab orders, results management, test profiles |
| **Enzymology** | Enzyme activity measurement | ALT, AST, ALP, GGT, LDH, CK, amylase, lipase | **Complete** |
| **Protein Chemistry** | Protein quantification and electrophoresis | Total protein, albumin, SPEP, IFE, CRP, complement | **Complete** |
| **Lipid Panel** | Lipid metabolism assessment | Total cholesterol, HDL, LDL, triglycerides, apolipoproteins | **Complete** |
| **Carbohydrate Metabolism** | Glucose metabolism | Fasting glucose, HbA1c, OGTT, insulin, C-peptide | **Complete** |
| **Endocrine Chemistry** | Hormone measurement | TSH, T4, T3, cortisol, ACTH, sex hormones, growth hormone | **Present** |
| **Cardiac Markers** | Cardiac injury and failure | Troponin, CK-MB, BNP, NT-proBNP | **Present** |
| **Tumor Markers** | Cancer screening/monitoring | PSA, CA-125, CA 19-9, CEA, AFP, HCG, CA 15-3 | **Present** |
| **Therapeutic Drug Monitoring** | Drug level measurement | Digoxin, lithium, valproate, vancomycin, aminoglycosides | **Present** |
| **Trace Elements & Heavy Metals** | Nutritional/toxicological | Iron, ferritin, transferrin, zinc, selenium, lead, mercury | **Present** |
| **Vitamins & Metabolites** | Vitamin status | Vitamin D, B12, folate, vitamin A, E, K | **Present** |
| **Blood Gas Analysis** | Acid-base and oxygenation | pH, pCO2, pO2, bicarbonate, base excess, lactate | **Partial** — Results tracking; no POCT integration |
| **Urine Chemistry** | Urinalysis | Dipstick, microscopy, microalbumin, creatinine clearance | **Complete** |
| **CSF Analysis** | Cerebrospinal fluid assessment | Glucose, protein, cell count, culture | **Present** |
| **Bone & Mineral Metabolism** | Calcium/bone regulation | PTH, vitamin D, osteocalcin, NTx | **Present** |
| **Porphyrins & Heme Precursors** | Porphyria diagnosis | Porphobilinogen, delta-ALA, porphyrin profile | **Present** |
| **Inborn Errors of Metabolism** | Metabolic disease screening | Amino acids, acylcarnitines, organic acids | **Present** — General chemistry infrastructure |
| **Biochemical Genetics** | Lysosomal storage disease | Enzyme activity assays, biomarker screening | **Present** |

## 3.2 Hematology

| Sub-discipline | Description | Key Assays/Tests | GULA Coverage |
|----------------|-------------|-------------------|---------------|
| **Complete Blood Count** | Cellular blood components | WBC, RBC, hemoglobin, hematocrit, platelets, differential, indices | **Complete** — Core lab functionality |
| **Coagulation** | Hemostasis assessment | PT, aPTT, INR, fibrinogen, D-dimer, factor assays | **Present** |
| **Flow Cytometry** | Cellular immunophenotyping | Lymphocyte subsets, leukemia/lymphoma panels, CD4 count | **Missing** — No flow cytometry data management |
| **Hemoglobinopathies** | Hemoglobin disorders | Hb electrophoresis, Hb HPLC, sickle cell screen | **Present** |
| **Bone Marrow** | Marrow examination | Aspirate and biopsy interpretation, cytochemistry | **Present** — Pathology results tracking |
| **Thrombophilia Workup** | Hypercoagulability | Protein C, Protein S, antithrombin, Factor V Leiden, lupus anticoagulant | **Present** |
| **Anticoagulation Monitoring** | DOAC/warfarin management | Anti-Xa, thrombin time, DOAC levels | **Present** |
| **Complete Blood Count with Reticulocytes** | RBC production assessment | Reticulocyte count, immature reticulocyte fraction | **Complete** |
| **Erythrocyte Sedimentation Rate** | Inflammation | ESR (Westergren) | **Complete** |
| **Hemolysis Workup** | Hemolytic anemia | Haptoglobin, LDH, bilirubin, direct Coombs test | **Present** |
| **Body Fluid Analysis** | Non-blood fluids | Cell count, differential, chemical analysis | **Present** |
| **Malaria/Babesia** | Parasite detection | Thick/thin smear, antigen testing | **Present** |
| **Special Coagulation** | Factor assays, inhibitors | Factor VIII, IX, inhibitor assays, von Willebrand profile | **Present** |

## 3.3 Microbiology

| Sub-discipline | Description | Key Assays/Tests | GULA Coverage |
|----------------|-------------|-------------------|---------------|
| **Bacteriology** | Bacterial pathogen identification | Culture & sensitivity, Gram stain, identification panels, MIC | **Present** — Lab results for culture/sensitivity |
| **Mycology** | Fungal identification | Fungal culture, KOH prep, fungal antigen (galactomannan, beta-D-glucan) | **Present** |
| **Parasitology** | Parasitic identification | Ova & parasite exam, blood parasites, serology | **Present** |
| **Virology** | Viral detection | Viral culture, antigen detection, serology, molecular | **Present** |
| **Mycobacteriology** | TB and NTM | AFB smear, culture, GeneXpert, TB PCR, IGRA | **Present** |
| **Anaerobic Bacteriology** | Oxygen-sensitive bacteria | Anaerobic culture, gas chromatography | **Present** |
| **Antimicrobial Susceptibility Testing** | Resistance profiling | Disk diffusion, Etest, VITEK/MIC, ESBL/MRSA/VRE detection | **Present** |
| **Infection Control Microbiology** | Healthcare-associated infections | MRSA screening, VRE screening, environmental cultures | **Present** |
| **Syphilis Serology** | Treponemal detection | VDRL, RPR, TPHA, FTA-ABS | **Present** |
| **Molecular Microbiology** | Nucleic acid detection | PCR, multiplex panels, sequencing, metagenomics | **Present** — Molecular lab support |
| **Antimicrobial Stewardship** | Resistance monitoring | Cumulative antibiogram, reporting | **Present** — Epidemiology service |
| **Environmental Microbiology** | Water/food testing | Coliform count, heterotrophic plate count | **Missing** |
| **Point-of-Care Microbiology** | Rapid testing | Strep A, influenza, RSV, HIV rapid, malaria rapid | **Present** |

## 3.4 Immunology / Serology

| Sub-discipline | Description | Key Assays/Tests | GULA Coverage |
|----------------|-------------|-------------------|---------------|
| **Autoimmune Serology** | Autoantibody detection | ANA, anti-dsDNA, RF, anti-CCP, ANCA, ENA panel | **Present** |
| **Allergy Testing** | Allergen-specific IgE | Total IgE, specific IgE panel, component-resolved diagnostics | **Present** |
| **Complement Testing** | Complement system | C3, C4, CH50, complement factor assays | **Present** |
| **Immunoglobulin Testing** | Antibody quantification | IgG, IgA, IgM, IgE, IgD, IgG subclasses | **Present** |
| **Immune Complex Testing** | Circulating complexes | CIC, cryoglobulins, Clq binding | **Present** |
| **Cellular Immunology** | T-cell/B-cell function | Lymphocyte proliferation, NK cell function, cytokine assays | **Missing** |
| **HLA Typing** | Tissue typing | Class I and II typing (serologic, molecular), organ transplant matching | **Missing** |
| **Infectious Disease Serology** | Antibody and antigen detection | HIV, hepatitis panel, EBV, CMV, toxoplasma, rubella | **Present** |
| **Vaccine Response Testing** | Post-vaccination immunity | Anti-HBs, anti-measles, anti-varicella titers | **Present** |
| **Monoclonal Gammopathy** | Paraprotein detection | SPEP, IFE, serum free light chains, heavy chain disease | **Present** |

## 3.5 Molecular Biology / Molecular Diagnostics

| Sub-discipline | Description | Key Assays/Tests | GULA Coverage |
|----------------|-------------|-------------------|---------------|
| **Real-Time PCR** | Quantitative nucleic acid detection | Viral load (HIV, HCV, HBV, CMV, EBV), bacterial quantification | **Present** |
| **Digital PCR** | Absolute quantification | Rare mutation detection, copy number variation | **Missing** |
| **Nucleic Acid Sequencing (Sanger)** | Targeted sequencing | Single gene disorders, confirmatory testing | **Missing** |
| **Next-Generation Sequencing** | High-throughput sequencing | Whole exome, whole genome, targeted panels, RNA-seq | **Missing** |
| **Genotyping** | Genetic variant detection | Pharmacogenomics, HLA genotyping, disease risk variants | **Missing** |
| **Methylation Analysis** | Epigenetic markers | MGMT methylation, imprinting disorders | **Missing** |
| **Gene Expression Profiling** | RNA expression analysis | Tumor subtyping, Oncotype DX, MammaPrint | **Missing** |
| **Microarray Analysis** | Array-based genomic testing | Chromosomal microarray, SNP array, array CGH | **Missing** |
| **Fluorescence In Situ Hybridization** | Chromosomal FISH | HER2 amplification, BCR-ABL, translocation detection | **Missing** |
| **Liquid Biopsy** | Circulating tumor components | ctDNA, circulating tumor cells, exosome analysis | **Missing** |
| **Microbiome Analysis** | Microbial community profiling | 16S rRNA sequencing, shotgun metagenomics | **Missing** |
| **Molecular Infectious Disease** | Pathogen nucleic acid detection | Multiplex respiratory panels, GI panels, meningitis panels | **Present** |
| **Transplant Molecular Diagnostics** | Transplant monitoring | dd-cfDNA, gene expression profiling for rejection | **Missing** |

## 3.6 Histopathology & Surgical Pathology

| Sub-discipline | Description | Key Procedures | GULA Coverage |
|----------------|-------------|-------------------|---------------|
| **General Surgical Pathology** | Tissue diagnosis | Frozen section, permanent section interpretation | **Present** — Pathology results tracking |
| **Gynecologic Pathology** | Female tract pathology | Endometrial, ovarian, cervical, vulvar pathology | **Present** |
| **Dermatopathology** | Skin pathology | Melanocytic, inflammatory, neoplastic skin | **Present** |
| **Neuropathology** | Nervous system pathology | Brain tumor, neurodegenerative, muscle/nerve biopsy | **Present** |
| **Renal Pathology** | Kidney pathology | Medical renal disease, transplant pathology | **Present** |
| **Gastrointestinal Pathology** | GI tract pathology | Inflammatory bowel disease, polyps, neoplasia | **Present** |
| **Hepatopathology** | Liver pathology | Hepatitis, cirrhosis, tumor pathology | **Present** |
| **Thoracic Pathology** | Lung/pleura pathology | Lung cancer, mesothelioma, interstitial lung disease | **Present** |
| **Cardiovascular Pathology** | Heart/vascular pathology | Cardiac tumor, myocarditis, vascular pathology | **Present** |
| **Bone & Soft Tissue Pathology** | MSK pathology | Sarcoma diagnosis, bone tumor, soft tissue tumor | **Present** |
| **Breast Pathology** | Breast disease | Breast cancer grading, DCIS, benign breast disease | **Present** |
| **Genitourinary Pathology** | GU tract pathology | Prostate cancer grading, bladder, testicular | **Present** |
| **Endocrine Pathology** | Endocrine organ pathology | Thyroid FNA, adrenal, pituitary, parathyroid | **Present** |
| **Head & Neck Pathology** | H&N region pathology | Thyroid, salivary gland, oral cavity | **Present** |
| **Pediatric Pathology** | Children's pathology | Pediatric tumors, congenital anomalies, placental | **Present** |
| **Ophthalmic Pathology** | Eye pathology | Eye tumor, corneal, retinal pathology | **Present** |
| **Transplant Pathology** | Transplant rejection | Rejection grading, BK nephropathy, GVHD | **Present** |
| **Immunohistochemistry** | Protein expression in tissue | Receptor status (ER/PR/HER2), lineage markers, predictive markers | **Missing** |
| **Autopsy Pathology** | Post-mortem examination | Complete autopsy, limited, forensic | **Missing** |
| **Digital Pathology** | Whole-slide imaging | Remote pathology consultation, AI-assisted diagnosis | **Missing** |

## 3.7 Cytology

| Sub-discipline | Description | Key Procedures | GULA Coverage |
|----------------|-------------|-------------------|---------------|
| **Exfoliative Cytology** | Shed cell analysis | Pap smear, respiratory cytology, urine cytology, effusion cytology | **Present** — Results tracking |
| **Fine Needle Aspiration** | Needle sampling | Thyroid FNA, breast FNA, lymph node, deep organ FNA | **Present** |
| **Liquid-Based Cytology** | Modified preparation | ThinPrep, SurePath | **Present** |
| **Cytotechnology** | Screening | Slide screening, cell preparation, triage | **Present** |

## 3.8 Genetics & Cytogenetics

| Sub-discipline | Description | Key Procedures | GULA Coverage |
|----------------|-------------|-------------------|---------------|
| **Standard Karyotyping** | Chromosome analysis | G-banding, constitutional, leukemia | **Missing** |
| **FISH** | Targeted chromosome analysis | Aneuploidy, deletions, gene fusions | **Missing** |
| **Chromosomal Microarray** | High-resolution copy number | Microdeletions, duplications, LOH | **Missing** |
| **Cancer Cytogenetics** | Neoplastic chromosome changes | Leukemia karyotype, solid tumor cytogenetics | **Missing** |
| **Prenatal Cytogenetics** | Fetal chromosome analysis | Amniocentesis, CVS, NIPT confirmation | **Missing** |
| **Molecular Genetics** | Gene-level testing | Single gene sequencing, repeat expansion | **Missing** |
| **Population Genetics** | Ancestry/admixture | Pharmacogenetic variation, disease association | **Missing** |

## 3.9 Toxicology

| Sub-discipline | Description | Key Procedures | GULA Coverage |
|----------------|-------------|-------------------|---------------|
| **Therapeutic Drug Monitoring** | Drug level optimization | Antiepileptics, immunosuppressants, psychotropics, antibiotics | **Present** |
| **Forensic Toxicology** | Legal/medicolegal analysis | Drugs of abuse, alcohol, heavy metals, volatiles | **Partial** — General toxicology, no forensic chain-of-custody |
| **Clinical Toxicology** | Poison management | Acetaminophen level, salicylate, drug screen, alcohol | **Present** |
| **Drugs of Abuse Testing** | Substance use detection | Urine drug screen, confirmation (GC-MS, LC-MS/MS) | **Present** |
| **Pharmacogenomics** | Genetic drug response | CYP450 genotyping, TPMT, UGT1A1 | **Missing** |
| **Occupational Toxicology** | Workplace exposure | Lead, mercury, cadmium, solvents, pesticide exposure | **Missing** |

## 3.10 Blood Bank & Transfusion Medicine

| Sub-discipline | Description | Key Procedures | GULA Coverage |
|----------------|-------------|-------------------|---------------|
| **Blood Group Serology** | ABO/Rh typing | Forward/reverse typing, Rh phenotype | **Present** |
| **Antibody Screening & Identification** | Unexpected antibodies | Antibody screen, panel identification, DAT | **Present** |
| **Crossmatching** | Compatibility testing | Immediate spin, AHG crossmatch, electronic | **Present** |
| **Component Therapy** | Blood product management | RBCs, platelets, FFP, cryoprecipitate | **Present** |
| **Apheresis** | Therapeutic plasma exchange | TPE, RBC exchange, plateletpheresis, stem cell harvest | **Partial** — No dedicated apheresis module |
| **Donor Management** | Blood donor processing | Donor screening, phlebotomy, infectious disease testing | **Present** — Unit type supports `blood_bank` |
| **Transfusion Reactions** | Adverse event investigation | Hemolytic, allergic, febrile, TRALI, TACO | **Present** |
| **Perinatal Transfusion** | Fetal/maternal blood | RhIG (RhoGAM) management, fetal anemia | **Present** |
| **Massive Transfusion Protocol** | Emergency blood delivery | MTP activation, ratio management | **Missing** |
| **Immunohematology Reference** | Complex antibody problems | Rare blood typing, adsorption/elution, genotyping | **Present** |
| **Cord Blood Banking** | Stem cell storage | Collection, processing, HPC inventory | **Missing** |
| **Patient Blood Management** | Optimizing hemostasis | Anemia management, coagulation optimization | **Missing** |

## 3.11 Quality Management in Laboratory Medicine

| Area | Description | Key Requirements | GULA Coverage |
|------|-------------|-------------------|---------------|
| **IQCP (Individualized Quality Control Plan)** | CLIA-compliant QC | Risk assessment, QC frequency, rules | **Present** — `routes/quality_control.py`, `models/quality_control.py` |
| **Proficiency Testing (PT/EQA)** | External quality assessment | PT enrollment, result submission, performance scoring | **Present** |
| **Internal Quality Control** | Daily QC monitoring | Levey-Jennings charts, Westgard rules, multi-rule QC | **Present** |
| **Method Validation** | Analytical performance | Precision, accuracy, linearity, LOD, LOQ | **Present** |
| **Reference Range Establishment** | Normal values | Transference, verification, pediatric/geriatric ranges | **Present** |
| **Pre-analytical Quality** | Specimen integrity | Rejection criteria, hemolysis/index, stability | **Present** — Sample management, rejection reasons |
| **Post-analytical Quality** | Result validation | Delta checks, critical value reporting, turnaround time | **Present** — Critical alerts system |
| **Laboratory Accreditation** | CAP/ISO 15189/CLIA | Document control, internal audit, management review | **Present** — Compliance module |
| **Six Sigma in Laboratory** | Process improvement | Sigma metrics, TPS, defect tracking | **Present** — Quality indicators |
| **Lean Laboratory** | Waste reduction | Value stream mapping, 5S, kanban | **Missing** |
| **Data Integrity** | ALCOA+ principles | 21 CFR Part 11 compliance, audit trail | **Complete** — Audit log, immutable records |

## 3.12 Laboratory Informatics (LIS)

| Component | Description | Key Features | GULA Coverage |
|-----------|-------------|--------------|---------------|
| **Laboratory Information System** | Core lab operations | Order entry, specimen tracking, results reporting, QC | **Complete** — GULA is a LIMS at its core |
| **Middlewares** | Instrument data management | Results validation, autoverification, instrument interfacing | **Present** — Device integration gateway |
| **Pre-analytical Automation** | Specimen processing | Labeling, sorting, centrifugation, aliquoting | **Missing** |
| **Result Autoverification** | Automated validation | Rules engine, multistep verification, delta checking | **Present** — In clinical intelligence |
| **Reference Laboratory Interface** | Send-out testing | External lab ordering, result reconciliation | **Partial** — Integration gateway supports |
| **Barcode Tracking** | Chain of custody | 2D barcode, RFID, positive patient identification | **Present** — QR/ID scanning |
| **Point-of-Care Connectivity** | POCT data management | POCT device docking, LIS bridge, QC management | **Partial** — Via integration gateways |
| **Clinical Decision Support in Lab** | Interpretation | Interpretive comments, algorithmic reporting, reflex testing | **Present** — CDS module, clinical intelligence |

## 3.13 Point-of-Care Testing (POCT)

| Domain | Description | Key Tests | GULA Coverage |
|--------|-------------|-----------|---------------|
| **Blood Gas & Electrolytes** | Critical care POC | i-STAT, ABL, GEM systems | **Partial** |
| **Glucose Monitoring** | Blood glucose | BGM, CGM | **Partial** |
| **Cardiac Markers POC** | Troponin/BNP POC | Point-of-care troponin, NT-proBNP | **Partial** |
| **Infectious Disease POC** | Rapid diagnostics | HIV, malaria, dengue, Strep A, influenza, RSV | **Partial** |
| **Pregnancy / Fertility POC** | Urine HCG, ovulation | hCG, LH kits | **Partial** |
| **Coagulation POC** | INR, ACT | CoaguChek, i-STAT PT/INR, ACT | **Partial** |
| **Urinalysis POC** | Dipstick | Automation-compatible strips | **Partial** |
| **HbA1c POC** | Diabetes monitoring | Siemens DCA, Afinion | **Partial** |
| **Drugs of Abuse POC** | Rapid drug screen | Multi-panel dip cards | **Partial** |
| **Critical Care POC** | Multi-parameter | Whole blood analysis platforms | **Partial** |

## 3.14 Andrology, Embryology & Reproductive Laboratory

| Sub-discipline | Description | Key Procedures | GULA Coverage |
|----------------|-------------|-------------------|---------------|
| **Semen Analysis** | Male fertility | Sperm count, motility, morphology, DFI | **Present** — Lab results management |
| **Sperm Preparation** | Assisted reproduction | Swim-up, density gradient | **Missing** |
| **Embryology** | IVF/embryo culture | IVF, ICSI, embryo grading, blastocyst culture, vitrification | **Missing** |
| **Sperm & Embryo Cryopreservation** | Freezing | Slow freezing, vitrification, storage tracking | **Missing** |
| **Preimplantation Genetic Testing** | Embryo genetic screening | PGT-A, PGT-M, PGT-SR | **Missing** |
| **Fertility Preservation** | Gamete banking | Egg freezing, sperm banking, ovarian/testicular tissue | **Missing** |
| **Endocrine Fertility Lab** | Hormone measurement | AMH, FSH, LH, estradiol, progesterone | **Present** |

## 3.15 Future Laboratory Fields

| Field | Description | GULA Coverage |
|-------|-------------|---------------|
| **Digital Pathology / AI-Pathology** | Whole-slide imaging with AI interpretation | **Missing** |
| **Multi-Omics Integration** | Combined genomics, proteomics, metabolomics | **Missing** |
| **Single-Cell Analysis** | Cell-by-cell molecular profiling | **Missing** |
| **Liquid Biopsy Platforms** | Circulating tumor analysis | **Missing** |
| **Proteomics** | Large-scale protein analysis | **Missing** |
| **Metabolomics** | Comprehensive metabolite profiling | **Missing** |
| **Glycomics** | Glycan structure analysis | **Missing** |
| **Lipidomics** | Comprehensive lipid analysis | **Missing** |
| **Point-of-Care Sequencing** | Bedside genomics | **Missing** |
| **Organ-on-a-Chip** | Microphysiological systems | **Missing** |
| **Wearable Lab Integration** | Continuous biomarker monitoring | **Missing** |
| **AI-Driven Reflex Testing** | Automated algorithmic testing | **Missing** |

---

# PHASE 4: Nursing Specialties

## 4.1 Clinical Nursing Specialties

### Core Nursing Practice Domains

The nursing profession encompasses four broad practice domains that cut across all specialties:

| Domain | Description | Informatics Requirements | GULA Coverage |
|--------|-------------|-------------------------|---------------|
| **Clinical Practice** | Direct patient care, assessment, intervention, evaluation | Nursing documentation, assessment flowsheets, medication administration, clinical decision support | **Partial** — Documentation platform exists; nursing-specific flowsheets missing |
| **Education** | Patient education, staff development, student preceptorship | Patient education materials library, competency tracking, learning management | **Missing** |
| **Research** | Evidence-based practice, quality improvement, clinical research | Research registry, IRB workflow, EBP documentation | **Present** — Research module |
| **Leadership** | Unit management, quality improvement, policy development | Staff scheduling, budget management, quality indicators, incident reporting | **Partial** — Admin/management tools |

### Specialty Nursing Practice Areas

| Specialty | Description | Common Responsibilities | GULA Coverage |
|-----------|-------------|------------------------|---------------|
| **Medical-Surgical Nursing** | Adult acute care | Patient assessment, medication administration, wound care, post-op monitoring | **Present** — Clinical documentation, care plans, orders |
| **Critical Care Nursing (ICU)** | Life-threatening conditions | Ventilator management, hemodynamic monitoring, CRRT, code response | **Partial** — ICU unit/bed management; no nursing-specific documentation |
| **Emergency Nursing** | Acute care in ED | Triage, trauma resuscitation, emergency procedures, crisis intervention | **Partial** — Emergency room types, triage potential |
| **Perioperative Nursing (OR)** | Surgical patient care | Pre-op assessment, sterile technique, intraoperative documentation, PACU | **Partial** — OT management; no nursing perioperative documentation |
| **Pediatric Nursing** | Care of children | Growth/development assessment, family-centered care, pediatric medication | **Partial** — General pediatric support |
| **Neonatal Nursing (NICU)** | Care of newborns | Thermoregulation, feeding support, phototherapy, developmental care | **Present** — NICU unit/bed types |
| **Oncology Nursing** | Cancer care | Chemotherapy administration, symptom management, central line care, patient education | **Present** — Clinical documentation for cancer care |
| **Psychiatric / Mental Health Nursing** | Mental health care | Therapeutic communication, crisis intervention, psychotropic medication | **Partial** — Clinical documentation |
| **Cardiac Nursing** | Heart disease patients | ECG monitoring, post-MI care, cardiac rehabilitation education | **Partial** |
| **Nephrology Nursing** | Kidney disease | Dialysis management, transplant care, fluid/electrolyte management | **Partial** — Dialysis units |
| **Pulmonary Nursing** | Respiratory conditions | Oxygen therapy, chest physiotherapy, pulmonary rehabilitation | **Partial** |
| **Neurology Nursing** | Neurological disorders | Stroke care, seizure management, neuro assessment, ICP monitoring | **Partial** |
| **Gastroenterology Nursing** | GI disorders | Endoscopy assistance, ostomy care, feeding tube management | **Partial** |
| **Gerontological Nursing** | Elderly care | Comprehensive geriatric assessment, fall prevention, dementia care | **Missing** |
| **Rehabilitation Nursing** | Functional recovery | ADL training, bowel/bladder program, mobility assistance | **Missing** |
| **Wound, Ostomy & Continence Nursing** | Wound care | Complex wound management, ostomy care, continence assessment | **Missing** |
| **Pain Management Nursing** | Pain control | Assessment, patient-controlled analgesia, nerve block management | **Missing** |
| **Palliative Care Nursing** | End-of-life | Symptom management, advance care planning, family support | **Missing** |
| **Hospice Nursing** | Terminally ill | Comfort measures, bereavement support | **Missing** |
| **Transplant Nursing** | Transplant patients | Pre/post-transplant care, immunosuppression management | **Missing** |
| **PeriAnesthesia Nursing (PACU)** | Post-anesthesia recovery | Emergence monitoring, pain control, airway management | **Missing** |
| **Infection Control Nursing** | HAI prevention | Surveillance, isolation, outbreak management | **Present** — Infection control via epidemiology |
| **Burns Nursing** | Burn patients | Wound dressing, fluid resuscitation, skin graft care | **Missing** |
| **Telemetry Nursing** | Cardiac monitoring | Rhythm interpretation, antiarrhythmic management | **Missing** |
| **Flight Nursing** | Air medical transport | In-flight critical care, altitude physiology, rapid assessment | **Missing** |

## 4.2 Advanced Practice Nursing

| Specialty | Description | Common Responsibilities | GULA Coverage |
|-----------|-------------|------------------------|---------------|
| **Family Nurse Practitioner (FNP)** | Primary care across lifespan | Diagnosis, treatment, prescribing, health promotion | **Partial** — Primary care infrastructure |
| **Adult-Gerontology Acute Care NP** | Adult acute care | Hospital-based advanced practice, procedures, critical care | **Partial** |
| **Adult-Gerontology Primary Care NP** | Adult primary care | Chronic disease management, preventive care | **Partial** |
| **Pediatric Nurse Practitioner (PNP)** | Pediatric primary/acute care | Well-child, acute illness, developmental assessment | **Partial** |
| **Neonatal Nurse Practitioner (NNP)** | Newborn intensive care | Delivery room resuscitation, NICU management | **Partial** |
| **Psychiatric-Mental Health NP** | Mental health | Psychotherapy, medication management, crisis care | **Missing** |
| **Women's Health NP (WHNP)** | Women's health | Gynecologic care, contraception, prenatal/postpartum | **Partial** |
| **Certified Nurse-Midwife (CNM)** | Maternity care | Prenatal, labor/delivery, postpartum, well-woman care | **Present** — Pregnancy records, delivery, postnatal |
| **Certified Registered Nurse Anesthetist (CRNA)** | Anesthesia | Pre-op assessment, anesthesia delivery, post-anesthesia care | **Missing** |
| **Clinical Nurse Specialist (CNS)** | Expert clinical practice | All specialties: education, consultation, research, leadership | **Partial** |

## 4.3 Nursing Informatics

| Area | Description | Key Technologies | GULA Coverage |
|------|-------------|-------------------|---------------|
| **Nursing Documentation** | Electronic nursing records | Flowsheets, nursing notes, care plan charting, MAR | **Present** — Clinical documentation platform |
| **Nurse Scheduling** | Staff management | Shift scheduling, acuity-based staffing, overtime tracking | **Missing** |
| **Clinical Decision Support for Nursing** | Evidence-based nursing | Nursing CDS, standing orders, protocols | **Present** — CDS infrastructure |
| **Nursing Quality Indicators** | Nurse-sensitive outcomes | NDNQI reporting, fall rates, pressure ulcers, CAUTI, CLABSI | **Present** — Quality indicators, incident reporting |
| **Nursing Workload Measurement** | Acuity/staffing | Patient classification systems, nursing intensity | **Missing** |

## 4.4 Nursing Leadership & Administration

| Role | Description | Responsibilities | GULA Coverage |
|------|-------------|------------------|---------------|
| **Nurse Manager** | Unit leadership | Staff management, budgeting, quality improvement, scheduling | **Partial** — Employee management, cost centers |
| **Director of Nursing** | Department leadership | Policy development, regulatory compliance, strategic planning | **Partial** |
| **Chief Nursing Officer (CNO)** | Executive nursing | Executive leadership, nursing strategy, board reporting | **Partial** |
| **Nursing Education / Professional Development** | Training | Orientation, continuing education, competency assessment | **Missing** |
| **Nursing Research** | Evidence generation | Research design, IRB, publication, EBP implementation | **Present** — Research module |

---

# PHASE 5: Pharmacy Specialties

## 5.1 Clinical Pharmacy Specialties

### Pharmacy Practice Domains

| Domain | Description | Informatics Requirements | GULA Coverage |
|--------|-------------|-------------------------|---------------|
| **Dispensing** | Medication preparation and distribution | CPOE, eMAR, automated dispensing, barcode scanning, unit dose packaging, IV workflow, Pyxis/Omnicell interfaces | **Partial** — CPOE exists, dispensing workflow missing |
| **Clinical Services** | Pharmacotherapy optimization, drug information | Drug interaction checking, allergy checking, dose recommendations, pharmacokinetic monitoring, antibiotic stewardship | **Present** — CDS infrastructure |
| **Inventory Management** | Drug procurement, storage, expiration | Inventory tracking, bar code scanning, wholesaler EDI, narcotic control, cold chain monitoring | **Partial** — Cold chain monitor exists |
| **Compounding** | Sterile and non-sterile preparation | IV room workflow, chemotherapy preparation, TPN compounding, USP 797/800 compliance, environmental monitoring | **Missing** |
| **Billing & Reimbursement** | Medication billing | Third-party billing, prior authorization, 340B program management, medication assistance programs | **Partial** — Claims module |
| **Regulatory Compliance** | DEA, state board, Joint Commission | Controlled substance logs, PDMP integration, DEA 222 forms, diversion detection | **Missing** |

| Specialty | Description | Key Services | GULA Coverage |
|-----------|-------------|--------------|---------------|
| **Clinical Pharmacy (General)** | Optimal medication use | Medication reconciliation, drug information, pharmacotherapy monitoring | **Present** — Medication management in EHR |
| **Ambulatory Care Pharmacy** | Outpatient medication management | Chronic disease medication optimization, anticoagulation clinics | **Present** |
| **Critical Care Pharmacy** | ICU medications | Sedation, vasopressors, TPN, antimicrobial optimization | **Partial** |
| **Oncology Pharmacy** | Cancer chemotherapy | Hazardous drug compounding, chemotherapy protocols, supportive care | **Present** |
| **Pediatric Pharmacy** | Children's medications | Weight-based dosing, neonatal TPN, pediatric-specific formulations | **Present** |
| **Geriatric Pharmacy** | Elderly medications | Polypharmacy review, Beers criteria, deprescribing | **Missing** — No Beers list integration |
| **Psychiatric Pharmacy** | Psychotropic medications | Therapeutic drug monitoring, metabolic monitoring, compliance | **Partial** |
| **Infectious Diseases Pharmacy** | Antimicrobial therapy | Antibiotic stewardship, PK/PD optimization, antifungal/antiviral management | **Partial** |
| **Cardiology Pharmacy** | Cardiovascular medications | Anticoagulation management, heart failure medication optimization | **Partial** |
| **Nutrition Support Pharmacy** | Parenteral/enteral nutrition | TPN compounding, electrolyte management, nutrition assessment | **Partial** |
| **Transplant Pharmacy** | Transplant immunosuppression | Calcineurin inhibitor management, drug interaction management | **Missing** |
| **Pain & Palliative Care Pharmacy** | Symptom management | Opioid stewardship, PCA management, adjuvant analgesic optimization | **Missing** |
| **Emergency Medicine Pharmacy** | Acute care medication | Code response, RSI, thrombolytics, antidote stocking | **Missing** |
| **Pharmacogenomics** | Genetic-based prescribing | Genotype-guided dosing, adverse reaction prevention | **Missing** |

## 5.2 Nuclear Pharmacy

| Area | Description | GULA Coverage |
|------|-------------|---------------|
| **Radiopharmaceutical Preparation** | Compounding of radioactive tracers | **Missing** |
| **PET/SPECT Radiopharmacy** | Cyclotron/generator-based imaging agents | **Missing** |
| **Therapeutic Radiopharmaceuticals** | Radioisotope therapy | **Missing** |
| **Radiation Safety** | ALARA, shielding, waste management | **Missing** |

## 5.3 Pharmacy Practice Settings

| Setting | Description | GULA Coverage |
|---------|-------------|---------------|
| **Community/Retail Pharmacy** | Outpatient dispensing | **Partial** — Prescription management potential |
| **Hospital/Health-System Pharmacy** | Inpatient medication | **Partial** — Hospital unit type `pharmacy` exists |
| **Compounding Pharmacy** | Custom formulations | **Missing** |
| **Long-Term Care Pharmacy** | Nursing home patients | **Missing** |
| **Hospice Pharmacy** | End-of-life medications | **Missing** |
| **Managed Care Pharmacy** | Insurance/ formulary | **Partial** — Insurance/claims module |
| **Veterinary Pharmacy** | Animal medications | **Missing** |
| **Mail-Order/Telepharmacy** | Remote dispensing | **Missing** |

## 5.4 Pharmaceutical Informatics

| Area | Description | GULA Coverage |
|------|-------------|---------------|
| **Computerized Physician Order Entry (CPOE)** | Electronic prescribing | **Present** — Clinical orders module |
| **Clinical Decision Support for Pharmacy** | Drug-drug interaction, allergy checking | **Present** — CDS module, drug interaction check |
| **Automated Dispensing Cabinets** | Pyxis/Omniceil management | **Missing** |
| **Pharmacy Management System (PMS)** | Inventory, purchasing, billing | **Missing** |
| **Barcode Medication Administration (BCMA)** | Patient-safe administration | **Missing** |
| **Smart Infusion Pump Integration** | Dose error reduction | **Missing** |
| **Formulary Management** | Drug library administration | **Missing** |
| **Adverse Drug Event Reporting** | Pharmacovigilance | **Present** — Incident/safety event reporting |
| **Medication Reconciliation** | Transitions of care | **Present** — Transitions of care module |

---

# PHASE 6: Radiology/Imaging Specialties

## 6.1 Diagnostic Radiology

### Imaging Modality Coverage Assessment

| Modality | Procedure Types | GULA Support Required | GULA Status |
|----------|----------------|----------------------|-------------|
| **X-Ray (Radiography/Fluoroscopy)** | Chest, skeletal, abdominal, contrast studies (GI/GU), fluoroscopy-guided procedures | DICOM modality worklist, image storage, structured report | **Missing** |
| **CT (Computed Tomography)** | Head/brain, chest, abdomen/pelvis, spine, CTA, CT perfusion, CT colonography | DICOM storage, study management, CTDI/dose tracking, structured reporting | **Missing** |
| **MRI (Magnetic Resonance Imaging)** | Brain, spine, MSK, cardiac, abdomen, MRA, MRCP, spectroscopy, DTI, fMRI | DICOM storage, MR safety documentation, contrast tracking, structured reports | **Missing** |
| **Ultrasound** | Abdomen, pelvic, OB/GYN, vascular, MSK, cardiac (echo), breast, pediatric | DICOM storage, structured reports, measurement tracking | **Missing** |
| **Nuclear Medicine** | Bone scan, V/Q, hepatobiliary, renal, cardiac (MUGA, perfusion), PET/CT, SPECT | Dose tracking, radiopharmaceutical documentation, DICOM, structured report | **Missing** |
| **Mammography** | Screening, diagnostic, tomosynthesis, breast biopsy | DICOM, BI-RADS reporting, breast density, dose tracking | **Missing** |
| **Interventional Radiology** | Biopsy, drainage, angiography, embolization, ablation | Procedural documentation, contrast tracking, fluoroscopy time, DICOM | **Missing** |
| **Bone Densitometry (DXA)** | Spine, hip, forearm | T-score, Z-score, FRAX integration | **Missing** |

| Subspecialty | Description | Key Studies | GULA Coverage |
|--------------|-------------|-------------|---------------|
| **Neuroradiology** | Brain, spine, head & neck imaging | CT head/brain, MRI brain, CTA, MRA, MR spectroscopy, CT/MR myelography | **Partial** — Radiology orders via clinical orders system |
| **Musculoskeletal Radiology** | Bone, joint, soft tissue | X-ray extremities, MRI joint, CT bone, arthrography, bone densitometry (DXA) | **Partial** |
| **Abdominal Radiology** | Abdomen and pelvis | CT abdomen/pelvis, MRI abdomen, CT colonography, MRCP | **Partial** |
| **Chest Radiology** | Thoracic imaging | Chest X-ray, CT chest, CT pulmonary angiogram, HRCT | **Partial** |
| **Cardiovascular Radiology** | Heart and vessels | CT coronary angiography, cardiac MRI, CTA, MRA, peripheral angiography | **Partial** |
| **Breast Imaging** | Breast disease | Mammography, breast ultrasound, breast MRI, stereotactic biopsy | **Partial** |
| **Pediatric Radiology** | Children's imaging | Age-appropriate protocols, dose optimization, congenital studies | **Partial** |
| **Genitourinary Radiology** | Renal/reproductive imaging | CT urogram, renal ultrasound, hysterosalpingography | **Partial** |
| **Emergency Radiology** | Acute imaging | Trauma CT, FAST ultrasound, acute stroke imaging | **Partial** |
| **Gastrointestinal Radiology** | GI tract imaging | Barium studies, CT enterography, MR enterography, defecography | **Partial** |
| **Head & Neck Radiology** | ENT/orbit imaging | CT sinuses, MRI neck, CT temporal bones | **Partial** |
| **Nuclear Radiology** | Functional imaging (see Nuclear Medicine) | Bone scan, V/Q scan, renal scan, hepatobiliary scan | **Partial** |

## 6.2 Interventional Radiology

| Subspecialty | Description | Key Procedures | GULA Coverage |
|--------------|-------------|----------------|---------------|
| **General Interventional Radiology** | Image-guided therapy | Biopsy, drainage, abscess drain, central line placement | **Partial** |
| **Vascular Interventional Radiology** | Blood vessel access | Angioplasty, stent, embolization, TIPS, IVC filter | **Partial** |
| **Neurointerventional Radiology** | Brain/spine intervention | Coiling, mechanical thrombectomy, AVM embolization | **Missing** |
| **Interventional Oncology** | Cancer intervention | TACE, Y90 radioembolization, tumor ablation (RFA/MWA/cryo) | **Missing** |
| **Hepatobiliary Intervention** | Liver/bile duct | ERCP, PTC, biliary drain/stent | **Missing** |
| **Genitourinary Intervention** | Kidney/prostate | Nephrostomy, ureteral stent, prostate artery embolization | **Missing** |
| **Pain Intervention** | Image-guided pain management | Epidural steroid injection, nerve block, facet joint injection | **Missing** |
| **Musculoskeletal Intervention** | MSK procedures | Vertebroplasty, kyphoplasty, MSK biopsy | **Missing** |

## 6.3 Nuclear Medicine

| Subspecialty | Description | Key Studies | GULA Coverage |
|--------------|-------------|-------------|---------------|
| **General Nuclear Medicine** | Gamma camera imaging | Bone scan, thyroid scan, renal scan, hepatobiliary scan, lung V/Q | **Partial** — Clinical orders |
| **PET/CT** | Metabolic/anatomic fusion | FDG PET/CT for oncology, infection/inflammation, neurology | **Partial** |
| **PET/MRI** | Hybrid metabolic imaging | Advanced oncology, neuro, cardiac | **Missing** |
| **Cardiac Nuclear Medicine** | Heart function/perfusion | Myocardial perfusion (SPECT/PET), MUGA scan | **Partial** |
| **Radionuclide Therapy** | Radioisotope treatment | I-131 for thyroid, Lu-177 for NET, Ra-223 for bone metastases | **Missing** |
| **Theranostics** | Integrated diagnostic/therapeutic | PSMA theranostics, DOTATATE, theranostic pairs | **Missing** |

## 6.4 Radiation Oncology

| Area | Description | Key Technologies | GULA Coverage |
|------|-------------|------------------|---------------|
| **External Beam Radiation** | Teletherapy | IMRT, VMAT, SBRT, SRS, proton therapy, stereotactic radiosurgery (Gamma Knife) | **Missing** |
| **Brachytherapy** | Internal radiation | HDR, LDR, interstitial, intracavitary | **Missing** |
| **Treatment Planning** | Dosimetry | CT simulation, contouring, dose calculation, inverse planning | **Missing** |
| **Radiation Physics** | Quality assurance | Linac QA, TPS validation, dosimetry audit | **Missing** |
| **Radiation Biology** | Radiosensitivity | Fractionation, normal tissue tolerance, combination therapy | **Missing** |
| **Palliative Radiation** | Symptom control | Bone metastases, brain metastases, spinal cord compression, bleeding | **Missing** |

## 6.5 Ultrasound

| Subspecialty | Description | Key Applications | GULA Coverage |
|--------------|-------------|------------------|---------------|
| **General Ultrasound** | Sonography | Abdomen, pelvic, thyroid, scrotal, soft tissue | **Partial** |
| **OB/GYN Ultrasound** | Pregnancy & gynecology | Fetal anatomy scan, growth scan, TVS, hysterosonography | **Partial** |
| **Vascular Ultrasound** | Blood vessel imaging | Carotid duplex, venous Doppler, arterial duplex, AAA screening | **Partial** |
| **Echocardiography** | Heart ultrasound (see Cardiac Sonography) | TTE, TEE, stress echo | **Missing** |
| **Musculoskeletal Ultrasound** | MSK sonography | Joint evaluation, tendon/ligament, guided injection | **Missing** |
| **Point-of-Care Ultrasound (POCUS)** | Bedside ultrasound | eFAST, cardiac, lung, procedural guidance | **Missing** |
| **Pediatric Ultrasound** | Children's US | Hip dysplasia (Graf), pyloric stenosis, cranial US | **Missing** |
| **Contrast-Enhanced Ultrasound (CEUS)** | Microbubble imaging | Liver lesion characterization, vesicoureteral reflux | **Missing** |

## 6.6 Advanced & Emerging Modalities

| Modality | Description | Clinical Use | GULA Coverage |
|----------|-------------|--------------|---------------|
| **Molecular Imaging** | Cellular/molecular visualization | PET, SPECT, optical, targeted molecular probes | **Missing** |
| **Hybrid Imaging** | Multi-modality fusion | PET/CT, SPECT/CT, PET/MRI | **Missing** |
| **Multiparametric MRI** | Quantitative tissue characterization | Prostate mpMRI, liver, breast | **Missing** |
| **Functional MRI (fMRI)** | Brain activation mapping | Pre-surgical planning, cognitive research | **Missing** |
| **Diffusion Tensor Imaging (DTI)** | White matter tractography | Brain tumor, stroke, spinal cord | **Missing** |
| **Perfusion Imaging** | Tissue blood flow | Stroke, tumor, myocardial perfusion | **Missing** |
| **MR Spectroscopy** | Metabolic imaging | Brain tumor, prostate, hepatic steatosis | **Missing** |
| **Photon Counting CT** | Spectral CT | Multi-energy, material decomposition | **Missing** |
| **Phase-Contrast Imaging** | X-ray phase shift | Soft tissue contrast, lung imaging | **Missing** |
| **Photoacoustic Imaging** | Light and sound | Vascular imaging, melanoma depth | **Missing** |
| **Optoacoustic Imaging** | Molecular optoacoustic | Breast cancer, inflammatory arthritis | **Missing** |
| **Magnetic Particle Imaging** | Superparamagnetic nanoparticles | Vascular imaging, cell tracking, cancer | **Missing** |
| **Artificial Intelligence in Radiology** | AI-assisted diagnosis | Detection (CAD), triage, segmentation, quantification, reporting | **Missing** |
| **Radiomics** | Quantitative feature extraction | Tumor phenotyping, treatment response prediction | **Missing** |
| **Radiogenomics** | Imaging-genetic correlation | Genotype-phenotype imaging associations | **Missing** |

## 6.7 Radiology Informatics

| Component | Description | GULA Coverage |
|-----------|-------------|---------------|
| **PACS (Picture Archiving & Communication)** | Image storage and viewing | **Missing** |
| **RIS (Radiology Information System)** | Radiology workflow management | **Missing** |
| **DICOM Modality Worklist** | Modality integration | **Missing** |
| **Voice Recognition / Dictation** | Structured reporting | **Missing** |
| **Computer-Aided Detection (CAD)** | AI screening tools | **Missing** |
| **Teleradiology** | Remote interpretation | **Missing** |
| **Dose Tracking / Dose Index Registry** | Radiation dose monitoring | **Missing** |
| **Structured Reporting (RSNA Template)** | Standardized reports | **Missing** |

---

# PHASE 7: Dentistry Specialties

## 7.1 Dental Specialties (Complete Catalog)

### Dental Practice Domains

| Domain | Description | Informatics Requirements | GULA Coverage |
|--------|-------------|-------------------------|---------------|
| **Practice Management** | Scheduling, billing, patient communication | Appointment scheduling, treatment planning, insurance claim (ADA 2010), patient portal | **Missing** |
| **Clinical Documentation** | Charting, periodontal assessment, treatment notes | Dental charting (periodontal charting, hard tissue charting, existing restorations, caries detection, missing teeth, conditions, treatments, prosthetics), treatment planning with tooth-surface coding, clinical notes, digital imaging integration (intraoral camera, CBCT, panoramic X-ray) with DICOM dental extension | **Missing** |
| **Radiology** | Dental X-ray management | Panoramic, periapical, bitewing, CBCT image storage, DICOM dental extensions, AI caries detection, 2D/3D visualization | **Missing** |
| **Laboratory Integration** | Dental lab communication | Digital impressions (STL files), design files (CAD/CAM transmission), order tracking, case communication, and result integration | **Missing** |
| **Billing & Coding** | Procedure coding and insurance | ADA CDT codes, procedure transaction codes, dental insurance (D0100-D9999), Denti-Cal (US), NHS dental banding (UK), national dental insurance | **Missing** |

| Specialty | Description | Key Procedures | GULA Coverage |
|-----------|-------------|----------------|---------------|
| **General Dentistry** | Comprehensive oral health | Exam, cleaning, fillings, crowns, bridges, radiographs | **Missing** |
| **Endodontics** | Root canal therapy | Root canal treatment, apicoectomy, endodontic retreatment | **Missing** |
| **Orthodontics & Dentofacial Orthopedics** | Tooth/jaw alignment | Braces, Invisalign, palatal expanders, orthognathic surgery coordination | **Missing** |
| **Periodontics** | Gum disease and implants | Scaling/root planing, periodontal surgery, dental implant placement, gum grafting | **Missing** |
| **Prosthodontics** | Prosthetic tooth replacement | Crowns, bridges, dentures (complete/partial), implant-supported prosthetics, maxillofacial prosthetics | **Missing** |
| **Oral & Maxillofacial Surgery** | Face, mouth, jaw surgery | Wisdom tooth extraction, dental implants, orthognathic surgery, TMJ surgery, facial trauma, cleft lip/palate repair | **Missing** |
| **Pediatric Dentistry (Pedodontics)** | Children's dentistry | Preventive care, sealants, pulp therapy, space maintenance, behavior guidance | **Missing** |
| **Oral & Maxillofacial Pathology** | Oral disease diagnosis | Biopsy interpretation, oral cancer diagnosis, odontogenic tumor management | **Missing** |
| **Oral & Maxillofacial Radiology** | Dental imaging | Panoramic radiograph, CBCT, sialography, TMJ imaging interpretation | **Missing** |
| **Dental Public Health** | Community oral health | Community water fluoridation, school sealant programs, epidemiology, policy | **Missing** |
| **Forensic Odontology** | Dental legal identification | Human remains identification, bite mark analysis, age estimation | **Missing** |
| **Oral Medicine** | Oral mucosal disease | Lichen planus, leukoplakia, pemphigus, oral manifestations of systemic disease | **Missing** |
| **Orofacial Pain / TMD** | Jaw joint and muscle pain | TMJ disorder management, bruxism, occlusal therapy | **Missing** |
| **Special Care Dentistry** | Patients with disabilities | Hospital dentistry, sedation, disability-adapted care, geriatric dental care | **Missing** |
| **Dental Sleep Medicine** | Sleep-related breathing | Oral appliance therapy for sleep apnea, snoring management | **Missing** |
| **Implant Dentistry** | Advanced implantology | Full-arch rehabilitation, zygomatic implants, guided surgery | **Missing** |
| **Aesthetic Dentistry** | Cosmetic dental procedures | Veneers, teeth whitening, composite bonding, smile design | **Missing** |
| **Craniofacial Genetics** | Genetic dental syndromes | Cleft lip/palate, ectodermal dysplasia, amelogenesis imperfecta | **Missing** |

---

# PHASE 8: Allied Health Professions

## 8.1 Therapy & Rehabilitation Professions

| Profession | Description | Key Interventions | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **Physical Therapy (PT)** | Movement and function restoration | Therapeutic exercise, gait training, manual therapy, ultrasound, electrical stimulation | **Missing** |
| **Occupational Therapy (OT)** | Activities of daily living | ADL training, fine motor rehabilitation, splinting, home modification assessment, sensory integration | **Missing** |
| **Speech-Language Pathology (SLP)** | Communication and swallowing | Language therapy, articulation, voice therapy, augmentative communication, dysphagia management, fluency | **Missing** |
| **Respiratory Therapy (RT)** | Cardiopulmonary care | Mechanical ventilation, oxygen therapy, chest physiotherapy, pulmonary function testing, ABG interpretation | **Missing** |
| **Cardiac Rehabilitation** | Post-cardiac event rehab | Exercise prescription, risk factor management, lifestyle counseling | **Missing** |
| **Recreation Therapy** | Recreational treatment | Therapeutic recreation, leisure counseling, community reintegration | **Missing** |
| **Music Therapy** | Music-based intervention | Neurologic music therapy, improvisation, therapeutic singing | **Missing** |
| **Art Therapy** | Creative expression | Visual arts for emotional processing, trauma recovery | **Missing** |
| **Dance/Movement Therapy** | Body movement | Somatic intervention, non-verbal expression, psychomotor therapy | **Missing** |
| **Vestibular Rehabilitation** | Balance disorders | Canalith repositioning, habituation, balance retraining | **Missing** |
| **Hand Therapy** | Upper extremity rehab | Post-surgical hand rehab, splinting, scar management | **Missing** |
| **Pelvic Floor Therapy** | Pelvic health | Biofeedback, manual therapy, exercises for incontinence/pain | **Missing** |
| **Lymphedema Therapy** | Swelling management | Complete decongestive therapy, manual lymphatic drainage | **Missing** |

## 8.2 Dietetics & Nutrition

| Profession | Description | Key Interventions | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **Registered Dietitian Nutritionist (RDN)** | Medical nutrition therapy | Therapeutic diets, enteral/parenteral nutrition, weight management, diabetes education | **Partial** — Clinical documentation, nutrition orders |
| **Clinical Dietetics** | Hospital nutrition | NPO management, calorie count, malnutrition diagnosis, TPN monitoring | **Partial** |
| **Pediatric Nutrition** | Children's nutrition | Growth assessment, feeding therapy, metabolic disease diet, picky eating | **Missing** |
| **Sports Nutrition** | Athletic performance | Performance nutrition, hydration, supplements, body composition | **Missing** |
| **Renal Nutrition** | Kidney disease diet | Electrolyte management, protein restriction, dialysis nutrition | **Missing** |
| **Oncology Nutrition** | Cancer nutrition | Cachexia management, anti-nausea diet, supplement counseling | **Missing** |
| **Gerontological Nutrition** | Elderly nutrition | Dysphagia diets, appetite stimulation, malnutrition prevention | **Missing** |
| **Integrative & Functional Nutrition** | Whole-person nutrition | Elimination diets, micronutrient testing, gut health | **Missing** |
| **Public Health Nutrition** | Community nutrition | WIC programs, school nutrition policy, food security | **Missing** |
| **Food Service Management** | Food operations | Menu planning, safety compliance, inventory, patient satisfaction | **Missing** |

## 8.3 Medical Imaging & Diagnostic Professionals

| Profession | Description | Key Responsibilities | GULA Coverage |
|-----------|-------------|---------------------|---------------|
| **Radiologic Technologist (Radiographer)** | X-ray and general imaging | Patient positioning, radiation safety, image acquisition | **Missing** |
| **CT Technologist** | Computed tomography | Cross-sectional imaging, contrast administration, 3D reconstruction | **Missing** |
| **MRI Technologist** | Magnetic resonance imaging | Magnet safety, sequence selection, contrast protocols | **Missing** |
| **Sonographer (Ultrasound)** | Ultrasound imaging | OB/GYN, abdominal, vascular, MSK, cardiac (echo) sonography | **Missing** |
| **Nuclear Medicine Technologist** | Radionuclide imaging | Radiopharmaceutical administration, gamma camera, PET/CT operation | **Missing** |
| **Radiation Therapist** | Radiation treatment delivery | Linac operation, treatment setup, immobilization, dosimetry verification | **Missing** |
| **Mammography Technologist** | Breast imaging | Mammographic compression, positioning, QC | **Missing** |
| **Cardiac Sonographer (Echocardiographer)** | Heart ultrasound | TTE, TEE, stress echo, strain imaging | **Missing** |
| **Vascular Technologist (RVT)** | Vascular ultrasound | Carotid duplex, venous/arterial Doppler, ABI | **Missing** |
| **Dosimetrist** | Radiation treatment planning | Dose calculation, IMRT optimization, plan evaluation | **Missing** |
| **PACS Administrator** | Image management | DICOM/RIS/PACS workflow, data integrity, storage management | **Missing** |
| **Medical Physicist (Imaging)** | Imaging physics | QC, radiation safety, accreditation, protocol optimization | **Missing** |
| **Medical Physicist (Therapy)** | Radiation oncology physics | Linac calibration, TPS validation, brachytherapy physics | **Missing** |
| **Radiology Assistant (RA)** | Advanced imaging practice | Contrast administration, fluoroscopy, image-guided procedures | **Missing** |

## 8.4 Medical Laboratory Professionals

| Profession | Description | Key Responsibilities | GULA Coverage |
|-----------|-------------|---------------------|---------------|
| **Medical Laboratory Scientist (MLS/MLT)** | Clinical lab testing | Sample analysis, QC, result validation, instrument operation | **Complete** — LIMS is GULA's core function |
| **Clinical Chemistry Specialist** | Automated chemistry | Method validation, troubleshooting, reference range management | **Complete** |
| **Hematology Technologist** | Blood cell analysis | CBC, differential, coagulation, body fluid analysis | **Complete** |
| **Microbiology Technologist** | Pathogen identification | Culture, ID/AST, molecular, mycology, parasitology | **Complete** |
| **Blood Bank Technologist (SBB)** | Transfusion service | Antibody ID, crossmatch, component management | **Complete** |
| **Immunology Technologist** | Immune testing | ELISA, flow cytometry, HLA, autoantibody testing | **Present** |
| **Molecular Biology Technologist** | Genetic/molecular testing | PCR, sequencing, genotyping, FISH | **Present** |
| **Histotechnologist / Histotechnician** | Tissue processing | Embedding, microtomy, H&E staining, IHC | **Present** |
| **Cytotechnologist** | Cell examination | Pap smear screening, FNA preparation, liquid-based cytology | **Present** |
| **Cytogenetic Technologist** | Chromosome analysis | Karyotyping, FISH, microarray | **Missing** |
| **Phlebotomist** | Blood collection | Venipuncture, capillary puncture, specimen handling, patient identification | **Present** — Sample collection workflow |
| **Point-of-Care Coordinator** | POC testing management | Device management, operator training, QC oversight | **Partial** |
| **Laboratory Manager** | Lab operations | Personnel, finance, accreditation, quality management | **Complete** — Lab admin module |
| **Laboratory Informatics Specialist** | LIS management | System configuration, interface management, data analytics | **Complete** |

## 8.5 Pharmacy Technicians

| Role | Description | Key Responsibilities | GULA Coverage |
|------|-------------|---------------------|---------------|
| **Pharmacy Technician (Community)** | Retail pharmacy | Prescription processing, inventory, insurance billing | **Missing** |
| **Pharmacy Technician (Hospital)** | Inpatient pharmacy | Unit dose, IV admixture, controlled substance, narcotic count | **Missing** |
| **Sterile Compounding Technician** | Aseptic preparation | Chemotherapy preparation, TPN, epidural, IV piggyback | **Missing** |
| **Pharmacy Informatics Technician** | System support | Pyxis inventory, barcode scanning, automation | **Missing** |
| **Nuclear Pharmacy Technician** | Radioactive drugs | Preparation, shipping, waste management | **Missing** |
| **Veterinary Pharmacy Technician** | Animal medications | Animal-specific compounding, dosing | **Missing** |

## 8.6 Surgical & Anesthesia Professionals

| Profession | Description | Key Responsibilities | GULA Coverage |
|-----------|-------------|---------------------|---------------|
| **Surgical Technologist (Scrub Tech)** | OR assistance | Sterile field, instrument handling, surgical count, wound closure assistance | **Partial** — OT management |
| **Anesthesia Technologist / Technician** | Anesthesia support | Anesthesia machine setup, monitoring equipment, airway equipment | **Missing** |
| **Surgical First Assistant (CSA/CFA)** | Direct surgical assistance | Retraction, hemostasis, suturing, tissue handling | **Partial** |
| **Perioperative Nurse** | OR/Aesthesia (see 4.1) | Circulating nurse, scrub nurse, PACU | **Partial** |
| **Central Sterile Processing Technician** | Instrument sterilization | Decontamination, sterilization, pack assembly, inventory | **Missing** |
| **Cardiovascular Perfusionist** | Heart-lung bypass | CPB management, ECMO, cell saver, IABP | **Missing** |
| **Orthopedic Technologist (Cast Tech)** | Casting and traction | Cast application/removal, traction setup, OR assist | **Missing** |
| **Surgical Neurophysiologist** | Intraoperative monitoring | SSEP, MEP, EMG, EEG monitoring during surgery | **Missing** |
| **Ophthalmic Technician** | Eye care support | Vision testing, tonometry, refractometry, OCT | **Missing** |

## 8.7 Emergency Medical Services (EMS)

| Level | Description | Key Skills | GULA Coverage |
|-------|-------------|------------|---------------|
| **First Responder** | Immediate life support | BLS, oxygen, AED, basic first aid | **Missing** |
| **Emergency Medical Technician (EMT-Basic)** | Basic life support | Patient assessment, spinal immobilization, splinting, epinephrine auto-injector | **Missing** |
| **Advanced EMT (AEMT)** | Limited advanced life support | IV access, supraglottic airway, limited medication administration | **Missing** |
| **Paramedic** | Advanced life support | Intubation, cardiac monitoring, defibrillation, advanced medication, 12-lead ECG interpretation | **Missing** |
| **Critical Care Paramedic (CCP)** | ICU-level pre-hospital | Ventilator management, invasive monitoring, blood product administration | **Missing** |
| **Community Paramedic** | Mobile integrated health | Home visit, chronic disease management, preventative care | **Missing** |
| **EMS Dispatcher** | Emergency dispatch | EMD protocols, resource allocation, real-time coordination | **Missing** |
| **Flight Paramedic / Flight Nurse** | Air medical transport | In-flight critical care, confined space medicine, hoist rescue | **Missing** |

## 8.8 Behavioral & Mental Health Professionals

| Profession | Description | Key Interventions | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **Clinical Psychologist** | Mental health diagnosis/therapy | CBT, DBT, psychodynamic therapy, psychological testing | **Missing** |
| **Counseling Psychologist** | Adjustment/life issues | Career counseling, relationship therapy, stress management | **Missing** |
| **School Psychologist** | Educational psychology | Learning assessment, behavioral intervention, IEP consultation | **Missing** |
| **Marriage & Family Therapist** | Relationship therapy | Couples counseling, family systems therapy | **Missing** |
| **Licensed Clinical Social Worker (LCSW)** | Social work-therapy | Case management, therapy, crisis intervention, discharge planning | **Missing** |
| **Addictions Counselor** | Substance use | Detox support, relapse prevention, 12-step facilitation | **Missing** |
| **Rehabilitation Counselor** | Disability adjustment | Vocational counseling, independent living skills | **Missing** |
| **Art/Music/Drama Therapist** | Creative therapy | Expressive arts intervention | **Missing** |
| **Psychiatric Technician** | MH support | Milieu management, medication monitoring, group facilitation | **Missing** |
| **Behavior Analyst (BCBA)** | Behavioral therapy | ABA for autism, functional behavior assessment | **Missing** |

## 8.9 Audiology & Hearing Health

| Profession | Description | Key Services | GULA Coverage |
|-----------|-------------|--------------|---------------|
| **Audiologist** | Hearing and balance | Hearing assessment, hearing aid fitting, cochlear implant programming, balance evaluation | **Missing** |
| **Pediatric Audiologist** | Children's hearing | Newborn hearing screening, auditory-verbal therapy, FM systems | **Missing** |
| **Educational Audiologist** | School hearing | Classroom acoustics, assistive listening, IEP consultation | **Missing** |
| **Hearing Instrument Specialist** | Hearing aid dispensing | Hearing aid selection, fitting, repair, counseling | **Missing** |
| **Cochlear Implant Audiologist** | Implantable devices | CI mapping, rehabilitation, device management | **Missing** |

## 8.10 Optometry & Vision Health

| Profession | Description | Key Services | GULA Coverage |
|-----------|-------------|--------------|---------------|
| **Optometrist (OD)** | Primary eye care | Refraction, contact lens fitting, glaucoma management, binocular vision, low vision | **Missing** |
| **Pediatric Optometrist** | Children's vision | Vision therapy, amblyopia, strabismus assessment | **Missing** |
| **Low Vision Specialist** | Visual impairment | Low vision aids, rehabilitation, magnification assessment | **Missing** |
| **Optician** | Eyeglass dispensing | Lens fabrication, frame selection, dispensing | **Missing** |
| **Orthoptist** | Eye movement | Strabismus measurement, vision training, prisms | **Missing** |
| **Contact Lens Specialist** | Contact lenses | Complex fit, keratoconus, orthokeratology, scleral lenses | **Missing** |

## 8.11 Complementary & Integrative Health Professions

| Profession | Description | Key Interventions | GULA Coverage |
|-----------|-------------|-------------------|---------------|
| **Acupuncturist** | Traditional Chinese medicine acupuncture | Needle insertion, electroacupuncture, moxibustion, cupping | **Missing** |
| **Chiropractor** | Spinal adjustment | Spinal manipulation, mobilization, soft tissue therapy, rehabilitation exercises | **Missing** |
| **Naturopath (ND)** | Natural medicine | Botanical medicine, clinical nutrition, homeopathy, hydrotherapy | **Missing** |
| **Massage Therapist** | Therapeutic massage | Swedish, deep tissue, sports, trigger point, myofascial release | **Missing** |
| **Osteopath (DO - outside USA)** | Manual medicine | Cranial osteopathy, visceral manipulation, structural integration | **Missing** |
| **Homeopath** | Homeopathic treatment | Constitutional prescribing, acute prescribing, remedy management | **Missing** |
| **Traditional Chinese Medicine Practitioner** | TCM system | Chinese herbal medicine, acupuncture, Tui Na, Qi Gong, dietetics | **Missing** |
| **Ayurvedic Practitioner** | Ayurvedic medicine | Dosha assessment, herbal therapy, Panchakarma, lifestyle | **Missing** |
| **Mind-Body Practitioner** | Meditation/mindfulness | Mindfulness-based stress reduction (MBSR), biofeedback, guided imagery | **Missing** |
| **Herbalist** | Medicinal plants | Phytotherapy, formulation, tincture preparation | **Missing** |
| **Aromatherapist** | Essential oils | Therapeutic application of essential oils, inhalation, topical | **Missing** |
| **Reflexologist** | Reflex point therapy | Foot/hand reflexology, zone therapy | **Missing** |
| **Hypnotherapist** | Clinical hypnosis | Therapeutic suggestion, smoking cessation, pain management | **Missing** |

## 8.12 Genetic Counseling

| Area | Description | Key Services | GULA Coverage |
|------|-------------|--------------|---------------|
| **Preconception/Prenatal Genetics** | Family planning | Carrier screening, NIPT counseling, prenatal diagnosis | **Missing** |
| **Cancer Genetics** | Hereditary cancer | BRCA counseling, Lynch syndrome, multigene panel interpretation | **Missing** |
| **Pediatric Genetics** | Childhood genetic disorders | Autism genetics, metabolic disease, developmental delay | **Missing** |
| **Cardiovascular Genetics** | Hereditary heart disease | Long QT, HCM, familial hypercholesterolemia | **Missing** |
| **Neurogenetics** | Neurologic genetic disorders | Huntington's, ALS, neurofibromatosis | **Missing** |
| **Pharmacogenetics** | Drug-gene interaction | Genotype-guided prescribing counseling | **Missing** |
| **Direct-to-Consumer Genetics** | Consumer interpretation | DTC raw data interpretation, risk communication | **Missing** |

## 8.13 Health Administration & Informatics

| Profession | Description | Key Responsibilities | GULA Coverage |
|-----------|-------------|---------------------|---------------|
| **Healthcare Administrator** | Facility operations | Strategic planning, regulatory compliance, operations, HR, financial management, payer contracting, facility master planning, community needs assessment, board governance | **Present** — Hospital admin module |

### Complementary Health Regulation & Governance

| Regulatory Body | Scope | GULA Relevance |
|----------------|-------|----------------|
| **WHO** | Global health policy, classification, emergencies | ICD-11, ICF, ICHI alignment |
| **World Medical Association** | Medical ethics, physician rights | Declaration of Helsinki, Geneva |
| **International Council of Nurses** | Nursing standards, workforce | ICN Code of Ethics |
| **International Pharmaceutical Federation (FIP)** | Pharmacy practice, education | Pharmacy workforce development |
| **World Confederation for Physical Therapy** | PT standards, education | PT practice alignment |
| **International Association of Speech-Language Pathology** | SLP standards | SLP practice alignment |
| **World Federation of Occupational Therapists** | OT standards, education | OT practice alignment |
| **International Society of Radiographers** | Imaging standards | Radiography practice alignment |
| **FDI World Dental Federation** | Dental standards | Dental terminology, CDT codes |
| **World Health Professions Alliance** | Interprofessional collaboration | Cross-professional coordination |
| **International Society for Quality in Healthcare (ISQua)** | Healthcare quality | Quality framework alignment |
| **Joint Commission International** | Hospital accreditation | Quality/safety framework |
| **International Hospital Federation** | Hospital management | Hospital governance |
| **HL7 International** | Health data interoperability | FHIR/terminology alignment |
| **IHE International** | Health system integration | Workflow profiles |
| **ISO/TC 215** | Health informatics standards | All ISO standards |
| **DICOM Standards Committee** | Medical imaging | Imaging interoperability |
| **CDISC** | Clinical research data | Research data standards |
| **GA4GH** | Genomic data sharing | Genomic data standards |

### Emerging Allied Health Roles

| Role | Description | Justification | GULA Priority |
|------|-------------|---------------|---------------|
| **Community Health Worker (CHW)** | Community-based health outreach, navigation, health education | WHO recommendation; essential for LMIC deployment | **High** |
| **Patient Navigator** | Guide patients through complex healthcare systems, reduce barriers | Cancer care, chronic disease, health equity | **High** |
| **Health Coach** | Behavior change, goal setting, motivation for lifestyle medicine | Chronic disease prevention and management | **Medium** |
| **Digital Health Coach** | App-based health coaching, wearable data interpretation | Digital health ecosystem expansion | **Medium** |
| **Peer Support Specialist** | Lived-experience based support for mental health, substance use | Behavioral health, recovery support | **Medium** |
| **Doulas (Birth/Bereavement)** | Non-clinical labor support, postpartum support, loss support | Maternity care, palliative care | **Medium** |
| **Emergency Medical Dispatcher** | Pre-arrival instructions, resource allocation | EMS integration | **Low** |
| **Surgical First Assistant** | Advanced OR support | Surgical services, resource-constrained settings | **Low** |
| **Clinical Documentation Integrity Specialist** | Documentation improvement for coding/reimbursement | Revenue cycle, compliance | **Low** |
| **Clinical Decision Support Specialist** | CDS optimization, maintenance, governance | Advanced CDS implementation | **Low** |
| **Certified Tumor Registrar** | Cancer registry abstraction, follow-up, survival | Oncology program accreditation (CoC) | **Low** |
| **Trauma Registrar** | Trauma registry data abstraction, ACS verification | Trauma center verification | **Low** |
| **Transplant Coordinator** | Organ transplant candidate evaluation, waiting list, post-transplant | Transplant program accreditation | **Low** |
| **Donor Coordinator** | Deceased donor management, organ recovery coordination | Organ procurement | **Low** |
| **Medical Interpreter** | Language access services | Multi-language healthcare environment | **Medium** |
| **Patient Experience Officer** | Patient satisfaction, service recovery, experience design | Value-based care, consumerism | **Low** |
| **Medical Practice Manager** | Clinic management | Scheduling, billing, staffing, workflow optimization | **Present** |
| **Health Information Manager (HIM)** | Medical records | Coding (ICD-10/CPT), release of information, privacy, transcription | **Present** — Clinical documentation, coding |
| **Clinical Informaticist** | Health IT optimization | System design, workflow analysis, training, CDS optimization | **Complete** — Platform core competency |
| **Healthcare Data Analyst** | Analytics & reporting | Quality metrics, population health, operations analysis, dashboards | **Present** — Stats, quality dashboard |
| **Medical Scribe** | Physician documentation | Real-time charting, EHR support | **Present** |
| **Credentialing Specialist** | Provider credentialing | Initial/appointment, reappointment, privileging, CAQH | **Missing** |
| **Patient Access/Registration** | Pre-service | Insurance verification, pre-authorization, financial clearance | **Present** — Patient registration |
| **Medical Biller/Coder** | Revenue cycle | Charge capture, claim submission, denial management | **Present** — Insurance/claims |
| **Utilization Management Coordinator** | Resource management | Admission review, concurrent review, discharge planning | **Missing** |
| **Case Manager (Non-nursing)** | Care coordination | Resource referral, benefit coordination, patient advocacy | **Partial** — Care coordination |

## 8.14 Other Allied Health Professions

| Profession | Description | GULA Coverage |
|-----------|-------------|---------------|
| **Child Life Specialist** | Pediatric emotional support | **Missing** |
| **Orthotist / Prosthetist (CPO)** | Orthotic/prosthetic devices | **Missing** |
| **Pedorthist** | Foot orthotics | **Missing** |
| **Seating & Mobility Specialist** | Wheelchair/seating | **Missing** |
| **Perfusionist** | Cardiopulmonary bypass (see Surg) | **Missing** |
| **Medical Illustrator** | Clinical visualization | **Missing** |
| **Certified Diabetes Educator (CDE)** | Diabetes self-management | **Partial** — General clinical education |
| **Lactation Consultant (IBCLC)** | Breastfeeding support | **Present** — Breastfeeding records |
| **Infant Toddler Specialist** | Early childhood development | **Missing** |
| **Athletic Trainer (ATC)** | Sports injury prevention | **Missing** |
| **Exercise Physiologist** | Exercise prescription | **Missing** |
| **Kinesiotherapist** | Therapeutic exercise | **Missing** |
| **Art Therapist (ATR)** | Creative arts therapy | **Missing** |
| **Dance Therapist** | Movement therapy | **Missing** |
| **Drama Therapist** | Theater-based therapy | **Missing** |
| **Horticultural Therapist** | Gardening therapy | **Missing** |
| **Equine-Assisted Therapist** | Horse-based therapy | **Missing** |
| **Animal-Assisted Therapist** | Animal interaction | **Missing** |
| **Music Therapist (MT-BC)** | Clinical music therapy | **Missing** |
| **Recreational Therapist (CTRS)** | Therapeutic recreation | **Missing** |
| **Therapeutic Recreation Specialist** | Adaptive recreation | **Missing** |
| **Cardiovascular Technologist (CVT)** | Cardiac diagnostic testing | **Missing** |
| **Electroneurodiagnostic Technologist** | EEG, evoked potentials | **Missing** |
| **Polysomnographic Technologist** | Sleep study | **Missing** |
| **Ophthalmic Medical Technologist** | Eye testing support | **Missing** |
| **Optometric Technician** | Vision testing | **Missing** |
| **Orthoptic Technician** | Eye movement testing | **Missing** |
| **Mammography Technologist** | Breast imaging | **Missing** |
| **Dosimetrist** | Radiation planning | **Missing** |
| **Medical Physicist** | Physics support | **Missing** |
| **Health Physicist** | Radiation safety | **Missing** |
| **MRI Safety Officer** | MRI safety | **Missing** |
| **Nuclear Medicine Technologist** | Nuclear imaging | **Missing** |
| **Radiation Therapy Technologist** | Radiation treatment | **Missing** |
| **Radiology Manager** | Imaging admin | **Missing** |
| **Sonographer (General)** | Ultrasound | **Missing** |
| **Vascular Sonographer** | Vascular US | **Missing** |
| **Echocardiographer (Cardiac Sonographer)** | Heart US | **Missing** |
| **Dental Assistant** | Dental chairside | **Missing** |
| **Dental Hygienist** | Oral prophylaxis | **Missing** |
| **Dental Laboratory Technician** | Dental prosthetics | **Missing** |
| **Dental Therapist** | Basic restorative | **Missing** |
| **Orthodontic Assistant** | Ortho support | **Missing** |
| **Pharmacy Technician** | Medication dispensing | **Missing** |
| **Phlebotomy Technician** | Blood draw | **Present** |
| **ECG Technician** | ECG recording | **Missing** |
| **Holter Monitor Technician** | Ambulatory monitoring | **Missing** |
| **Stress Test Technician** | Exercise stress | **Missing** |
| **Telemetry Technician** | Remote monitoring | **Missing** |
| **Dialysis Technician** | Renal dialysis | **Partial** — Dialysis unit |
| **Surgical Technologist** | OR assistance | **Partial** |
| **Anesthesia Technician** | Anesthesia support | **Missing** |
| **Sterile Processing Technician** | Sterilization | **Missing** |
| **Medical Assistant** | Clinical support | **Partial** |
| **CNA / Nursing Assistant** | Basic patient care | **Missing** |
| **Patient Care Technician** | Acute care support | **Missing** |
| **Home Health Aide** | In-home support | **Partial** — Home care plans |
| **Orderly** | Hospital support | **Missing** |
| **Transport Technician** | Patient transport | **Missing** |
| **Unit Secretary** | Nursing unit admin | **Missing** |
| **Scribes** | Documentation | **Partial** |

---

## APPENDIX A: Coverage Summary Matrix

| Phase | Domain | Total Entries | Complete | Present | Partial | Missing | Coverage Rate (%) |
|-------|--------|---------------|----------|---------|---------|---------|------------------|
| 1 | Healthcare Domains | 48 | 1 | 12 | 10 | 25 | 48% |
| 2 | Medical Specialties | 105 | 0 | 17 | 48 | 40 | 62% |
| 3 | Laboratory Sciences | 80 | 15 | 48 | 12 | 5 | 94% |
| 4 | Nursing Specialties | 52 | 0 | 8 | 18 | 26 | 50% |
| 5 | Pharmacy Specialties | 28 | 0 | 6 | 10 | 12 | 57% |
| 6 | Radiology/Imaging | 55 | 0 | 0 | 20 | 35 | 36% |
| 7 | Dentistry Specialties | 18 | 0 | 0 | 0 | 18 | 0% |
| 8 | Allied Health Professions | 105 | 4 | 7 | 8 | 86 | 18% |
| **TOTAL** | | **491** | **20** | **98** | **126** | **247** | **50%** |

**GULA Platform Strengths** (Coverage >80%):
- Laboratory Sciences (94%) — Core competency and primary value proposition
- Clinical Chemistry, Hematology, Microbiology, Histopathology
- Laboratory Informatics, Quality Management
- Security, Audit, Compliance Infrastructure

**GULA Platform Gaps** (Coverage <30%):
- Dentistry (0%) — No dental modules implemented
- Radiology/Imaging (36%) — Limited to general orders, no PACS/RIS
- Allied Health (18%) — Vast majority unimplemented
- Pharmacy Modules — No dedicated pharmacy system
- Rehabilitation Services — No PT/OT/SLP modules

---

## APPENDIX B: International Standards & Reference Frameworks

| Standard / Framework | Domain | GULA Alignment |
|----------------------|--------|----------------|
| **WHO International Classification of Diseases (ICD-11)** | Diagnosis coding | **Present** — ICD-10/ICD-11 terminology support via FHIR |
| **WHO International Classification of Functioning (ICF)** | Disability & function | **Missing** |
| **WHO International Classification of Health Interventions (ICHI)** | Procedure coding | **Missing** |
| **HL7 FHIR R4** | Health data exchange | **Complete** — FHIR routes, $expand/$lookup |
| **HL7 V2.x** | Legacy lab/hospital messaging | **Present** — Device bridge ASTM/HL7 |
| **DICOM** | Medical imaging | **Missing** |
| **LOINC** | Laboratory terminology | **Present** — Terminology service with LOINC |
| **SNOMED CT** | Clinical terminology | **Present** — Terminology service with SNOMED |
| **ISO 15189:2022** | Medical laboratory quality | **Present** — Quality management, IQCP, PT |
| **ISO 27001** | Information security | **Present** — Security framework |
| **HIPAA** | US privacy/security | **Present** — Consent, audit, encryption |
| **GDPR** | EU data protection | **Partial** — Consent management |
| **CAP Accreditation** | Pathology/lab accreditation | **Partial** — Quality module supports |
| **CLIA '88** | US lab regulation | **Present** — IQCP, QC management |
| **JCI** | Hospital accreditation | **Partial** — Quality, safety events |
| **ACR** | Radiology accreditation | **Missing** |
| **GA4GH** | Genomic data sharing | **Missing** |
| **IHE (Integrating the Healthcare Enterprise)** | Interoperability profiles | **Partial** — FHIR gateway |

---

## APPENDIX C: Recommendations (Committee Findings)

### Immediate Priorities (Months 1-6)

1. **Radiology Module (RIS/PACS)** — Highest gap given hospital management module exists. Add DICOM integration, structured reporting, and image management. Radiology orders flow through clinical orders but have no downstream system.

2. **Pharmacy Module** — Add medication management, CPOE enhancement, drug interaction checking (beyond basic CDS), BCMA support, and formulary management.

3. **Dental Module** — Starting with general dentistry charting, treatment planning, and integration with the hospital/patient management systems. Add dental terminology (FDI, ADA codes).

4. **Physical Therapy Module** — Add PT evaluation, treatment notes, therapeutic exercise library, functional outcome measures (FIM, WOMAC), and scheduling.

5. **Telemedicine Infrastructure** — Add video consultation, remote monitoring, tele-ICU, and telehealth-specific documentation.

### Medium Priority (Months 7-18)

1. **Genomic Medicine Integration** — GA4GH-compliant storage, VCF management, ACMG variant classification, ClinVar integration, pharmacogenomic CDS.

2. **Behavioral Health Module** — DSM-5/ICD-11 integrated assessment tools (PHQ-9, GAD-7, PCL-5), suicide risk engine, therapy note templates.

3. **EMS/Pre-Hospital Module** — Field data collection, ePCR, dispatch integration, hospital notification, trauma registry.

4. **Precision Medicine Platform** — Biomarker registry, targeted therapy decision support, clinical trial matching, multi-omics viewer.

5. **Rehabilitation (Allied Health) Platform** — Unified PT/OT/SLP module with assessment tools, plan of care, progress tracking, outcome measures.

### Long-Term Strategic (Months 18-36)

1. **P4 Medicine Platform** — Full predictive modeling, prevention tracking, personalization engine, patient participation tools.

2. **AI Diagnostic Assistant Expansion** — Radiology AI (CXR, mammography, CT), pathology AI (digital slides), dermatology AI, ophthalmology AI.

3. **Complete Social Determinants Module** — SDOH screening, community resource referral (Z-codes), food/pharmacy/housing/transportation, social prescribing.

4. **Population Health Command Center** — Real-time population dashboards, outbreak detection, risk stratification at scale, resource optimization.

5. **Planetary & One Health Module** — Zoonotic surveillance, antimicrobial resistance monitoring, climate-health impact tracking, cross-species registries.

---

## APPENDIX D: Methodology & Classification Criteria

### Coverage Classification Definitions

| Classification | Criteria | Implication |
|---------------|----------|-------------|
| **Complete** | Module exists with production-grade implementation, full test coverage, audit support, and international standard compliance | Ready for global deployment |
| **Present** | Module exists with core functionality, basic test coverage, and standard data models | Deployable with caveats; enrichment needed |
| **Partial** | Some components exist (e.g., data model, basic routes, or references in other modules) | Functional gaps; integration required |
| **Missing** | No code, models, routes, or services identified in the codebase | Needs new development |

### Committee Composition (Virtual)

| Role | Organization |
|------|-------------|
| Healthcare Domain Architect | WHO Digital Health |
| Clinical Standards Lead | HL7 International |
| Laboratory Medicine Advisor | CAP / CLSI |
| Health Informatics Professor | HIMSS Analytics |
| Hospital CEO Representative | Joint Commission International |
| Medical Education Dean | World Medical Association |
| Public Health Strategist | CDC / ECDC |
| Enterprise Architect | ISO/TC 215 |
| AI in Medicine Researcher | Nature Digital Medicine |
| Quality & Safety Officer | Institute for Healthcare Improvement |
| Nursing Informatics Lead | ICN / ANA |
| Pharmacy Informatics Director | ASHP |
| Radiology Informatics Chair | RSNA / SIIM |
| Dental Public Health Officer | FDI World Dental |
| Allied Health Dean | World Confederation for Physical Therapy |
| Genomic Medicine Lead | GA4GH / ACMG |
| Military Medicine Advisor | NATO Medical |

---

---

## APPENDIX E: Cross-Cutting Clinical Process Integration Analysis

This appendix maps GULA's ability to support end-to-end clinical processes that span multiple domains, specialties, and departments.

### E.1 Chronic Disease Management (Diabetes as Reference)

| Process Step | Department | GULA Module | Coverage |
|-------------|------------|-------------|----------|
| Diagnosis & Registration | Primary Care | Primary care encounter, Problem list | **Present** |
| Risk Stratification | Primary Care/Pop Health | Risk stratification model | **Present** |
| Lab Monitoring (HbA1c) | Laboratory | Lab order, result, trend | **Complete** |
| Medication Prescription | Pharmacy/Endo | Medication request | **Present** |
| Complications Screening | Ophthalmology/Nephrology | Orders for microalbumin, retinal exam | **Partial** |
| Dietary Counseling | Nutrition/Dietetics | Nutrition orders | **Partial** |
| Self-management Education | Patient Education | Patient education materials | **Partial** |
| Foot Exam Documentation | Podiatry/Primary Care | Clinical exam documentation | **Present** |
| Specialty Referral | Referral Network | Internal/external referral | **Present** |
| Population Registry | Population Health | Chronic disease registry | **Present** |
| Quality Measure (HbA1c <7%) | Quality | Quality indicator tracking | **Present** |
| Annual Review Due Reminder | Preventive Care | Reminder schedule | **Present** |
| Insulin Pump/CGM Data | Endocrinology | Continuous glucose data import | **Missing** |
| Telemedicine Follow-up | Telehealth | Remote visit | **Partial** |

### E.2 Cancer Care Pathway (Breast Cancer as Reference)

| Process Step | Department | GULA Module | Coverage |
|-------------|------------|-------------|----------|
| Screening (Mammogram) | Radiology/Preventive | Screening campaign, order | **Partial** |
| Abnormal Finding Tracking | Radiology/Breast | Abnormal result follow-up | **Partial** |
| Biopsy & Pathology | Pathology | Pathology result | **Present** |
| Staging | Oncology | Staging documentation | **Partial** |
| Multi-disciplinary Tumor Board | Multiple | Research registry | **Partial** |
| Surgical Treatment | Surgery | OT management | **Present** |
| Chemotherapy Planning | Medical Oncology | Chemotherapy protocol | **Missing** |
| Radiation Therapy Planning | Radiation Oncology | Radiation orders | **Missing** |
| Hormonal Therapy | Medical Oncology | Medication management | **Present** |
| Survivorship Care Plan | Oncology Survivorship | Care plan | **Partial** |
| Regular Surveillance | Multi-department | Follow-up schedule | **Present** |
| Genetic Counseling | Genetics | BRCA risk documentation | **Missing** |
| Palliative Care Integration | Palliative Care | Palliative consultation | **Missing** |
| Clinical Trial Enrollment | Research | Trial management | **Partial** |

### E.3 Acute Stroke Care Pathway

| Process Step | Department | GULA Module | Coverage |
|-------------|------------|-------------|----------|
| EMS Pre-notification | EMS/ED | Pre-hospital notification | **Missing** |
| ED Arrival & Triage | Emergency Medicine | ED triage documentation | **Missing** |
| Stroke Team Activation | Emergency/Neurology | Code alerting | **Missing** |
| CT Brain (non-contrast) | Radiology (CT) | Imaging order | **Partial** |
| NIHSS Assessment | Neurology | Stroke scale documentation | **Missing** |
| IV Thrombolysis Decision | Emergency/Neurology | CDS for tPA eligibility | **Missing** |
| Door-to-Needle Time Tracking | Quality | Time-stamped protocol | **Missing** |
| Mechanical Thrombectomy | Interventional Radiology | Interventional procedure | **Missing** |
| Admission to Stroke Unit | Inpatient (Neurology) | Bed assignment | **Present** |
| Dysphagia Screening | Speech-Language Pathology | Swallow screen | **Missing** |
| Secondary Prevention | Neurology/Preventive | Medication, risk factor | **Present** |
| Rehabilitation | PM&R/PT/OT/SLP | Rehab referral | **Missing** |
| Discharge & Follow-up | Case Management | Transition of care | **Present** |
| Stroke Registry | Quality/Research | Registry enrollment | **Partial** |

### E.4 Maternal Care Pathway

| Process Step | Department | GULA Module | Coverage |
|-------------|------------|-------------|----------|
| Pregnancy Confirmation | Primary Care/OB | Pregnancy record create | **Present** |
| Initial Prenatal Visit | OB | Antenatal care visit | **Present** |
| Prenatal Lab Screening | Laboratory | Lab orders (CBC, type/Rh, infectious) | **Complete** |
| Ultrasound/Anatomy Scan | Radiology (OB US) | Imaging order | **Partial** |
| Gestational Diabetes Screening | OB/Lab | OGTT, lab order | **Present** |
| Fetal Monitoring/NST | OB | Fetal surveillance documentation | **Missing** |
| Labor Admission | OB/ED | Admission documentation | **Partial** |
| Intrapartum Care (Partograph) | OB/Nursing | Labor progress documentation | **Missing** |
| Delivery Documentation | OB | Delivery record | **Present** |
| Newborn Assessment | Pediatrics | Newborn exam, APGAR, vitals | **Present** |
| Postpartum Care | OB | Postnatal care visit | **Present** |
| Breastfeeding Support | Lactation | Breastfeeding record | **Present** |
| Newborn Screening | Laboratory | Screening panel order | **Present** |
| Immunization (Birth) | Pediatrics | HepB, BCG, OPV documentation | **Present** |
| Postpartum Follow-up | OB | 6-week check | **Present** |
| Well-Child Schedule | Pediatrics | Well-child visit schedule | **Present** |

### E.5 Surgical Care Pathway

| Process Step | Department | GULA Module | Coverage |
|-------------|------------|-------------|----------|
| Pre-op H&P | Surgery/Anesthesia | Clinical documentation | **Present** |
| Surgical Consent | Surgery | Consent management | **Present** |
| Pre-op Orders | Anesthesia | Pre-op orders (NPO, labs, etc.) | **Present** |
| OR Scheduling | Surgery/OR | OT scheduling | **Present** |
| Surgical Time-Out | OR | Timeout documentation | **Missing** |
| Intra-operative Documentation | OR/Surgery | Op note | **Partial** |
| Anesthesia Record | Anesthesia | Anesthesia documentation | **Missing** |
| Specimen Management | Pathology | Specimen labeling/pathology result | **Present** |
| PACU Recovery | PACU/Nursing | Recovery documentation | **Partial** |
| Post-op Orders | Surgery | Post-op order set | **Present** |
| Pain Management | Surgery | Pain assessment, orders | **Partial** |
| Discharge Planning | Surgery/Case Management | Discharge summary | **Present** |
| Wound Check Follow-up | Surgery/Clinic | Follow-up appointment | **Present** |
| Surgical Site Infection Surveillance | Infection Control | Infection tracking | **Present** |
| Surgical Quality Registry | Quality | Registry enrollment | **Partial** |
| Post-operative VTE Prophylaxis | Surgery/Pharmacy | Prophylaxis orders | **Present** |

---

## APPENDIX F: Detailed Regulatory & Standards Compliance Matrix

| Regulation / Standard | Jurisdiction | Domain | GULA Readiness | Key Gaps |
|-----------------------|-------------|--------|----------------|----------|
| **HIPAA Privacy Rule (45 CFR 164)** | USA | Health privacy | **Present** | Full BAAs support |
| **HIPAA Security Rule (45 CFR 164)** | USA | Health security | **Present** | Encryption, audit controls |
| **HIPAA Breach Notification Rule** | USA | Breach response | **Partial** | Automated notification workflow |
| **HITECH Act** | USA | Health IT | **Present** | Meaningful use measures |
| **21 CFR Part 11** | USA | Electronic records/signatures | **Present** | Audit trail, electronic signatures |
| **CLIA '88** | USA | Laboratory certification | **Present** | IQCP, QC, PT |
| **CAP Laboratory Accreditation** | USA/Global | Lab quality | **Partial** | Full CAP checklist items |
| **FDA 21 CFR 820 (QSR)** | USA | Medical device | **Missing** | Not applicable to LIMS |
| **EU GDPR** | Europe | Data protection | **Partial** | Full DPO workflow, data portability |
| **EU IVDR 2017/746** | Europe | In vitro diagnostics | **Missing** | Performance evaluation reporting |
| **UK Data Protection Act 2018** | UK | Data protection | **Partial** | UK-specific DPO |
| **KSA NPHIES** | Saudi Arabia | Health claims | **Missing** | Claim formatting, eligibility |
| **UAE DOH / DHA Standards** | UAE | Healthcare regulation | **Missing** | Local licensing, coding |
| **Iraqi MOH Standards** | Iraq | National health | **Present** | SNDHS integration active |
| **Jordan Hakeem Program** | Jordan | National HIE | **Missing** | HIE connectivity |
| **Canadian PIPEDA** | Canada | Privacy | **Partial** | Consent framework adaptable |
| **Australian My Health Record** | Australia | National EHR | **Missing** | HIE connectivity |
| **Singapore NEHR** | Singapore | National EHR | **Missing** | HIE connectivity |
| **ISO 27001:2022** | Global | Information security | **Present** | ISMS framework |
| **ISO 27799** | Global | Health informatics security | **Present** | Aligned with 27001 |
| **ISO 15189:2022** | Global | Lab quality | **Present** | Quality framework |
| **ISO 15190:2020** | Global | Lab safety | **Missing** | Safety management |
| **ISO 22870** | Global | POCT | **Partial** | POC coordinator role |
| **ISO 80001-1** | Global | Medical IT networks | **Partial** | Risk management for IT networks |
| **IEC 62304** | Global | Medical device software | **Partial** | Software lifecycle |
| **IEC 82304-1** | Global | Health software | **Partial** | General health software safety |
| **ISO 13485** | Global | Quality management | **Missing** | Medical device QMS |
| **ISO 14971** | Global | Risk management | **Partial** | Risk management for software |
| **ISO 27789** | Global | Audit trails for EHR | **Present** | Comprehensive audit log |
| **ISO 13606** | Global | EHR communication | **Missing** | Archetype-based exchange |
| **ISO 12967 (HISA)** | Global | Healthcare architecture | **Partial** | Service-oriented architecture |
| **ISO 22600** | Global | Privilege management | **Present** | RBAC/ABAC |
| **ISO 21298** | Global | Identity management | **Present** | Identity infrastructure |
| **NIST SP 800-53** | USA | Security controls | **Present** | NIST framework alignment |
| **NIST Cybersecurity Framework** | USA | Cyber resilience | **Present** | Tiers, profiles |
| **SOC 2 Type II** | USA | Service organization | **Partial** | Full readiness for audit |
| **HITRUST CSF** | USA | Security framework | **Partial** | MRA alignment |
| **ONC 2015 Edition** | USA | EHR certification | **Partial** | API certification criteria |
| **WADA Code** | Global | Anti-doping | **Missing** | Doping control |
| **NATO STANAG 6027** | NATO | Military health | **Missing** | NATO medical reporting |
| **WHO International Health Regulations** | Global | Public health | **Partial** | IHR reporting |
| **WHO SCORE** | Global | Health data | **Partial** | Data quality metrics |

---

## APPENDIX F: Module-by-Module Evidence Inventory

This appendix catalogues every identifiable software module, route file, model, and service in the GULA codebase with its global healthcare domain alignment.

### F.1 Core Application Structure (`backend/app/`)

| File/Module | Domain Alignment | Phase | Coverage |
|-------------|------------------|-------|----------|
| `main.py` | Platform core / middleware | ALL | Complete |
| `config.py` | Platform configuration | ALL | Complete |
| `database.py` | Data persistence | ALL | Complete |
| `worker.py` | Background processing | ALL | Complete |
| `_compat.py` | Compatibility layer | ALL | Complete |

### F.2 Route Modules (`backend/app/routes/`)

| Route Module | Healthcare Domain | Phase | Lines | Coverage |
|-------------|-------------------|-------|-------|----------|
| `admin.py` | System administration | ALL | ~400 | Complete |
| `ai.py` | Clinical AI / Digital Health | 1 | ~200 | Present |
| `ai_telemetry.py` | AI Monitoring | 1 | ~150 | Present |
| `batch.py` | Batch operations | ALL | ~100 | Present |
| `canonical_patient.py` | MPI / Patient Identity | 1 | ~300 | Present |
| `care_continuum.py` | Primary Care / Public Health / Community | 1 | ~1016 | Present |
| `citizen_portal.py` | Citizen Health / Patient Portal | 1 | ~200 | Present |
| `claims.py` | Insurance / Health Financing | 1 | ~300 | Present |
| `clinical.py` | Clinical Knowledge / CDS / Quality / Research | 1 | ~1324 | Present |
| `clinical_documentation.py` | Clinical Documentation | 1 | ~369 | Present |
| `clinical_orders.py` | CPOE / Order Management | 1 | ~325 | Present |
| `clinical_quality.py` | Quality Management | 1 | ~200 | Present |
| `compliance.py` | Regulatory Compliance | ALL | ~200 | Present |
| `consent.py` | Patient Consent / Privacy | 1 | ~150 | Present |
| `critical_alerts.py` | Critical Value Alerting | 3 | ~150 | Present |
| `dashboard.py` | Analytics Dashboard | ALL | ~100 | Present |
| `device_results.py` | Device Integration (LIS) | 3 | ~100 | Present |
| `edge.py` | Edge Computing / Offline | 1 | ~200 | Present |
| `ehr.py` | Electronic Health Record | 1 | ~2072 | Present |
| `ehr_fhir.py` | FHIR API / Interoperability | 1 | ~300 | Present |
| `hospital.py` | Hospital Management | 1 | ~793 | Present |
| `id_scan.py` | Identity Scanning | ALL | ~50 | Present |
| `identity.py` | Identity Management | ALL | ~200 | Present |
| `insurance.py` | Insurance Management | 1 | ~150 | Present |
| `integrations.py` | Third-party Integration | ALL | ~200 | Present |
| `labs.py` | Laboratory Administration | 3 | ~231 | Complete |
| `login.py` | Authentication | ALL | ~300 | Complete |
| `metrics.py` | System Metrics | ALL | ~100 | Complete |
| `mfa.py` | Multi-factor Authentication | ALL | ~200 | Complete |
| `mobile.py` | Mobile Health / mHealth | 1 | ~300 | Present |
| `national_data.py` | National Health Data | 1 | ~400 | Present |
| `national_identity.py` | National ID Integration | 1 | ~200 | Present |
| `national_streaming.py` | National Health Streaming | 1 | ~100 | Present |
| `notifications.py` | Notification Service | ALL | ~200 | Present |
| `oauth2.py` | OAuth2 Provider | ALL | ~400 | Complete |
| `optimizer.py` | System Optimization | ALL | ~100 | Present |
| `password_reset.py` | Password Management | ALL | ~100 | Complete |
| `patient_card.py` | Patient Card / QR | 1 | ~200 | Present |
| `patients.py` | Patient Management | 1 | ~400 | Complete |
| `qr.py` | QR Code Generation | 1 | ~50 | Present |
| `quality_control.py` | Lab QC | 3 | ~200 | Complete |
| `register.py` | User Registration | ALL | ~100 | Complete |
| `results.py` | Lab Results / Orders | 3 | ~379 | Complete |
| `saml.py` | SAML SSO | ALL | ~300 | Complete |
| `samples.py` | Sample Management | 3 | ~217 | Complete |
| `security.py` | Security Settings | ALL | ~200 | Complete |
| `service_accounts.py` | Service Account Management | ALL | ~200 | Complete |
| `setup.py` | Initial Setup | ALL | ~100 | Complete |
| `stats.py` | Statistics / Analytics | 1 | ~300 | Present |
| `test_results.py` | Public Test Results | 3 | ~100 | Present |
| `tiers.py` | Subscription Tiers | 1 | ~100 | Present |

### F.3 Model Modules (`backend/app/models/`)

| Model | Clinical Entity | Phase | Coverage |
|-------|----------------|-------|----------|
| `ai_interaction.py` | AI/ML Interaction Log | 1 | Present |
| `audit_log.py` | Audit Trail | ALL | Complete |
| `base.py` | Base Declarative | ALL | Complete |
| `canonical_patient.py` | Master Patient Index | 1 | Present |
| `claim.py` | Insurance Claim | 1 | Present |
| `consent.py` | Patient Consent | 1 | Present |
| `edge.py` | Edge Device | 1 | Present |
| `lab_order.py` | Lab Order | 3 | Complete |
| `lab_result.py` | Lab Result | 3 | Complete |
| `lab_user.py` | Lab User/Staff | ALL | Complete |
| `lab.py` | Laboratory | 3 | Complete |
| `mfa_device.py` | MFA Device | ALL | Complete |
| `oauth2_client.py` | OAuth2 Client | ALL | Complete |
| `oauth2_token.py` | OAuth2 Token | ALL | Complete |
| `organization.py` | Organization | ALL | Present |
| `outbox.py` | Outbox Pattern | ALL | Complete |
| `patient.py` | Patient | 1 | Complete |
| `quality_control.py` | QC Data | 3 | Complete |
| `sample.py` | Specimen | 3 | Complete |
| `service_account.py` | Service Account | ALL | Complete |
| `subscription.py` | Subscription | 1 | Present |
| `test_result.py` | Test Result | 3 | Complete |
| `test_type.py` | Test Catalog | 3 | Complete |
| `user.py` | User | ALL | Complete |

### F.4 Service Modules (`backend/app/services/`)

| Service Module | Function | Phase | Coverage |
|----------------|----------|-------|----------|
| `ali_reza_engine.py` | Clinical Intelligence Engine | 1 | Present |
| `audit_service.py` | Audit Logging | ALL | Complete |
| `care_continuum_service.py` | Care Continuum Operations | 1 | Present |
| `claims_service.py` | Claims Processing | 1 | Present |
| `clinical_engine.py` | Clinical Decision Engine | 1 | Present |
| `clinical_intelligence.py` | Clinical AI/Intelligence | 1 | Present |
| `clinical_service.py` | Clinical Service Layer | 1 | Present |
| `clinical_state.py` | Clinical State Management | 1 | Present |
| `consent_service.py` | Consent Management | 1 | Present |
| `critical_alerts.py` | Critical Value Alerts | 3 | Present |
| `data_platform_service.py` | Data Platform Integration | 1 | Present |
| `device_trust_service.py` | Device Trust/Security | 1 | Present |
| `ehr_service.py` | EHR Operations | 1 | Present |
| `epidemiology.py` | Public Health Epidemiology | 1 | Present |
| `hospital_service.py` | Hospital Operations | 1 | Present |
| `identity_matching.py` | Patient Identity Matching | 1 | Present |
| `identity.py` | Identity Service | ALL | Present |
| `interpretation.py` | Result Interpretation | 3 | Present |
| `national_id.py` | National ID Service | 1 | Present |
| `offline_sync_service.py` | Offline Sync | 1 | Present |
| `order_service.py` | Order Management | 3 | Complete |
| `outbox_service.py` | Event Outbox | ALL | Complete |
| `patient_card.py` | Patient Card Generation | 1 | Present |
| `patient_service.py` | Patient Service | 1 | Complete |
| `pdf_report.py` | PDF Generation | ALL | Present |
| `risk_based_auth_service.py` | Risk-based Authentication | ALL | Present |
| `samir_engine.py` | SAMIR AI Engine | 1 | Present |

### F.5 Supporting Packages

| Package | Modules | Domain | Coverage |
|---------|---------|--------|----------|
| `app/ai/` | approval, guardrails, sandbox, system_optimizer | Clinical AI | Present |
| `app/clinical/` | cds, knowledge, quality, research, terminology | Clinical Knowledge | Present |
| `app/ehr/` | allergy, attachment, care_plan, clinical_note, clinical_summary, family_history, immunization, medication, risk_factor, social_history, timeline | Electronic Health Record | Present |
| `app/care_continuum/` | care_journey, chronic_disease, immunization, maternal, patient_tasks, primary_care, public_health, referral | Care Continuum / Public Health | Present |
| `app/hospital/` | Hospital hierarchical models (bed, campus, department, etc.) | Hospital Management | Present |
| `app/edge/` | config, governance, identity, maintenance, policy, registry, scheduler, telemetry, trust | Edge Computing | Present |
| `app/security/` | abac, auth, consent_dep, dependencies, encryption, intrusion_detection, mfa_service, oauth2_provider, rate_limit, rbac, redis_client, saml_service, service_accounts, session | Security Infrastructure | Complete |
| `app/financial/` | pricing, ranking | Financial Engine (Phase A) | Partial |
| `app/audit/` | audit_log | Audit Management | Complete |
| `app/notifications/` | service, telegram | Notification Service | Present |
| `app/firewall/` | api_firewall | API Security | Present |
| `app/gateways/` | cloudflare_gateway, google_ai, insurance_gateway, lab_device_gateway, mode, national_identity_gateway, residency_gateway | Integration Gateways | Present |
| `app/legal/` | consent | Legal/Compliance | Present |
| `app/tasks/` | queue, registry, schema, worker | Background Tasks | Present |
| `app/core/` | auto_repair, cache_manager, decision_guard, events, feature_flags, idempotency, kill_switch, logging_config, policy_engine, resilience, risk_engine, runtime_guard, self_healing, sndhs_flags, startup_guard | Core Infrastructure | Complete |

---

## APPENDIX G: Clinical Workflow Coverage by Care Setting

### G.1 Ambulatory / Outpatient Care

| Workflow Step | Required Module | GULA Coverage | Priority |
|---------------|----------------|---------------|----------|
| Patient Registration | Patient demographics, insurance capture | **Complete** | Must have |
| Appointment Scheduling | Calendar, provider availability, online booking | **Present** | Must have |
| Pre-visit (intake) | Chief complaint, vitals, medication reconciliation | **Present** | Must have |
| Clinical Documentation | HPI, PE, assessment, plan (SOAP) | **Present** | Must have |
| Order Entry (lab/imaging) | CPOE, lab orders, imaging orders | **Complete** | Must have |
| Prescription (e-Rx) | Medication orders, e-prescribing | **Present** | Must have |
| Procedure Documentation | Minor procedures, injections, wound care | **Partial** | Should have |
| Referral Management | Internal/external referral, prior authorization | **Present** | Must have |
| Patient Instructions | After-visit summary, patient education | **Partial** | Should have |
| Coding & Billing | ICD-10, CPT, E&M coding | **Present** | Must have |
| Preventive Care Reminders | Due for screening, due for immunization | **Present** | Should have |
| Patient Portal Access | Results, messaging, appointment request | **Present** | Must have |

### G.2 Inpatient / Hospital Care

| Workflow Step | Required Module | GULA Coverage | Priority |
|---------------|----------------|---------------|----------|
| Admission | Registration, insurance verification, consent | **Present** | Must have |
| Bed Management | Bed assignment, transfer, discharge tracking | **Complete** | Must have |
| Nursing Documentation | Flowsheets, nursing notes, MAR | **Partial** | Must have |
| Provider Documentation | H&P, progress notes, discharge summary | **Present** | Must have |
| CPOE (all order types) | Medications, labs, imaging, nursing, dietary | **Present** | Must have |
| Medication Administration | Barcode scanning, eMAR, pump integration | **Missing** | Must have |
| Critical Care Flowsheets | Ventilator, hemodynamics, I/O, drips | **Missing** | Should have |
| OR Management | Scheduling, intraoperative documentation | **Present** | Must have |
| Anesthesia Records | Pre-op, intra-op, PACU documentation | **Missing** | Should have |
| Consultations | Specialty consult workflow, documentation | **Partial** | Should have |
| Discharge Planning | Discharge summary, medication reconciliation | **Present** | Must have |
| Case Management | Utilization review, care coordination | **Partial** | Should have |
| Quality Measures | Core measures, VBP, readmission reduction | **Present** | Must have |

### G.3 Laboratory Workflow

| Workflow Step | Required Module | GULA Coverage | Priority |
|---------------|----------------|---------------|----------|
| Test Ordering | Provider order, standing order, protocol-based | **Complete** | Must have |
| Specimen Collection | Labeling, phlebotomy, tube type, transport | **Complete** | Must have |
| Specimen Receipt | Accessioning, scanning, rejection criteria | **Complete** | Must have |
| Result Entry | Manual, instrument interface, batch | **Complete** | Must have |
| Result Verification | Technical, clinical, autoverification | **Present** | Must have |
| Critical Value Reporting | Alerting, read-back, escalation | **Complete** | Must have |
| Quality Control | Levey-Jennings, Westgard rules, lot tracking | **Complete** | Must have |
| Proficiency Testing | Registration, result submission, performance | **Present** | Must have |
| Reference Lab Send-out | External lab interface, resulting | **Partial** | Should have |
| Instrument Interface | ASTM/HL7 unidirectional and bidirectional | **Present** | Must have |
| Microbiology Workflow | Culture, sensitivity, result cascading | **Present** | Must have |
| Blood Bank Workflow | Type and screen, crossmatch, component | **Present** | Must have |
| Anatomic Pathology | Gross description, block/slide tracking | **Partial** | Should have |

### G.4 Emergency Department Workflow

| Workflow Step | Required Module | GULA Coverage | Priority |
|---------------|----------------|---------------|----------|
| Triage | ESI/CTAS scoring, chief complaint, acuity | **Missing** | Must have |
| Registration / Quick Reg | Fast registration for critical patients | **Partial** | Must have |
| ED Tracking Board | Visual status of all ED patients, wait times | **Missing** | Must have |
| Provider Evaluation | ED-specific charting templates | **Partial** | Must have |
| Orders (ED-specific) | Rapid lab orders, STAT imaging | **Present** | Must have |
| Trauma Documentation | Trauma activation, timestamps, injury scores | **Missing** | Should have |
| Stroke/STEMI Protocols | Time-stamped protocol compliance | **Missing** | Should have |
| Observation Management | Observation status, time tracking | **Missing** | Should have |
| Disposition | Admit, discharge, transfer, AMA | **Partial** | Must have |
| ED Discharge Instructions | Condition-specific instructions, follow-up | **Partial** | Should have |
| EMS Integration | ePCR data, pre-hospital EKG, radio log | **Missing** | Nice to have |
| Disaster/MCI Module | Mass casualty tracking, resource allocation | **Missing** | Nice to have |

---

## APPENDIX H: ICD-11 Chapter Mapping & GULA Coverage

| ICD-11 Chapter | Description | GULA Coverage |
|----------------|-------------|---------------|
| 01 | Certain infectious or parasitic diseases | **Present** – ID, Microbiology |
| 02 | Neoplasms | **Present** – Oncology, Pathology |
| 03 | Diseases of the blood or blood-forming organs | **Present** – Hematology |
| 04 | Diseases of the immune system | **Present** – Immunology |
| 05 | Endocrine, nutritional or metabolic diseases | **Present** – Endocrinology |
| 06 | Mental, behavioral or neurodevelopmental disorders | **Partial** – No MH module |
| 07 | Sleep-wake disorders | **Missing** |
| 08 | Diseases of the nervous system | **Partial** – General neurology |
| 09 | Diseases of the visual system | **Partial** – Ophthalmology |
| 10 | Diseases of the ear or mastoid process | **Missing** |
| 11 | Diseases of the circulatory system | **Present** – Cardiology |
| 12 | Diseases of the respiratory system | **Present** – Pulmonology |
| 13 | Diseases of the digestive system | **Present** – GI |
| 14 | Diseases of the skin | **Present** – Dermatology |
| 15 | Diseases of the musculoskeletal system or connective tissue | **Present** – Ortho/Rheum |
| 16 | Diseases of the genitourinary system | **Present** – Nephro/Uro |
| 17 | Conditions related to sexual health | **Missing** |
| 18 | Pregnancy, childbirth or the puerperium | **Present** – OB |
| 19 | Certain conditions originating in the perinatal period | **Present** – NICU |
| 20 | Developmental anomalies | **Present** – Genetics/Path |
| 21 | Symptoms, signs or clinical findings, not elsewhere classified | **Present** – General |
| 22 | Injury, poisoning or certain other consequences of external causes | **Present** – ER/Surgery |
| 23 | External causes of morbidity or mortality | **Present** – Public Health |
| 24 | Factors influencing health status or contact with health services | **Present** – Care Continuum |
| 25 | Codes for special purposes | **Present** – Research |
| 26 | Traditional medicine conditions – Module I | **Missing** |
| V | Supplementary section for functioning assessment | **Missing** |
| X | Extension codes | **Present** – Terminology |

---

## APPENDIX I: GULA Platform Competitive Position by Global Region

| Region | Healthcare System Type | Key Interoperability Standards | GULA Fit | Recommended Adaptations |
|--------|----------------------|-------------------------------|----------|------------------------|
| **Iraq (Home Market)** | Public/Private mix (MOH, KRG) | SNDHS, Iraqi MOH | **Excellent** — Native SNDHS, Arabic-first | Deploy as-is |
| **Saudi Arabia** | Public (MOH) + Private | NPHIES, Sehhaty, Wasfaty | **Good** — Add NPHIES claim format | Claims adapter, CDA |
| **UAE** | Public (SEHA, DHA) + Private | DOH Standards, Malaffi, Riayati | **Good** — FHIR-native | Local HIE adapters |
| **Qatar** | Public (PHCC, HMC) + Private | Qatar HIE standards | **Good** — FHIR-native | HIE integration |
| **Kuwait** | Public (MOH) | Kuwait MOH standards | **Good** — FHIR-native | MOH reporting |
| **Oman** | Public (MOH) | Oman MOH standards | **Good** | MOH reporting adaptation |
| **Bahrain** | Public (MOH) + Private | Bahrain iSeha | **Good** | NHRA compliance |
| **Jordan** | Public (MOH) + Private | Hakeem, CDA | **Good** | HIE adapter, CDA |
| **Egypt** | Public (MOH) + Private | Egyptian HIE | **Good** | HIE adapter |
| **Morocco** | Public (MOH) | RAMED, Sehati | **Good** | French localization |
| **Tunisia** | Public (MOH) | CNSS, CNAM | **Good** | French localization |
| **Algeria** | Public | CNAS, CASNOS | **Good** | French localization |
| **GCC States (Collective)** | Public/Private mix | GCC HIE, NPHIES-like | **Good** | Multi-tenant |
| **Sub-Saharan Africa** | Public (MOH, vertical programs) | DHIS2, OpenMRS, FHIR | **Good** — Edge platform sync | DHIS2 integration, OpenMRS adapter, offline-first |
| **Southeast Asia** | Mixed public/private | various national HIE | **Fair** | Localization for each nation |
| **South Asia (India)** | Public (Ayushman Bharat) | ABDM, FHIR, HCX | **Good** — FHIR native | ABDM integration, HCX adapter |
| **Pakistan** | Public/Private | DHIS2, national ID | **Good** | NADRA integration |
| **United Kingdom** | Public (NHS) | NHS FHIR, SNOMED, DM+D | **Good** | NHS England API |
| **Continental Europe** | Social health insurance | FHIR, IHE, XDS, ELGA, e-Health | **Fair** | XDS integration |
| **North America (USA)** | Private insurance, Medicare/Medicaid | FHIR, C-CDA, X12, NCPDP | **Fair** | X12 claims, C-CDA |
| **Canada** | Provincial public | FHIR, pan-Canadian standards | **Fair** | Provincial HIE adapters |

---

## APPENDIX J: Clinical AI & Intelligence Capability Catalog

| AI Capability | Description | GULA Current State | Future Potential |
|---------------|-------------|-------------------|-----------------|
| **Clinical Copilot** | AI-assisted clinical reasoning, differential diagnosis, care suggestions | **Present** (`/ai/copilot`) | Full differential generator |
| **Risk Prediction** | Disease/event risk modeling using patient data | **Present** (`/ai/risk-prediction`) | Multi-disease risk, polygenic risk |
| **Care Gap Detection** | Identify missing preventive/screening care | **Present** (`/ai/care-gaps`) | Automated patient outreach |
| **Diagnostic Assistant** | Symptom-based diagnostic decision support | **Present** (`/ai/diagnostic-assistant`) | Specialty-specific triage |
| **Explainability Engine** | AI decision explanation for clinical trust | **Present** (`/ai/explain`) | Counterfactual explanations |
| **Retina Screening AI** | Diabetic retinopathy detection | **Missing** | OphthAI integration |
| **Radiology AI** | Chest X-ray, mammography, CT interpretation | **Missing** | FDA-cleared CAD integration |
| **Pathology AI** | Digital slide interpretation | **Missing** | WSI analysis |
| **Dermatology AI** | Skin lesion classification | **Missing** | Dermoscopy analysis |
| **ECG AI** | ECG interpretation and arrhythmia detection | **Missing** | Real-time rhythm analysis |
| **Sepsis Prediction** | Early sepsis detection algorithm | **Missing** | EMR-integrated sepsis alert |
| **Deterioration Index** | Patient deterioration early warning | **Missing** | Modified early warning score (MEWS) |
| **Drug Interaction AI** | Advanced drug-drug, drug-gene, drug-food interaction | **Present** (Basic) | Full PharmGKB integration |
| **Clinical Trial Matching** | AI matching patients to available trials | **Missing** | Trial.protocol integration |
| **NLP / Clinical Language** | Medical text extraction and coding | **Missing** | ICD-10/SNOMED coding from notes |
| **Predictive Scheduling** | No-show prediction, resource optimization | **Missing** | Machine learning scheduling |
| **Fraud Detection** | Healthcare billing fraud identification | **Missing** | Claim anomaly detection |
| **Population Risk Stratification** | Population-level risk scoring | **Present** (Basic) | Claims + clinical risk modeling |
| **AI Transcription** | Ambient clinical documentation | **Missing** | Medical speech recognition |
| **Clinical Summarization** | Automated summary generation from notes | **Missing** | Support handoff, discharge |

---

## APPENDIX K: Multi-language & Localization Requirements

| Region | Language | Required | GULA Status |
|--------|----------|----------|-------------|
| Iraq (Home) | Arabic (ar-IQ), Kurdish (ckb) | **Required** | **Arabic (ar-IQ) — Complete**, Kurdish planned |
| KSA | Arabic (ar-SA) | Required | Present (Arabic variants compatible) |
| UAE | Arabic (ar-AE), English | Required | Present |
| Kuwait | Arabic (ar-KW), English | Required | Present |
| Qatar | Arabic (ar-QA), English | Required | Present |
| Egypt | Arabic (ar-EG) | Required | Present |
| Jordan | Arabic (ar-JO) | Required | Present |
| Morocco | Arabic (ar-MA), French (fr) | Required | French missing |
| Tunisia | Arabic (ar-TN), French (fr) | Required | French missing |
| Algeria | Arabic (ar-DZ), French (fr) | Required | French missing |
| UK | English (en-GB) | Required | English present |
| USA | English (en-US) | Required | English present |
| India | English (en-IN), Hindi (hi) | Required | Hindi missing |
| Pakistan | Urdu (ur), English | Required | Urdu missing |
| Malaysia | Malay (ms) | Required | Malay missing |
| Indonesia | Indonesian (id) | Required | Indonesian missing |
| Turkey | Turkish (tr) | Required | Turkish missing |
| Iran | Farsi/Persian (fa) | Required | Farsi missing |
| France | French (fr-FR) | Required | French missing |
| Germany | German (de-DE) | Required | German missing |

---

## APPENDIX L: Laboratory Test Catalog Coverage

The GULA platform supports a comprehensive test catalog. Below is a representative sample of the depth of laboratory test coverage available:

| Test Category | Example Tests | GULA Coverage |
|---------------|---------------|---------------|
| **Complete Blood Count** | WBC, RBC, Hgb, Hct, MCV, MCH, MCHC, RDW, Plt, MPV, PDW, Differential (Neut, Lymph, Mono, Eos, Baso) | **Complete** |
| **Comprehensive Metabolic Panel** | Glucose, BUN, Creatinine, eGFR, Na, K, Cl, CO2, Ca, TP, Alb, Glob, A/G, TBili, DBili, ALP, ALT, AST | **Complete** |
| **Renal Function Panel** | BUN, Creat, eGFR, Na, K, Cl, CO2, Ca, Phos, Mg, Uric Acid | **Complete** |
| **Hepatic Function Panel** | TBili, DBili, IBili, ALP, ALT, AST, GGT, TP, Alb, Glob, A/G, PT | **Complete** |
| **Lipid Panel** | Total Chol, HDL, LDL (calculated), LDL (direct), VLDL, Trig, Non-HDL Chol, ApoA1, ApoB, Lp(a) | **Complete** |
| **Thyroid Panel** | TSH, T4 (Free, Total), T3 (Free, Total), T3 Uptake, FTI, Anti-TPO, Anti-Tg | **Complete** |
| **Coagulation** | PT, aPTT, INR, Fibrinogen, D-Dimer, AT-III, Protein C, Protein S, Factor Activity Assays | **Present** |
| **Cardiac Markers** | Troponin I/T, CK-MB, Myoglobin, BNP, NT-proBNP, hs-CRP, Lp-PLA2 | **Present** |
| **Iron Studies** | Serum Iron, TIBC, UIBC, %Saturation, Ferritin, Transferrin, sTfR, Hepcidin | **Present** |
| **Diabetes** | Glucose (fasting/random), HbA1c, Microalbumin, Urine ACR, OGTT, Insulin, C-peptide, β-Hydroxybutyrate | **Complete** |
| **Hepatitis Panel** | HBsAg, HBsAb, HBcAb (IgM, Total), HBeAg, HBeAb, HBV DNA | **Present** |
| **HIV** | HIV 1/2 Ab/Ag Combo, HIV RNA, CD4 Count, HIV Genotype | **Present** |
| **Autoimmune** | ANA (pattern, titer), Anti-dsDNA, ENA (Sm, RNP, Ro/SSA, La/SSB, Scl-70, Jo-1), RF, Anti-CCP, ANCA (MPO, PR3), C3, C4, CH50 | **Present** |
| **Tumor Markers** | PSA (Total, Free), CA-125, CA 19-9, CA 15-3, CEA, AFP, HCG (Quant), β2M, HE4, ROMA | **Present** |
| **Therapeutic Drug Monitoring** | Digoxin, Lithium, Valproate, Phenytoin, Carbamazepine, Phenobarbital, Vancomycin, Gentamicin, Tobramycin, Cyclosporine, Tacrolimus, Sirolimus, Everolimus, Methotrexate | **Present** |
| **Urinalysis** | Dipstick (pH, SG, Leu, Nit, Prot, Gluc, Ket, Urob, Bili, Blood), Microscopy (RBC, WBC, Casts, Crystals, Bacteria, Yeast), Microalbumin, Creatinine, Protein, ACR | **Complete** |
| **Infectious Disease Serology** | EBV (VCA IgM/IgG, EA, EBNA), CMV IgM/IgG, Toxoplasma, Rubella, Measles, Mumps, Varicella, RPR, VDRL, TPHA, Lyme | **Present** |
| **CSF Analysis** | Cell Count, Differential, Glucose, Protein, LDH, Culture, Oligoclonal Bands, IgG Index, Albumin Index | **Present** |
| **Body Fluid Analysis** | Cell Count, Differential, Total Protein, LDH, Glucose, pH, Amylase, Triglyceride | **Present** |

---

## APPENDIX M: FHIR Resource Coverage

| FHIR R4 Resource | GULA Implementation | Endpoint |
|------------------|---------------------|----------|
| **Patient** | **Complete** | `routes/patients.py`, `routes/ehr.py` |
| **Practitioner** | **Present** | `models/lab_user.py` |
| **PractitionerRole** | **Present** | User roles/privileges |
| **Organization** | **Present** | `models/organization.py` |
| **HealthcareService** | **Partial** | Hospital services |
| **Location** | **Complete** | Hospital hierarchy (campus, building, floor, room) |
| **Encounter** | **Present** | `routes/care_continuum.py`, `routes/ehr.py` |
| **Condition** | **Present** | `routes/ehr.py` — Problem list |
| **Observation** | **Complete** | `models/lab_result.py`, `routes/results.py` |
| **DiagnosticReport** | **Complete** | Lab result reporting |
| **Specimen** | **Complete** | `routes/samples.py`, `models/sample.py` |
| **MedicationRequest** | **Present** | `routes/ehr.py` — Medication orders |
| **MedicationAdministration** | **Present** | EHR medication administration |
| **MedicationStatement** | **Present** | Medication list |
| **AllergyIntolerance** | **Present** | `app/ehr/models/allergy.py` |
| **Immunization** | **Present** | `routes/care_continuum.py`, EHR immunization |
| **CarePlan** | **Present** | `routes/care_continuum.py` |
| **CareTeam** | **Present** | Care team composition |
| **Provenance** | **Present** | Audit log tracking |
| **AuditEvent** | **Complete** | `models/audit_log.py` |
| **Consent** | **Present** | `models/consent.py`, `routes/consent.py` |
| **Goal** | **Present** | `routes/care_continuum.py` — Goals in care plans |
| **ClinicalImpression** | **Present** | Clinical documentation |
| **Communication** | **Present** | Notifications, messaging |
| **FamilyMemberHistory** | **Present** | EHR family history |
| **Procedure** | **Present** | Clinical orders, procedures |
| **Appointment** | **Present** | `routes/hospital.py` |
| **Schedule** | **Partial** | Appointment scheduling |
| **Slot** | **Partial** | Time slot management |
| **Questionnaire** | **Missing** | Patient-reported outcomes |
| **QuestionnaireResponse** | **Missing** | Survey responses |
| **RiskAssessment** | **Present** | `routes/ai.py` — Risk prediction |
| **ResearchStudy** | **Present** | Research registries |
| **Substance** | **Present** | Medications, vaccines |
| **MedicationDispense** | **Partial** | Limited pharmacy workflow |
| **SupplyRequest** | **Missing** | Inventory management |
| **SupplyDelivery** | **Missing** | Supply tracking |
| **DetectedIssue** | **Present** | CDS alerts |
| **Flag** | **Present** | Patient alerts, flags |
| **RelatedPerson** | **Present** | Next of kin, contacts |
| **Person** | **Present** | Patient/person deduplication |
| **Coverage** | **Present** | Insurance, claims |
| **Claim** | **Present** | Claims processing |
| **ExplanationOfBenefit** | **Present** | EOB management |

---

## APPENDIX N: Emergency Codes & Patient Safety Framework

| Safety Domain | GULA Module | Coverage |
|---------------|-------------|----------|
| **Patient Identification** | Positive patient ID (QR/barcode scanner) | **Present** — `routes/id_scan.py` |
| **Hand Hygiene** | No specific module | **Missing** |
| **Medication Safety** | Drug-drug interaction check, allergy check | **Present** — CDS module |
| **Surgical Safety** | WHO Surgical Safety Checklist | **Missing** |
| **Fall Prevention** | Bed/patient mobility assessment | **Missing** |
| **Pressure Ulcer Prevention** | Braden scale, skin assessment | **Missing** |
| **Sepsis Management** | Early warning, sepsis bundles | **Partial** — Critical alerts |
| **Code Blue (Cardiac Arrest)** | Code documentation | **Missing** |
| **Code Stroke** | Stroke protocol documentation | **Missing** |
| **Code Sepsis** | Sepsis protocol documentation | **Missing** |
| **Rapid Response Team** | MEWS/EWS early warning scoring | **Missing** |
| **Patient Transfers** | Bed-to-bed, facility transfer | **Present** — `routes/hospital.py` |
| **Critical Values** | Lab critical value alerting | **Complete** — `routes/critical_alerts.py` |
| **Informed Consent** | Procedure consent management | **Present** — `routes/consent.py` |
| **Advance Directives** | Living will, DNR/POLST | **Missing** |
| **Never Events** | Reportable event tracking | **Present** — Incident reporting |
| **Root Cause Analysis** | RCA documentation | **Present** — Quality service |
| **Failure Mode Effects Analysis** | Proactive risk assessment | **Missing** |
| **Accreditation Readiness** | JCI, CAP, ISO checklist tracking | **Partial** — Compliance module |

---

## APPENDIX Q: Detailed Coverage by Phase — Domain-by-Domain Breakdown

### Q.1 Healthcare Domains — Implementation Readiness Assessment

| Domain | Architecture Fit | Data Model Readiness | API Coverage | UI/UX Coverage | Test Coverage | Overall Readiness |
|--------|-----------------|---------------------|--------------|----------------|---------------|-------------------|
| Primary Care | High | High | High | Medium | Medium | **Launch Ready** |
| Secondary Care | High | High | High | Medium | Medium | **Launch Ready** |
| Tertiary Care | Medium | Medium | Medium | Low | Low | **Needs Enrichment** |
| Quaternary Care | Low | Low | Low | None | None | **Exploratory** |
| Preventive Medicine | High | High | High | Medium | Medium | **Launch Ready** |
| Public Health | High | High | High | Medium | Medium | **Launch Ready** |
| Emergency Medicine | Low | Low | Low | None | None | **Not Implemented** |
| Military Medicine | None | None | None | None | None | **Not Implemented** |
| Disaster Medicine | None | None | None | None | None | **Not Implemented** |
| Space Medicine | None | None | None | None | None | **Not Implemented** |
| Occupational Health | Medium | Medium | High | Low | Low | **Functional** |
| Sports Medicine | None | None | None | None | None | **Not Implemented** |
| Travel Medicine | None | None | None | None | None | **Not Implemented** |
| Digital Health | High | High | High | High | High | **Market Leading** |
| Precision Medicine | None | None | None | None | None | **Not Implemented** |
| Genomic Medicine | None | None | None | None | None | **Not Implemented** |
| Telemedicine | Low | Low | Low | Medium | Low | **Foundation Only** |
| Home Care | Medium | Medium | High | Low | Low | **Functional** |
| Long-Term Care | None | None | None | None | None | **Not Implemented** |
| Palliative Care | None | None | None | None | None | **Not Implemented** |
| Hospice Care | None | None | None | None | None | **Not Implemented** |
| Mental Health | Low | Low | Low | None | None | **Foundation Only** |
| Community Health | High | High | High | Medium | Medium | **Launch Ready** |
| School Health | Medium | Medium | High | Low | Low | **Functional** |
| Environmental Health | None | None | None | None | None | **Not Implemented** |
| One Health | None | None | None | None | None | **Not Implemented** |
| Concierge/DPC | Low | Low | Low | None | None | **Foundation Only** |
| Population Health | High | High | High | Medium | Medium | **Launch Ready** |
| Regenerative Medicine | None | None | None | None | None | **Not Implemented** |
| Functional Medicine | None | None | None | None | None | **Not Implemented** |
| Integrative Medicine | None | None | None | None | None | **Not Implemented** |
| Hyperbaric Medicine | None | None | None | None | None | **Not Implemented** |
| Tropical Medicine | None | None | None | None | None | **Not Implemented** |
| Adolescent Medicine | Low | Low | Low | None | None | **Foundation Only** |
| Transitional Care | Medium | Medium | High | Low | Low | **Functional** |
| Urgent Care | Low | Low | Low | None | None | **Foundation Only** |
| Retail Health | None | None | None | None | None | **Not Implemented** |
| Lifestyle Medicine | None | None | None | None | None | **Not Implemented** |
| Gender-Affirming Care | None | None | None | None | None | **Not Implemented** |
| Global Health | Medium | Medium | Medium | Low | Low | **Foundation Only** |
| Planetary Health | None | None | None | None | None | **Not Implemented** |
| Evolutionary Medicine | None | None | None | None | None | **Not Implemented** |
| Nanomedicine | None | None | None | None | None | **Not Implemented** |
| Systems Medicine | None | None | None | None | None | **Not Implemented** |
| Network Medicine | None | None | None | None | None | **Not Implemented** |
| Exposome Medicine | None | None | None | None | None | **Not Implemented** |
| P4 Medicine | Low | Low | Low | None | None | **Foundation Only** |
| Emerging Domains (20) | None | None | None | None | None | **Not Implemented** |

### Q.2 Medical Specialty Implementation Detail

| Specialty | Ordered Entry | Results | Clinical Notes | Care Plans | Billing/Coding | Analytics | CDS |
|-----------|--------------|---------|----------------|------------|----------------|-----------|-----|
| Internal Medicine | Complete | Complete | Present | Present | Present | Present | Present |
| Cardiology | Present | Present | Present | Present | Present | Present | Partial |
| Gastroenterology | Present | Present | Present | Present | Present | Present | Partial |
| Pulmonology | Present | Present | Present | Present | Present | Present | Partial |
| Nephrology | Present | Present | Present | Present | Present | Present | Partial |
| Endocrinology | Present | Present | Present | Present | Present | Present | Partial |
| Rheumatology | Present | Present | Present | Present | Present | Present | Partial |
| Hematology | Present | Present | Present | Present | Present | Present | Partial |
| Infectious Disease | Present | Present | Present | Present | Present | Present | Present |
| Medical Oncology | Present | Present | Present | Present | Present | Present | Partial |
| Critical Care | Partial | Present | Present | Present | Present | Present | Partial |
| Geriatrics | Present | Present | Present | Present | Present | Present | Missing |
| General Surgery | Present | Present | Present | Present | Present | Present | Present |
| Cardiothoracic Surgery | Present | Present | Present | Present | Present | Present | Partial |
| Neurosurgery | Present | Present | Present | Present | Present | Present | Partial |
| Orthopedic Surgery | Present | Present | Present | Present | Present | Present | Partial |
| Plastic Surgery | Present | Present | Present | Present | Present | Present | Partial |
| Vascular Surgery | Present | Present | Present | Present | Present | Present | Partial |
| Urology | Present | Present | Present | Present | Present | Present | Partial |
| Ophthalmology | Partial | Partial | Present | Present | Present | Present | Missing |
| ENT | Present | Present | Present | Present | Present | Present | Partial |
| Pediatrics | Present | Present | Present | Present | Present | Present | Present |
| OB/GYN | Present | Present | Present | Present | Present | Present | Present |
| Psychiatry | Present | Present | Present | Present | Present | Missing | Missing |
| Neurology | Present | Present | Present | Present | Present | Present | Partial |
| Radiology | Present | Present | Present | Present | Present | Present | Missing |
| Emergency Medicine | Present | Present | Present | Present | Present | Present | Missing |
| Anesthesiology | Present | Present | Partial | Present | Present | Present | Missing |
| Pathology | Complete | Complete | Present | Partial | Present | Present | Present |
| Dermatology | Present | Present | Present | Present | Present | Present | Missing |
| PM&R | Present | Present | Present | Missing | Present | Missing | Missing |
| Family Medicine | Present | Present | Present | Present | Present | Present | Present |
| Medical Genetics | Present | Present | Present | Present | Present | Missing | Missing |
| Nuclear Medicine | Present | Present | Present | Present | Present | Present | Missing |
| Radiation Oncology | Present | Present | Present | Missing | Present | Missing | Missing |

### Q.3 Lab Sub-discipline Integration Maturity

| Sub-discipline | Order Interface | Analyzer Interface | Result Validation | QC Management | Reference Ranges | Autoverification | Delta Check | Critical Alerts | Interpretation |
|----------------|-----------------|-------------------|-------------------|---------------|------------------|-----------------|-------------|-----------------|----------------|
| Clinical Chemistry | Complete | Present | Complete | Complete | Complete | Present | Present | Complete | Present |
| Hematology | Complete | Present | Complete | Complete | Complete | Present | Present | Complete | Present |
| Microbiology | Complete | Present | Complete | Complete | Complete | Partial | Partial | Complete | Present |
| Immunology | Complete | Present | Complete | Complete | Complete | Present | Present | Complete | Present |
| Molecular | Complete | Present | Present | Present | Present | Partial | Partial | Complete | Present |
| Histopathology | Present | Missing | Present | Present | Present | Missing | Missing | Complete | Present |
| Cytology | Present | Missing | Present | Present | Present | Missing | Missing | Complete | Present |
| Genetics | Present | Missing | Present | Partial | Partial | Missing | Missing | Partial | Missing |
| Toxicology | Complete | Present | Complete | Complete | Complete | Present | Present | Complete | Present |
| Blood Bank | Complete | Present | Complete | Complete | Complete | Present | Present | Complete | Present |

---

## APPENDIX R: GULA Platform — Ecosystem Integration Map

### R.1 External Systems Integration

| External System Type | Examples | Integration Mechanism | GULA Status |
|---------------------|----------|----------------------|-------------|
| **National HIE** | SNDHS (Iraq), Sehhaty (KSA), Malaffi (UAE) | FHIR, REST | **Present** (SNDHS) |
| **National Identity** | Iraqi National ID, Absher (KSA) | REST API | **Present** |
| **Payment Gateways** | ZainCash, AsiaHawala, Visa/Mastercard | REST API | **Partial** |
| **Insurance Portals** | Local Iraqi insurers | REST/EDI | **Present** |
| **e-Government** | Iraqi ITA, e-services | SAML/OAuth | **Present** |
| **Pharmacy Systems** | Local pharmacy management | HL7 FHIR | **Partial** |
| **Radiology PACS** | DICOM-capable systems | DICOM/HL7 | **Missing** |
| **Device/Instrument** | Sysmex, Roche, Mindray analyzers | ASTM/HL7 v2 | **Present** |
| **Public Health Registries** | WHO, CDC, ECDC | FHIR/CSV | **Partial** |
| **Laboratory Reference** | Send-out labs, national reference labs | HL7 v2, PDF | **Present** |
| **Blood Bank / Donor System** | National blood service | HL7 v2 | **Partial** |
| **Tissue Typing / Registry** | National transplant center | REST/FHIR | **Missing** |
| **AI/ML Platforms** | Google Health, locally hosted models | REST, TensorFlow | **Present** |
| **Cloud Infrastructure** | AWS, Azure, GCP, private cloud | Native | **Present** |
| **Analytics/BI** | PowerBI, Tableau, Metabase | SQL/API | **Present** |
| **Patient Portals** | Citizen portal, mobile app | REST, FHIR | **Present** |
| **Telehealth/Virtual Care** | Video platforms | REST, WebRTC | **Partial** |
| **Drug Database** | DrugBank, Micromedex, Lexicomp | API integration | **Partial** |
| **Knowledge Base** | UpToDate, DynaMed, BMJ Best Practice | API | **Partial** |
| **Wearable Device** | Apple Watch, Fitbit, CGM, BP monitor | REST/Bluetooth | **Missing** |

### R.2 GULA Platform Internal Module Dependencies

```
Patient → Labs → Orders → Samples → Results → Interpretations
   ↓        ↓         ↓         ↓          ↓            ↓
EHR ←--- Care Continuum ---→ CDS ---→ Quality ---→ Research
   ↓                            ↓                      ↓
Notifications ←--- AI/Clinical Intelligence ←--- Registries
   ↓                                                  ↓
Mobile ←--- Citizen Portal ←--- Edge Platform ←--- National Data
```

---

## APPENDIX S: Healthcare Informatics Sub-domains

Health informatics is a critical enabler for all healthcare domains. This appendix maps the informatics sub-disciplines against GULA coverage.

| Informatics Sub-discipline | Description | Key Standards | GULA Coverage |
|---------------------------|-------------|---------------|---------------|
| **Clinical Informatics** | Use of data and IT to improve clinical care and outcomes | FHIR, SNOMED, LOINC, CDS Hooks, SMART on FHIR | **Complete** — Core platform |
| **Nursing Informatics** | Integration of nursing science, computer science, information science | ICNP, NNLI, TIGER, ANA Scope & Standards | **Partial** — Foundation exists |
| **Pharmacy Informatics** | Medication use process optimization | NCPDP, RxNorm, NDC, GS1, eMAR, BCMA, CPOE | **Partial** — CDS and orders exist |
| **Radiology Informatics** | Imaging workflow and data management | DICOM, IHE SWF, RIS, PACS, GSPS, KOS, SR | **Missing** |
| **Laboratory Informatics** | Lab workflow, instrument interface, QC | LOINC, CLSI LIS-2, LIS-2A, ASTM, HL7 v2 ORM/ORU | **Complete** — Core platform |
| **Dental Informatics** | Dental practice and imaging management | DICOM Dental, ADA CDT, SNODENT, FDI | **Missing** |
| **Public Health Informatics** | Population health surveillance, reporting | PHIN, NEDSS, HL7 v2 (ELR, VXU), FHIR | **Present** |
| **Consumer Health Informatics** | Patient-facing health IT | FHIR, patient portals, mHealth, HL7 PHD/PHR | **Present** |
| **Translational Bioinformatics** | Genomics, molecular data to clinical practice | GA4GH, VCF, BAM, CRAM, htsget, refget, Beacon | **Missing** |
| **Clinical Research Informatics** | Clinical trial and research data management | CDISC (CDASH, SDTM, ADaM), ODM, IEEE 11073 SDC, OHDSI OMOP CDM, PCORnet, i2b2, tranSMART | **Present** — Partial |
| **Population Health Informatics** | Risk stratification, care management, outcomes | HEDIS, QOF, FHIR, ADT streaming, ETL/EDW | **Present** |
| **Rehabilitation Informatics** | PT/OT/SLP documentation and analytics | ICF, FOTO, IRF-PAI, OASIS, MDS, WeeFIM, FIM, COPM | **Missing** |
| **Mental Health Informatics** | Behavioral health IT, privacy | 42 CFR Part 2, DSM-5/ICD-11, PHQ-9/GAD-7 APIs | **Missing** |
| **Emergency Medicine Informatics** | ED workflow, syndromic surveillance | EDIS standards, NEMSIS (EMS), syndromic surveillance | **Missing** |
| **Anesthesia Informatics** | Perioperative documentation and monitoring | AIMS standards, ASTM, ISO 11073-10207, IHE PFE | **Missing** |
| **Pathology Informatics** | Anatomic pathology workflow | DICOM Pathology, IHE APW, CAP checklists, SNOMED | **Present** — Partial |
| **Blood Bank Informatics** | Transfusion service management | ICCBBA/ISBT 128, FDA bar code rule, AABB standards | **Present** |
| **Bioinformatics** | DNA/RNA sequence analysis and interpretation | FASTQ, BAM, VCF, GA4GH, BioPAX, PSI-MI | **Missing** |
| **Imaging Informatics** | Image storage, processing, and AI analysis | DICOM, IHE, AIM, TFS, PyRadiomics, MONAI | **Missing** |
| **Medical Device Informatics** | Device integration and data management | IEEE 11073, IHE DEC/DEV, BLUETOOTH HDP, FHIR | **Present** — Device bridge |
| **Nutrition Informatics** | Food service, diet ordering, nutrition assessment | IDNT, AND codes, USDA/CDC food data | **Missing** |
| **Telehealth Informatics** | Remote care delivery technology | ATA standards, Telehealth parity laws, CMS telemedicine modifiers | **Partial** |
| **Cardiovascular Informatics** | ECG, telemetry, cardiac device management | SCP-ECG, DICOM Cardiology, IHE CATH/ECG, XML-ECG | **Missing** |
| **Respiratory Informatics** | Pulmonary function, ventilator management | SMILE, PFT DB, IHE PFT, HL7 PFT | **Missing** |
| **Opioid Informatics** | PDMP, controlled substance monitoring, OUD treatment | PDMP standards, SCRIPT (PMP Gateway), NASTECH | **Missing** |

## APPENDIX T: Global Health System Classification & GULA Applicability

### T.1 Health System Archetypes

| Archetype | Characteristics | Example Countries | GULA Fit |
|-----------|----------------|-------------------|----------|
| **National Health Service (Beveridge)** | Tax-funded, publicly delivered | UK, Spain, Italy, Nordic countries, Cuba | **High** — Population-focused, national HIE |
| **Social Health Insurance (Bismarck)** | Employer/employee funded, private/public delivery | Germany, France, Japan, Netherlands, Switzerland | **High** — Insurance gateways, claims |
| **Private Insurance (Out-of-pocket)** | Market-driven, private delivery | USA (mixed), Switzerland (mixed), Singapore (mixed) | **Medium** — Claims, subscription tiers |
| **Mixed Public/Private (LMIC)** | Donor-funded programs + private delivery | India, Nigeria, Kenya, Bangladesh, Pakistan | **Excellent** — Edge platform, offline, modular |
| **State-Dominated (Former Soviet)** | State-funded, state-delivered | Russia, Belarus, Central Asian republics | **Medium** — SNDHS-like integration |
| **Oil-based Gulf Model** | Generous public funding + private delivery | Saudi Arabia, UAE, Qatar, Kuwait, Oman | **Excellent** — Arabic-first, SNDHS aligned |
| **Chinese Model** | Public insurance (urban/rural) mixed delivery | China | **Medium** — Localization required |
| **Out-of-Pocket Dominant** | Mostly private payment, limited public | Many Sub-Saharan African, South Asian nations | **Good** — DPC/subscription model |

### T.2 GULA Regional Readiness Matrix

| Region | Market Need | Regulatory Complexity | Competition | GULA Advantage | Overall Priority |
|--------|-------------|----------------------|-------------|----------------|------------------|
| **Iraq** | Very High | Medium | Low | Home market, native SNDHS | **Tier 1** |
| **Kurdistan Region** | Very High | Medium | Very Low | Home market | **Tier 1** |
| **Saudi Arabia** | High | High | Medium | Arabic, Nahdi/private labs | **Tier 1** |
| **UAE** | High | Medium | High | Arabic, FHIR native | **Tier 1** |
| **Kuwait** | High | Medium | Low | Arabic, government labs | **Tier 1** |
| **Qatar** | High | Medium | Low | Arabic, HMC labs | **Tier 1** |
| **Oman** | Medium | Medium | Low | Arabic | **Tier 2** |
| **Bahrain** | Medium | Medium | Low | Arabic | **Tier 2** |
| **Jordan** | High | Medium | Medium | Arabic, Hakeem | **Tier 2** |
| **Egypt** | High | Medium | High | Arabic, scale | **Tier 2** |
| **Libya** | High | Low | Very Low | Arabic | **Tier 2** |
| **Tunisia** | Medium | Medium | Low | French + Arabic | **Tier 2** |
| **Morocco** | Medium | Medium | Low | French + Arabic | **Tier 2** |
| **Algeria** | Medium | Medium | Low | French + Arabic | **Tier 2** |
| **Lebanon** | Medium | Medium | Medium | Arabic, established health IT | **Tier 2** |
| **Palestine** | High | Low | Very Low | Arabic, NGO support | **Tier 2** |
| **Yemen** | Very High | Low | Very Low | Arabic, humanitarian, EMRO | **Tier 2** |
| **Syria** | Very High | Low | Very Low | Arabic, humanitarian | **Tier 2** |
| **Somalia** | Very High | Low | Very Low | Arabic, EMRO, offline | **Tier 2** |
| **Sudan** | Very High | Low | Very Low | Arabic, EMRO | **Tier 2** |
| **Mauritania** | High | Low | Very Low | Arabic, EMRO | **Tier 2** |
| **Djibouti** | High | Low | Very Low | Arabic, EMRO | **Tier 2** |
| **Comoros** | Medium | Low | Very Low | Arabic, EMRO | **Tier 3** |
| **Pakistan** | Very High | Medium | Medium | Urdu, large lab market | **Tier 2** |
| **Bangladesh** | Very High | Medium | Medium | Large market, NGO sector | **Tier 3** |
| **India** | Very High | High | Very High | Scale opportunity | **Tier 3** |
| **Sub-Saharan Africa** | Very High | Low | Low | Humanitarian, DHIS2, offline | **Tier 2** |
| **Turkey** | Medium | Medium | High | Turkish, cross-border health | **Tier 3** |
| **Iran** | High | High | Low | Farsi, sanctions-resilient | **Tier 2** |
| **Afghanistan** | Very High | Low | Very Low | Dari/Pashto, humanitarian | **Tier 3** |

## APPENDIX U: Strategic Roadmap — Phased Implementation

### Phase A: Foundation (Complete — v1.0 to v2.1.0)
- [x] Core LIMS (Orders, Samples, Results)
- [x] Patient Management & MPI
- [x] Laboratory Quality Management (QC, PT, IQCP)
- [x] Hospital/Facility Management
- [x] EHR Foundation (Notes, Medications, Allergies, Problems)
- [x] Care Continuum Platform
- [x] Security & Compliance (RBAC, ABAC, MFA, OAuth2, SAML)
- [x] Audit Trail & Data Integrity
- [x] FHIR API & Terminology Services
- [x] Clinical Decision Support (Basic)
- [x] Clinical AI Copilot & Intelligence
- [x] Edge Platform for Offline Capability
- [x] Citizen Portal & Mobile Access
- [x] National ID Integration (SNDHS)
- [x] Insurance/Claims Management
- [x] Subscription/Tier Management

### Phase B: Expansion (Months 1-12)
- [ ] **Pharmacy Module** — Full pharmaceutical care workflow (CPOE, eMAR, BCMA, pharmacy management)
- [ ] **Radiology/RIS Module** — DICOM integration, structured reporting, imaging workflow
- [ ] **Dental Module** — General dentistry, charting, treatment planning, dental terminology
- [ ] **Physical Therapy/Rehab Module** — PT evaluation, exercise prescription, outcome measures
- [ ] **Behavioral Health Module** — MH assessment tools, standardized scales, therapy notes
- [ ] **Telemedicine Infrastructure** — Video consultation, remote monitoring, telehealth workflows
- [ ] **Laboratory Expansion** — Microbiology/AST workflow enhancement, blood bank automation
- [ ] **Population Health Expansion** — Advanced analytics, risk models (ACG/HCC), outreach engine
- [ ] **Emergency Department Module** — Triage, tracking board, time-stamped protocols
- [ ] **Clinical Nutrition Module** — Dietetics, TPN management, food service

### Phase C: Specialization (Months 13-24)
- [ ] **Oncology Module** — Chemotherapy protocols, infusion center, tumor board, staging
- [ ] **Cardiology Module** — ECG management, echo workflow, cath lab, device clinic
- [ ] **OB/GYN Expansion** — Fetal monitoring, partograph, NST, labor documentation
- [ ] **Nephrology/Dialysis Module** — Dialysis treatment records, access management, transplant
- [ ] **Genomic Medicine** — VCF management, variant classification, GA4GH APIs, pharmacogenomics
- [ ] **Precision Oncology** — Molecular tumor board, biomarker registry, trial matching
- [ ] **Ophthalmology Module** — Refraction, OCT, visual fields, cataract workflow
- [ ] **Dermatology Module** — Teledermatology, dermoscopy, Mohs documentation
- [ ] **Nursing Informatics** — Flowsheets, nursing notes, patient acuity, staffing
- [ ] **Anesthesia Information Management** — AIMS, pre-op/intra-op/PACU documentation

### Phase D: Advanced (Months 25-36)
- [ ] **AI Clinical Decision Support Expansion** — All major specialties
- [ ] **Digital Pathology** — Whole-slide imaging, AI pathology, remote consultation
- [ ] **P4 Medicine Platform** — Predictive, preventive, personalized, participatory
- [ ] **Population Health Command Center** — Real-time monitoring, outbreak detection
- [ ] **Palliative & Hospice Care Module** — End-of-life care workflows
- [ ] **Social Determinants of Health** — Screening, community resource referral, social prescribing
- [ ] **Military/Disaster Medicine** — Field operations, MCI management, tactical medicine
- [ ] **Global Health & One Health** — Multi-country deployment, zoonotic surveillance
- [ ] **Advanced Interoperability** — IHE XDS, cross-enterprise document sharing, national HIE connections
- [ ] **Healthcare Marketplace** — Provider directory, consumer choice, price transparency

---

## APPENDIX T: Key Performance Indicators by Domain

| Domain | Metric | Benchmark | GULA Baseline |
|--------|--------|-----------|---------------|
| **Laboratory** | Test order-to-result TAT | <60 min (STAT), <24h (routine) | Monitoring via audit |
| **Laboratory** | QC failure rate | <2% | Tracked via QC module |
| **Laboratory** | Critical value reporting rate | 100% | Complete coverage |
| **Laboratory** | Autoverification rate | >70% | Partial implementation |
| **Hospital** | Bed occupancy rate | 75-85% | Dashboard available |
| **Hospital** | Average length of stay | Domain-specific | Trackable |
| **Hospital** | Readmission rate (30-day) | <15% | Care transition tracking |
| **Primary Care** | Preventive screening rates | >80% | Care gap analysis |
| **Primary Care** | Immunization rates | >90% (per WHO) | Immunization registry |
| **Public Health** | Notifiable disease reporting | 100% within 24h | Reporting infrastructure |
| **Population Health** | Chronic disease registry completeness | >95% | Registry module |
| **Quality** | Adverse event rate | <5% | Incident reporting |
| **Patient Safety** | Wrong patient/wrong site events | 0 | Identification scanning |
| **Patient Engagement** | Patient portal utilization | >40% | Portal deployed |
| **Security** | Authentication failures | Tracked | IDS monitoring |

---

## APPENDIX O: GULA Platform Technical Architecture & Interoperability

### Interoperability Layer

| Interface | Standard | Direction | Status |
|-----------|----------|-----------|--------|
| Lab Instrument | ASTM E1381, E1394 (LIS2-A) | Bidirectional | **Present** |
| Lab Instrument | HL7 v2.5.1 (ORM, ORU) | Bidirectional | **Present** |
| Lab Instrument | POCT1-A (LIS to POC) | Bidirectional | **Partial** |
| Health Information Exchange | HL7 FHIR R4 (STU3, R4) | Bidirectional | **Present** |
| Health Information Exchange | HL7 v2.5.1 (ADT, SCH, SIU) | Bidirectional | **Partial** |
| Health Information Exchange | IHE PIX (Patient Identity Cross-reference) | Receive | **Partial** |
| Health Information Exchange | IHE PDQ (Patient Demographics Query) | Query | **Partial** |
| Health Information Exchange | IHE XDS (Cross-enterprise Document Sharing) | Document | **Missing** |
| Health Information Exchange | C-CDA / Consolidated CDA | Export | **Partial** |
| EHR Interface | SMART on FHIR | API | **Present** |
| EHR Interface | CDS Hooks | Services | **Present** |
| National ID | REST-based service | Query | **Present** |
| Insurance Gateway | REST/Claim X12 837 | Submit | **Present** |
| Notification | Webhook, Telegram, Email, SMS | Outgoing | **Present** |
| Payment Gateway | REST | Bidirectional | **Partial** |
| Identity Provider | SAML 2.0, OAuth 2.0, OIDC | SSO | **Present** |
| Cloud Storage | S3-compatible API | Document | **Present** |
| AI Model Serving | REST, gRPC, TensorFlow Serving | Inference | **Present** |

---

## APPENDIX P: Global Clinical Terminology Integration

| Terminology | Domain | GULA Status |
|-------------|--------|-------------|
| **ICD-10-WHO** | Mortality and morbidity statistics | **Present** — Terminology service |
| **ICD-10-AM** | Australian modification | **Present** — Terminology compatible |
| **ICD-11** | Latest WHO classification | **Partial** — ICD-10 basis, upgrade path |
| **ICD-O-3** | Oncology morphology/topography | **Present** |
| **SNOMED CT International** | Clinical terms | **Present** — Terminology service |
| **SNOMED CT US Edition** | US clinical extension | **Present** |
| **SNOMED CT UK Edition** | UK clinical extension | **Present** |
| **LOINC** | Laboratory, clinical observations | **Present** — Terminology service |
| **CPT (Current Procedural Terminology)** | US procedure codes | **Present** |
| **HCPCS Level II** | US supplies, drugs, services | **Partial** |
| **NDC (National Drug Code)** | US drug identification | **Present** |
| **RxNorm** | US clinical drugs | **Partial** |
| **ATC (Anatomical Therapeutic Chemical)** | WHO drug classification | **Present** |
| **UNII (Unique Ingredient Identifier)** | FDA substances | **Present** |
| **DSM-5-TR** | Mental disorders | **Missing** |
| **ICF** | Functioning, disability, health | **Missing** |
| **ICHI** | Health interventions | **Missing** |
| **ISO 3166** | Country codes | **Complete** |
| **ISO 639** | Language codes | **Complete** |
| **UCUM** | Units of measure | **Present** |
| **FHIR ValueSets** | Standard FHIR value sets | **Present** |
| **DICOM** | Medical imaging | **Missing** |
| **FDI World Dental** | Dental notation | **Missing** |
| **ICD-10-CM** | US clinical modification | **Present** |
| **ICD-10-PCS** | US procedure coding | **Present** |
| **OPCS-4** | UK OPCS classification | **Missing** |
| **DRG (Diagnosis Related Groups)** | Inpatient payment | **Partial** |
| **HEDIS** | Healthcare Effectiveness Data and Information Set | **Partial** |
| **QOF** | Quality and Outcomes Framework (UK) | **Partial** |

---

*End of Document — GLOBAL HEALTHCARE ATLAS v2.1.0*

*This document represents a comprehensive discovery inventory of every recognized healthcare domain, specialty, and profession mapped against the GULA Platform codebase. It is intended as a strategic planning reference for the platform's global expansion, not as a commitment to implement every listed module.*

*Classification evidence based on codebase analysis of backend/app/routes/ (53 route modules), backend/app/models/ (26 model files), backend/app/services/ (34 service modules), backend/app/core/ (18 infrastructure modules), backend/app/security/ (16 security modules), and supporting packages (ehr, care_continuum, clinical, hospital, ai, financial, edge, audit, notifications, firewall, gateways, legal, tasks).*
