# تقرير Command 03 — Verification & OTP Hardening

**المنصة:** GULA Platform
**الفرع:** `chore/security-ddos-hardening-clean`
**PR:** `#226`
**التاريخ:** 2026-08-16
**المؤلف:** Manus AI
**قرار Command 03:** **`VERIFICATION_PARTIAL`**
**الحكم الأمني:** Contact Verification وOTP **REMEDIATED**؛ مسارات Government/Professional/Organization/Trust ما تزال **PROVIDER_DEPENDENCY / UNVERIFIED** أو **FAIL-CLOSED**، ولذلك لا يجوز اعتبار تكامل الهوية الكامل جاهزاً للإنتاج.

## 1. الملخص التنفيذي

تم استكمال تقوية دورة **Contact Verification** في الخادم والواجهة، مع الحفاظ على مبدأ أن حالة التحقق لا يقررها العميل. أصبح رمز OTP عشوائياً تشفيرياً، قصير العمر، مخزناً كـdigest فقط، محدود المحاولات، محمياً من إعادة الإرسال المتكرر وإعادة الاستخدام، وغير قابل للتخمين من خلال رسائل متساوية للمُعرّفات الموجودة وغير الموجودة. كما تمت معالجة فشل مزود البريد/الرسائل بحيث لا يتحول إلى نجاح ولا يعيد الرمز في الاستجابة عند فشل التسليم [1].

تم أيضاً إغلاق مسارات Trust/Proofing بالكامل حتى تتوفر آلية تفويض محكومة على مستوى الحساب والمؤسسة والنطاق. وأصبح مسار Government Identity لا يقبل نتائج STUB أو SHADOW كإثبات هوية؛ لا يعمل إلا مع مزود `LIVE` فعلي ومصرح به [2]. هذا يمنع الجاهزية الوهمية، لكنه يعني أن مستويات الهوية الرسمية والمهنية والمؤسسية غير متاحة في هذه البيئة.

> النتيجة العملية: **Contact Verification محمي وقابل للاختبار، لكن Identity Verification وProfessional Verification وOrganization Verification وGovernment Identity ليست متصلة بمزودات رسمية عاملة، ولذلك بقيت الحالة الكلية `VERIFICATION_PARTIAL`.**

## 2. نطاق المراجعة

شملت المراجعة مسارات `/auth/verification/request` و`/auth/verification/confirm`، وطبقة cache المستخدمة للـOTP، ومزودات Trust/Proofing في `/niam/trust/*`، ومسار `/national-id/verify`، ومصادر نموذج `VerificationRecord` و`AssuranceEngine`، وواجهة `/verify`، واختبارات backend/frontend، وخصائص النشر وAlembic وحالة Vercel.

لم يتم تعديل أي قاعدة بيانات إنتاجية أو متغيرات بيئية خارجية أو إعدادات Vercel. فحص Vercel كان قراءة فقط، ولم يتم تشغيل نشر أو تغيير حماية deployment.

## 3. الإصلاحات المنفذة

| المجال | المشكلة | المعالجة | الدليل الأمني |
|---|---|---|---|
| توليد OTP | الحاجة إلى رمز قصير غير قابل للتنبؤ | استخدام `secrets.randbelow` مع ستة أرقام | لا يوجد مصدر pseudo-random أو رمز ثابت في المسار [1] |
| تخزين OTP | خطر تسريب الرمز من cache أو السجلات | تخزين SHA-256 digest مع `user_id` و`channel` فقط | لا يتم تخزين النص الصريح للرمز [1] |
| انتهاء الصلاحية | احتمال بقاء الرمز صالحاً طويلاً | TTL مدته 15 دقيقة للرمز ومحاولاته وmarker الاستهلاك | كل مفاتيح OTP ذات TTL محدد [1] |
| إعادة الإرسال | سباق بين workers أو إعادة إرسال متكرر | `set_if_absent` ذري مع cooldown مدته 60 ثانية | الاختبار المتوازي يثبت فائزاً واحداً فقط [3] |
| إعادة الاستخدام | قبول replay بعد نجاح التحقق | consumed marker ذري، ثم حذف رمز OTP بعد النجاح | replay يعيد `400` ولا ينشئ نجاحاً ثانياً [1][3] |
| brute force | عداد محاولات غير ذري أو غير محدود | `incr` ذري، TTL، وحد أقصى خمس محاولات مع `429` | اختبار brute-force ناجح [3] |
| enumeration | اختلاف الرسالة بين حساب موجود وغير موجود | استجابة عامة ثابتة في request | اختبار enumeration resistance ناجح [3] |
| provider failure | نجاح أو إرجاع `demo_code` بعد فشل التسليم | حذف cache، تسجيل audit عام، وإرجاع استجابة عامة بلا OTP | اختبار provider failure ناجح، ولا يظهر OTP في audit [3] |
| Redis fallback | عدم مشاركة in-memory cache بين workers في الإنتاج | مؤشر `is_shared` وحاجز يعيد `503` للـOTP في production عند غياب backend مشترك | اختبارات production cache guard ناجحة [3][4] |
| Trust/Proofing | endpoints قادرة نظرياً على إنشاء أو اعتماد evidence بلا authorization governed | dependency عامة تعيد `410 Gone` قبل استدعاء أي service | كل routes ترث fail-closed gate [5] |
| Government Identity | STUB/SHADOW قد يوحيان بإثبات هوية | السماح فقط بـ`AdapterMode.LIVE`؛ STUB وSHADOW يعيدان `503` | اختبارات STUB وSHADOW وLIVE ناجحة [2][6] |
| واجهة المستخدم | غياب رحلة تحقق واضحة وآمنة | إضافة `/verify` مع request/code/resend/expired/error/verified states | الواجهة لا تعرض demo OTP ولا تمنح session أو permission [7] |

## 4. API Hardening Audit

| المسار | نموذج الوصول | التحقق من المدخلات | التحكم في الإساءة | Object-level authorization | الحكم |
|---|---|---|---|---|---|
| `POST /auth/verification/request` | غير مصادق عمداً لأنه pre-login onboarding | `identifier` بطول 5–100 وتطبيع lowercase/trim | auth rate limiter، resend cooldown ذري | لا توجد هوية مؤسسة مطلوبة في contact verification legacy | **مقبول للغرض المحدد، مع بقاء فصل legacy/NIAM** |
| `POST /auth/verification/confirm` | غير مصادق عمداً لأنه pre-login confirmation | `identifier` وOTP من ستة أرقام | auth rate limiter، خمس محاولات، TTL، single-use marker | يطابق digest مع `user_id` الموجود في cache | **مقبول بعد الإصلاح** |
| `/niam/trust/*` | أي محاولة مرفوضة قبل تنفيذ service | schemas الحالية لا تصبح قابلة للاستخدام أثناء gate | `410 Gone` fail-closed | authorization المؤسسي الحاكم غير موصول بعد | **محجوب عمداً** |
| `POST /national-id/verify` | يعتمد على legacy `get_current_user` | national ID بطول 5–20 | مزود live فقط؛ لا يوجد قبول stub | ليس canonical NIAM actor ولا يكتب VerificationRecord | **Provider dependency / partial** |
| Canonical `VerificationRecord` service | داخلي في هذه الشجرة ولا توجد route CRUD عامة مطابقة | النتائج تبنى server-side من `VerificationResult` | `VerificationPolicy` وstate machine | `AssuranceEngine` منفصل عن permission | **محمى داخلياً، غير مكتمل كرحلة API عامة** |

مسارات `/auth/verification/*` غير المصادق عليها ليست bypass؛ هي نقطة تصميم لازمة للتحقق قبل تسجيل الدخول، وتظل محكومة بالتطبيع، والـrate limiting، والـTTL، والرسائل غير الكاشفة. أما مسارات المؤسسة والهوية الرسمية فلا تستخدم هذا الاستثناء.

لم يُعثر في مسارات Command 03 على endpoint يقبل `verified=true` أو `assurance_level` أو `provider_result` كحالة موثوقة من العميل. ووفق نموذج السياسة، **Assurance Level ليس Permission**؛ قرار السماح يجب أن يجمع policy وmembership وrole وscope وcontext [8].

## 5. الاختبارات والأدلة

| المجموعة | النتيجة |
|---|---:|
| Backend full suite | **2687 passed, 4 skipped** خلال 311.45 ثانية |
| Verification/Trust/National-ID targeted suite | **36 passed** |
| Frontend unit tests | **61 passed / 17 test files** |
| Frontend typecheck | **PASS** |
| Frontend lint | **PASS** |
| Frontend production build وPWA generation | **PASS**؛ 191 precached entries |
| Frontend Playwright E2E | **53/53 passed** |
| Ruff targeted checks | **PASS — All checks passed** |
| Bandit targeted checks | **PASS — لا findings عند المستوى المطلوب** |
| `git diff --check` | **PASS** |

توجد تحذيرات بيئية أو deprecated APIs في suite، منها `datetime.utcnow()` وغياب `httpx2` وغياب PostgreSQL المحلي، لكنها لم تسبب فشل الاختبارات. لم يتم تحويل هذه التحذيرات العامة إلى تغييرات خارج نطاق Command 03.

## 6. Production Safety Gate

أظهر فحص المصادر أن التسجيل العام معطل افتراضياً، وAPI docs معطلة افتراضياً، وSNDHS National ID flag معطل افتراضياً، بينما adapter mode الافتراضي هو STUB. وفي الإنتاج، Redis مطلوب افتراضياً ولا يُسمح بالـdegraded fallback إلا عبر إقرار بيئي صريح؛ إضافة إلى ذلك، مسارات OTP نفسها ترفض in-memory cache غير المشترك وتعيد `503` في production [4][9].

| الفحص | النتيجة | الملاحظة |
|---|---|---|
| `PUBLIC_SELF_REGISTRATION_ENABLED` | **SAFE DEFAULT: false** | account request فقط؛ لا public registration |
| `ENABLE_API_DOCS` | **SAFE DEFAULT: false** | factory لا يفتح docs في production إلا بتفعيل صريح |
| `SNDHS_ENABLE_NATIONAL_ID` | **SAFE DEFAULT: false** | national-ID surface غير مفعّل افتراضياً |
| `GULA_ADAPTER_MODE_NID` | **DEFAULT: stub** | endpoint الآن fail-closed ولا يعتبره verification |
| `ALLOW_DEGRADED_REDIS` | **DEFAULT: false** | production startup guard يطلب Redis |
| Alembic heads | **PASS: single head `20260815_0022`** | لا migration جديدة مطلوبة لتغييرات Command 03 |
| Alembic current | **UNVERIFIED** | PYTHONPATH عولج محلياً، لكن PostgreSQL على localhost:5432 غير متاح؛ لم تُجرَ migration rehearsal |
| Vercel project | **BLOCKED في الفحص السابق للدفع** | deployment المرتبط بـ`e4fe5d1b` كان `BLOCKED`، وVercel يشير إلى account/project collaboration configuration؛ لم يتم تعديل Vercel ولم تتم إعادة قراءة deployment الجديد بعد push |

## 7. حدود ما تم إثباته

Contact Verification لا يزال على نموذج `User` legacy، بينما `VerificationRecord` canonical يستخدم حساب NIAM وهوية NIAM. لم يتم الادعاء بأن هذين المسارين أصبحا كياناً واحداً؛ توحيدهما يحتاج قراراً معماريّاً وموافقة على توافق الجلسات والهوية، ولذلك بقيت هذه النقطة **HUMAN_APPROVAL_REQUIRED**.

Government Identity لا يملك مزوداً رسمياً حياً في هذه البيئة، وProfessional/Organization providers تستخدم `NotConnectedProvider`. لذلك لا يوجد OCR أو NFC أو biometrics أو registry success وهمي، ولا يتم رفع assurance إلى L2–L4. Trust/Proofing بقيت `410 Gone` حتى يتم ربط authorization الحاكم بالمؤسسة والنطاق والسجل التدقيقي.

لم تُجرَ migration rehearsal على PostgreSQL staging، ولم يُتحقق محلياً من Flutter native CI لأن Flutter SDK غير متوفر في البيئة الحالية. كما أن أحدث Vercel deployment على الفرع محجوب؛ هذا يمنع اعتبار preview أو production deployment دليلاً على جاهزية النشر.

## 8. القرار النهائي والتوصية

قرار Command 03 هو **`VERIFICATION_PARTIAL`** وليس `VERIFICATION_REMEDIATED` الكامل. الجزء الذي تمت معالجته هو contact OTP security، كما أن المسارات غير الجاهزة أصبحت fail-closed بدلاً من تقديم نجاح شكلي. لا ينبغي تفعيل Government/Professional/Organization verification أو رفع assurance قبل اعتماد مزود رسمي، security architecture، legal basis، authorization governed، واختبار staging حقيقي.

التوصية التالية هي إعادة فحص deployment الذي أنشأه push الجديد، ثم معالجة سبب Vercel `BLOCKED` من حساب/صلاحيات المشروع خارج الكود إذا استمر الحظر. بعد ذلك يلزم تشغيل PostgreSQL/Alembic rehearsal وnative CI، ثم تنفيذ قرار معماري موثق لتوحيد legacy contact verification مع NIAM VerificationRecord دون كسر session أو workspace isolation.

## 9. المراجع الداخلية

[1]: ../backend/app/routes/verification.py "OTP/contact verification route"
[2]: ../backend/app/routes/national_identity.py "Government identity LIVE-only gate"
[3]: ../backend/tests/test_security_demo_contract.py "Verification security contract tests"
[4]: ../backend/app/security/redis_client.py "Atomic cache primitives and shared-backend marker"
[5]: ../backend/app/identity/trust/routes.py "Fail-closed NIAM trust/proofing routes"
[6]: ../backend/tests/test_national_identity_production_guard.py "National identity provider mode tests"
[7]: ../frontend-v3/src/pages/auth/VerificationPage.tsx "Contact verification UX"
[8]: ../backend/app/identity/services/verification_service.py "Verification policy and assurance engine"
[9]: ../backend/app/config.py "Production Redis and onboarding safety defaults"

## 10. Remediation Addendum — Account Scope وCookie-only Sessions

بعد المراجعة اللاحقة، أُغلقت أربع فجوات إضافية قابلة للإصلاح داخل الكود من دون تغيير قاعدة بيانات أو بيئة إنتاج. أولاً، لم تعد استجابة `/login` للويب تعيد `access_token` أو `refresh_token` أو `token` داخل JSON؛ تبقى الرموز داخل cookies محمية بـ`HttpOnly`، بينما يظل contract التطبيقات الأصلية منفصلاً في `/auth/refresh` عندما يرسل العميل native refresh token صراحةً في body. وبذلك لا تُعاد bearer material إلى JavaScript في مسار الويب.

ثانياً، أُضيف claim موقّع باسم `account_kind` إلى JWT legacy (`lab` أو `user`). أصبح `get_current_user` وmobile refresh وlogout يختارون جدول الحساب من هذا claim فقط، ويرفضون token القديم أو الملتبس بـ`401 Invalid token account scope`. هذا يعالج خطر تصادم numeric IDs بين `LabUser` و`User`، ويمنع أن تُفسَّر جلسة مواطن على أنها جلسة مؤسسة أو العكس. ثالثاً، أصبح cache payload التالف في confirm verification يعيد `400 Invalid or expired verification code` بدلاً من خطأ داخلي أو تحويل فساد داخلي إلى مسار نجاح.

تمت إضافة اختبارات regression لهذه السلوكيات، كما تم تحديث test fixtures التي كانت تنشئ bearer claims غير محددة النطاق لتستخدم `account_kind` صراحةً، واختبار auth infrastructure ليقرأ access token من cookie. لم تتم إضافة inference أو bypass في production؛ token غير المعرّف بالنطاق يبقى مرفوضاً.

| الدليل بعد remediation | النتيجة |
|---|---:|
| Backend full suite | **2692 passed, 4 skipped** |
| Remediation regression suite | **498 passed** |
| Frontend typecheck/lint/build | **PASS** |
| Frontend unit tests | **61 passed / 17 files** |
| Frontend Playwright E2E | **53/53 passed** |
| Ruff على source وملفات remediation | **PASS** |
| Bandit على security/auth source | **PASS** |
| `git diff --check` | **PASS** |

أُعيد فحص Vercel بعد الدفع الأخير، فظهر deployment `dpl_HFVVqbgsQGBkYYEh2GPyNANqzxvk` المرتبط بالـcommit `dfbd048b2b691403604350476b57d44c5dd288ea` بحالة `BLOCKED`، ورابطه [Vercel deployment](https://gula-platform-oodq3sg2j-samertts-projects.vercel.app). كما أظهر فحص الحماية أن password protection معطل، وtrusted IPs معطلة، بينما SSO protection مفعلة على كل deployments باستثناء custom domains. لذلك أصبح سبب الحظر موثقاً كإعداد حماية/حساب أو مشروع Vercel خارج كود GULA؛ لم يتم تعطيل SSO أو تغيير إعدادات Vercel تلقائياً حفاظاً على سلامة الإنتاج.

**الحالة بعد remediation:** الإصلاحات البرمجية الجديدة **REMEDIATED** ضمن نطاق session confidentiality وaccount namespace isolation وmalformed OTP cache handling. تبقى الحالة الكلية **`VERIFICATION_PARTIAL`** بسبب عدم توحيد legacy User مع NIAM VerificationRecord، وعدم توفر مزودات رسمية Government/Professional/Organization، وعدم تنفيذ PostgreSQL rehearsal أو Flutter native CI، وبقاء Vercel deployment محجوباً بحماية خارجية.
