# GLOSI Roadmap

**Version:** 1.0.0
**Date:** 2026-11-15
**Status:** Phase 0 PASS; Phase 1 PASS; Phase 2 PASS; Phase 3 PARTIAL; Phase 4 PARTIAL; Phase 5 initiation report published. No project approved.

---

## 1. المبادئ

- الأولوية لاستقرار GULA Stable v1.0.0.
- لا تغيير في GULA Core أو قاعدة البيانات بسبب GLOSI.
- لا اعتماد مشروع من البحث وحده.
- كل مرحلة تنتهي بتقرير حالة (PASS/FAIL/BLOCKED/PARTIAL/NOT RUN/UNKNOWN).

## 2. المراحل

### Phase 0 — Discovery ✅
- فحص المستودعين وحالة Git.
- التأكد من عدم وجود سجل GLOSI سابق.
- جرد أصول البحث القائمة (`docs/discovery`, `docs/health-tech`, `docs/architecture`).
- تحديد نقاط التكامل والمخاطر.
- التقرير: `REPORTS/PHASE_0_DISCOVERY.md`.

### Phase 1 — Governance ✅
- تأسيس الحوكمة والأدوار والصلاحيات.
- سياسة الأمن والترخيص.
- سياسة التكامل.
- نموذج التقييم من 100 نقطة.
- التقارير: `REPORTS/PHASE_1_GOVERNANCE.md`.

### Phase 2 — Registry ✅
- مخطط السجل وملف JSON.
- المدقق الآلي (Python stdlib).
- اختبارات سلامة السجل.
- التقرير: `REPORTS/PHASE_2_REGISTRY.md`.

### Phase 3 — Initial Research ⚠️ PARTIAL
- 16 مورداً في الدفعة الأولى.
- تحقق من المصدر والإصدار والترخيص والصيانة.
- تسجيل `PARTIAL` و`LOW` لكل السجلات؛ لا درجة كلية ولا اعتماد.
- التقرير: `REPORTS/PHASE_3_INITIAL_RESEARCH_BATCH_1.md`.

### Phase 4 — Quality Assurance ⚠️ PARTIAL
- تشغيل المدقق والاختبارات.
- التحقق من التصدير والاستعادة.
- مراجعة اتساق الوثائق والروابط.
- لا مراجعة أمنية/قانونية بشرية بعد.
- التقرير: `REPORTS/PHASE_4_QUALITY_ASSURANCE.md`.

### Phase 5 — Reporting ✅
- تقرير التأسيس النهائي.
- ترتيب فرص الاستفادة.
- أولويات البحث التالية.
- التقرير: `REPORTS/PHASE_5_PROGRAM_INITIATION_REPORT.md`.

## 3. الدفعات البحثية التالية

| الدفعة | النطاق | الأولوية |
|---|---|---|
| B2 | المعايير والمصطلحات: FHIR R4, HL7 v2, DICOM, LOINC, SNOMED CT, ICD, UCUM, IHE | عالية |
| B3 | الهوية والخصوصية: SMART on FHIR، OpenID Connect، Consent Management، Record Linkage/MPI | عالية |
| B4 | الصحة العامة والترصد: أدوات WHO، Outbreak، Contact Tracing، OpenHIE components | متوسطة |
| B5 | البنية والمزامنة: CRDT، Conflict Resolution، DTN/Mesh، Backup/DR | متوسطة |
| B6 | الذكاء الاصطناعي السريري: تقييم محلي، RAG، معرفة طبية، حوكمة | متوسطة |
| B7 | البيانات المفتوحة والاختبار: Synthea، datasets، simulation | منخفضة |
| B8 | الأنظمة الوطنية: تجارب OpenHIE/National HIE الحكومية | منخفضة |

## 4. آلية الاكتشاف المستمر (تصميم فقط، غير منفذة)

| المهمة | مصدر مجاني | التنفيذ الحالي |
|---|---|---|
| إصدارات جديدة | GitHub Releases API | يدوي عند المراجعة |
| توقف الصيانة | `pushed_at` + سجل الإصدارات | يدوي |
| ثغرات | GitHub Advisories / OSV.dev / NVD | غير منفذ |
| تغيّر الترخيص | LICENSE/NOTICE diff | غير منفذ |
| أبحاث جديدة | Crossref/PubMed/WHO | غير منفذ |
| مقارنة أداء | تقارير مستقلة فقط | غير منفذ |
| بدائل | بحث يدوي موثق | جزئي |

**ممنوع الآن:** خدمات مدفوعة، مفاتيح API، مراقبة دورية آلية، أو تنفيذ قرارات دمج.

## 5. مؤشرات نجاح البرنامج

1. سجل متسق وقابل للتحقق آلياً.
2. مقياس تقييم موحد مع أدلة.
3. مصادر رسمية قابلة للتتبع.
4. قرارات موثقة وقابلة للمراجعة.
5. خفض تكرار التطوير دون خفض الجودة.
6. حماية قانونية وأمنية.
7. عدم تأثير على استقرار GULA.
8. قابلية تصدير/استعادة.
9. تقارير مراحل موثقة.
10. وضوح الفرص التالية لـGULA.

## 6. شروط التوقف

يتوقف العمل ويُطلب قرار بشري عند:
- الحاجة لدمج كود خارجي في GULA.
- تغيير قاعدة بيانات أو ترحيل.
- اعتماد قانوني أو أمني نهائي.
- إضافة خدمة مدفوعة.
- تغيير معماري في Core أو Platform-Core.
