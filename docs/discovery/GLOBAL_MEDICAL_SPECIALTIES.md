# GLOBAL MEDICAL SPECIALTIES

> **GULA Platform — Complete Medical Specialty Discovery & Coverage Assessment**
>
> Classification based on: WHO, ACGME, WMA, AMA, BMA, WFME, UEMS, American Board of Medical Specialties (ABMS),
> Royal College of Physicians and Surgeons of Canada, General Medical Council (UK), Australian Medical Council,
> Saudi Commission for Health Specialties, Iraqi Medical Specialty Board, Jordanian Medical Council,
> Egyptian Medical Syndicate, Arab Board of Health Specialties, Emirates Medical Association,
> Qatar Council for Healthcare Practitioners, Kuwait Institute for Medical Specializations,
> Oman Medical Specialty Board, Sudanese Medical Specialization Board, Syrian Medical Council,
> Lebanese Order of Physicians, Palestine Medical Council, Yemeni Medical Council, Libyan Medical Union,
> Tunisian National Council of Medical Orders, Algerian Order of Physicians, Moroccan National Order of Physicians
>
> **Coverage Scale:**
> - **Complete** — Production module with full test coverage, audit support, international standard compliance
> - **Present** — Module exists with core functionality; deployable with caveats
> - **Partial** — Some components exist (data model, basic routes, or references in other modules)
> - **Missing** — No code, models, routes, or services identified in the codebase
> - **Planned** — Documented in strategic roadmap for future implementation
>
> **Version:** 2.1.0 — Last Updated: July 2026

---

## TABLE OF CONTENTS

1. [Internal Medicine & Subspecialties](#1-internal-medicine--subspecialties)
2. [Surgery & Subspecialties](#2-surgery--subspecialties)
3. [Pediatrics & Subspecialties](#3-pediatrics--subspecialties)
4. [Obstetrics & Gynecology & Subspecialties](#4-obstetrics--gynecology--subspecialties)
5. [Psychiatry & Subspecialties](#5-psychiatry--subspecialties)
6. [Neurology & Subspecialties](#6-neurology--subspecialties)
7. [Radiology & Subspecialties](#7-radiology--subspecialties)
8. [Emergency Medicine & Subspecialties](#8-emergency-medicine--subspecialties)
9. [Anesthesiology & Subspecialties](#9-anesthesiology--subspecialties)
10. [Pathology & Subspecialties](#10-pathology--subspecialties)
11. [Ophthalmology & Subspecialties](#11-ophthalmology--subspecialties)
12. [Dermatology & Subspecialties](#12-dermatology--subspecialties)
13. [Physical Medicine & Rehabilitation & Subspecialties](#13-physical-medicine--rehabilitation--subspecialties)
14. [Preventive Medicine & Subspecialties](#14-preventive-medicine--subspecialties)
15. [Other Recognized Specialties](#15-other-recognized-specialties)
16. [Appendix A: Coverage Summary Matrix](#appendix-a-coverage-summary-matrix)
17. [Appendix B: Specialty-by-Specialty Implementation Detail](#appendix-b-specialty-by-specialty-implementation-detail)
18. [Appendix C: Technology Dependency Catalog](#appendix-c-technology-dependency-catalog)
19. [Appendix D: Regional Specialty Recognition](#appendix-d-regional-specialty-recognition)

---

# 1. Internal Medicine & Subspecialties

Internal Medicine is the cornerstone of adult medical care, encompassing the prevention, diagnosis, and non-surgical treatment of diseases affecting internal organ systems. Internists manage complex multi-system diseases and serve as diagnostic consultants.

## 1.1 General Internal Medicine

| Attribute | Detail |
|-----------|--------|
| **Definition** | Comprehensive diagnosis and non-surgical management of adult diseases, serving as primary care for adults with complex medical needs or as hospital-based diagnosticians |
| **Common Conditions** | Hypertension, diabetes mellitus type 2, coronary artery disease, COPD, asthma, pneumonia, UTIs, anemia, thyroid disorders, osteoarthritis, gout, cellulitis, venous thromboembolism, chronic kidney disease, heart failure, atrial fibrillation, hyperlipidemia, cirrhosis, IBD, depression, undifferentiated symptoms |
| **Procedures/Interventions** | Comprehensive history & physical, diagnostic test interpretation (ECG, imaging, lab), joint aspiration/injection, lumbar puncture, abdominal paracentesis, thoracentesis, central line placement, ABG collection, skin biopsy, exercise stress test interpretation, Holter monitor interpretation, cardioversion, therapeutic phlebotomy, trigger point injections |
| **Typical Technology Dependencies** | EHR/EMR, CPOE, clinical decision support (CDS), drug interaction databases, imaging order entry (RIS), LIS, ECG management, telemedicine, patient portal, risk stratification, problem list management, medication reconciliation, transition of care documentation, coding/billing (ICD-10, CPT), preventive care reminders |
| **GULA Coverage Status** | **Present** — Clinical orders, documentation, lab results, EHR, care continuum, primary care encounters; clinical documentation and problem list management exist; transition of care module supports inpatient-to-outpatient handoffs; CDS provides basic drug interaction and guideline-based alerts |

## 1.2 Cardiology

| Subspecialty | Definition | Common Conditions | Procedures/Interventions | Tech Dependencies | GULA |
|---|---|---|---|---|---|
| **General Cardiology** | Heart and cardiovascular diseases | CAD, heart failure, valvular disease, arrhythmias, pericardial disease, cardiomyopathies, hypertension, hyperlipidemia, syncope | ECG interpretation, echocardiography (TTE), stress testing, cardiac catheterization (diagnostic), Holter/event monitoring, tilt-table testing, cardioversion, pericardiocentesis | ECG management system (MUSE/GE/Mortara), PACS for cardiac imaging, stress test databases, Holter analysis software, EHR, CPOE, LIS for cardiac biomarkers | **Partial** — Lab orders for cardiac markers, clinical documentation, ECG order entry; no dedicated cardiology module, no ECG waveform storage/management |
| **Interventional Cardiology** | Catheter-based coronary and structural heart treatment | Acute coronary syndrome, chronic total occlusions, multivessel CAD, in-stent restenosis, structural heart disease (AS, MR, PFO/ASD) | Coronary angiography, PCI (balloon/stent), rotational/orbital/laser atherectomy, IVUS, OCT, FFR, iFR, transradial/transfemoral access, TAVR, TEER, PFO/ASD closure, LAA occlusion, Impella/IABP, ECMO | Angiography suite (biplane/single plane), IVUS/OCT consoles, FFR/iFR systems, Mac-Lab hemodynamic monitoring, PCI registry, stent inventory, antiplatelet CDS | **Missing** — No cath lab documentation, no hemodynamic data storage, no PCI registry |
| **Electrophysiology** | Cardiac rhythm disorders | AFib, atrial flutter, AVNRT, WPW, VT, VF, Brugada, LQTS, CPVT, ARVC, sick sinus, AV block, syncope | EPS, RF/cryo/pulsed-field ablation, AFib ablation (PVI), VT ablation, 3D mapping (CARTO/NavX/Rhythmia), pacemaker/ICD/CRT implantation, lead extraction, His-bundle/LBB pacing | 3D electroanatomic mapping system, RF generator/cryoablation, ICE, EP recording system, pacemaker/ICD programmer, remote monitoring (CareLink/Merlin/LATITUDE) | **Missing** — No EP documentation, no device interrogation data management, no remote monitoring integration |
| **Advanced Heart Failure & Transplant Cardiology** | End-stage heart disease, MCS, transplantation | HFrEF, HFpEF, advanced HF (Stage D), cardiogenic shock, ADHF, HCM, restrictive cardiomyopathy (amyloid/sarcoid), myocarditis, Takotsubo | GDMT optimization, heart transplant evaluation/transplantation, immunosuppression, endomyocardial biopsy, LVAD (HeartMate 3), Impella, VA-ECMO, CardioMEMS, ultrafiltration | Hemodynamic monitoring (Swan-Ganz), CPET, cardiac MRI (T1/T2 mapping/ECV/LGE), LVAD controller, transplant registry (UNOS/ISHLT), immunosuppression tracking, CardioMEMS analytics | **Missing** — No heart failure module, no LVAD registry, no transplant waiting list, no immunosuppression tracking |
| **Adult Congenital Heart Disease** | Lifelong care for adult CHD | ASD, VSD, PDA, Tetralogy of Fallot, TGA, coarctation, Ebstein, single ventricle/Fontan, Eisenmenger, aortopathy | ACHD-specific echo (3D TEE), cardiac MRI (3D SSFP/flow quantification), CPET, percutaneous ASD/PFO/VSD closure, pulmonary valve replacement (Melody/Sapien), pregnancy counseling (mWHO) | Structural heart imaging (3D reconstruction/printing), ACHD registry (CONCOR/IMPACT), pregnancy risk CDS, Fontan surveillance protocol | **Missing** — No ACHD module, no CHD-specific documentation, no Fontan surveillance workflow |
| **Cardiovascular Prevention & Lipidology** | CVD prevention through risk factor modification | Familial hypercholesterolemia, hypertriglyceridemia, elevated Lp(a), metabolic syndrome, obesity, prediabetes, subclinical atherosclerosis | Advanced lipid panel, genetic testing for dyslipidemias, ASCVD risk scores (PCE/QRISK3/SCORE2), CAC scoring, CCTA with plaque characterization, lifestyle intervention, pharmacotherapy (statin/ezetimibe/PCSK9/inclisiran/bempedoic acid/icosapent ethyl) | EHR with CDS for risk assessment, LIS for advanced lipid testing, lifestyle medicine documentation templates, patient-facing tools (portal/dashboard) | **Missing** — No prevention/lipid module, no CAC score management, no risk score CDS |
| **Cardiovascular Imaging** | Advanced non-invasive cardiac imaging | CAD, cardiomyopathy phenotyping, valvular quantification, aortic disease, pericardial disease, cardiac masses, congenital heart disease | Echo (TTE/TEE/stress/3D/strain), cardiac CT (CAC/CCTA/CT-FFR/plaque characterization/structural planning), cardiac MRI (cine/T1/T2 mapping/LGE/perfusion/strain/4D flow/flow quantification) | PACS for cardiac imaging, structured reporting (RSNA templates), post-processing (Terarecon/Vital/Medis/Circle), AI (Aidoc/RapidAI/HeartFlow/Circle CVI) | **Missing** — No cardiovascular imaging module, no structured reporting, no cardiac MRI workflow, no DICOM-based image management |
| **Cardiogenetics** | Genetic basis of CVD | HCM, DCM, ARVC, RCM, LVNC, FH, aortic aneurysm syndromes (Marfan/Loeys-Dietz/vEDS), bicuspid AV, PAH, channelopathies (LQTS/Brugada/CPVT) | Genetic testing (NGS panels/WES/WGS), variant classification (ACMG/AMP/ClinGen), cascade screening, family-based risk stratification, functional studies (iPSC-cardiomyocytes/patch clamping) | NGS sequencing platforms, variant interpretation (Alamut/VarSeq/Alissa), ClinVar submission, pedigree software, LIMS for genetic testing | **Missing** — No cardiogenetics module, no variant classification workflow, no cascade screening tracking |
| **Cardiac Critical Care** | Life-threatening cardiac conditions in CICU/CCU | ACS with cardiogenic shock, post-cardiac arrest, malignant arrhythmias/electrical storm, massive PE, type A aortic dissection, post-cardiac surgery care | Mechanical ventilation, hemodynamic monitoring (Swan-Ganz/PiCCO/FloTrac), TEE/POCUS, targeted temperature management, ECMO/Impella/IABP/LVAD management, thrombolysis, vasoactive drug titration | CICU-specific EMR with high-resolution flowsheets (ICCA/CARESCAPE), continuous cardiac output monitoring, critical care ultrasound, lactate clearance tracking | **Missing** — No CICU-specific module, no high-resolution flowsheet, no hemodynamic data capture, no ECMO/LVAD flowsheet |
| **Cardiac Rehabilitation** | Secondary prevention program | Post-MI, post-CABG, post-PCI, chronic angina, HFrEF, post-heart transplant, PAD | Exercise prescription (FITT-VP), ECG-monitored exercise sessions, nutritional counseling, BP/lipid/diabetes/tobacco management, stress management, cardiac telerehabilitation | Telerehabilitation platform, wearable technology (HR monitor/activity tracker), cardiac rehab mobile app, outcome tracking (6MWT/KCCQ-12/SAQ-7) | **Missing** — No cardiac rehab module, no exercise prescription management, no telerehabilitation platform |

## 1.3 Gastroenterology

| Subspecialty | Definition | Common Conditions | Procedures/Interventions | Tech Dependencies | GULA |
|---|---|---|---|---|---|
| **General Gastroenterology** | Digestive system diseases | GERD, PUD, H. pylori, IBS, IBD, celiac disease, diverticulitis, gallstone disease, pancreatitis, hepatitis, cirrhosis, HCC, GI bleeding, Barrett's, EoE, gastroparesis, SIBO, EPI, PSC, PBC | EGD with biopsy, colonoscopy with polypectomy (cold snare/EMR/ESD), capsule endoscopy, enteroscopy, ERCP, EUS (radial/linear/FNA/FNB), esophageal dilation, stent placement, PEG/PEG-J, variceal band ligation, hemostasis (clip/APC/injection/Hemospray/OTSC) | Endoscopic tower (Olympus EXERA/Fuji/Pentax), ERBE electrosurgical generator, CO2 insufflator, HRM system, 24-hr pH/impedance, motility testing, SmartPill wireless motility capsule | **Partial** — Lab orders for GI markers, pathology results, clinical documentation; no endoscopy documentation, no colonoscopy tracking, no ERCP/EUS documentation |
| **Hepatology** | Liver diseases | Viral hepatitis (A/B/C/D/E), ALD, NAFLD/MASH, cirrhosis (compensated/decompensated), HCC, ACLF/ALF, AIH, PBC, PSC, IgG4-SC, DILI, hemochromatosis, Wilson, A1AT, PFIC | Transient elastography (FibroScan/2D-SWE/MRE), liver biopsy (percutaneous/transjugular with HVPG), HCC surveillance (US/AFP q6mo), DAAs for HCV, NAs for HBV, TIPS, BRTO, HCC locoregional therapy (TACE/Y90/ablation) | FibroScan, 2D-SWE ultrasound, MRE post-processing, LIS for viral hepatitis/autoimmune serology, HCC imaging (CT quadriphasic/MRI ECA-EOB/LI-RADS), MELD/MELD-Na scoring | **Partial** — Lab orders for LFTs/hepatitis serologies/viral load/fibrosis markers, HCC surveillance documentation, clinical documentation; no hepatology module, no NASH registry, no elastography integration |
| **Transplant Hepatology** | Medical management of LT candidates/recipients | ALF (status 1/1A), decompensated cirrhosis with HCC (Milan/UCSF criteria), perihilar CCA (Mayo protocol), metabolic disease (FAP/MSUD/PH1), PCLD | LT evaluation (MELD/MELD-Na/exception points), immunosuppression (tacrolimus/MMF/prednisone), post-LT surveillance (Doppler US, rejection monitoring, CMV/EBV, biliary stricture, de novo malignancy, NASH recurrence) | UNET/SRSTR/DonorNetLink, organ transplant management system (Epic Transplant/Cerner TX), immunosuppression drug level management, living donor evaluation workflow, paired exchange registry | **Missing** — No transplant hepatology module, no LT evaluation workflow, no immunosuppression management, no post-transplant surveillance system |
| **Neurogastroenterology & Motility** | GI motility and functional disorders | Gastroparesis (diabetic/idiopathic/post-surgical), chronic intestinal pseudo-obstruction (CIPO), Hirschsprung, dyssynergic defecation, fecal incontinence | Gastric emptying scintigraphy/breath test, antroduodenal manometry, wireless motility capsule, anorectal manometry (HR-ARM/3D-HDAM), biofeedback therapy, G-POEM, gastric electrical stimulation (Enterra), sacral nerve stimulation, pyloric Botox | HRM (ManoScan), HR-ARM, SmartPill, EndoFLIP for pyloric distensibility, autonomic testing (tilt-table/QSART), pH-impedance monitoring | **Missing** — No motility lab module, no HRM data management, no pH/impedance reporting, no gastroparesis registry |
| **Advanced Endoscopy** | Advanced endoscopic pancreaticobiliary management | Pancreaticobiliary strictures/malignancies, bile leak, choledocholithiasis, chronic pancreatitis, PD strictures, pancreatic duct leak, bile duct injury | ERCP with sphincterotomy, biliary/pancreatic stent placement (plastic/SEMS/FCSEMS), stone extraction (balloon/basket/lithotripsy), cholangioscopy (SpyGlass), IDUS, PTC with PTBD, EUS-guided drainage | C-arm fluoroscopy, SpyGlass DS cholangioscope, EHL/laser lithotripsy, mechanical lithotriptor, ERCP/EUS platform with accessories | **Missing** — No advanced endoscopy module, no ERCP/EUS documentation, no fluoroscopy time/dose tracking |
| **Inflammatory Bowel Disease** | Crohn's and ulcerative colitis management | Crohn's (Montreal L1-L4/B1-B3/p), UC (E1-E3), IBD-U, microscopic colitis | Biologic therapy management (anti-TNF/anti-integrin/anti-IL12/23/JAKi/S1PR), disease activity scores (Mayo/HBI/SES-CD), calprotectin monitoring, colonoscopic surveillance for dysplasia, IBD-related surgery coordination | IBD registry (IBD Qorus/CCFA Partners), LIS for calprotectin/CRP/biologic drug levels/antibodies, PACS for MRE/CTE, structured IBD pathology reporting | **Partial** — Lab orders for inflammatory markers/calprotectin, clinical documentation; no IBD registry, no biologic drug level management, no disease activity score CDS |

## 1.4 Pulmonology

| Subspecialty | Definition | Common Conditions | Procedures/Interventions | Tech Dependencies | GULA |
|---|---|---|---|---|---|
| **General Pulmonology** | Lung and respiratory diseases | COPD, asthma, pneumonia, ILD, pulmonary nodules, pleural effusion, pneumothorax, sleep apnea, pulmonary hypertension, lung cancer, bronchiectasis, sarcoidosis, TB, COVID-19 | PFT interpretation (spirometry/DLCO/lung volumes), bronchoscopy (BAL/biopsy/transbronchial), EBUS-TBNA, thoracentesis, pleural biopsy, chest tube, pleurodesis, thoracoscopy (medical), pulse oximetry, ABG | PFT system (Vyaire/CareFusion/ndd), bronchoscopy tower, EBUS console (Olympus/Fuji), PACS for chest imaging, sleep study system (Polysomnography CPAP), LIS for ABG/microbiology | **Partial** — Lab orders (ABG, respiratory cultures), clinical documentation, PFT order entry; no PFT waveform integration, no bronchoscopy documentation, no sleep study management |
| **Pulmonary/Critical Care** | Combined lung and ICU medicine | ARDS, sepsis, ventilator-associated pneumonia, shock, AKI, DIC, multi-organ failure, respiratory failure, pulmonary embolism, massive hemoptysis | Mechanical ventilation (volume/pressure control, PRVC, APRV, PSV, HFOV, HFNC, NIV), hemodynamic monitoring, bronchoscopy in ICU, percutaneous dilational tracheostomy, central line/arterial line placement, CRRT, ECMO, TTM | Ventilator (Drager/GE/Hamilton/Maquet/Servo), hemodynamic monitoring (Swan-Ganz/PiCCO/Vigileo), ARDS protocol CDS, ventilator weaning protocol, sedation/paralysis management, ABG interpretation CDS | **Partial** — ICU unit model, clinical documentation; no ventilator integration, no PFT system interface, no ARDS protocol CDS, no ECMO documentation |
| **Interventional Pulmonology** | Advanced diagnostic and therapeutic bronchoscopy | Central airway obstruction, hemoptysis, complex airway stenosis, tracheoesophageal fistula, pleural disease (malignant effusion), peripheral pulmonary nodules | Rigid bronchoscopy, stent placement (SEMS/silicone/Y-stent), balloon bronchoplasty, electrocautery/APC/cryotherapy/laser, endobronchial tumor debulking, photodynamic therapy, brachytherapy, EBUS-TBNA, EUS-B-FNA, electromagnetic navigation bronchology (ENB), cone-beam CT bronchoscopy, medical thoracoscopy, tunneled pleural catheter, indwelling pleural catheter | Rigid bronchoscope (Dumon/Efer), flexible bronchoscope (Olympus/Pentax/Fuji), EBUS scope, ENB platform (SuperDimension/Veran/Medtronic), Cone-beam CT, pleuroscopy system (Karl Storz), LIS for microbiology/pathology | **Missing** — No interventional pulmonology module, no bronchoscopy documentation, no ENB tracking, no medical thoracoscopy documentation |
| **Pulmonary Hypertension** | Pulmonary vascular disease | Pulmonary arterial hypertension (idiopathic/heritable/CTD-associated/CHD/portopulmonary/HIV/schistosomiasis), CTEPH, PH due to lung disease/hypoxia, PH due to left heart disease | Right heart catheterization (with vasoreactivity testing), PAH therapy (ERA/PDE5i/prostacyclin IPA/selexipag/riociguat), pulmonary thromboendarterectomy (CTEPH), balloon pulmonary angioplasty (CTEPH), 6MWT, CPET | PAH registry (REVEAL/COMPERA/PHAR), RHC documentation, echocardiography, CPET system (CareFusion/Cosmed), PAH therapy CDS (risk stratification COMPERA 2.0/REVEAL 2.0) | **Missing** — No PH module, no RHC documentation, no PAH therapy management, no registry |
| **Sleep Medicine** | Sleep disorders (also Psychiatry/Neurology) | OSA, central sleep apnea (Cheyne-Stokes), complex sleep apnea, insomnia, RLS/PLMD, narcolepsy (type 1/2), hypersomnolence, parasomnias, circadian rhythm disorders, sleep-related movement disorders | Polysomnography (PSG: attended/unattended), home sleep apnea testing (HSAT Type III/IV), CPAP/BiPAP/ASV auto-titration, CPAP adherence monitoring, MSLT, MWT, actigraphy, CBT-I | CPAP device (ResMed/Philips), PSG system (Compumedics/Natus/Cadwell/Alice), CPAP telemonitoring (AirView/EncoreAnywhere), Sleep lab EMR, AHI tracking | **Missing** — No sleep module, no PSG management, no CPAP adherence tracking |

## 1.5 Nephrology

| Subspecialty | Definition | Common Conditions | Procedures/Interventions | Tech Dependencies | GULA |
|---|---|---|---|---|---|
| **General Nephrology** | Kidney diseases | CKD (stage 1-5), AKI, glomerulonephritis (IgA/Membranous/FSGS/MCD/MPGN/Lupus/ANCA), nephrotic syndrome, nephritic syndrome, hypertension, electrolyte disorders, acid-base disorders, kidney stones, UTIs, PKD, Alport | Renal biopsy (US/CT guided), dialysis (HD/PD/CRRT), electrolyte management, fluid management, BP management, anemia management (ESA), CKD-MBD management, metabolic acidosis management | LIS for renal function (eGFR/creatinine/electrolytes/UA/proteinuria), dialysis machine (Fresenius/Gambro/NxStage), home PD cycler, renal biopsy tracking, transplant waitlist from UNOS/OPTN, calcineurin levels | **Partial** — Lab orders (creatinine/eGFR/electrolytes), dialysis units; no dialysis-specific EMR, no renal biopsy documentation, no CKD registry |
| **Dialysis (Intermittent Hemodialysis & Peritoneal Dialysis)** | Renal replacement therapy | ESRD on HD, ESRD on PD, acute HD for AKI/ESRD initiation, home HD, nocturnal dialysis | Hemodialysis (conventional/convective: HDF, HF, UF), peritoneal dialysis (CAPD/APD), vascular access management (AVF/AVG/CVC tunneled/non-tunneled), PD catheter insertion/removal, dialysis adequacy (Kt/V, URR), volume management/UF rate | Dialysis machine (Fresenius 5008/Gambro Artis/NxStage System One), water treatment system, PD cycler (Baxter Amia/HomeChoice), Kt/V modeling software, dialysis EMR (nephrology-specific), ESA/epoetin tracking | **Partial** — Hospital unit type supports dialysis unit, bed type supports dialysis; no dialysis-specific EMR, no HD treatment record, no Kt/V management, no vascular access tracking |
| **Transplant Nephrology** | Kidney transplant medical management | Kidney transplant evaluation, living donor evaluation, immunosuppression management, rejection (acute cellular/antibody-mediated/chronic), BK polyoma virus nephropathy, CNI nephrotoxicity, recurrent GN in transplant | Transplant evaluation (cardiac/pulmonary/malignancy/infection screening), immunosuppression (tacrolimus/MMF/prednisone/belatacept), protocol/for-cause biopsy, DSA monitoring, BK virus screening and management, anti-rejection therapy | UNOS/OPTN waitlist management, CPRA calculator, paired exchange, donor management (living/deceased), post-transplant protocol management, immunosuppression drug level management, DSA monitoring (Luminex single antigen bead assay) | **Missing** — No transplant nephrology module, no immunosuppression management, no DSA monitoring, no post-transplant protocol management |
| **Interventional Nephrology** | Dialysis access and procedures | Dialysis catheter dysfunction, AV fistula/graft stenosis/thrombosis/aneurysm, PD catheter malfunction/hydraulic failure/drain pain | Dialysis catheter placement (tunneled: IJV/SC/subclavian/femoral), PD catheter placement (laparoscopic/percutaneous/open), renal biopsy, AV fistula creation/revision, AV fistula thrombectomy/angioplasty/stent/graft, peritoneal equilibration test (PET) | Ultrasound-guided intervention skills, fluoroscopy C-arm, fistulogram/venography/angioplasty balloon, dialysis catheter kit (Tesio/AshSplit/Palindrome/HemoSplit/Gildea/Deerfield/Bard), PD catheter kit (Tenckhoff) | **Missing** — No interventional nephrology documentation |
| **Onco-Nephrology** | Kidney disease in cancer patients | Chemotherapy-induced AKI/CKD, tumor lysis syndrome, myeloma cast nephropathy, light chain deposition disease, thrombotic microangiopathy, radiation nephritis, post-transplant lymphoproliferative disorder, paraneoplastic GN | Electrolyte management (TLS: rasburicase/allopurinol), myeloma kidney management (bortezomib-based chemo + high cutoff HD), TMA workup (aHUS/TTP), cancer drug dose adjustment for kidney function, AKI in CAR T-cell therapy/HSCT | LIS for tumor lysis monitoring (uric acid/phosphate/creatinine/LDH/potassium/calcium), chemotherapy drug dose CDS for renal function, AKI alerting system | **Missing** — No onco-nephrology module, no TLS protocol CDS, no cancer drug dose adjustment CDS |

## 1.6 Endocrinology

| Subspecialty | Definition | Common Conditions | Procedures/Interventions | Tech Dependencies | GULA |
|---|---|---|---|---|---|
| **General Endocrinology** | Hormone and metabolic disorders | Diabetes (type 1/type 2/GDM), thyroid disorders (hypo/hyper/thyroiditis/nodules/goiter/cancer), obesity, metabolic syndrome, osteoporosis, pituitary disorders, adrenal disorders, lipid disorders | Diabetes management (insulin titration/CGM interpretation), thyroid ultrasound/FNA, dynamic endocrine testing (OGTT/ACTH stim/cortisol suppression/CRH/TRH/GHRH-arginine/glucagon stim/insulin tolerance test), DXA scan | EMR with diabetes flowsheet (BGM/CGM/insulin), CGM platform (Dexcom Clarity/Freestyle LibreView/Medtronic CareLink), insulin pump (Medtronic/Tandem/Omnipod), DXA scanner (Hologic/GE Lunar) | **Partial** — Lab orders (HbA1c/thyroid panel/hormones), clinical documentation; no endocrine-specific CDS, no CGM data integration, no insulin pump management |
| **Diabetes & Metabolic Disease** | Comprehensive diabetes care | Type 1 diabetes (autoimmune/latent LADA), type 2 diabetes, monogenic diabetes (MODY/neonatal), secondary diabetes (CFRD/post-transplant/steroid-induced/hemochromatosis), GDM, diabetic ketoacidosis (DKA), hyperosmolar hyperglycemic state (HHS) | Insulin therapy (MDI/CSII/patch pump/automated insulin delivery), GLP-1 RA/SGLT2i/DPP4i/insulin secretagogues/thiazolidinediones/metformin/AGIs, CGM (Dexcom G7/Freestyle Libre 3/Medtronic Guardian 4), AID systems (Omnipod 5/t:slim X2 Control-IQ/Medtronic 780G/Cami APS/iLet), diabetes self-management education (DSMES) | CGM platform, insulin pump with AID system, diabetes management app (mySugr/Glooko/Diasend/Clarity/LibreView/Tidepool), smart insulin pen (InPen/NovoPen6/NovoPenEcho), DKA protocol CDS | **Partial** — Lab orders (HbA1c/GMI/TIR/TAR/TBR/glucose), clinical documentation; no CGM data integration, no AID system data management, no diabetes registry |
| **Thyroidology** | Thyroid diseases | Hypothyroidism (Hashimoto/post-ablative/post-surgical/central), hyperthyroidism (Graves/thyroiditis/TSHoma), thyroid nodules, thyroid cancer (PTC/FTC/MTC/ATC), subacute thyroiditis (De Quervain/postpartum/silent), euthyroid sick syndrome, amiodarone-induced thyroid dysfunction | Thyroid ultrasound (ACR TI-RADS), thyroid FNA (Bethesda classification), RAI ablation (I-131 for hyperthyroidism/thyroid cancer), thyroid hormone therapy (levothyroxine/liothyronine/desiccated thyroid/combination T4+T3), anti-thyroid drugs (methimazole/PTU), thyroid hormone withdrawal or recombinant TSH for whole-body scan/thyroglobulin | Thyroid US with elasticiy and Doppler, LIS for thyroid function tests (TSH/T4/T3/TPO/Tg/TgAb/TSI/TRAb/calcitonin), ACR TI-RADS structured reporting, nuclear medicine for RAI therapy (dosimetry/post-therapy scan SPECT/CT) | **Partial** — Lab orders (TSH/free T4/T3/TPO/Tg/calcitonin), clinical documentation; no thyroid nodule management, no TI-RADS structured reporting, no RAI therapy workflow |
| **Pituitary & Neuroendocrinology** | Pituitary and hypothalamic disorders | Pituitary adenomas (prolactinoma/Cushing/ acromegaly/TSHoma/nonfunctioning), hypopituitarism (panhypo/selective), diabetes insipidus (central/nephrogenic), SIADH, craniopharyngioma, Rathke cleft cyst, lymphocytic hypophysitis | Pituitary MRI (thin-slice sella protocol), dynamic endocrine testing (OGTT for acromegaly, dexamethasone suppression/CRH/DDAVP for Cushing, ITT/glucagon/arginine/GHRH for GH deficiency, saline infusion/water deprivation test for DI/SIADH), transsphenoidal surgery, pituitary radiotherapy/SRS | Pituitary MRI (3T with dynamic contrast), laboratory with ultrasensitive GH/IGF-1/cortisol/ACTH/prolactin/FSH/LH/TSH/testosterone/estradiol), pituitary tumor board documentation (tumor registry), R1/R2-weighted pituitary MRI interpretation | **Missing** — No pituitary module, no dynamic endocrine testing workflow, no pituitary tumor registry |
| **Adrenal Disorders** | Adrenal gland diseases | Adrenal insufficiency (primary/Addison/secondary/tertiary), Cushing syndrome (pituitary/ectopic/adrenal), Conn syndrome/primary hyperaldosteronism, pheochromocytoma/paraganglioma, adrenal incidentaloma, CAH (21-hydroxylase deficiency classic/non-classic, 11-beta-hydroxylase, 17-alpha-hydroxylase, 3-beta-HSD, lipoid CAH), adrenal carcinoma | Dynamic testing (ACTH stim/cosyntropin for AI, dexamethasone suppression test/CRH/DDAVP for Cushing, saline infusion/captopril challenge/supine-standing aldosterone-renin ratio for PA, metanephrines/plasma free metanephrines for pheochromocytoma), adrenal vein sampling, adrenalectomy, adrenal radiation | LIS for cortisol/ACTH/aldosterone/PRA/metanephrines/catecholamines/17-OHP/DHEAS/androstenedione/testosterone/estradiol/corticosterone/11-deoxycortisol/renin), adrenal CT/MRI protocol, AVS laboratory | **Missing** — No adrenal module, no dynamic testing workflow, no AVS documentation, no adrenal tumor registry |
| **Bone & Mineral Metabolism** | Calcium and bone disorders | Osteoporosis (primary/secondary), osteomalacia, primary hyperparathyroidism, hypoparathyroidism, Paget disease of bone, renal osteodystrophy, hypercalcemia (PTHrP/1,25-D/malignancy/granulomatous/HIV/thyrotoxicosis/adrenal insufficiency/TN), hypocalcemia | DXA (central/peripheral), FRAX fracture risk assessment, bone turnover markers (P1NP/CTX), calcium infusion test, parathyroid localization US/sestamibi, cinacalcet/calcitriol management, zoledronic acid/denosumab/teriparatide/romosozumab/abaloparatide | DXA scanner (Hologic Horizon/GE Lunar Prodigy/Norland/ACE), LIS for PTH/vitamin D/calcium/phosphate/1,25-D/24-hour urine calcium/phosphate/cAMP, FRAX integration, IOF calculator, FLS coordinator workflow (fracture liaison service) | **Partial** — Lab orders for calcium/PTH/vitamin D/bone turnover markers, DXA orders; no osteoporosis registry, no FRAX CDS, no FLS workflow |
| **Reproductive Endocrinology** | Hormonal aspects of reproduction | See also OB/GYN for female and Urology for male: hypogonadism (male/female), delayed/ precocious puberty, PCOS, hirsutism, gynecomastia, functional hypothalamic amenorrhea | GnRH agonist/antagonist testing, clomiphene/testolactone testing, sex steroid measurement, semen analysis, gonadotropin replacement, aromatase inhibitor management | LIS for FSH/LH/testosterone/free testosterone/SHBG/estradiol/progesterone/AMH/inhibin B/anti-sperm antibodies, semen analysis system (CASA: Computer-Assisted Semen Analysis) | **Partial** — Lab orders for reproductive hormones, semen analysis results; no dedicated reproductive endocrinology module |

## 1.7 Other Internal Medicine Subspecialties

| Subspecialty | Definition | Common Conditions | Procedures/Interventions | Tech Dependencies | GULA |
|---|---|---|---|---|---|
| **Rheumatology** | Autoimmune and inflammatory joint/connective tissue diseases | RA, SLE, Sjogren, scleroderma/systemic sclerosis, dermatomyositis/polymyositis, MCTD, ANCA vasculitis (GPA/MPA/EGPA), giant cell arteritis/polymyalgia rheumatica, Takayasu arteritis, Behcet, ankylosing spondylitis, psoriatic arthritis, reactive arthritis, gout, pseudogout (CPPD), Still disease | Joint aspiration/injection (synovial fluid analysis), autoimmune serology interpretation, DMARD/biologic management (MTX/LEF/HCQ/SSZ, anti-TNF/abatacept/rituximab/tocilizumab/sarilumab/anakinra/belimumab/baricitinib/upadacitinib/filgotinib/janus kinase inhibitors), MSK ultrasound, bone densitometry | LIS for autoimmune panels (ANA/ENA/ANCA/dsDNA/RF/anti-CCP/complement/CRP/ESR), MSK US (with Doppler for synovitis), DXA scanner, disease activity score CDS (DAS28-CRP/BASDAI/CLASI/SLEDAI/HAQ), biologic registry | **Partial** — Lab orders (autoimmune panels/inflammatory markers), clinical documentation; no disease activity score CDS, no biologic registry, no MSK ultrasound documentation |
| **Hematology** | Blood disorders | Anemia (iron/B12/folate/AI/hemolytic/thalassemia/sickle cell/aplastic/BMF), leukopenia/neutropenia, thrombocytopenia, hemophilia (A/B), VWD, hemochromatosis, myeloproliferative neoplasms (PV/ET/MF/CML/CMML), myelodysplastic syndrome (MDS), amyloidosis, porphyria, histiocytosis, hypercoagulable states | Bone marrow biopsy/aspiration, chemotherapy for hematologic malignancies, apheresis (therapeutic plasma exchange), anticoagulation management, iron chelation, phlebotomy, coagulation factor replacement | LIS (CBC/coagulation/hemoglobin electrophoresis/flow cytometry/cytogenetics/molecular/FISH/NGS), bone marrow reporting system, apheresis machine (Spectra Optia/COBE), MDS registry (IWG-PM), MPN registry | **Partial** — Lab orders (CBC/coagulation/hemoglobinopathy/iron studies), clinical documentation; no hematology-specific EMR, no bone marrow documentation, no apheresis tracking |
| **Infectious Disease** | Bacterial, viral, fungal, parasitic infections | HIV/AIDS, TB, pneumonia, UTI, skin/soft tissue infections, osteomyelitis/septic arthritis, meningitis, endocarditis (native/prosthetic/IVDU), fungemia, C. diff, viral hepatitis, tropical diseases (malaria/dengue/leishmaniasis/schistosomiasis/Chagas/leprosy), emerging infections (COVID-19/MPOX/Marburg/Ebola/nipah/Zika/chikungunya) | Antimicrobial stewardship (prospective audit with feedback/preauthorization), infection control consultation, travel medicine consultation, HIV management (ART/PrEP/PEP), TB therapy (RIPE/MDR/XDR-TB protocols), antifungal therapy (echinocandin/azoles/amphotericin), immunocompromised host management | Microbiology LIS with antibiogram, antimicrobial stewardship software (TheraDoc/Sentri7/Firstline/Epic ASP), HH/SBAR/CDC NHSN for HAI surveillance | **Present** — Microbiology lab integration, antibiotic stewardship potential, epidemiology service; no dedicated ASP module |
| **Medical Oncology** | Cancer diagnosis and systemic treatment | Solid tumors (lung/breast/colorectal/prostate/pancreatic/GU/GYN/H&N/melanoma/sarcoma/GIST/NET/thyroid/unknown primary), tumor types by histology/grade/stage/molecular subtype/biomarker | Chemotherapy planning/administration, immunotherapy (checkpoint inhibitors/anti-PD-1/PD-L1/CTLA-4), targeted therapy (TKIs/mAbs/ADC/antibody drug conjugates, bispecific T-cell engagers, cellular therapy CAR-T cells), tumor board documentation, clinical trial enrollment | Oncology EMR (OncoEMR/Flatiron/Epic Beacon/ARIA/MOSAIQ), chemotherapy protocol library, tumor registry, clinical trial management system (Velos/OnCore/CTMS), biomarker testing CDS | **Partial** — Lab orders (tumor markers), clinical documentation, research registries; no oncology EMR workflow, no chemotherapy protocol module, no tumor board documentation |
| **Clinical Immunology/Allergy** | Immune system and allergic disorders | Allergic rhinitis/conjunctivitis, asthma, food allergy (IgE-mediated/FPIES/EoE), drug allergy (penicillin/cephalosporin/NSAID/chemotherapy/monoclonal antibody), venom allergy (Hymenoptera), anaphylaxis, immunodeficiency (CVID/CGD/SCID/HIES/LAD/chronic mucocutaneous candidiasis), mastocytosis/MCAS, angioedema (HAE)/urticaria | Allergy skin testing (SPT/intradermal/patch), serum specific IgE, component-resolved diagnostics, oral food challenge, drug desensitization, venom immunotherapy, SCIT/SLIT, immunoglobulin replacement (IVIG/SCIG), biologic therapy for asthma/urticaria/eczema (omalizumab/mepolizumab/benralizumab/reslizumab/dupilumab/tezepelumab/lebrikizumab) | LIS for specific IgE/tryptase/complement/C1-INH/immunoglobulins, skin testing software, challenge documentation, desensitization protocol library, immunotherapy extract management system, IVIG infusion documentation | **Partial** — Lab orders (allergy/immunology panels), clinical documentation; no allergy skin testing module, no immunotherapy tracking, no challenge workflow |
| **Geriatric Medicine** | Elderly patient care | Frailty, dementia (Alzheimer/vascular/Lewy body/FTD), falls, polypharmacy, urinary incontinence, pressure ulcers, delirium, osteoporosis, malnutrition, sarcopenia, CHF, COPD, CKD, multimorbidity, geriatric syndromes | Comprehensive geriatric assessment (CGA), falls risk evaluation, polypharmacy review/Beers criteria, cognitive assessment (MoCA/MMSE), functional assessment (ADL/IADL), frailty assessment (CFS/Fried/cognitive frailty), advance care planning | Geriatric-specific EMR templates (CGA/MoCA/clock-drawing/ADL/IADL/falls risk/Beers list), Frailty index calculator, polypharmacy deprescribing CDS, advance care planning documentation | **Missing** — No geriatric module, no CGA documentation, no Beers list integration |
| **Sports Medicine (IM)** | Exercise and athletic injuries in adults | Stress fractures, tendinopathy (Achilles/patellar/rotator cuff/gluteal/hamstring/elbow), ligament sprains (ACL/MCL/PCL/LCL/ankle), meniscal tears, concussions, osteoarthritis in athletes, heat illness/exertional, overtraining syndrome, RED-S, exercise-induced asthma/bronchoconstriction | MSK ultrasound, joint injection (corticosteroid/PRP/HA), concussion assessment (SCAT/ImPACT), exercise prescription, platelet-rich plasma injection, dextrose prolotherapy, bone marrow aspirate concentrate, tenotomy | MSK US (high-frequency linear probe), concussion management platform (ImPACT/Carepoint/SCAT5), biologic injection tracking, Athlete EMR/electronic health record with sports-specific templates | **Missing** — No sports medicine module, no MSK ultrasound documentation, no concussion assessment |
| **Sleep Medicine** | Sleep disorders (multidisciplinary) | See Sleep Medicine under Pulmonology — overlaps with Neurology, Psychiatry, and Pulmonology | PSG, HSAT, MSLT, MWT, CPAP/BiPAP/ASV, CBT-I, actigraphy, sleep study interpretation | Sleep lab platform, PSG equipment, CPAP telemonitoring, actigraphy, sleep diary apps, sleep disorder CDS | **Missing** — No sleep medicine module |
| **Critical Care Medicine (Intensivist)** | Life-threatening conditions in ICU | Sepsis/septic shock, ARDS, respiratory failure, AKI requiring CRRT, shock (distributive/cardiogenic/hypovolemic/obstructive), DIC, multi-organ dysfunction syndrome, severe pancreatitis, burns, polytrauma | MV (volume/pressure control/PRVC/APRV/PSV/HFOV/HFNC/NIV/ECMO), central line/arterial line/Swan-Ganz/PiCCO placement, bronchoscopy, POCUS (FoCUS/RUSH/BLUE/eFAST), CRRT/SLED/TTM/therapeutic hypothermia/lactate clearance/permissive hypercapnia/daily SBT/ABCDE bundle | ICU EMR (EPIC/Cerner/Meditech/GE CARESCAPE/Philips ICCA), ventilator (Drager/GE/Servo/Hamilton/Covidien Puritan Bennett), POCUS machine, CRRT (Prismaflex/NxStage), ECMO circuit, arterial blood gas analyzer, sedation scale (RASS/SAS) | **Partial** — ICU unit/bed management, clinical documentation; no ventilator/hemodynamic integration, no ECMO documentation, no CRRT flowsheet |
| **Hospital Medicine (Hospitalist)** | Inpatient general medical care | All adult acute illness requiring hospitalization, perioperative medical management, sepsis, pneumonia, CHF exacerbation, COPD exacerbation, AKI, DKA/HHS, GI bleeding, cellulitis, PE/DVT, stroke, delirium, alcohol withdrawal | Admission H&P, daily progress notes, discharge summary, medication reconciliation, central line/ LP/paracentesis/thoracentesis, code team participation, transitions of care, co-management with surgical services | Hospital EMR (EPIC/Cerner/Meditech), results management, CPOE, discharge planning tools, care coordination software (transition of care) | **Present** — Clinical documentation, hospital admission notes, progress notes, discharge summary, medication reconciliation, transitions of care module |
| **Clinical Pharmacology** | Drug therapy optimization | Complex pharmacotherapy, pharmacokinetic consultation, adverse drug reactions, drug interactions, drug-disease interactions, therapeutic drug monitoring, dose adjustment in organ failure, pregnancy/lactation drug safety | Pharmacokinetic consultation, dose adjustment (renal/hepatic), drug interaction analysis, TDM interpretation, adverse drug reaction assessment, medication error analysis | TDM calculators, drug interaction databases (Lexicomp/Micromedex/UpToDate/Facts & Comparisons), pharmacokinetic modeling software (DoseMe/InsightRx/Bayesian PK software), pregnancy registry | **Missing** — No clinical pharmacology module |
| **Adolescent Medicine** | Healthcare for ages 10-25 | Confidential care, reproductive health (contraception/STI/pregnancy), substance use disorder, eating disorders (anorexia/bulimia/BED), mental health (depression/anxiety/suicide), transition to adult care, vaccine-preventable disease, sports medicine | HEADSSS assessment (Home/Education/Activities/Drugs/Sexuality/Suicide/Safety), confidential care documentation, contraceptive counseling, STI testing/counseling, eating disorder medical stabilization, transition planning | Adolescent EMR with confidential care templates, HEADSSS/CD-RISK/PHQ-A/CRAFFT/GAD-7, motivational interviewing documentation | **Missing** — No adolescent medicine module, no confidential care documentation, no HEADSSS template |
| **Perioperative Medicine** | Pre-operative optimization and post-operative medical management | Pre-operative cardiac/ pulmonary/ diabetes/ anticoagulation/ anemia/ thyroid optimization, post-operative MI/ HF/ AF/ pneumonia/ UTI/ delirium/VTE/ AKI/ bleeding/ transfusion reactions | Pre-operative risk assessment (RCRI/NSQIP MICA/ACS NSQIP surgical risk calculator), beta-blocker/ statin/ anticoagulation management perioperatively, post-operative medical co-management, enhanced recovery after surgery (ERAS) pathways | Pre-operative assessment documentation, ERAS protocol CDS, risk calculator integration, medical co-management documentation | **Missing** — No perioperative medicine module, no ERAS protocol CDS, no risk calculator integration |
| **Brain Injury Medicine** | Medical management of TBI (also PM&R/Neurology) | Traumatic brain injury (mild/moderate/severe), post-concussive syndrome, subdural/epidural hematoma, intracerebral hemorrhage (traumatic), diffuse axonal injury, penetrating head injury | TBI management (ICP monitoring/CPP management/brain tissue oxygenation monitoring, jugular venous oximetry, microdialysis, EEG monitoring/seizure prophylaxis), post-concussion assessment (SCAT/ImPACT/BESS), cognitive rehabilitation coordination | ICP monitor (Camino/Bolt/Integra), brain tissue oxygen monitor (Licox), EEG/continuous EEG, TBI registry (TBI Model Systems), neuropsychological testing | **Missing** — No brain injury medicine module, no ICP documentation, no neuropsych testing tracking |

## 1.8 Infectious Disease (detailed)

| Subspecialty | Definition | Common Conditions | Procedures/Interventions | Tech Dependencies | GULA |
|---|---|---|---|---|---|
| **General Infectious Disease** | Diagnosis and management of complex infections | HIV/AIDS, TB, S. aureus bacteremia, candidemia, C. diff, complicated UTI/pyelonephritis, osteomyelitis, septic arthritis, infective endocarditis (native/prosthetic/IVDU-related), CNS infections (meningitis/encephalitis/brain abscess), intra-abdominal infections, skin and soft tissue infections (NSTI/necrotizing fasciitis/Fournier gangrene), device-related infections (CVC/VAD/PPM/ICD/VPS/orthopedic hardware), febrile neutropenia, FUO, post-surgical infections, prosthetic joint infection, orthopedic implant infection, shunt infection, VP shunt | Antibiotic selection/MIC-based dosing/therapeutic drug monitoring (vancomycin/aminoglycoside/beta-lactams/daptomycin/colistin), antimicrobial stewardship (prospective audit/feedback, preauthorization, de-escalation, IV-to-oral switch, duration optimization, therapeutic substitution, dose optimization, extended infusion beta-lactams, therapeutic drug monitoring for vancomycin/aminoglycoside/beta-lactams), OPAT (outpatient parenteral antimicrobial therapy) management, Infection prevention (CLABSI/CAUTI/VAE/SSI/MRSA/CDI/VRE/ESBL/CRE surveillance bundles, hand hygiene monitoring, isolation precaution management, outbreak investigation), TB contact investigation, travel medicine consultation (pre-travel counseling, vaccinations (yellow fever/typhoid/hepatitis A&B/rabies/meningococcal/Japanese encephalitis/cholera/ polio typhoid TAB), malaria prophylaxis (atovaquone-proguanil/doxycycline/mefloquine/chloroquine/tafenoquine/ primaquine/ Malarone), chemoprophylaxis, altitude illness prevention (acetazolamide), traveler's diarrhea self-treatment (azithromycin/rifaximin/ciprofloxacin), motion sickness/jet lag management), post-exposure prophylaxis (HIV PEP/nPEP/rPEP, hepatitis B, rabies, tetanus, meningococcal), pre-exposure prophylaxis (HIV PrEP: TDF/FTC (Truvada), TAF/FTC (Descovy), cabotegravir LA (Apretude)), C. diff treatment (oral vancomycin/fidaxomicin/metronidazole/bezlotoxumab/fecal microbiota transplantation/FMT/FMT capsule), immunocompromised host/transplant ID (CMV/EBV/BKV/HSV/VZV/HHV6/adenovirus, PCP prophylaxis (TMP-SMX/pentamidine/atovaquone/dapsone), mold-active prophylaxis (posaconazole/voriconazole/isavuconazole), antifungal therapy (echinocandins/triazoles/amphotericin/liposomal amphotericin), CMV management/preemptive/ganciclovir/valganciclovir/letermovir/maribavir/foscarnet/cidofovir, BK virus management (reduction of immunosuppression, cidofovir/leflunomide/FK778/IVIG/ fluoroquinolone/leftunomide rescue), PTLD management (rituximab/ reduction of IS), EBV monitoring by PCR, HHV6 encephalitis, nocardia/mycobacterium/legionella/pneumocystis/bartonella/listeria/nocardia/aspergillus/mucor/fusarium/scedosporium/lomentospora/talaromyces/histoplasma/blastomyces/coccidioides/paracoccidioides/penicillium/talaromyces/ sporotrichosis/cryptococcus/ Candida auris/ C. parapsilosis/ C. glabrata/ C. krusei/ C. lusitaniae/ T. marneffei | Microbiology LIS (culture/sensitivies/MICs/MALDI-TOF/PCR/NAAT/BioFire/GI panel/meningitis panel/respiratory panel/film array), antibiogram, antimicrobial stewardship software (TheraDoc/Sentri7/Firstline/Epic ASP/DPAS/VigilLanz/ILumen/ID Stewardship/LOINC/CLSI M100/M02/M07/M11/M24/M38/M44/M45/M51/M57/M59/M61), OPAT management software, travel clinic EMR, PEP tracking, PrEP monitoring | **Present** — Microbiology lab integration, epidemiology service, antibiotic stewardship potential; no dedicated ASP module, no OPAT management |
| **HIV Medicine** | Comprehensive HIV care | HIV/AIDS, acute HIV, chronic HIV (ART management, resistance testing, adherence support), AIDS-defining illnesses (PCP/Toxoplasma/Mycobacterium avium/CMV/ Cryptococcus/ lymphoma/KS/ PML/ wasting syndrome), HIV-associated comorbidities (CVD/CKD/liver disease/osteoporosis/neurocognitive impairment/ depression/non-AIDS malignancies), HIV and pregnancy (PMTCT), HIV and TB co-infection, HIV and hepatitis B/C co-infection, HIV-associated lipodystrophy, immune reconstitution inflammatory syndrome (IRIS) | ART regimen selection (NNRTI/NRTI/PI/INSTI/entry inhibitor/FI/CCR5 antagonist/ CD4 post-attachment inhibitor/attachment inhibitor/ capsid inhibitor/ maturation inhibitor/ pharmacokinetic booster: darunavir/cobicistat/ritonavir), ART resistance testing (genotype/phenotype/Trofile for CCR5 tropism), HIV viral load, CD4 count monitoring, HLA-B*5701 screening, PrEP and nPEP, rapid ART initiation (same-day ART/RAPID ART), antiretroviral pregnancy registry, HIV and aging comorbidity screening | HIV EMR (CAREWare/LABAS/LAB/DHCS/ARMS/ eClinicalWorks/ Epic/ Athena/ NextGen/ Centricity/ NXGN/ Azara Healthcare/ DRVS/ Power BI/ Tableau/ RSR/ HRSA HAB HIV/AIDS Bureau ADAP AIDS Drug Assistance Program, HIVQUAL/Ryan White), LIS for HIV viral load/CD4/genotyping/ HLA-B*5701/tropism, medication adherence tracking, PrEP adherence CDS (tenofovir/FTC concentrations, urine POC, DBS/ dried blood spot testing for PrEP adherence) | **Missing** — No HIV module, no ART management CDS, no HIV registry |
| **Medical Toxicology** | Poisoning and overdose management | Acetaminophen overdose, opioid overdose, NSAID overdose, antidepressant overdose (TCA/SSRI/SNRI/MAOI), neuroleptic malignant syndrome, serotonin syndrome, toxic alcohols (methanol/ethylene glycol/isopropanol), heavy metal poisoning (lead/mercury/arsenic/iron/cadmium/thallium), organophosphate/carbamate poisoning, carbon monoxide/caustic ingestion/snake/spider/ scorpion bite/venomous envenomation/brown recluse/ black widow/coral snake/rattlesnake/copperhead/cottonmouth/Gila monster/cone snail/stonefish/box jellyfish/blue ringed octopus/pufferfish fugu/strychnine/cyanide | Toxidrome recognition (anticholinergic/cholinergic/opioid/sedative-hypnotic/sympathomimetic/serotonin/neuroleptic malignant/ extrapyramidal/hallucinogenic), antidote administration (N-acetylcysteine (acetaminophen), naloxone (opioid), flumazenil (benzodiazepine, but contraindicated in mixed OD/ seizure), fomepizole/ethanol (alcohols), physostigmine (anticholinergic), sodium bicarbonate (TCA), lipid emulsion therapy (local anesthetic toxicity/ LA/ cyclic antidepressants/ calcium channel blocker/ beta-blocker/ bupropion/ verapamil/ diltiazem/ quetiapine/ lamotrigine/ tricyclic antidepressants/ lipid rescue), venom antivenom (CroFab/Anavip/BoyScout), digoxin immune fab (digitalis), glucagon (beta-blocker), high-dose insulin euglycemia (calcium channel blocker/beta-blocker), methylene blue (methemoglobinemia), hydroxocobalamin/sodium thiosulfate (cyanide), dimercaprol/BAL, succimer/DMSA, EDTA, penicillamine (heavy metals), deferoxamine/deferasirox/deferiprone (iron), pyridoxine (INH/Vitamin B6/ethylene glycol metabolic acidosis), L-carnitine (valproate), sodium phenylacetate/sodium benzoate/ arginine/ carglumic acid (ammonia/urea cycle), octreotide (sulfonylurea), dantrolene (malignant hyperthermia/ NMS), cyproheptadine (serotonin syndrome) | Toxicology laboratory (serum acetaminophen/salicylate/ethanol/methanol/ethylene glycol/iron/lithium/digoxin/carboxyhemoglobin/methemoglobin/cholinesterase/heavy metals), Poisindex/Toxnet (currently NIH, but also UpToDate/Micromedex/Poisindex clinical toxicology), antidote stocking management software, hospital code tox kit/antidote inventory tracking | **Missing** — No medical toxicology module, no antidote inventory tracking, no toxidrome CDS |

## 1.9 Hematology (detailed)

| Subspecialty | Definition | Common Conditions | Procedures/Interventions | Tech Dependencies | GULA |
|---|---|---|---|---|---|
| **General Hematology** | Comprehensive blood disorder management | Cytopenias (anemia/leukopenia/thrombocytopenia/pancytopenia), aplastic anemia/Bone Marrow Failure syndromes, hemolytic anemias (AIHA/ sickle cell/thalassemia/ G6PD/HS/HPP/PKD/ Hgb C/Hgb E/Hgb D/Hgb O/ Unstable hemoglobin variant/ MDS/PNH/congenital dyserythropoietic anemia/ macrocytic anemias: B12 folate/ copper deficiency/ MDS/ medication/ alcohol/ liver/ thyroid/ hypothyroidism/ pregnancy/ hemolysis/ leukemia/ aplastic/ pure red cell aplasia/ Diamond-Blackfan/ transient erythroblastopenia of childhood/ Fanconi/ dyskeratosis congenita/ Shwachman-Diamond/ Pearson syndrome/ congenital sideroblastic anemia/ mitochondrial cytopathy/ Pearson syndrome), hemoglobinopathies, coagulopathies (hemophilia A/B, VWD, factor deficiencies, acquired coagulation factor inhibitors), hypercoagulable states (inherited: Factor V Leiden/Prothrombin G20210A/AT deficiency/Protein C deficiency/Protein S deficiency/ MTHFR/PAI-1/ elevated Lp(a)/dysfibrinogenemia; acquired: antiphospholipid syndrome/ HIT/MPN/cancer/ pregnancy/ oral contraceptives/inflammation/nephrotic syndrome/Cushing/ obesity/Smoking/hyperhomocysteinemia) | Bone marrow aspiration and biopsy (posterior iliac crest/tibial in infants/anterior iliac crest/sternal), bone marrow processing (touch prep/core biopsy for BMBx/aspirate smears/ decalcified H&E/Jones silver stain/ IHC/ flow cytometry/ cytogenetics/FISH/Next-generation sequencing), therapeutic phlebotomy (PV/hemochromatosis/porphyria cutanea tarda/polycythemia secondary to CHD/esrd/CPAP/ testosterone/TRT/Erythropoietin/ Altitude/high-performance athletes/Epo doping testing), iron chelation therapy for transfusion-dependent anemia (deferoxamine/ deferiprone/ deferasirox), erythropoietin-stimulating agents (darbepoetin/ epoetin alfa/ epoetin beta/ epoetin zeta/ Mircera/ methoxy peg-epoetin beta/ Biosimilars: retacrit), granulocyte colony-stimulating factor (filgrastim/pegfilgrastim/lenograstim/nartograstim/ lipegfilgrastim/ efbemalenograstim alfa/ balugrastim/ empegfilgrastim/ biosimilar G-CSF), thrombopoietin receptor agonists (eltrombopag/ romiplostim/ avatrombopag/hetrombopag/ lusutrombopag/recombinant thrombopoietin), anticoagulation reversal (andexanet alfa for anti-Xa/ DOAC reversal, idarucizumab/Praxbind for dabigatran, vitamin K/ Octaplex/ Beriplex/ Kcentra/ 4F-PCC/ FEIBA for warfarin reversal, protamine for heparin, recombinant factor VIIa/NovoSeven/ FEIBA for hemophilia with inhibitors/ acquired hemophilia/ trauma/ ICH/ surgical bleeding, desmopressin/DDAVP for VWD type 1/2A/2M/ hemophilia A mild-moderate; tranexamic acid/epsilon-aminocaproic acid for mucous membrane bleeding/ heavy menstrual bleeding/ dental bleeding/ epistaxis/ post-partum hemorrhage/ trauma/ cardiac surgery | LIS (CBC/coagulation/ hemoglobin electrophoresis/HPLC/ IEF/capillary electrophoresis/ flow cytometry/ NGS panel/ FISH/cytogenetics/molecular/FISH/MLPA/Sanger sequencing/NGS for MDS/AML/MPN/ALL/CLL/ lymphoma/aplastic anemia/PNH/BMT/ hereditary hemochromatosis/ hereditary hypercoagulable state), apheresis machine (Spectra Optia/ COBE Spectra/ Amicus separator), coagulation/hemostasis analyzer (STA-R EVOLUTION/CS-5100/ACL Top/BCS XP/BCS/CA-7000/ Sysmex CS-5100/ Dade Behring/STAGO/Diagnostica Stago/Instrumentation Laboratory/ Werfen), bone marrow collection kit, bone marrow biopsy needle (Jamshidi/ T-Lok/ Henke Sass Wolf/ Angiotech/ MDTech/ CareFusion/ Cook/ Cardinal Health), Trephine needle (Angiotech/ T-Lok/ Simple+Secure/ MDTech/ HSW/ Angiotech/ MDTech), clot section for CD138 IHC/multiple myeloma/plasma cell dyscrasia/Cherry red/glycogen/PAS/chloroacetate esterase/nonspecific esterase/toluidine blue/reticulin stain/trichrome/Perls Prussian blue iron stain/Diff-Quik/Wright-Giemsa stain | **Partial** — Lab orders (CBC/coagulation/hemoglobinopathy/iron studies), clinical documentation; no hematology-specific EMR, no bone marrow documentation, no apheresis tracking, no PNH registry |
| **Hemostasis & Thrombosis** | Bleeding and clotting disorders | Hemophilia A (factor VIII deficiency: severe <1%, moderate 1-5%, mild 5-40%), hemophilia B (factor IX deficiency), von Willebrand disease (type 1/2A/2B/2M/2N/3 — RIPA, VWF multimers, VWF:RCo to VWF:Ag ratio, VWF:FVIIIB, VWFpp/VWF:Ag ratio, DDAVP challenge), rare bleeding disorders (factor I/fibrinogen deficiency/ dysfibrinogenemia/ factor II deficiency/prothrombin deficiency/ factor V deficiency/ combined factor V+VIII deficiency/ factor VII deficiency/ factor X deficiency/ factor XI deficiency/ factor XIII deficiency/ alpha-2-antiplasmin deficiency/ PAI-1 deficiency/ plasminogen deficiency/ congenital TTP/ Upshaw-Schulman syndrome/ ADAMTS13 deficiency), acquired hemophilia A (autoantibody to FVIII), acquired VWD (LVAD/LPAD/aortic stenosis/ Wilms tumor/ hypothyroidism/ lymphoproliferative/ autoimmune/myeloproliferative/ plasma cell dyscrasia/ amyloid/ medications (valproate/ ciprofloxacin/ tetracycline/ griseofulvin/ hydroxyethyl starch/ PPV/ JAK2 inhibitors/VEGFR TKI)), HIT (Heparin-induced thrombocytopenia: 4Ts score, anti-PF4/heparin ELISA, SRA/serotonin release assay, HIPA, platelet Act, optical density, HIT Alert/ IT-based HIT risk score calculator, argatroban/bivalirudin/ fondaparinux/ danaparoid), antiphospholipid syndrome (lupus anticoagulant/anti-cardiolipin/anti-beta2 glycoprotein I; triple positive highest risk, catastrophic APS), TTP (thrombotic thrombocytopenic purpura: ADAMTS13 activity <10%, PLASMIC score, ADAMTS13 inhibitor titer, ADAMTS13 autoantibody; PEX/plasmapheresis + steroids/ rituximab/ caplacizumab/ N-acetylcysteine, splenectomy for refractory TTP, TMA/ thrombotic microangiopathy workup), HUS (typical/STEC-HUS/ atypical aHUS/complement-mediated TMA: complement gene mutations, anti-factor H antibody, MCP/CD46, CFHR1-5 genes, eculizumab/ravulizumab/avacopan/ iptacopan, atypical HUS), DIC (overt DIC ISTH score >5: bleeding, platelets, PT-INR, fibrinogen, D-dimer; non-overt DIC: coagulopathy of sepsis, ISTH overt DIC score, ISTH DIC scoring, DIC treatment: anticoagulation (UFH/LMWH/danaparoid/ recombinant human soluble thrombomodulin/ antithrombin/ TFPI/ nafamostat/ FUT-175/ gabexate mesilate), supportive: FFP/platelets/cryoprecipitate/Vitamin K, underlying condition management, DIC different from coagulopathy of liver disease (low factor V, factor VIII normal in liver disease vs low in DIC, DIC vs TTP vs aHUS vs HELLP vs preeclampsia vs SLE/antiphospholipid vs HIT vs ITP vs drug-induced TMA vs post-transfusion purpura) | Hemostasis analyzer (STA R Max/ CS-5100/ ACL TOP/ BCS XP), platelet function testing (PFA-100/200/ Innovance PFA, Multiplate/ impedance aggregometry/ aggregometry/ light transmission aggregometry LTA/ VerifyNow aspirin/ P2Y12/ GP IIb/IIIa), VWF multimers (gel electrophoresis/chemiluminescence/ ELISA/ LIA/ WESTERMARK/ agarose gel electrophoresis/ immunoblot, rapid VWF multimer assay, VWF:RCo/VWF:GPIbR/VWF:GPIbM/ VWF:Ab / VWF:FVIIIB/ collagen binding VWF:CB/ VWFpp/ VWF:Ag/ VWF activity, RIPA (ristocetin-induced platelet aggregation), Mixing studies: PTT mixing (immediate/1-2 hour incubation to detect time-dependent inhibitor like factor VIII inhibitor), PT mixing (for lupus anticoagulant/ factor inhibitor mixing study/INR mixing study), DRVVT/ PTT-LA/ KCT/ Kaolin clotting time/ silica clotting time for lupus anticoagulant, dilute Russell viper venom time+hexagonal phase phospholipase neutralization to confirm lupus anticoagulant, anti-Xa activity for LMWH/UFH/fondaparinux, anti-IIa for heparin monitoring, DOAC level (anti-Xa for rivaroxaban/apixaban/edoxaban/ fondaparinux, direct thrombin inhibitor level/dilute thrombin time for dabigatran, Ecarin clotting time for dabigatran/argatroban, Hemoclot thrombin inhibitor assay for dabigatran | **Missing** — No hemostasis/thrombosis module, no coagulation lab data management, no anticoagulation management system, no TMA registry |
| **Sickle Cell Disease & Thalassemia** | Hereditary hemoglobin disorders | Sickle cell disease (HbSS/HbSC/HbS-beta thal/HbSO-Arab/HbSD/HbSE/HbS-Lepore/HbS-Memphis/ untyped sickle syndromes), sickle cell trait, beta-thalassemia (major/intermedia/minor/silent), alpha-thalassemia (silent carrier/trait/HbH disease/Hb Bart hydrops fetalis), HbE/beta thalassemia, HbH disease, Hb constant spring, hereditary persistence of fetal hemoglobin (HPFH), sickle cell disease complications: VOC pain crisis/ACS (acute chest syndrome)/stroke/TIA/ silent cerebral infarct/ priapism/ AVN/ leg ulcers/ retinopathy/ splenic sequestration/ aplastic crisis (parvovirus B19)/ hepatic sequestration/ pulmonary hypertension/ chronic kidney disease/ nephropathy/ proteinuria/ hematuria/ enuresis/ nocturnal enuresis/ osteomyelitis (Salmonella/Staphylococcus) | Pain management (NSAIDs/opioid PCA/ standing regimen/patient controlled analgesia/IV fluids/ incentive spirometry for acute chest syndrome prevention in VOC), hydroxyurea therapy (for HbF induction: starting dose 15-20 mg/kg/day, maximum 35 mg/kg/day, dose escalation per absolute neutrophil count/platelet count/reticulocyte count/HbF%/MTD), chronic transfusion therapy for primary/secondary prevention of stroke in SCD (target HbS <30% for primary prevention if TCD abnormal >200 cm/s TAMV in MCA, target pre-transfusion HbS <30-50% for secondary stroke prevention, simple vs exchange transfusion, manual partial exchange, automated red cell exchange with apheresis, RCE for acute stroke/chest syndrome/priapism/ multi-organ failure/COVID), erythrocytapheresis (automated red cell exchange), iron chelation therapy (deferoxamine SC/IV, deferasirox oral, deferiprone TID, combination chelation), L-glutamine oral daily (Endari), crizanlizumab humanized anti-P-selectin monoclonal antibody IV monthly (Adakveo), voxelotor HbS polymerization inhibitor (Oxbryta), LentiGlobin/Lovo-cel gene therapy for SCD, exagamglogene autotemcel/CASGEVY/CRISPR gene editing via CTX001, hydroxyurea management CDS | TCD ultrasound (TCD/TCCD/MCA TAMMV for SCD primary stroke prevention: normal <170 cm/s, conditional 170-199 cm/s, abnormal >200 cm/s, TAMMV mma), hemoglobin electrophoresis/HPLC/IEF/capillary electrophoresis, SCD newborn screening program, SCD registry, exchange transfusion documentation (automated RCE machine: Spectra Optia/ COBE Spectra), iron load monitoring (serum ferritin/ liver MRI T2* for iron/R2-MRI for liver iron concentration/ FerriScan/ R2* for cardiac iron T2* >20 ms normal, 10-20 ms moderate, <10 ms severe iron overload /LIC T2*), LIS for HbF% monitoring/ complete blood count/ hemolysis labs/LDH/ haptoglobin/ bilirubin/ reticulocyte count/ absolute neutrophil count/ absolute reticulocyte count/ platelet count/ Hgb S%/HgbF% | **Missing** — No SCD/thalassemia module, no TCD documentation/tracking, no exchange transfusion documentation, no hydroxyurea dose management CDS, no SCD registry |
| **Benign Hematology** | Non-malignant blood disorders excluding hemoglobinopathy (above) and excluding coagulation (above) | Immune thrombocytopenia (ITP: primary, secondary to SLE/APS/CVID/Evans syndrome/post-viral/post-vaccination/COVID/DITP/drug-induced/HIT/pregnancy/cirrhosis), autoimmune hemolytic anemia (warm AIHA/IgG, cold agglutinin disease IGM/CAD, mixed, paroxysmal cold hemoglobinuria PCH/D-L antibody, Evans syndrome AIHA+ITP, drug-induced hemolytic anemia: alpha-methyldopa/penicillin/ cephalosporins/NSAIDs/fludarabine/cladribine/ platinum agents/ibrutinib/ribavirin/ TMP-SMX/piperacillin-tazobactam/ceftriaxone), PNH: paroxysmal nocturnal hemoglobinuria (with/without thrombosis, LDH, complement inhibitor therapy eculizumab/ ravulizumab/ pegcetacoplan/ iptacopan/ danicopan), aplastic anemia (severe/vs hypoplastic MDS: PNH clone, telomere length, IST: ATG equine+cyclosporine+eltrombopag, eltrombopag/romiplostim, bone marrow transplant), cyclic neutropenia, severe congenital neutropenia (Kostmann: ELANE/HAX1/GFI1), myelodysplastic syndrome (MDS: IPSS-R very low/low/intermediate/high/very high risk, MDS treatment: lenalidomide for del5q (Revlimid), luspatercept for ring sideroblasts (Reblozyl), hypomethylating agents: azacitidine/decitabine, IST for hypoplastic MDS similar to AA, allogeneic stem cell transplant, MDS/MPN overlap: CMML, MDS with ring sideroblasts and thrombocytosis MDS-RS-T: SF3B1+JAK2 V617F), pure red cell aplasia (PRCA: parvovirus B19/thymoma/post ABO-mismatched BMT/ large granular lymphocyte LGL leukemia/autoimmune), hemophagocytic lymphohistiocytosis (HLH: primary familial/ secondary to infection/malignancy/ autoimmune/ macrophage activation syndrome MAS: HLH-2004 criteria/diagnostic criteria: fever, splenomegaly, cytopenia, hyperferritinemia, hemophagocytosis, low NK cell activity, elevated sCD25/IL2RA, hypertriglyceridemia/hypofibrinogenemia, ferritin >500 ng/mL, HScore >169, HLH treatment: dexamethasone/etoposide/cyclosporine/anti-IL1: anakinra for MAS/ anti-IFNgamma: emapalumab for refractory HLH, HSCT for familial HLH), histiocytic disorders (Langerhans cell histiocytosis LCH/Rosai-Dorfman/Erdheim-Chester), TMA (thrombotic microangiopathy above at TTP/aHUS) | LIS (CBC/ reticulocyte count/ bilirubin (indirect)/ LDH/ haptoglobin/ DAT direct antiglobulin test/ IAT indirect antiglobulin test/ Donath-Landsteiner antibody/ cold agglutinin titer/ thermal amplitude/ eluate/ flow cytometry for PNH: FLAER/CD14/CD15/CD24/CD59/CD55 on monocytes and granulocytes, PNH clone size, GPI-AP deficient cells type I/II/III, FLAER assay, high-sensitivity PNH assay, PNH red cell and granulocyte clone quantitation), LIS for ferritin/ triglycerides/ sCD25/ sIL-2R/ fibrinogen/ NK cell activity/ cytokines/ hemophagocytosis on bone marrow aspirate/ cytopenias | **Missing** — No benign hematology module, no PNH registry, no ITP documentation, no HLH protocol CDS |


# 2. Surgery & Subspecialties

## 2.1 General Surgery

| Subspecialty | Common Procedures | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Surgery | Laparoscopic cholecystectomy, appendectomy, hernia repair, exploratory laparotomy | OR scheduling, instrument tracking, surgical notes | **Missing** |
| Colorectal Surgery | Colectomy, low anterior resection, abdominoperineal resection, ileostomy/colostomy | Stoma care documentation, bowel prep protocols | **Missing** |
| Hepatobiliary Surgery | Hepatectomy, Whipple procedure, bile duct repair, liver resection | Liver surgery planning software, PACS integration | **Missing** |
| Pancreatic Surgery | Pancreaticoduodenectomy, distal pancreatectomy, enucleation | Pancreatic enzyme management, glucose monitoring | **Missing** |
| Bariatric Surgery | Gastric bypass, sleeve gastrectomy, duodenal switch | Bariatric EMR, nutritional tracking, weight loss registry | **Missing** |
| Breast Surgery | Lumpectomy, mastectomy, sentinel lymph node biopsy, axillary dissection | Breast imaging integration, oncoplastic documentation | **Missing** |
| Endocrine Surgery | Thyroidectomy, parathyroidectomy, adrenalectomy | Calcium monitoring post-thyroidectomy, voice assessment | **Missing** |
| Trauma Surgery | Damage control laparotomy, thoracotomy, extremity fasciotomy | Trauma registry, ATLS protocol adherence | **Missing** |
| Surgical Critical Care | Post-operative ICU management, ventilator management, resuscitation | ICU flowsheet, ventilator integration | **Missing** |
| Transplant Surgery | Kidney, liver, pancreas, heart, lung transplantation | Transplant registry, organ allocation system, immunosuppression tracking | **Missing** |

## 2.2 Cardiothoracic Surgery

| Subspecialty | Common Procedures | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| Adult Cardiac Surgery | CABG, valve repair/replacement, aortic surgery, Maze procedure | Cardiopulmonary bypass machine, perfusion documentation | **Missing** |
| Congenital Heart Surgery | ASD/VSD repair, Tetralogy of Fallot repair, Norwood procedure | Pediatric cardiac surgery registry, bypass documentation | **Missing** |
| Thoracic Surgery | Lobectomy, pneumonectomy, esophagectomy, mediastinoscopy | Thoracic surgery database, lung cancer staging | **Missing** |
| Heart/Lung Transplant | Heart transplantation, lung transplantation, combined heart-lung | UNOS listing, transplant waiting list | **Missing** |

## 2.3 Neurosurgery

| Subspecialty | Common Procedures | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Neurosurgery | Craniotomy for tumor, spinal decompression, shunt placement | Neuronavigation (Stealth/BrainLab), OR microscope | **Missing** |
| Cerebrovascular Surgery | Aneurysm clipping, AVM resection, EC-IC bypass | Cerebral angiography, ICG angiography | **Missing** |
| Spine Surgery | Discectomy, fusion, laminectomy, deformity correction | O-arm navigation, spinal cord monitoring | **Missing** |
| Functional Neurosurgery | DBS for Parkinson's, epilepsy surgery, pain surgery | Stereotactic frame, MER recording, SEEG | **Missing** |
| Neuro-oncology | Glioma resection, meningioma resection, skull base surgery | Intraoperative MRI, fluorescence-guided surgery | **Missing** |
| Pediatric Neurosurgery | Myelomeningocele repair, craniosynostosis correction | Pediatric neurosurgery registry | **Missing** |
| Peripheral Nerve Surgery | Carpal tunnel release, nerve repair, nerve transfer | EMG/NCS integration, microsurgical instruments | **Missing** |
| Neurocritical Care | ICP monitoring, multimodality monitoring, post-op care | ICP monitor, brain tissue oxygenation, EEG | **Missing** |

## 2.4 Orthopedic Surgery

| Subspecialty | Common Procedures | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| Adult Reconstruction | Total hip/knee/shoulder/elbow arthroplasty | Joint registry (NJR/AOANJRR), implant catalog | **Missing** |
| Sports Medicine | ACL reconstruction, meniscal repair, rotator cuff repair | Arthroscopy tower, suture anchor inventory | **Missing** |
| Spine Surgery | Discectomy, fusion, laminectomy, vertebral augmentation | Pedicle screw navigation, bone graft tracking | **Missing** |
| Hand Surgery | Carpal tunnel, trigger finger, tendon repair, fracture fixation | Microsurgery instruments, hand therapy protocols | **Missing** |
| Foot & Ankle Surgery | Hammer toe correction, ankle fusion, Achilles repair | Orthobiologics tracking, gait analysis | **Missing** |
| Orthopedic Trauma | ORIF of fractures, intramedullary nailing, external fixation | Fracture registry, implant removal tracking | **Missing** |
| Pediatric Orthopedics | Scoliosis correction, clubfoot repair, hip dysplasia | Growth prediction software, brace management | **Missing** |
| Orthopedic Oncology | Sarcoma resection, limb salvage, endoprosthetic reconstruction | Musculoskeletal tumor registry | **Missing** |
| Musculoskeletal Oncology | Bone/soft tissue tumor management | MSK tumor staging, chemotherapy protocols | **Missing** |

## 2.5 Vascular Surgery

| Subspecialty | Common Procedures | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Vascular | Carotid endarterectomy, AAA repair, peripheral bypass | Vascular lab integration, duplex ultrasound | **Missing** |
| Endovascular | EVAR, TEVAR, peripheral angioplasty/stenting, thrombectomy | Angiography suite, contrast documentation | **Missing** |
| Venous Surgery | Varicose vein ablation, venous stenting | Venous duplex, compression therapy tracking | **Missing** |
| Dialysis Access | AV fistula/graft creation/revision | Vascular access registry, patency tracking | **Missing** |

## 2.6 Plastic Surgery

| Subspecialty | Common Procedures | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| Reconstructive Surgery | Free flap reconstruction, skin grafting, microsurgery | Microscope, Doppler monitoring, flap chart | **Missing** |
| Craniofacial Surgery | Cleft lip/palate repair, craniosynostosis, facial fracture | 3D CT reconstruction, virtual surgical planning | **Missing** |
| Hand Surgery | Tendon/nerve repair, finger replantation | Microsurgical instruments, hand therapy | **Missing** |
| Burn Surgery | Excision and grafting, escharotomy | Burn registry, fluid resuscitation protocol | **Missing** |
| Aesthetic Surgery | Rhytidectomy, blepharoplasty, rhinoplasty, abdominoplasty | 3D imaging for surgical planning | **Missing** |
| Gender-Affirming Surgery | Vaginoplasty, phalloplasty, chest reconstruction | Gender-affirming care protocols | **Missing** |

## 2.7 Pediatric Surgery

| Subspecialty | Common Procedures | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Pediatric Surgery | Congenital diaphragmatic hernia, esophageal atresia, Hirschsprung | Neonatal surgery registry | **Missing** |
| Pediatric Urology | Hypospadias repair, pyeloplasty, reflux surgery | Pediatric urodynamics | **Missing** |
| Fetal Surgery | Fetoscopic repair, EXIT procedure | Fetal MRI, high-frequency ultrasound | **Missing** |
| Pediatric Oncology Surgery | Wilms tumor resection, neuroblastoma resection | Pediatric oncology protocols | **Missing** |

## 2.8 Surgical Oncology

| Subspecialty | Common Procedures | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| Surgical Oncology | Tumor resection, lymphadenectomy, HIPEC | Tumor registry, margin assessment | **Missing** |
| Oncoplastic Surgery | Breast-conserving with reconstruction | 3D imaging, wire localization | **Missing** |
| Liver Metastasectomy | Hepatic resection for metastases | Intraoperative ultrasound | **Missing** |

---

# 3. Pediatrics & Subspecialties

| Subspecialty | Common Conditions | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Pediatrics | Well-child care, acute infections, growth monitoring | Pediatric EHR, growth charts (WHO/CDC), immunization registry | **Partial** — Care continuum module covers basic pediatric encounters |
| Neonatology | Prematurity, RDS, NEC, jaundice, congenital anomalies | NICU monitor integration, bilirubin nomogram, incubator monitoring | **Missing** — No NICU module |
| Pediatric Cardiology | Congenital heart disease, Kawasaki, rheumatic fever | Pediatric echo, fetal echocardiography | **Missing** |
| Pediatric Pulmonology | Asthma, CF, bronchopulmonary dysplasia | Spirometry (pediatric), CF registry | **Missing** |
| Pediatric Gastroenterology | IBD, celiac, eosinophilic esophagitis | Pediatric endoscopy documentation | **Missing** |
| Pediatric Nephrology | Nephrotic syndrome, UTI, congenital nephropathy | Pediatric dialysis documentation | **Missing** |
| Pediatric Endocrinology | Diabetes type 1, growth disorders, puberty | Pediatric growth hormone registry | **Missing** |
| Pediatric Hematology-Oncology | Leukemia, lymphoma, sickle cell, hemophilia | Pediatric chemotherapy protocols, port management | **Missing** |
| Pediatric Critical Care | Sepsis, respiratory failure, post-operative care | PICU monitor integration, ventilator management | **Missing** |
| Pediatric Emergency Medicine | Trauma, poisoning, respiratory distress | Pediatric resuscitation cart tracking | **Missing** |
| Pediatric Infectious Disease | Congenital infections, recurrent infections | Pediatric vaccine registry | **Missing** |
| Pediatric Neurology | Seizures, developmental delay, headache | Pediatric EMU, ketogenic diet management | **Missing** |
| Developmental-Behavioral Pediatrics | Autism, ADHD, learning disabilities | Developmental screening tools | **Missing** |
| Adolescent Medicine | Confidential care, eating disorders, substance use | HEADSSS assessment template | **Missing** |
| Child Abuse Pediatrics | Suspected abuse/neglect evaluation | Child advocacy documentation | **Missing** |
| Pediatric Genetics | Congenital anomalies, metabolic disorders | Genetic testing coordination | **Missing** |
| Pediatric Rheumatology | JIA, SLE, vasculitis | Pediatric disease activity scores | **Missing** |
| Pediatric Palliative Care | Symptom management, end-of-life | Pediatric pain assessment tools | **Missing** |

---

# 4. Obstetrics & Gynecology & Subspecialties

| Subspecialty | Common Procedures | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Obstetrics | Prenatal care, labor management, vaginal delivery, C-section | OB EMR, partograph, EFM integration | **Partial** — Maternal health in care_continuum |
| Maternal-Fetal Medicine | High-risk pregnancy, multiple gestation, fetal anomalies | Fetal ultrasound, NST, fetal echocardiography | **Missing** |
| General Gynecology | Well-woman exam, menstrual disorders, pelvic pain | Gynecology EMR, colposcopy documentation | **Missing** |
| Gynecologic Oncology | Ovarian/uterine/cervical/vulvar cancer surgery | Cancer staging, chemotherapy protocols | **Missing** |
| Reproductive Endocrinology | Infertility evaluation, ART/IUI/IVF | Fertility tracking, embryo management, IVF lab | **Missing** |
| Urogynecology | Pelvic organ prolapse, urinary incontinence | Urodynamics, pelvic floor PT referral | **Missing** |
| Minimally Invasive GYN | Laparoscopic hysterectomy, myomectomy, endometriosis excision | Laparoscopic tower integration | **Missing** |
| Pediatric & Adolescent GYN | Congenital anomalies, menstrual disorders in youth | Age-appropriate documentation | **Missing** |
| Menopausal Medicine | HRT management, osteoporosis prevention | Menopause symptom tracking | **Missing** |

---

# 5. Psychiatry & Subspecialties

| Subspecialty | Common Conditions | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Psychiatry | Depression, anxiety, bipolar, schizophrenia | Psychiatric EMR, PHQ-9/GAD-7 tracking, e-prescribing | **Missing** |
| Child & Adolescent Psychiatry | ADHD, autism, conduct disorder, eating disorders | Pediatric mental health screening | **Missing** |
| Consultation-Liaison Psychiatry | Delirium, depression in medically ill, somatic symptom | Hospital EMR integration | **Missing** |
| Forensic Psychiatry | Competency evaluation, criminal responsibility | Legal documentation, risk assessment tools | **Missing** |
| Addiction Psychiatry | Substance use disorders, MAT | SUD treatment tracking, controlled substance monitoring | **Missing** |
| Geriatric Psychiatry | Dementia, late-life depression, behavioral symptoms | Cognitive assessment tracking, caregiver resources | **Missing** |
| Psychosomatic Medicine | Stress-related disorders, health anxiety | Biopsychosocial assessment template | **Missing** |
| Emergency Psychiatry | Suicidal ideation, acute psychosis, agitation | Crisis documentation, involuntary hold forms | **Missing** |
| Interventional Psychiatry | ECT, TMS, ketamine therapy | ECT/TMS documentation, seizure tracking | **Missing** |

---

# 6. Neurology & Subspecialties

| Subspecialty | Common Conditions | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Neurology | Headache, epilepsy, stroke, neuropathy, dementia | Neurology EMR, NIHSS scoring | **Missing** |
| Vascular Neurology | Acute stroke, TIA, cerebral venous thrombosis | Stroke registry, tPA tracking, thrombectomy documentation | **Missing** |
| Epilepsy | Seizure disorders, status epilepticus | EMU integration, EEG management, video EEG | **Missing** |
| Movement Disorders | Parkinson's, essential tremor, dystonia | UPDRS tracking, DBS programming | **Missing** |
| Neuroimmunology/MS | Multiple sclerosis, neuromyelitis optica, autoimmune encephalitis | MS registry, infusion documentation, EDSS tracking | **Missing** |
| Neurocritical Care | Stroke, TBI, SAH, status epilepticus in ICU | ICP monitoring, continuous EEG, TCD integration | **Missing** |
| Neuromuscular Medicine | ALS, myasthenia gravis, muscular dystrophy | EMG/NCS integration, pulmonary function tracking | **Missing** |
| Neuro-oncology | Primary/secondary brain tumors | Tumor board documentation, chemotherapy protocols | **Missing** |
| Neurogenetics | Huntington's, hereditary ataxias, neurofibromatosis | Genetic counseling integration | **Missing** |
| Cognitive Neurology | Alzheimer's, frontotemporal dementia, Lewy body dementia | Cognitive assessment tracking (MoCA/MMSE) | **Missing** |
| Headache Medicine | Migraine, cluster, tension-type | Headache diary, preventive treatment tracking | **Missing** |

---

# 7. Radiology & Subspecialties

| Subspecialty | Common Studies | Technology Dependencies | GULA Coverage |
|-------------|---------------|----------------------|---------------|
| General Diagnostic Radiology | X-ray, CT, MRI, ultrasound interpretation | PACS, voice recognition reporting | **Present** — Radiology module exists, Cornerstone.js |
| Neuroradiology | Brain CT/MRI, spine imaging, CTA/MRA | Advanced neuro imaging, perfusion, DTI | **Partial** — PACS present |
| Musculoskeletal Radiology | Joint MRI, CT arthrography, musculoskeletal ultrasound | MSK PACS integration | **Partial** |
| Breast Imaging | Mammography, breast ultrasound, MRI, stereotactic biopsy | Breast imaging CAD, BI-RADS tracking | **Missing** |
| Cardiac Radiology | Coronary CTA, cardiac MRI, calcium scoring | Cardiac post-processing software | **Missing** |
| Abdominal Radiology | CT abdomen/pelvis, MR enterography, virtual colonoscopy | CT colonography software | **Missing** |
| Thoracic Radiology | Chest CT, lung nodule management, PE protocol | Lung-RADS tracking, nodule management | **Partial** |
| Pediatric Radiology | Pediatric radiation dose optimization | Pediatric PACS protocols | **Missing** |
| Interventional Radiology | Angiography, embolization, biopsy, drain placement, ablation | Angiography suite, radiation dose tracking | **Missing** |
| Nuclear Medicine | PET/CT, SPECT, bone scan, thyroid therapy | NM PACS, isotope inventory, dose tracking | **Missing** |
| Radiation Oncology | External beam, IMRT, SRS, SBRT, brachytherapy | Treatment planning system (Eclipse/Pinnacle/RayStation), OIS (ARIA/MOSAIQ), TPS integration | **Missing** |
| Emergency Radiology | Trauma CT/X-ray, acute findings | Emergency workflow, STAT reporting | **Partial** |

---

# 8. Emergency Medicine & Subspecialties

| Subspecialty | Common Conditions | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Emergency Medicine | Chest pain, abdominal pain, trauma, respiratory distress | ED EMR, tracking board, patient flow | **Present** — EMS module, triage |
| Emergency Medical Toxicology | Poisoning, overdose, envenomation | Toxicology lab integration, antidote inventory | **Missing** |
| Emergency Ultrasound | FAST exam, cardiac echo, vascular access | POCUS device integration, image archival | **Missing** |
| Disaster Medicine | MCI management, decontamination, triage | MCI tracking, hospital incident command | **Missing** |
| Wilderness Medicine | Environmental emergencies, austere care | Offline protocols, remote communication | **Missing** |
| Tactical Medicine | Point of injury care, tactical evacuation | Tactical medical kit documentation | **Missing** |
| Critical Care EM | Resuscitation, airway management, CVC placement | ED ventilator integration, CRRT in ED | **Missing** |
| EMS/Prehospital | Ambulance dispatch, field treatment, handoff | CAD system, ePCR, ambulance tracking | **Partial** — Dispatch in EMS module |
| Observation Medicine | Protocol-driven ED observation pathways | Observation order sets, status tracking | **Missing** |
| Sports Medicine (EM sideline) | Acute athletic injury, concussion sideline assessment | SCAT documentation, return-to-play tracking | **Missing** |
| Global Health EM | Resource-limited emergency care | Portable documentation, WHO protocols | **Missing** |

---

# 9. Anesthesiology & Subspecialties

| Subspecialty | Common Procedures | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Anesthesiology | GA induction/maintenance, neuraxial anesthesia, peripheral nerve block | Anesthesia machine, vital signs monitor, EMR integration | **Missing** |
| Critical Care Medicine | ICU ventilator management, resuscitation, TEE | ICU EMR, ventilator integration, hemodynamic monitoring | **Missing** |
| Pain Medicine | Epidural steroid injection, RF ablation, spinal cord stimulation | Pain procedure documentation, stimulator programming | **Missing** |
| Pediatric Anesthesia | Congenital heart, neonatal surgery anesthetic | Pediatric anesthesia machine, warming protocols | **Missing** |
| Cardiothoracic Anesthesia | CPB management, TEE, anticoagulation reversal | Bypass machine record, TEE archival | **Missing** |
| Neuroanesthesia | Cerebral protection, awake craniotomy, EEG monitoring | Neuro-monitoring integration, burst suppression tracking | **Missing** |
| Obstetric Anesthesia | Labor epidural, C-section anesthesia, hemorrhage management | PCA tracking, obstetric hemorrhage protocol | **Missing** |
| Regional Anesthesia | US-guided nerve block, catheter placement | Ultrasound guidance documentation, block tracking | **Missing** |
| Transplant Anesthesia | Liver/kidney/heart transplant anesthetic | OR record, immunosuppression timing | **Missing** |

---

# 10. Pathology & Subspecialties

| Subspecialty | Common Services | Technology Dependencies | GULA Coverage |
|-------------|----------------|----------------------|---------------|
| Anatomic Pathology | Surgical pathology, autopsy, frozen section | LIS integration, digital pathology, slide tracking | **Partial** — Lab results, no pathology module |
| Clinical Pathology | Lab management, test interpretation, consultation | LIS, middleware, QC management | **Present** — LIMS module |
| Surgical Pathology | Gross examination, microscopic diagnosis, synoptic reporting | Synoptic reporting (CAP protocols), voice recognition | **Missing** |
| Cytopathology | Pap smear interpretation, FNA adequacy assessment | ThinPrep integration, cytotechnology workload | **Missing** |
| Hematopathology | Lymph node pathology, bone marrow, flow cytometry | Flow cytometry analysis, digital morphology | **Partial** — Lab results only |
| Neuropathology | Brain tumor, neurodegenerative disease | IHC interpretation, molecular testing | **Missing** |
| Dermatopathology | Skin lesion diagnosis, melanocytic lesion assessment | Dermoscopy imaging integration | **Missing** |
| Renal Pathology | Glomerular disease, transplant biopsy, IF/EM | Electron microscopy documentation, IF tracking | **Missing** |
| Molecular Pathology | NGS, PCR, FISH, microarray | Molecular LIS, variant interpretation, bioinformatics pipeline | **Missing** |
| Forensic Pathology | Medicolegal autopsy, death investigation | Autopsy documentation, evidence chain of custody | **Missing** |
| Transfusion Medicine | Blood bank, component therapy, apheresis | Blood bank LIS, ISBT 128 barcode | **Partial** — Blood bank module |
| Pediatric Pathology | Perinatal autopsy, congenital malformation | Pediatric pathology reference | **Missing** |
| Pulmonary Pathology | Lung cancer, ILD, pulmonary infection | ILD registry, molecular testing | **Missing** |
| GI Pathology | IBD, Barrett's esophagus, colorectal cancer | Synoptic reporting, FIT tracking | **Missing** |
| GU Pathology | Prostate, bladder, kidney cancer diagnosis | Gleason scoring, molecular subtypes | **Missing** |
| Breast Pathology | DCIS/IDC diagnosis, biomarker assessment | IHC quantification, receptor status tracking | **Missing** |
| Soft Tissue/Bone Pathology | Sarcoma classification, grading | Sarcoma registry, molecular testing | **Missing** |

---

# 11. Ophthalmology & Subspecialties

| Subspecialty | Common Procedures | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Ophthalmology | Comprehensive eye exam, refractive error management | EMR with visual acuity, refraction, slit lamp integration | **Missing** |
| Cornea & External Disease | Corneal transplant, cross-linking, pterygium, dry eye | Specular microscopy, topography, pachymetry | **Missing** |
| Glaucoma | Trabeculectomy, drainage implant, SLT, VF progression | Perimetry (Humphrey/OCT), OCT imaging | **Missing** |
| Retina/Vitreous | AMD treatment, diabetic retinopathy, retinal detachment, macular hole | OCT, OCTA, fluorescein angiography, laser | **Missing** |
| Pediatric Ophthalmology | Strabismus surgery, amblyopia treatment, ROP screening | Pediatric vision screening tools | **Missing** |
| Neuro-ophthalmology | Optic neuropathy, visual field defects, pupil abnormalities | Visual field analyzer, OCT, neuroimaging integration | **Missing** |
| Oculoplastic Surgery | Ptosis repair, blepharoplasty, orbital decompression | Orbital imaging, facial measurement | **Missing** |
| Uveitis/Ocular Immunology | Intraocular inflammation, intermediate/posterior uveitis | Ocular imaging, immunomodulatory therapy tracking | **Missing** |
| Ocular Oncology | Intraocular tumor management, plaque brachytherapy | Ocular ultrasound, OCT, fundus photography | **Missing** |
| Refractive Surgery | LASIK, PRK, SMILE, ICL | Excimer laser, corneal topography, wavefront | **Missing** |

---

# 12. Dermatology & Subspecialties

| Subspecialty | Common Conditions | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General Dermatology | Acne, eczema, psoriasis, skin cancer screening | Dermatology EMR, dermoscopy imaging | **Missing** |
| Dermatopathology | Skin biopsy interpretation, melanocytic lesions | Dermpath LIS, IHC tracking | **Missing** |
| Pediatric Dermatology | Atopic dermatitis, hemangioma, congenital nevi | Pediatric dosing calculators | **Missing** |
| Procedural Dermatology | Mohs micrographic surgery, laser surgery, cryosurgery | Mohs mapping software, frozen section tracking | **Missing** |
| Cutaneous Oncology | Melanoma management, non-melanoma skin cancer | Skin cancer registry, sentinel node documentation | **Missing** |
| Contact/Irritant Dermatitis | Patch testing interpretation | Allergen database, patch test tracking | **Missing** |
| Immunodermatology | Pemphigus, pemphigoid, lupus erythematosus | Immunofluorescence documentation | **Missing** |
| Cosmetic Dermatology | Botox, filler, chemical peel, microneedling | Cosmetic procedure tracking, photographic documentation | **Missing** |
| Teledermatology | Store-and-forward, live video consultation | Telederm platform, image management | **Missing** |

---

# 13. Physical Medicine & Rehabilitation & Subspecialties

| Subspecialty | Common Conditions | Technology Dependencies | GULA Coverage |
|-------------|-------------------|----------------------|---------------|
| General PM&R | Low back pain, neck pain, fibromyalgia, post-stroke | Physiatry EMR, functional assessment tools | **Missing** |
| Spinal Cord Injury Medicine | Complete/incomplete SCI, neurogenic bowel/bladder | SCI registry, FIM scoring | **Missing** |
| Brain Injury Medicine | TBI rehabilitation, post-concussive syndrome | Cognitive assessment tracking, PTA monitoring | **Missing** |
| Pediatric Rehabilitation | Cerebral palsy, spina bifida, developmental delay | GMFCS tracking, orthotics management | **Missing** |
| Sports Medicine (non-surgical) | Tendinopathy, overuse injury, biomechanical assessment | Video gait analysis, running analysis | **Missing** |
| Pain Medicine | Chronic pain, complex regional pain syndrome, myofascial pain | Pain diary, functional outcome tracking | **Missing** |
| Electrodiagnostic Medicine | EMG, NCS, SSEP | EMG machine integration, normative database | **Missing** |
| Amputee Rehabilitation | Prosthetic training, residual limb management | Prosthetic registry, socket fitting documentation | **Missing** |
| Stroke Rehabilitation | Motor recovery, aphasia, dysphagia | Stroke rehab protocols, modified Rankin tracking | **Missing** |

---

# 14. Preventive Medicine & Subspecialties

| Subspecialty | Common Services | Technology Dependencies | GULA Coverage |
|-------------|----------------|----------------------|---------------|
| General Preventive Medicine | Health screening, risk assessment, lifestyle counseling | Preventive care reminders, risk calculators | **Partial** — Screening in care continuum |
| Aerospace Medicine | Flight crew medical certification, hypobaric physiology | Aerospace medical documentation, altitude exposure tracking | **Missing** |
| Occupational Medicine | Worker health surveillance, fitness for duty, exposure tracking | Occupational health EMR, exposure registry, hearing conservation | **Missing** |
| Public Health | Population health, epidemiology, disease surveillance | Disease reporting system, outbreak investigation | **Present** — Public health module |
| Medical Toxicology | Occupational/environmental exposure, poisoning | Toxicology lab integration | **Missing** |
| Undersea/Hyperbaric Medicine | Dive medicine, hyperbaric oxygen therapy | Hyperbaric chamber documentation, dive log | **Missing** |
| Addiction Medicine | Substance use treatment, MAT | Controlled substance agreements | **Missing** |
| Clinical Informatics | Health IT, data analytics, clinical decision support | Informatics dashboard, data quality monitoring | **Partial** — Analytics in research |
| Global Health | International health program management | Field data collection, WHO reporting | **Missing** |

---

# 15. Other Recognized Specialties

| Specialty | Scope | Technology Dependencies | GULA Coverage |
|-----------|-------|----------------------|---------------|
| Family Medicine | Comprehensive primary care for all ages | Family medicine EMR, preventive care, chronic disease management | **Partial** — Primary care in care_continuum |
| Medical Genetics & Genomics | Hereditary disease, genetic counseling, testing | Genetic testing lab integration, pedigree software, variant interpretation | **Missing** |
| Nuclear Medicine | Radionuclide imaging and therapy | Gamma camera PET/CT, dose calculation, isotope inventory | **Missing** |
| Allergy & Immunology | Allergic disease, immunodeficiency | Skin testing documentation, immunotherapy management | **Partial** — Lab tests |
| Clinical Informatics (physician) | HIS, CDS, clinical analytics, data governance | Informatics tools, clinical analytics platform | **Partial** — Research |
| Sleep Medicine (multidisciplinary) | Sleep disorder diagnosis and treatment | Polysomnograph, CPAP telemonitoring, sleep lab | **Missing** |
| Sports Medicine (multidisciplinary) | Athletic injury and performance | MSK ultrasound, concussion management | **Missing** |
| Pain Medicine (multidisciplinary) | Acute/chronic pain management | Pain assessment, procedure documentation | **Missing** |
| Hospice & Palliative Medicine | End-of-life symptom management, goals of care | Advance directive documentation, pain/symptom tracking | **Missing** |
| Medical Toxicology | Poisoning, environmental exposures | Toxicology lab, antidote inventory | **Missing** |

---

## APPENDIX A: Coverage Summary

| Category | Total Specialties | Complete | Present | Partial | Missing |
|----------|------------------|----------|---------|---------|---------|
| Internal Medicine | 18 | 0 | 2 | 8 | 8 |
| Surgery | 31 | 0 | 0 | 0 | 31 |
| Pediatrics | 18 | 0 | 0 | 1 | 17 |
| OB/GYN | 9 | 0 | 0 | 1 | 8 |
| Psychiatry | 10 | 0 | 0 | 0 | 10 |
| Neurology | 11 | 0 | 0 | 0 | 11 |
| Radiology | 13 | 0 | 1 | 4 | 8 |
| Emergency Medicine | 12 | 0 | 1 | 1 | 10 |
| Anesthesiology | 9 | 0 | 0 | 0 | 9 |
| Pathology | 16 | 0 | 2 | 3 | 11 |
| Ophthalmology | 10 | 0 | 0 | 0 | 10 |
| Dermatology | 8 | 0 | 0 | 0 | 8 |
| PM&R | 9 | 0 | 0 | 0 | 9 |
| Preventive Medicine | 8 | 0 | 1 | 1 | 6 |
| Other | 10 | 0 | 0 | 3 | 7 |
| **TOTAL** | **192** | **0** | **7** | **22** | **163** |

---

*End of Document — GLOBAL MEDICAL SPECIALTIES*

*This document represents a comprehensive discovery inventory of every recognized medical specialty and subspecialty mapped against the GULA Platform codebase. Coverage assessed as of July 2026. Specialties marked Missing represent future expansion opportunities.*
