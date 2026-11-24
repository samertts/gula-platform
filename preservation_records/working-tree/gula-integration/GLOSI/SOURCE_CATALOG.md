# GLOSI Source Catalog

**Version:** 1.0.0
**Date:** 2026-11-15
**Purpose:** تحديد المصادر المقبولة، ودرجة موثوقيتها، وطريقة التحقق منها.

---

## 1. تصنيف الموثوقية

| المستوى | الوصف | يُستخدم كدليل؟ |
|---|---|---|
| **A — Primary Official** | المستودع الرسمي، موقع المشروع، وثائق المطوّر، الإصدارات الرسمية | نعم، دليل أساسي |
| **B — Standards Body** | HL7، IHE، ISO، WHO، NIST، DICOM، UCUM | نعم، دليل معياري |
| **C — Peer-Reviewed** | مجلات محكمة، مراجعات منهجية، دراسات سريرية | نعم مع توثيق المنهج |
| **D — Government / Institutional** | وزارات صحة، برامج وطنية، جهات حكومية | نعم مع توثيق المصدر |
| **E — Secondary Aggregator** | فهارس، أدلة مجتمعية، مقالات تقنية | مساعد فقط، لا يُعتمد وحده |
| **F — Marketing** | صفحات تسويقية، ادعاءات بلا مصدر | لا |

---

## 2. المصادر الرسمية للدفعة الأولى

| المورد | المصدر الأساسي | مصدر ثانوي | مستوى |
|---|---|---|---|
| OpenELIS Global | https://github.com/DIGI-UW/OpenELIS-Global-2 | https://openelis-global.org/ | A |
| SENAITE | https://github.com/senaite/senaite.core | https://www.senaite.com/ | A |
| OpenMRS | https://github.com/openmrs/openmrs-core | https://openmrs.org/ | A |
| Bahmni | https://github.com/Bahmni/bahmni-core | https://bahmni.org/ | A |
| DHIS2 | https://github.com/dhis2/dhis2-core | https://dhis2.org/ + https://community.dhis2.org/ | A |
| SORMAS | https://github.com/SORMAS-Foundation/SORMAS-Project | https://sormas.org/ | A |
| OpenHIE | https://ohie.org/ | https://github.com/openhie/openhie-specification | A/B |
| OpenHIM | https://github.com/jembi/openhim-core-js | https://openhim.org/ | A |
| HAPI FHIR | https://github.com/hapifhir/hapi-fhir | https://hapifhir.io/ | A |
| Open Concept Lab | https://github.com/OpenConceptLab/oclapi2 | https://openconceptlab.org/ | A |
| Keycloak | https://github.com/keycloak/keycloak | https://www.keycloak.org/ | A |
| OpenBao | https://github.com/openbao/openbao | https://openbao.org/ | A |
| OpenTelemetry | https://github.com/open-telemetry/opentelemetry-collector | https://opentelemetry.io/ | A |
| Prometheus | https://github.com/prometheus/prometheus | https://prometheus.io/ | A |
| Apache CouchDB | https://github.com/apache/couchdb | https://couchdb.apache.org/ | A |
| Automerge | https://github.com/automerge/automerge | https://automerge.org/ | A |

## 3. مصادر المعايير والتبادل

| المعيار | المصدر الرسمي | ملاحظة ترخيص |
|---|---|---|
| HL7 FHIR R4 | https://hl7.org/fhir/R4/ | HL7 IP policy / trademark |
| HL7 v2 | https://www.hl7.org/implement/standards/ | HL7 IP policy |
| DICOM | https://www.dicomstandard.org/ | مجاني للاستخدام مع شروط |
| LOINC | https://loinc.org/ | ترخيص LOINC |
| SNOMED CT | https://www.snomed.org/ | عضويات/تراخيص وطنية |
| ICD | https://icd.who.int/ | WHO |
| UCUM | https://ucum.org/ | مراجعة منفصلة |
| IHE Profiles | https://www.ihe.net/ | IHE IP policy |
| OpenHIE Specification | https://github.com/openhie/openhie-specification | MPL-2.0 + CC BY 4.0 |

**تنبيه:** الترخيص المعلن للمعيار لا يعني تلقائياً حرية استخدام المصطلحات أو الخرائط أو الترجمات. كل معيار يحتاج مراجعة قانونية مستقلة.

## 4. طريقة التحقق (المرحلة الحالية)

1. **تحديد الهوية:** اسم المستودع الرسمي والجهة المالكة من صفحة GitHub الرسمية أو موقع المشروع.
2. **البيانات الوصفية:** استخدام GitHub REST API العام (بدون مصادقة) للحصول على:
   `full_name`, `license.spdx_id`, `pushed_at`, `archived`, `default_branch`, `description`.
3. **آخر إصدار:** `/releases/latest`؛ إذا لم يوجد، تُستخدم صفحة الإصدارات الرسمية أو tags مع توضيح ذلك.
4. **الترخيص:** التحقق من ملف `LICENSE` الخام في المستودع عند غياب SPDX.
5. **الصيانة:** `pushed_at` + الإصدار الأخير + حالة `archived`؛ لا يُستنتج النشاط من النجوم.
6. **التسجيل:** يُحفظ ملخص الاستخراج في `REPORTS/evidence/` مع التاريخ والروابط.
7. **التقييم:** يبقى `PARTIAL` حتى تكتمل المراجعة الفنية والأمنية والقانونية.

### حدود التحقق الحالي
- بيانات GitHub API ليست مراجعة قانونية.
- SPDX من GitHub قد يكون `NOASSERTION` حتى عند وجود ترخيص؛ تم فحص LICENSE يدوياً عند الحاجة.
- `pushed_at` لا يثبت وجود إصدار مستقر أو دعم أمني.
- لا يتم فحص CVE أو SBOM أو الكود في الدفعة الأولى؛ لذلك `known_cves = UNKNOWN`.

## 5. تخزين الأدلة

| الملف | المحتوى |
|---|---|
| `REPORTS/evidence/phase3_source_verification.json` | ملخص آلي: المستودع، SPDX، آخر إصدار، `pushed_at`، `archived`، تاريخ الاستخراج |
| `REPORTS/PHASE_3_INITIAL_RESEARCH_BATCH_1.md` | التحليل والأدلة والملاحظات |
| `REGISTRY/registry.json` | السجل المعتمد للقراءة الآلية |

## 6. مصادر غير مقبولة

- Fork غير رسمي أو مرآة غير موثقة.
- مستودع بلا جهة مالكة واضحة.
- صفحة ترويجية تحتوي أرقاماً بلا رابط.
- بيانات مأخوذة من منشورات AI دون مصدر أولي.
- بيانات مرضى حقيقية أو أسرار تشغيلية.

## 7. الاستخدام المستقبلي

آلية الاكتشاف المستمر (غير منفذة الآن) ستستخدم:
- GitHub Releases API وAdvisories (مجانية).
- صفحات الإصدارات الرسمية وRSS إن وجد.
- NVD/CVE feeds المجانية.
- OSV.dev (مفتوح) لفحص الاعتماديات.
- SPDX/SBOM من المستودعات.

لا تُضاف مفاتيح API مدفوعة أو خدمات مراقبة خارجية في هذه المرحلة.
