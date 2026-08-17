# تقرير جاهزية مسار المريض الحكومي والمزامنة Offline

**التاريخ:** 2026-08-17
**الفرع:** `manus/government-patient-flow`
**النطاق:** Patient Flow، Offline Sync، التعارضات السريرية، Outbox، الأمن، واختبارات الجاهزية الحكومية.

> هذا التقرير يثبت نتائج تحقق هندسية داخل المستودع، ولا يمثل موافقة سريرية أو أمنية أو تشغيلية على الإنتاج الحكومي.

## الملخص التنفيذي

أضيفت طبقة تحقق إضافية تركز على سلامة المزامنة تحت الضغط، وعدم تكرار الآثار السريرية، ومنع تشغيل Outbox في الإنتاج دون backend تسليم مؤسسي، وتوسيع بوابة الأمن لتشمل مجلدات `routes` الوطنية. كما أضيف سيناريو k6 مستقل لمسار Patient Flow ودفعات Offline Sync، لكنه لا يعمل إلا بعد تزويده صراحة ببيانات staging ورمز جلسة جهاز صحيح.

النتيجة المحلية الحالية إيجابية بالنسبة لاختبارات المستودع، مع وجود حدود تشغيلية معلنة. نجحت مجموعة Backend الكاملة المستهدفة في **2674 اختبارًا** مع **4 اختبارات متجاوزة** و**252 تحذيرًا**. نجحت اختبارات الواجهة في **54 اختبارًا**، ونجح TypeScript وVite/PWA build. لم تُشغّل تجربة k6 على staging لأن أداة k6 ورموز staging غير متاحة في بيئة التطوير الحالية.

## التغييرات المنفذة

| المجال | التغيير | ضابط السلامة |
|---|---|---|
| اختبار الضغط | إضافة `k6/patient_flow_sync_load.js` بسيناريوهات smoke/load/stress وعتبات p95 ومعدل الأخطاء. | يرفض التشغيل عند غياب `BASE_URL` أو `AUTH_TOKEN` أو `DEVICE_SESSION_TOKEN` أو `DEVICE_ID`. |
| تشغيل الضغط | إضافة `make patient-flow-load` مع تحقق مسبق من المدخلات. | يمنع تجربة غير موثقة أو تشغيلًا عشوائيًا على بيئة غير معتمدة. |
| idempotency | إضافة اختبار إعادة تسليم العملية نفسها والتحقق من إنشاء Outbox واحد فقط. | يمنع الآثار السريرية المكررة. |
| Outbox | رفض `log sink` عند `IS_PRODUCTION=true`، مع retry وbackoff وdead-letter. | لا يُوسم الحدث `processed` في الإنتاج دون backend تسليم مؤسسي. |
| الأمن | توسيع `security-gate.py` من `backend/app/routes` إلى كل مجلدات `routes` تحت `backend/app`، بما فيها `national/api/routes`. | منع blind spot في كشف مسارات الكتابة التي لا يظهر فيها أثر تدقيق مباشر. |
| الجاهزية | إضافة `scripts/government_readiness_gate.py`. | فحص fail-closed للفرع والترحيلات وعقود Offline Sync والأسرار وOutbox. |
| CI | إضافة job باسم `Government Patient Flow Readiness` إلى workflow الأمني. | تشغيل readiness gate واختبارات sync/stress على checkout نظيف في CI. |

## اختبارات الضغط

### الاختبارات المحلية

اختبار `backend/tests/test_stress.py` الحالي نجح بالكامل: **21 اختبارًا**. ويغطي هذا الاختبار التزامن في محرك التفسير، Westgard، rate limiter، كشف التسلل، إصدار الرموز، التشفير، throughput، p99 latency، واستقرار الذاكرة.

أضيفت اختبارات المزامنة التالية داخل `backend/tests/test_sync_security_and_outbox.py`:

| السيناريو | النتيجة |
|---|---|
| إعادة تسليم العملية نفسها | `duplicate` دون Outbox إضافي |
| انتهاء جلسة الجهاز | رفض العملية |
| رمز جلسة خاطئ | رفض العملية |
| غياب `X-Device-Session` | رفض API قبل المعالجة |
| retry بعد فشل مؤقت | تأخير exponential backoff |
| عدم retry قبل الموعد | الحدث لا يُختار قبل `next_attempt_at` |
| dead-letter | بعد 8 محاولات فاشلة |
| log sink في الإنتاج | رفض fail-closed |

### اختبار k6 المطلوب على staging

يجب تنفيذ السيناريو الآتي على بيئة staging تحتوي بيانات اصطناعية فقط:

```bash
make patient-flow-load \
  BASE_URL=https://staging.example.gov \
  AUTH_TOKEN="$AUTH_TOKEN" \
  DEVICE_ID=ER-LOAD-001 \
  DEVICE_SESSION_TOKEN="$DEVICE_SESSION_TOKEN" \
  HOSPITAL_ID=1 \
  SCENARIO=smoke
```

العتبات المضمنة في الاختبار هي معدل أخطاء أقل من 1%، وp95 للقراءات أقل من 500ms، وp95 للكتابات أقل من 1000ms. أما سيناريو `stress` فيستخدم تصعيدًا حتى 200 VU، ولا يجوز تشغيله على الإنتاج أو على بيانات مرضى حقيقية.

## اختبارات الأمن والتدقيق

تتحقق بوابة الجاهزية من وجود ترحيل `20260817_0025` كرأس Alembic وحيد، ومن وجود رأس `X-Device-Session`، وتجزئة رمز الجلسة، وتشفير AES-GCM للطابور، وحد السعة، وbackoff للـOutbox، ومنع الدمج السريري التلقائي.

تم تشغيل فحص تغطية التدقيق الموسع على الإصدار الأولي. الرقم **44** كان إجمالي ملفات التحذير في جميع مجلدات `routes`، وليس 44 مسارًا وطنيًا؛ كان منها **12 ملفًا تحت `backend/app/national/api/routes`** و32 ملفًا في مسارات أخرى. بعد تطبيق AST gate والتدقيق الفعلي أصبحت مسارات National Patient Flow وOffline Sync بلا تحذيرات، بينما بقيت **30 ملفات غير وطنية** تحتاج دورة معالجة مستقلة أو marker تفويض تدقيقي بعد مراجعة خدماتها.

المعالجة لم تُخفِ التحذيرات المتبقية. فالـ30 ملفًا غير الوطني مسجلة كفجوة منفصلة، ولا يجوز اعتبار Security Gate أخضرًا بالكامل قبل إغلاقها أو اعتماد خطة مالك/موعد لكل مسار.

## بوابة الجاهزية الحكومية

التشغيل المحلي:

```bash
make government-readiness
```

يعطي التشغيل المحلي نتيجة ناجحة مع تحذيرين متوقعين: working tree غير نظيف أثناء التطوير، وعدم طلب فحص production environment. أما فحص الإنتاج فيجب أن يكون fail-closed:

```bash
IS_PRODUCTION=true \
RUNTIME_MODE=api \
DATABASE_URL="$GOVERNMENT_DATABASE_URL" \
GULA_SYNC_OUTBOX_DELIVERY=redis \
python3 scripts/government_readiness_gate.py --production --run-tests --json
```

يجب توفير الأسرار التشغيلية عبر مدير أسرار مؤسسي، ولا يجوز وضع قيم حقيقية في shell history أو CI logs. يتطلب الفحص `SECRET_KEY` و`ENCRYPTION_KEY` و`NID_HMAC_KEY` و`REFRESH_TOKEN_SECRET` و`DEVICE_HMAC_KEY`، ويرفض SQLite و`GULA_SYNC_OUTBOX_DELIVERY=log` في الإنتاج.

## نتائج التحقق

| التحقق | النتيجة |
|---|---|
| `compileall` للملفات المعدلة | ناجح |
| اختبارات Backend الكاملة مع استثناء `services/device_bridge` | 2674 ناجحًا، 4 متجاوزة، 252 تحذيرًا |
| اختبارات sync/security/readiness/stress المركزة | 36 ناجحة في آخر تشغيل مركّز |
| TypeScript | ناجح |
| Vitest | 54 ناجحًا |
| Vite/PWA build | ناجح |
| `git diff --check` | ناجح بعد الإصلاح |
| k6 staging | لم يُشغّل: k6 وبيانات staging غير متاحين محليًا |

## بوابات لا تزال مطلوبة قبل الإنتاج

لا يجوز اعتبار النظام جاهزًا للإنتاج الحكومي قبل تحقيق الشروط التالية:

1. تشغيل k6 على staging ببيانات اصطناعية وتسجيل تقرير thresholds معتمد.
2. ضبط `GULA_SYNC_OUTBOX_DELIVERY` على broker أو Redis أو Push مؤسسي، واختبار replay بين عقدتين.
3. معالجة ملفات التدقيق غير الوطنية الـ30 المتبقية route-by-route، مع إثبات أثر التدقيق أو توثيق false positive بوضوح.
4. تنفيذ اختبار ترقية IndexedDB v1 إلى v2 على أجهزة مدارة، مع اختبار فشل التشفير واسترجاع الطابور.
5. تنفيذ backup/restore وPITR وDR drill على نسخة غير إنتاجية، مع التحقق من audit anchors.
6. الحصول على اعتماد سريري وأمني وتغيير رسمي قبل تطبيق الترحيل `20260817_0025` على أي قاعدة حكومية.

## مراجع المستودع

[1]: ../k6/patient_flow_sync_load.js "سيناريو k6 لمسار المريض والمزامنة"

[2]: ../scripts/government_readiness_gate.py "بوابة الجاهزية الحكومية"

[3]: ../config/quality-gates/security-gate.py "بوابة الأمن وتغطية التدقيق"

[4]: ./DEPLOYMENT_READINESS.md "سجل الجاهزية التشغيلي"

[5]: ./GULA_OFFLINE_SYNC_IMPLEMENTATION_AR.md "توثيق Offline Sync العربي"
