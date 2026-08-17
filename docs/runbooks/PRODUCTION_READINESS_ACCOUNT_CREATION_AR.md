# تقرير جاهزية ميزة إنشاء الحسابات — GULA

**تاريخ المراجعة:** 2026-08-17

## القرار التنفيذي

> **القرار الحالي: NO-GO للإنتاج، وGO مشروط لبيئة Staging مغلقة فقط.**

أُصلحت جميع البنود التي يمكن معالجتها محلياً دون أسرار أو موارد خارجية. ما زال إعلان الجاهزية للإنتاج محجوباً بسبب ثمانية مراجع صور Kubernetes لخدمات GULA تستخدم `:latest` ولا يوجد في البيئة الحالية tag أو digest منشور يمكن إثبات توفره، وبسبب عدم تنفيذ اختبارات PostgreSQL/Redis وbackup/restore وNID والدفع والبريد وSMS وقارئات الشاشة على موارد Staging فعلية.

## نطاق العمل المنفذ

شمل الإصلاح فحص إعدادات CI وKubernetes وHelm وDocker Compose وملفات JSON، وتحسين security scanner، إصلاح manifests غير الصالحة، نقل كلمة مرور Prometheus من قيمة placeholder إلى `password_file`، تثبيت صور MinIO وMinIO Client وTempo، تحويل العناوين الخارجية القابلة للإصلاح إلى HTTPS، وتعطيل `automountServiceAccountToken` افتراضياً في Helm.

تم إبقاء التسجيل العام مغلقاً، وميزة إنشاء الحسابات في وضع Staging-only، ولم تُنفذ migrations أو اتصالات إنتاجية أو اتصالات NID أو دفع أو رسائل حقيقية.

## نتائج الاختبارات

| البوابة | النتيجة |
|---|---|
| Backend pytest | **2732 passed، 5 skipped، 20 warnings** |
| اختبارات frontend | 15/15 ملف اختبار و51/51 اختباراً ناجحة |
| اختبارات التسجيل والحسابات الاصطناعية | ناجحة، مع تنظيف قاعدة الجولة |
| اختبار API المحلي | 100 طلب اصطناعي، 100 استجابة 201، دون تكرار أو أخطاء |
| Audit Anchor | ناجح عند 100 سجل في مسار قابل للكتابة |
| Frontend check/build | ناجح |
| حجم frontend الإجمالي | 2,233,294 bytes، ضمن حد 2.5MB |
| ملف الدخول JavaScript | 198,314 bytes، ضمن حد 400KB |
| CSS | 145,352 bytes، ضمن حد 180KB |
| فحص JSON | seccomp وملفات capability صالحة بعد الإصلاح |
| migrations | لم تُنفذ؛ offline dry-run الكامل محجوب بمigration قديم يعتمد على `inspect` |
| Redis الحي وmigration schema | لم يُشغلا لعدم وجود URLs صريحة لموارد Staging |

## الإصلاحات المنفذة

### إصلاح security scanner

أصبح scanner يتعرف على placeholders مثل `REPLACE_WITH_*` و`${...}` و`{{...}}` وإحالات Terraform وSecret Manager وGitHub Secrets وShell environment. كما أصبح يتجاهل التعليقات وlocal reusable workflows ومرجع Apple PropertyList DTD القياسي. أضيف تمييز للعناوين الداخلية الخاصة بـDocker/Kubernetes وRFC1918، مع إبقاء العناوين الخارجية غير المشفرة محظورة. أضيف توثيق صريح للـRedis wildcard الداخلي عبر `security-scan: approved-internal-bind`.

تم استبعاد artifacts غير التنفيذية مثل `.audit` و`reports` و`assessment` و`archive` و`.semgrep` من النطاق الافتراضي، حتى لا تختلط التقارير أو قواعد scanner مع ملفات الإعداد القابلة للنشر.

### إصلاح ملفات الإعداد والبنية التحتية

أُصلح `seccomp-profile.json` بإكمال بنية JSON دون تغيير قائمة syscalls. طُبّعت عشرة ملفات `capability.json` إلى JSON قياسي مع التحقق من بقاء 21 حقلاً في كل ملف. نُقلت مصادقة Prometheus إلى:

```yaml
password_file: /etc/prometheus/secrets/remote_write_password
```

وثُبتت صور MinIO وmc وTempo على إصدار محدد موجود مسبقاً في المستودع. حُوّل `BASE_URL` الأساسي وعنوان التطوير إلى HTTPS، وعُطّل `automountServiceAccountToken` افتراضياً، مع إبقاء التفعيل اختيارياً عند الحاجة إلى workload identity.

### ما لم يُعدّل عمداً

لم أستبدل صور `ghcr.io/samertts/gula-platform/backend` والخدمات السبعة بـtag مخمّن أو digest غير مثبت؛ فمحاولة استخراج manifest من GHCR لم توفر digest قابلاً للوصول من البيئة الحالية. إدخال tag غير موجود قد يكسر النشر، لذلك بقيت هذه المراجع الثمانية عائقاً صريحاً يحتاج من مالك registry أو CI توفير tag/digest معتمد.

## نتائج scanner النهائية

بعد استبعاد artifacts وإصلاح false positives، انخفضت النتائج القابلة للنشر إلى:

| النوع | العدد |
|---|---:|
| Critical | 0 |
| High | 8 |
| Medium | 0 |
| المتبقي | 8 صور GULA تستخدم `:latest` |

النتائج الثمانية تقع في `k8s/base/backend/deployment.yaml` وسبع خدمات في `k8s/base/microservices/deployments.yaml`: lab، patient، order، result، sample، notification، ai.

## العوائق المتبقية

أولاً، يجب أن ينشر CI صوراً لكل خدمة باستخدام tag مبني على commit أو digest OCI، ثم تُحدّث overlays وbase manifests إلى digest غير قابل للتغيير. يجب التحقق من pull وsignature وSBOM قبل اعتماد الصورة.

ثانياً، يجب توفير PostgreSQL وRedis منفصلين لـStaging، مع أسرار جديدة عبر Secret Manager وvolume قابل للكتابة لـ`AUDIT_ANCHOR_DIR`. بعد ذلك فقط يمكن تشغيل migration schema وRedis fail-closed وbackup/restore واختبار Outbox الحقيقي.

ثالثاً، يجب تشغيل اختبارات E2E للحسابات المدعوة، MFA، الجلسات، العزل بين المنشآت، rate limiting، Mailpit/OTP mock، وسجل التدقيق على Staging حقيقي. لا يُفتح التسجيل العام أثناء هذه المرحلة.

رابعاً، يجب إجراء اختبار قارئات الشاشة الفعلي عبر TalkBack/Orca، ومراجعة بشرية أمنية، ثم Go/No-Go موثق قبل أي فتح إنتاجي.

## التوصية التالية

1. اعتماد سياسة CI تمنع نشر `:latest` وتنتج tags وdigests موقعة.
2. توفير موارد Staging المعزولة وتشغيل `staging_preflight.py` بالقيم الفعلية.
3. أخذ snapshot وتجربة restore قبل migrations.
4. تشغيل migrations في Staging فقط بعد مراجعة السلسلة ومعالجة اعتماد `inspect` القديم.
5. تحديث manifests إلى digests فعلية ثم إعادة scanner حتى تصبح النتيجة صفر High/Critical.
6. تشغيل E2E والحمل التدريجي ثم تنظيف `run_id` والتحقق من الصفر.
7. عقد مراجعة Go/No-Go بشرية؛ لا يُفتح التسجيل العام أو NID أو الدفع قبل اعتمادها.

## الخلاصة

أصبحت قاعدة الكود المحلية أكثر اتساقاً، وانخفضت نتائج scanner القابلة للتنفيذ إلى ثمانية عوائق محددة وواضحة. هذا لا يساوي جاهزية إنتاجية؛ الجاهزية النهائية تتطلب صوراً قابلة للسحب ومثبتة، وموارد Staging فعلية، واختبارات تكامل وتشغيل واستعادة ومراجعة بشرية. لم يحدث deployment أو merge إلى `main` أو تنفيذ migration أو استخدام بيانات حقيقية.
