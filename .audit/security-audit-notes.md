
## 2026-08-13 — Live browser DAST

فتح `https://www.gula-platform.org/login?security_audit=20260813` أظهر واجهة دخول GULA بالمسارين «دخول المواطن» و«دخول المؤسسات» مع اللغات العربية والإنجليزية والكردية والتركمانية والسريانية. نص الصفحة يعلن أن بيئة العرض التجريبي اصطناعية ومعزولة، وزر «فتح العرض التجريبي الآمن» ظاهر دون طلب بيانات حقيقية. أُجري الاختبار من خلال المتصفح المرتبط بالنطاق الرسمي؛ لم يتم إدخال بيانات اعتماد أو تنفيذ أي عملية سريرية أو كتابة بيانات.

## DAST observations

الفحص العام غير التدميري سجّل `200` للصفحة الرئيسية و`manifest.webmanifest` و`sw.js`، ولم يعكس وسم XSS في معامل query اختباري. سجّل `/login` و`robots.txt` و`/.well-known/security.txt` حالة `404`. كما سجّل `/api/health` و`/api/v1/health` والنطاق `api.gula-platform.org` حالة `526 Invalid SSL certificate` من طبقة Cloudflare، وهو عطل توافر وتكامل يجب معالجته قبل اعتبار الواجهات الخلفية جاهزة للإنتاج.

فحص `curl -I` للنطاق الرسمي أظهر `Access-Control-Allow-Origin: *` و`Strict-Transport-Security` وغياب ترويسات `Content-Security-Policy` و`X-Frame-Options` و`X-Content-Type-Options` و`Referrer-Policy` المتوقع تعريفها في `vercel.json`. هذا يشير إلى أن ترويسات الأمان المعلنة في الإعداد قد لا تصل إلى الاستجابة الحية، ويحتاج إلى إعادة تحقق بعد الإصلاح.

## SAST observations

اختبارات الأمن المحلية ذات الصلة بالمصادقة والعزل وDemo وRBAC ومحدد المعدل نجحت: `167 passed` مع أربعة تحذيرات غير مانعة. `npm audit --omit=dev` للجذر و`frontend-v3` أبلغ عن صفر ثغرات. `pip-audit` على `backend/requirements-lock.txt` أبلغ عن عدم وجود ثغرات معروفة في الحزم المفحوصة. فحص الأسرار المقنّع وجد مؤشرات غير placeholder، بينها رمز Telegram فعلي في `scripts/verify_telegram_bot.py`، وكتلة مفتاح خاص في `docs/DEPLOYMENT.md`، وقيَم سرية محتملة في ملفات إعدادات التشغيل؛ يجب اعتبارها أسراراً مكشوفة حتى يثبت العكس، وتدويرها خارج المستودع.

اختبار المتصفح الحي نجح في الوصول إلى `/dashboard` بعد الضغط على Demo. ظهرت هوية `زائر العرض التجريبي / demo_viewer`، ووسم `بيئة عرض تجريبية`، ورسالة تفيد بأن كل البيانات اصطناعية ومعزولة ولا تتاح عمليات سريرية أو بيانات مريض حقيقية.

## Telegram integration findings

المسار `backend/app/routes/telegram_webhook.py` يقبل `POST /telegram/webhook` ويحلل JSON ثم يمرر أي أمر يبدأ بـ `/` مباشرة إلى `handle_telegram_command`، من دون التحقق من ترويسة Telegram secret token أو توقيع/مصدر الطلب أو ربط `chat_id` بحساب GULA مصادق عليه. المسار يعيد تفاصيل الاستثناء في الحقل `detail` عند الفشل، ما قد يكشف معلومات تنفيذية.

في `backend/app/services/telegram_bot_commands.py`، أوامر `/alerts` و`/stats` تستخدم `lab_id=1` ثابتاً وتعيد أسماء مرضى وقيم نتائج مخبرية وأعلاماً سريرية إلى `chat_id` الوارد من الطلب، بلا تفويض أو allowlist. كما أن `POST /telegram/test-alert` لا يحتوي على مصادقة ظاهرة ويستطيع استدعاء إرسال رسالة خارجية. هذه النتائج مصنفة **حرجة/عالية** في نظام صحي، حتى لو كان API الحالي غير متاح خارجياً بسبب 526.

## GitHub Security UI observation

صفحة أمان GitHub المصادق عليها أظهرت `2,368` تنبيهاً مفتوحاً في Code scanning و`219` مغلقاً، مع رسالة `CodeQL is reporting errors`. من الأمثلة الظاهرة: تنبيهات **Critical** بعنوان `Partial server-side request forgery` في `backend/.../integration/testing.py`، وتنبيهات **High** بعنوان `Missing rate limiting` في `apps/.../_core/vite.ts` و`apps/.../_core/oauth.ts`، وتنبيهات **High** من Scorecard تخص Token-Permissions وBinary-Artifacts في workflows وملفات Gradle. هذه النتائج من صفحة GitHub الحالية، وليست استنتاجاً من فحص محلي فقط.

صفحة Dependabot المصادق عليها أظهرت `181 Open` و`191 Closed`، وتقول إن ملفات التبعيات فُحصت قبل نحو ساعتين عند commit `a211943`. أمثلة حالية: XXE في `org.jdom:jdom2` على Android، ثغرة قراءة ملفات عشوائية في Vite Dev Server WebSocket، DoS في protobuf-java، تنفيذ ملفات عشوائية/قراءة في Vitest UI، code injection في lodash، تجاوز `server.fs.deny` في Vite، arbitrary file write في Rollup، prototype pollution/DoS في axios، ومشكلات متعددة في Netty وBouncy Castle وfast-xml-parser. بعض النتائج موسومة Development، لكن بعضها Direct أو يخص mobile manifests، لذلك يلزم فصل مسارات الإنتاج عن أدوات التطوير ومعالجة كل direct/high/critical قبل إطلاقها.

صفحة Secret scanning في GitHub تُظهر أن **Secret scanning is not enabled** للمستودع، مع رابط لتفعيله من Advanced Security. لذلك لا توجد قائمة GitHub رسمية للتنبيهات يمكن الاعتماد عليها حالياً، رغم أن الفحص المحلي المقنّع وجد رمز Telegram فعلياً وكتلة مفتاح خاص وقيماً سرية محتملة في ملفات متتبعة.

تمت إضافة متغيري الإنتاج عبر Railway بعد تأكيد المستخدم: `TELEGRAM_WEBHOOK_SECRET_TOKEN` بقيمة عشوائية قوية مولدة محلياً، و`TELEGRAM_ALLOWED_CHAT_IDS=422685096`. تم الضغط على Deploy لتطبيق التغييرين، ثم أكدت لوحة Railway أن خدمة `gula-backend` عادت إلى `Online` وأن عدد متغيرات الخدمة أصبح 23. لم تُحفظ قيمة الـ Secret في المستودع أو التقرير.

اختبار الإنتاج بعد إضافة المتغيرين أعاد HTTP 503 في حالتين: Secret خاطئ مع Chat ID صحيح، وSecret صحيح مع Chat ID غير مصرح. النتيجة لا تثبت بعد أن المتغيرات دخلت بيئة العملية؛ يلزم فحص deployment/logs. لم يُرسل أي أمر Telegram ناجح ولم تُنفذ أي عملية خارجية.

واجهة Logs في Railway بقيت في حالة `Your logs are loading...` ولم تعرض نصاً قابلاً للقراءة عبر المتصفح، لذلك لم تُستخرج أي قيمة أو سر من السجلات.

بعد اكتمال إعادة التشغيل، استقر webhook الإنتاجي وأثبت الاختبارات الحية: JSON غير صالح أعاد `400 BAD_REQUEST` برسالة عامة؛ Secret Token خاطئ أعاد `403 FORBIDDEN`؛ وSecret صحيح مع `chat_id=999999999` غير المصرح أعاد `403 FORBIDDEN` برسالة `Telegram chat is not authorized`. لم يُشغّل الاختبار أمراً مصرحاً ولم يرسل أي رسالة Telegram. `/health` أعاد `200` و`system_ready=true`.
