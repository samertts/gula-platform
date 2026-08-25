# متطلبات DMZ / Staging Zone لاستلام البيانات الخارجية في GULA

**الحالة:** تصميم وتنفيذ طبقة backend غير مفعلة افتراضياً؛ لا يعني هذا أن DMZ إنتاجية قد أُنشئت أو أن أي جهة خارجية أصبحت مرتبطة.

> **قاعدة تشغيلية:** لا تُرسل ملفات النقابات أو وزارة الصحة أو وزارة الداخلية إلى واجهة التطبيق العامة. يجب أن تدخل عبر قناة مخصصة، إلى تخزين quarantine مشفر، ثم تُعالج على دفعات محدودة بعد التحقق والمراجعة.

## 1. الحدود الشبكية

```text
الجهة المالكة
   │  allowlist + mTLS أو OAuth2 client credentials
   ▼
External Transfer Gateway / WAF
   │  لا اتصال بقاعدة البيانات
   ▼
Quarantine Object Storage (private, encrypted, immutable retention)
   │  manifest/checksum + malware/DLP/schema scan
   ▼
Staging Worker (شبكة معالجة معزولة)
   │  يكتب metadata المسموح فقط إلى GULA DB
   ▼
GULA Backend / Review Queue
   │  لا يقرأ الخام إلا worker مصرح
   ▼
Canonical professional metadata وقرارات المطابقة
```

يجب أن تكون منطقة الاستلام في شبكة فرعية منفصلة عن API وواجهة المستخدم وقاعدة البيانات. لا يُسمح بقاعدة البيانات باتصالات واردة من الإنترنت أو من gateway؛ المسار الوحيد يكون من worker عبر allowlist داخلي ومنفذ قاعدة البيانات، ويفضل عبر خدمة هوية workload أو mTLS. لا يُسمح للـworker بالوصول إلى بقية خدمات GULA إلا إلى endpoint أو queue محددة.

| المكوّن | الاتصالات المسموحة | الاتصالات الممنوعة |
|---|---|---|
| Transfer Gateway | HTTPS/SFTP من عناوين الجهات المعتمدة، object storage الخاص | قاعدة البيانات، الواجهة العامة، الشبكات الإدارية |
| Quarantine Storage | gateway للكتابة، scanner للقراءة، worker بعد نجاح الفحص | public access، anonymous listing، download من المستخدم |
| Malware/DLP Scanner | قراءة الكائن المعزول وكتابة نتيجة الفحص | الكتابة إلى canonical tables |
| Staging Worker | قراءة كائنات passed، كتابة staging metadata، queue داخلية | إنشاء حسابات، تغيير RBAC، قراءة السجل السريري |
| GULA API | مراجعة admin محدودة وإرجاع metadata أقل قدر | رفع ملفات ضخمة، بحث عام بالرقم الوطني |
| Database | worker إلى جداول ingestion، backend إلى جداول التطبيق | اتصال مباشر من أي جهة خارجية |

## 2. متطلبات الاستلام للملفات الضخمة

يُرسل كل تصدير مع manifest منفصل يحتوي على `source_key` و`export_id` ونسخة المخطط ووقت التصدير وعدد السجلات و`SHA-256` ووقت انتهاء وسياسة الحقول. لا يقبل backend `file://` أو روابط عامة؛ عقد الاستلام المطبق يقبل مرجعاً إلى تخزين كائن خاص مثل `s3://` أو `gs://` أو `azure://` فقط.

تُقسم الملفات إلى كائنات أو chunks قابلة لإعادة المحاولة، ويكون لكل دفعة `idempotency_key`. يجب أن يتحقق worker من الحجم، وchecksum، وعدد السجلات، ونسخة المخطط، وحدود الحقول، ثم يمرر chunks صغيرة إلى GULA. لا يُستخدم رفع HTTP خام من المتصفح، ولا تُحمّل الدفعة كاملة في ذاكرة عملية واحدة.

تُحفظ النسخة الخام في quarantine لمدة محددة في العقد، مع تشفير KMS، وversioning، وobject lock أو retention policy، ومنع public ACL، وتعطيل listing، وتسجيل كل قراءة أو تنزيل. بعد انتهاء المدة تُتلف النسخة وفق سجل حذف، وتبقى metadata والتدقيق الأدنى فقط حسب سياسة الاحتفاظ.

## 3. المصادقة وإدارة الأسرار

يجب أن تملك كل جهة مصدراً مستقلاً وهوية خدمة مستقلة ومفتاحاً أو شهادة مستقلة. لا تُستخدم مفاتيح Telegram أو JWT أو مفاتيح تطبيق GULA لهذا المسار. يفضل mTLS أو OAuth2 client credentials قصيرة العمر مع تدوير ومراجعة دورية، وتخزين الأسرار في KMS/Vault لا في Git أو `.env` أو سجلات CI. في طبقة GULA الحالية، لا يقبل مسار الدفعات إلا حساب خدمة يحمل scope `integration:identity:write` أو مستخدم `master_admin`/`ministry_admin`؛ أما تفعيل المصدر وقرارات المطابقة فتبقى في مسار إدارة بشري.

يجب أن تتضمن كل دفعة correlation ID وsource identity وmanifest signature. تُرفض الدفعة إذا انتهت الشهادة أو العقد أو لم تطابق الجهة allowlist أو schema version. لا يكفي أن يكون المستخدم admin في واجهة GULA لتجاوز تحقق المصدر.

## 4. العزل داخل Kubernetes أو بيئة مكافئة

عند تنفيذ DMZ في Kubernetes يجب استخدام namespace منفصل، وNetworkPolicy افتراضية deny-ingress/deny-egress، ثم فتح الاتصالات المحددة فقط. يلزم التحقق من دعم CNI الفعلي قبل اعتماد السياسة؛ وجود YAML في المستودع لا يثبت أن العنقود يطبقها. يجب فصل service accounts، وRole/RoleBinding، وSecrets، وServiceMonitor، وPersistentVolume لكل بيئة.

يجب تشغيل worker بحاوية non-root، filesystem read-only قدر الإمكان، drop capabilities، seccomp/AppArmor، resource requests/limits، ووجود liveness/readiness منفصلين. تُحظر privileged containers وhostPath والاتصال بـDocker socket. تُفصل production عن demo وعن staging بقواعد شبكة وقواعد بيانات ومفاتيح مختلفة.

## 5. الفحص قبل إدخال أي سجل

يمر كل كائن بالمراحل الآتية دون side effects: التحقق من manifest والتوقيع، checksum، فحص البرمجيات الخبيثة، DLP للحقول غير المصرح بها، schema validation، حدود حجم وسجل، كشف التكرار، normalization، ثم تقرير dry-run. أي سجل غير مكتمل أو خارج العقد يذهب إلى `rejected` مع سبب عام لا يكشف PII.

لا ينقل scanner أو worker السجل إلى canonical user أو patient أو membership. التطبيق المنفذ في هذا التغيير يحفظ في قاعدة GULA fingerprints غير قابلة للعكس وmetadata للدفعات، ولا يحفظ الاسم أو الهاتف أو الرقم الوطني الخام.

## 6. المراقبة والاستجابة

تُراقب مؤشرات حجم الدفعات، زمن الفحص، checksum failures، schema failures، duplicate rate، ambiguous match rate، rejection rate، زمن سحب الصلاحية، ومحاولات الوصول غير المصرح. يجب عدم إرسال payload أو رقم وطني أو اسم إلى logs أو traces أو metrics.

يجب أن تكون هناك إجراءات جاهزة لإيقاف المصدر، عزل الكائنات، تدوير الشهادات، إلغاء service account، والتحقيق في download غير متوقع. عند وجود خلل في matching أو مصدر مخترق، تكون الاستجابة fail-closed: إيقاف الالتزام، إبقاء الدفعات في quarantine، وفتح incident موثق، لا محاولة تصحيح صامتة.

## 7. ما أُضيف في هذا المستودع

أُضيفت طبقة `app.external_ingestion` تحتوي على `ExternalSource` و`ExternalImportBatch` و`ExternalProfessionalRecord` و`ExternalProfessionalEntity` و`ExternalProfessionalMatchReview`. أُضيفت feature flags `EXTERNAL_INGESTION_ENABLED` و`EXTERNAL_INGESTION_COMMIT_ENABLED`، وكلاهما مغلق افتراضياً، مع اشتراط مفتاح HMAC قوي في البيئات الإنتاجية عند التفعيل. المسارات تقع تحت `/integration/external-ingestion`، ولا يصبح المسار قابلاً للتشغيل لمجرد وجود الكود.

تقبل المسارات manifest وmetadata وchunks مقيدة، ولا توفر رفعاً عاماً لملف خام. تبدأ المصادر `pending/disabled`، ويتطلب تفعيلها عقداً منتهياً في المستقبل ومراجع قانونية وأمنية ومراجعاً ثانياً مختلفاً. أي match يعتمد على national ID أو license + authority + profession يمكن أن يكون auto-match؛ الاسم أو الهاتف أو تاريخ الميلاد وحدها تنتج pending review أو conflict ولا تنشئ عضوية أو حساباً.

## 8. مراجع التصميم

[1]: https://hl7.org/fhir/uv/bulkdata/STU1.0.1/export/index.html — HL7 FHIR Bulk Data Access Implementation Guide؛ يحدد نمط التصدير غير المتزامن وNDJSON لكنه لا يحدد اتفاق المشاركة أو patient matching.

[2]: https://pages.nist.gov/800-63-4/ — NIST SP 800-63-4 Digital Identity Guidelines؛ مرجع تصميم لإثبات الهوية والمصادقة والاتحاد وإدارة المخاطر.

[3]: https://ur.gov.iq/index/show-eservice/51434/10042/cat — بوابة أور الرسمية؛ لا يُفترض منها وجود API عام لـGULA دون تفويض رسمي.

[4]: https://www.moj.gov.iq/view.9935/ — وزارة العدل العراقية، صفحة حماية البيانات الشخصية؛ لا تكفي وحدها لإثبات الأساس القانوني لمشاركة البيانات.
