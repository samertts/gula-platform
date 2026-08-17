# تقرير تنفيذ P4: أساس المواطن وخصوصية الهوية الوطنية

## 1. النطاق والقرار

يعتمد هذا التقرير على حالة الفرع الحالية ونتائج الاختبارات المحلية، وليس على أي تقرير قديم عند تعارضه مع Git أو runtime. نُفذت الإصلاحات الآمنة القابلة للتحقق فقط، ولم تُطبق أي migration على قاعدة إنتاج، ولم تُفعّل هوية حكومية أو OCR أو NFC أو Biometrics أو P5.

> **الحالة الحالية: `P4_PARTIAL` مع حدود `P4_UNVERIFIED` للـProduction وstaging الخارجي.**

لا يكفي نجاح CI أو وجود واجهة أو وثيقة لإعلان `P4_COMPLETE`. يتطلب الإغلاق الرسمي أدلة runtime وstaging وrollback وموافقات بشرية مستقلة.

## 2. baseline

الفرع التنفيذي هو `manus/government-patient-flow`. آخر تغييرات هذه الدفعة مبنية فوق إصلاحات device_bridge وتغطية الأمن غير الوطني. شجرة العمل يجب أن تُراجع قبل commit النهائي، ولا توجد صلاحية أو مسار تنفيذي لتعديل Production ضمن هذه الدفعة.

## 3. التغييرات المنفذة

| المجال | التغيير | الدليل |
|---|---|---|
| Golden Records | إزالة `national_patient_id` من serializer الروتيني، وإرجاع `national_identity_linked` كحالة منطقية فقط. | `backend/app/routes/national_data.py` و`test_national_data_privacy.py` |
| Tenant isolation | تقييد قراءة وحل Golden Records بمؤسسة المستخدم، والتحقق من ملكية `patient_id` قبل الإنشاء. | route-level filtering واختبارات أمنية |
| National ID linking | منع المستخدم المؤسسي العادي من تمرير `national_patient_id` في إنشاء Golden Record؛ الربط مقيد بسلطة `master_admin` إلى حين اعتماد governance أدق. | HTTP 403 وserver-side check |
| Citizen UI | إزالة عمود الرقم الوطني من `NationalDataPage` واستبداله بمعرفات تشغيلية وحالة ربط غير كاشفة. | `frontend-v3/src/pages/national-data/NationalDataPage.tsx` |
| OCR | إضافة `GOVERNMENT_IDENTITY_PROVIDER=UNVERIFIED` و`ENABLE_NATIONAL_ID_OCR=false` افتراضيًا، مع fail-closed في `/id-scan/scan`. | `backend/app/config.py` و`backend/app/routes/id_scan.py` |
| Device identity | إضافة scope `integration:results:write` ودعم ServiceAccount مربوط بمختبر في `/device/results`. | `service_accounts.py` و`device_results.py` |
| Device contract | تثبيت barcode وAuthorization في GulaClient واختبارات contract وBackend integration. | commit `3ba8705f` السابق واختبارات device bridge |

## 4. الهوية

النموذج المستهدف هو:

```text
National ID
    ↓
Identity Resolution / Master Identity
    ↓
GULA Health ID
    ↓
Patient ID
    ↓
Visit / Order / Report IDs
```

الرقم الوطني هو root identity anchor عند توفر تحقق رسمي، لكنه ليس معرف العرض اليومي ولا public resource identifier. Health ID معرف صحي للمواطن، وPatient ID معرف سياقي، وInsurance/Social Security ID معرف تغطية أو جهة دافعة. لا يجوز اشتقاق Health ID رياضيًا من National ID.

الحالة التنفيذية **جزئية**: توجد طبقات Identity وMPI وتشفير/HMAC في المستودع، لكن تحقق Government Identity Provider الرسمي وقيم Production ما زالا غير موثقين في هذه البيئة، ولذلك يبقى `GOVERNMENT_IDENTITY_PROVIDER=UNVERIFIED` هو الوضع الآمن.

## 5. الخصوصية

لا تعرض الواجهة الروتينية National ID في Dashboard أو نتائج المختبر أو الوصفات أو التقارير أو QR أو URL أو notification أو export. الإصلاح الحالي أغلق كشف Golden Records في الواجهة والـserializer. مسارات إدخال الرقم الوطني مثل identity linking وOCR ليست دليلًا على تحقق حكومي، وتحتاج purpose وauthorization وconfirmation وaudit ومزودًا رسميًا قبل تفعيلها.

لا يُسجل الرقم الوطني الخام في audit أو logs. يجب أن تبقى القيم المخزنة protected/encrypted أو HMAC بحسب الاستخدام، وألا تتكرر في domains بلا ضرورة. لا تُحذف سجلات طبية محفوظة قانونيًا عند حذف الحساب؛ يلزم retention policy معتمدة.

## 6. Citizen Foundation

يوجد في `frontend-v3` سطح citizen platform يستدعي dashboard/profile/health-summary/appointments/medications/lab-results، كما توجد مساحات الهوية وworkspace. الحالة ليست parity مكتملة؛ فالمصفوفة الحالية تصنف معظم المسارات `PARTIAL` لأن production alignment وruntime evidence غير متوفرين. لا يجوز إضافة واجهات وهمية لـappointments أو payments أو family management أو sharing ما لم يوجد Backend contract فعلي واختبارات وصلاحيات وتدقيق.

إكمال Citizen Foundation يحتاج verticals منفصلة: account/verification، health profile، appointments/check-in، laboratory results، reports، consent/data sharing، notifications، security center، privacy center، support والشكاوى. كل vertical يجب أن يملك Backend + permission + tenant/context policy + audit + tests + frontend states للتحميل والفراغ والخطأ والمنع و429 و503 وoffline.

## 7. الاختبارات

نجحت الاختبارات التالية بعد هذه الدفعة:

| المجموعة | النتيجة |
|---|---:|
| Golden serializer وSecurity Gate scope | 6 ناجحة، تحذير واحد غير حاجب |
| Device Bridge integration وdevice routes | 16 ناجحة، 3 تحذيرات غير حاجبة |
| Device Bridge service | 31 ناجحة، تحذير واحد غير حاجب |
| Privacy/OCR/Device/Security focused regression | 45 ناجحة، 4 تحذيرات غير حاجبة |
| OCR fail-closed + Golden privacy + device integration smoke | 6 ناجحة، 3 تحذيرات غير حاجبة |
| Backend suite الكاملة | **2691 ناجحًا، 4 متجاوزة، و252 تحذيرًا** |
| Frontend `pnpm run check` | ناجح: typecheck وVitest وcontract gates وbuild وbundle guard |

Security Gate الأخير أعاد **0 أخطاء و0 تحذيرات audit/SAST/SQL/Docker**، مع تحذيرين بيئيين فقط لأن Gitleaks وTrivy غير مثبتين في البيئة الحالية. فحوص credential لم تعد تعرض findings بعد تحويل fixtures الاختبارية إلى قيم مركبة غير قابلة للاستخدام.

## 8. ما بقي Partial أو Blocked أو Unverified

| البند | الحالة | سبب عدم الإغلاق |
|---|---|---|
| Government Identity Provider | `UNVERIFIED` | لا يوجد مزود رسمي موثق أو اعتماد حكومي متاح في البيئة |
| OCR/NFC/Biometrics | `BLOCKED` للتفعيل | ممنوع تفعيلها قبل governance وprovider وhuman approval |
| Production alignment | `UNVERIFIED` | لا توجد قراءة معتمدة من Railway/Vercel/Production runtime/database/flags |
| PostgreSQL live schema | `UNVERIFIED` | لم تُقرأ قاعدة Production ولم تُطبق migration |
| Mobile Android/iOS/Desktop parity | `NOT_BUILT/UNVERIFIED` | لا يوجد build evidence كامل في هذه الدفعة |
| Performance P50/P95/P99 | `PERFORMANCE_EVIDENCE_REQUIRED` | لا يجوز اختراع أرقام benchmark |
| Rollback rehearsal | `PARTIAL` | يلزم staging أو بيئة غير إنتاجية مستقلة لتجربة candidate → failure → rollback |
| Device results idempotency | `PARTIAL` | يلزم Idempotency-Key أو Inbox unique constraint واختبار timeout/retry لمنع duplicate LabResult |
| Full National ID reveal workflow | `BLOCKED` للتصميم الحالي | يلزم purpose/scope/confirmation/audit وpermission مخصص، لا يكفي role عام |

## 9. موافقات بشرية مطلوبة

تحتاج أي عملية Production أو database migration أو security exception أو breaking API أو Government Identity integration أو OCR/NFC/Biometrics أو public registration أو legal/privacy policy إلى موافقة بشرية صريحة. لا يُعتبر CI أو هذا التقرير موافقة.

## 10. القرار النهائي

```text
NATIONAL_ID_ARCHITECTURE_PARTIAL
P4_PARTIAL
P5_BLOCKED
```

السبب هو أن الإصلاحات المحلية الأمنية والخصوصية قابلة للاختبار، لكن أدلة Production وstaging، ومزود الهوية الرسمي، وidempotency السريري، وrollback، وmobile parity، والمراجعة القانونية والسريرية لم تُغلق بعد.

## 11. الخطوة التالية الدقيقة

إعادة تشغيل Backend suite وSecurity Gate على checkout نظيف، ثم تنفيذ staging smoke ببيانات اصطناعية يشمل cross-tenant، OCR disabled، service-account device results، timeout/retry/idempotency، وaudit verification. بعد ذلك تُرفع نتائج CI ومصفوفة P4 إلى مراجعة بشرية؛ ولا يبدأ P5 أو deployment قبل تحول كل blocker المطلوب إلى دليل مقبول.
