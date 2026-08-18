# GULA P4/P0 Master Remediation Baseline

**تاريخ baseline:** 18 آب/أغسطس 2026

**مصدر المتطلبات:** `/home/ubuntu/upload/pasted_content.txt`

**الفرع:** `chore/security-ddos-hardening-clean`

**HEAD المحلي والبعيد:** `0cff2733` — `docs(audit): document complete doctor journey gaps`

## حالة Git

الفرع المحلي يتطابق مع `origin/chore/security-ddos-hardening-clean`، وworking tree نظيف وقت baseline. لن يُستخدم force-push، ولن تُحذف migrations أو بيانات.

## حالة CI الحالية

آخر نتائج workflows المرئية عبر GitHub على SHA أقدم `8ff68c4d8d335a5f7a8ddf20641f5e32b93f0367` كانت فاشلة في Changed Files Quality Gate وCI Pipeline وMobile iOS وIAM Hardening Gate وFormatting Check وFrontend Bundle Budget وConstitution Compliance وMobile Android وFrontend PWA وQuality Gate. يجب إعادة تشغيل CI بعد كل دفعة، ولا تعتبر نتائج SHA القديم دليلاً على حالة HEAD الحالي.

استعلام PR status rollup تعذر بسبب `Resource not accessible by integration`، لذلك لا توجد موافقة على إغلاق P4 من هذا الاستعلام.

## حالة قاعدة البيانات والهجرات

`alembic` غير موجود في بيئة shell الحالية، لذلك migration heads وcurrent غير مثبتين بعد. هذا blocker تحقق بيئي، وليس دليلاً على عدم وجود migrations. يجب تثبيت/استعمال البيئة الرسمية أو تشغيل الأمر من virtualenv المشروع قبل كتابة migration جديدة.

## المسارات المسجلة فعلياً

`backend/app/factory.py` يسجل فعلياً:

- `/patient-card`.
- `/clinical/orders` عبر `clinical_orders_routes`.
- `/clinical/documentation` عبر `clinical_documentation_routes`.
- `/pharmacy`.
- `/api/v1/clinical` عبر `clinical_gateway_router`.

وجود canonical router لا يعطل legacy routers تلقائياً.

## حارس الأسرار

`python3 scripts/security/check_public_secrets.py` نجح ولم يكتشف أسراراً عامة في الملفات المتتبعة. هذا لا يعالج حادثة مفتاح Android التاريخية؛ تدوير المفتاح وتطهير Git history ما زالا خارجياً ومطلوبين.

## حالة الدومينات

| المجال | الوضع في baseline | الخطر |
|---|---|---|
| ClinicalDocument | legacy in-memory routes موجودة، canonical durable غير مثبتة لهذا المسار | Critical candidate |
| ClinicalOrder | legacy in-memory routes موجودة، canonical read أقوى من write | Critical candidate |
| ClinicalAccessContext | بوابة القراءة تملك context resolver؛ shift/task/assignment المركزي غير مكتمل كدورة تشغيلية | High / incomplete |
| Patient Card | lab-scoped مع HMAC/rate-limit/audit، لكنه يعرض phone/health_id ويعيد token | High |
| Prescription | DB service مع lab filter جزئي، prescriber/state/substitution policy غير مكتملة | High |
| Encounter | readiness prototype فقط، check-in/triage/close محجوبة | Blocked |
| Results | `results.read` canonical محلياً؛ review/validate/ack lifecycle غير مكتمل | High / incomplete |
| Appointment/Referral | نماذج متعددة ومسارات citizen/national؛ canonical doctor journey غير مثبت | High / incomplete |
| Patient Identity | health_id/patient_id/national_id surfaces متعددة؛ canonical privacy policy غير مكتملة على كل المسارات | High |
| Demo Patient Management | local synthetic state ظاهر بمظهر تشغيلي | Operational blocker |
| Native parity | Web/PWA مثبتة محلياً، Android/iOS/Desktop runtime evidence غير مثبت | Unverified |
| Android signing | incident خارجي لم يُغلق | SECURITY_BLOCKED |
| P5 | لا يُفتح | BLOCKED |

## قواعد التنفيذ

لن تُعدّل Production أو Production database، ولن تُحذف migrations تاريخية، ولن تُعطّل authorization، ولن تُحوّل security failure إلى warning، ولن تُقبل client-provided actor/prescriber/organization/facility/workspace/tenant كحقيقة، ولن تُستخدم mock data لإثبات workflow.

أي إصلاح واسع يغير schema أو state machine سيُنفذ أولاً على models/migrations/tests محلياً، ثم يُتوقف قبل أي تشغيل Production. أي بقاء لـCritical/High أو test gap في authorization/clinical writes/prescription/patient identity/encounter يبقي P4 PARTIAL/BLOCKED.

## Definition of baseline completion

تمت قراءة ملف المتطلبات حتى السطر 1966، وحفظ الحالة الحالية، وتحديد أن العمل التالي يبدأ من inventory/canonical registry ثم context/authorization ثم durable document/order migrations، مع الاحتفاظ بـSAFE_STOP للحواجز الخارجية.


## ملحق تنفيذ P4/P0 — 18 آب/أغسطس 2026

بعد تنفيذ دفعة Clinical Gateway وواجهة frontend parity، أصبحت عقود الأوامر canonical التالية مثبتة في `frontend-v3/src/api/endpoints.ts`: دورة Encounter (create/start/complete)، دورة workflow (shift/assignment/task)، ومراجعة نتائج المختبر (`results.review`). كما صُححت عقود بطاقة المريض بحيث تعكس استجابة التاريخ التجميعية وتتعامل مع الطباعة كـHTML/Blob بدلاً من نموذج JSON.

| الفحص | النتيجة | الدليل |
|---|---|---|
| Frontend tests | ناجح: 70 اختباراً في 19 ملفاً | `/tmp/gula-p4-frontend-parity-tests.log` |
| Frontend lint | ناجح دون warnings مسموحة | `/tmp/gula-p4-frontend-parity-lint.log` |
| Frontend build/PWA | ناجح | `/tmp/gula-p4-frontend-parity-build.log` |
| Backend full regression | ناجح: 2727 passed، 4 skipped، 172 warnings خلال 327.08 ثانية | `/tmp/gula-p4-full-regression.log` |
| Public secret guard | ناجح، لا أسرار عامة محتملة في الملفات المتتبعة | `python3 scripts/security/check_public_secrets.py` |
| JSON registry validation | ناجح | `python3 -m json.tool docs/architecture/canonical-domain-registry-2026.json` |

تم تحديث `docs/architecture/canonical-domain-registry-2026.json` لإضافة حالة `REVIEW_CANONICAL_ADDED` لمراجعة النتائج، و`EHR_DURABLE_QUERIES` لسجل أدوية المواطن، و`ENCOUNTER_WORKFLOW_CONTRACTS_ADDED` لعقود parity المرتبطة بـEncounter وShift وAssignment.

لا تغيّر هذه النتائج حالة الحواجز الخارجية: تدوير مفتاح توقيع Android الإنتاجي وتطهير Git history بعد التدوير ما زالا يتطلبان جهة مخولة خارج هذه الجلسة. لذلك يبقى `P4 = SECURITY_BLOCKED`، ويبقى `P5 = BLOCKED`، كما تبقى Department وReferral وAppointment وDiagnosticReport وAuditEvent وConsent فجوات canonicalization أو governance موثقة وليست مكتملة.
