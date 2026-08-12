# خطة تدوير وإبطال الأسرار — Gula Platform

**المالك:** فريق منصة Gula المخوّل من المالك الوحيد.
**النطاق:** الأسرار التي ظهرت في تاريخ Git، أسرار الإنتاج الحالية، أسرار CI/CD، مفاتيح مزودي الخدمة، ومفاتيح توقيع تطبيقات العميل.
**القاعدة الأساسية:** لا تُكتب أي قيمة سرية في Git أو التذاكر أو سجلات الطرفية أو تقارير التدقيق. هذا المستند يذكر أسماء المتغيرات والأماكن التشغيلية فقط.

> يجب اعتبار كل قيمة ظهرت في تاريخ Git **مكشوفة** حتى يثبت مزود الخدمة عكس ذلك. تدوير السر لا يمحو التاريخ، لكنه يوقف صلاحية القيمة القديمة. إزالة التاريخ عملية منفصلة عالية المخاطر ولا تُنفذ تلقائياً أو باستخدام force push.

## 1. قرار التنفيذ وضوابط السلامة

يُنفذ التدوير في نافذة تشغيلية موثقة، ويفضل أن يبدأ من staging ثم production، مع وجود مراقبة للصحة ومستخدم اختبار غير حقيقي. لا تُستخدم حسابات مرضى أو سجلات مختبر حقيقية، ولا تُرسل قيم الأسرار إلى المساعد أو إلى مستودع GitHub. قبل البدء، يُؤخذ backup مشفّر لإعدادات secret manager فقط، ويُسجل checksum أو معرّف الإصدار لا القيمة نفسها.

يجب أن يكون لكل سر مالك تشغيلي، ومزود أصلي، ونطاق صلاحيات، ووقت انتهاء أو سياسة تجديد. تُبنى الخطة على مبدأ أقل صلاحية وعلى التخزين خارج المصدر، بما يتوافق مع إرشادات إدارة الأسرار في OWASP [1].

## 2. قائمة الأسرار المرشحة للتدوير

الأسماء أدناه مستخرجة من إعدادات المصدر وworkflows والتقرير الأمني. بعضها قد يكون خاصاً ببيئة أو fixture؛ يجب التحقق من وجوده في مدير الأسرار دون طباعة قيمته. كل سر تاريخي من الفئات التالية يُبطل حتى لو لم يظهر في checkout الحالي.

| الفئة | الأسماء المرشحة | الإجراء المطلوب |
|---|---|---|
| توقيع الجلسات والرموز | `SECRET_KEY`, `REFRESH_TOKEN_SECRET`, `JWT_SECRET`, `DEVICE_HMAC_KEY`, `NID_HMAC_KEY`, `AUDIT_ANCHOR_KEY`, `ENCRYPTION_KEY` | توليد قيم عشوائية قوية في مدير الأسرار، تحديث staging ثم production، وإبطال الجلسات/الرموز القديمة وفق سياسة التطبيق. لا تُعاد أي قيمة تاريخية. |
| اتصال قاعدة البيانات | `DATABASE_URL`, `POSTGRES_PASSWORD`, وأي `DATABASE_PASSWORD` أو `DB_PASSWORD` | إنشاء كلمة مرور أو مستخدم خدمة جديد بصلاحية أقل، تحديث secret store، rolling restart، اختبار migration/read-write، ثم إلغاء المستخدم أو كلمة المرور القديمة. |
| Redis والجلسات | `REDIS_URL`, `REDIS_PASSWORD` | إنشاء credential جديد أو ACL مخصص، تحديث العملاء، اختبار rate-limit/session invalidation عبر أكثر من worker، ثم حذف credential القديم. |
| Health exchange والأجهزة | `LAB_PLATFORM_API_KEY`, `LAB_DEVICE_TOKEN`, `DEVICE_HMAC_KEY` | إصدار مفتاح جديد بنطاق endpoint محدود، تحديث الطرفين في ترتيب آمن، اختبار health exchange، ثم إبطال المفتاح القديم. |
| مزودو الذكاء والتكاملات | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`, `VLLM_API_KEY`, `MOI_NID_API_KEY`, `INSURANCE_API_KEY`, `RESIDENCY_API_KEY`, `CF_API_TOKEN`, `DATADOG_CLIENT_TOKEN`, `TELEGRAM_BOT_TOKEN` | الإبطال من لوحة كل مزود، إصدار مفاتيح scopes محدودة، تقييد النطاق/الشبكة عند توفره، تحديث secret store، وفحص usage والميزانية بعد التغيير. لا تُستخدم مفاتيح الذكاء مباشرة من المتصفح. |
| GitHub وCI/CD | `GITHUB_TOKEN`, `NODE_AUTH_TOKEN`, `NPM_TOKEN`, `PYPI_TOKEN`, `TWINE_PASSWORD`, `SONATYPE_PASSWORD` | `GITHUB_TOKEN` المدمج قصير العمر ولا يُدوّر كسر ثابت؛ تُراجع صلاحيات workflow. أي PAT أو token تاريخي يُلغى من GitHub/npm/PyPI/Sonatype ويُصدر بديله الأقل صلاحية. |
| Vercel والنشر | `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` | إبطال token القديم من Vercel، إنشاء token مخصص للمشروع وبأقل نطاق، تحديث إعدادات deploy، ثم تنفيذ deployment من commit معروف والتحقق من headers. IDs ليست أسراراً عادة، لكنها تبقى ضمن إعدادات CI ولا تُسجل مع tokens. |
| Sentry والمراقبة | `SENTRY_AUTH_TOKEN` | إبطال token التاريخي، إنشاء token بإذن release فقط إن كان مطلوباً، تحديث CI، وفحص أن event payloads لا تحتوي Authorization أو بيانات صحية. |
| توقيع التطبيقات | `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_PASSWORD`, `IOS_P12_PASSWORD`, `IOS_KEYCHAIN_PASSWORD`, `APP_STORE_CONNECT_PASSWORD`, `MACOS_APP_PASSWORD`, `KEYSTORE_PASSWORD`, `P12_PASSWORD` | فحص ما إذا ظهرت قيمة فعلية تاريخياً. لا تُحذف keystore أو شهادات الإنتاج قبل توثيق مسار الاسترجاع. عند التعرض: تدوير كلمة المرور/شهادة التوقيع وفق Android Play App Signing وApple certificate lifecycle، ثم إصدار build تجريبي موقّع والتحقق من القناة. |
| حسابات تشغيلية | كلمات مرور المديرين أو مزودي الخدمات مثل `GULA_ADMIN_PASSWORD`, `MINISTRY_ADMIN_PASSWORD`, `DIRECTORATE_ADMIN_PASSWORD`, `SECURITY_OFFICER_PASSWORD`, `LAB_MANAGER_PASSWORD` | إعادة تعيين الحسابات المتأثرة، تفعيل MFA، مراجعة الجلسات والأجهزة، وتطبيق RBAC. لا تُستخدم كلمات المرور في fixtures أو ملفات config. |

## 3. ترتيب التنفيذ الموصى به

### المرحلة أ: الجرد والإبطال السريع

يُستخرج سجل الأسرار التاريخي محلياً بصيغة أسماء وblob IDs فقط، ويُقارن مع سجلات مدير الأسرار وusage logs. يجب فحص GitHub secret scanning وDependabot وVercel deployment logs ومزودي API. إذا كان السر غير قابل للتحديد، يُعامل كمعرّض ويُلغى من المزود مباشرة.

تُبطل أولاً مفاتيح الأطراف الخارجية والـCI التي قد تسمح بالنشر أو الوصول إلى بيانات أو حسابات، ثم مفاتيح قواعد البيانات وRedis، ثم أسرار توقيع الجلسات والتشفير، ثم مفاتيح الأجهزة والتكاملات. لا يُعاد استخدام أي قيمة أو suffix تاريخي.

### المرحلة ب: تدوير staging

يُنشأ إصدار جديد لكل credential في secret manager مع وصف `gula-rotation-<date>-<scope>` ومدة صلاحية. تُحدّث staging فقط، ويُعاد تشغيل الخدمات بشكل rolling. تُنفذ اختبارات login/logout/refresh، MFA، RBAC/IDOR بمستخدمين اختبار، رفع ملف غير حساس، health exchange، rate limiting، WebSocket، وعمليات read/write الأساسية.

يُحفظ فقط: وقت التغيير، اسم السر، مزود الخدمة، رقم إصدار secret، ونتيجة الاختبار. لا تُحفظ القيمة أو request headers أو tokens.

### المرحلة ج: تدوير production

بعد نجاح staging، تُحدّث الأسرار في مدير الإنتاج أو إعدادات المنصة. تُراقب health checks و5xx و401/403 وlatency وqueue errors وdatabase connection failures وRedis errors لمدة لا تقل عن نافذة الاستقرار المتفق عليها. لا يتم rollback إلى قيمة قديمة؛ عند الفشل يُصلح secret الجديد أو يُصدر بديل ثالث.

بالنسبة لأسرار JWT، يفضل نشر verifier يقبل المفتاح الحالي والجديد لفترة انتقالية، مع إصدار رموز جديدة بالمفتاح الجديد، ثم إبطال القديم وإزالة قبول المفتاح القديم. إن كان التطبيق لا يدعم key IDs أو dual verification بعد، تُنفذ العملية في نافذة قصيرة مع invalidation لجميع الجلسات، ويُوثق الأثر للمستخدمين.

بالنسبة لمفتاح التشفير، لا يُستبدل مباشرة إذا كانت البيانات الحالية تعتمد عليه. يجب أولاً تنفيذ key versioning أو migration يقرأ القديم ويكتب الجديد، ثم إزالة قبول القديم بعد التحقق من إعادة تشفير كل السجلات المطلوبة. لا تُجرى migration تشفيرية على بيانات حقيقية دون خطة استرجاع مشفرة واختبار staging.

## 4. خطوات المزودين

### GitHub

يُراجع [Settings → Secrets and variables → Actions](https://github.com/samertts/gula-platform/settings/secrets/actions) ويُلغى أي token تاريخي أو PAT. تُراجع صلاحيات workflows وتبقى `permissions` في الحد الأدنى، مع إبقاء secret scanning وpush protection وDependabot فعالين. لا يُنفذ purge لتاريخ Git تلقائياً؛ إذا طلبه المالك لاحقاً، يُناقش مع GitHub مع خطة clone/redeploy ومراجعة جميع النسخ والـforks.

### Vercel

يُلغى `VERCEL_TOKEN` القديم من إعدادات Vercel، ويُنشأ token مخصص للمشروع. بعد تحديث CI، يُنفذ deployment من commit معروف. يُتحقق من `https://www.gula-platform.org/`, و`/login`, و`/register`, و`/api/health` إن كان المسار متاحاً، ومن وجود CSP وHSTS و`X-Content-Type-Options` و`Referrer-Policy` وعدم وجود CORS wildcard مع credentials.

### قاعدة البيانات وRedis

يُنشأ credential جديد في مزود الاستضافة، وتُحدّث `DATABASE_URL` و`REDIS_URL` في secret manager فقط. يُختبر اتصال backend من staging، ثم rolling restart production. بعد نجاح المراقبة، يُلغى credential القديم وتُراجع connection logs للتأكد من عدم وجود اتصالات به.

### مزودو API الخارجيون

يُلغى كل token تاريخي من لوحة المزود حتى لو لم تظهر عليه usage. تُستخدم scopes محدودة، وقيود origin/IP إن كانت متاحة، وtimeouts وbudgets. تُختبر requests من backend فقط، ويُراجع أن frontend لا يحتوي على أسماء متغيرات أو مفاتيح صالحة أو SDK مباشر لمزود سري.

### شهادات وتوقيع Android/iOS/desktop

تُراجع شهادات التوقيع ومخزن الأسرار في CI. لا يُنشر build جديد قبل التأكد من أن pinning يستخدم SPKI إنتاجياً مع pin احتياطي موثق. قبل تغيير شهادة API، يُضاف backup pin ويُختبر release build على جهاز أو محاكي؛ وبعد اكتمال الانتقال تُزال البصمة القديمة وفق نافذة مدروسة. يجب ألا تُرفع keystores أو ملفات P12 أو كلمات مرورها إلى Git.

## 5. التحقق بعد التدوير

| الاختبار | معيار النجاح |
|---|---|
| فحص Git الحالي والتاريخ | لا توجد قيم سرية جديدة؛ الحارس وGitleaks ينجحان؛ لا يُعرض secret في logs |
| Backend startup | يبدأ فقط مع أسرار production صريحة وقوية؛ لا fallback ضعيف أو random production key |
| Login/session | login وrefresh وlogout تعمل في staging؛ الرموز القديمة مرفوضة بعد invalidation؛ cookies آمنة وHttpOnly حيث تنطبق |
| MFA وRBAC/IDOR | مستخدم الاختبار لا يصل إلى مورد مختبر آخر ولا يتجاوز role أو MFA |
| Database/Redis | اتصالات جديدة فقط؛ rate limiting وsession invalidation يعملان عبر workers |
| Uploads | allowlist للحجم والنوع، تخزين غير قابل للتنفيذ، ورفض traversal/redirect غير آمن |
| Web headers | CSP وHSTS و`X-Content-Type-Options` و`Referrer-Policy` و`Permissions-Policy` تظهر فعلياً في HTML 200 وdeep links |
| DNS/TLS/API | `api.gula-platform.org` يحل من شبكة التشغيل، TLS صحيح، pinning يطابق SPKI الحالي، وhealth endpoint لا يكشف أسراراً |
| CI/CD | build من commit معروف، tokens الأقل صلاحية، artifacts لا تحتوي `.env` أو keystores، وsecurity workflows خضراء |
| Monitoring | لا توجد 401/403/5xx أو connection failures غير مفسرة بعد التغيير، وسجلات التطبيق منزوعة الرموز |

## 6. أدلة الإغلاق المطلوبة

يُعتبر كل عنصر مغلقاً فقط عند وجود رقم إصدار secret الجديد، وقت الإبطال، اسم المنفذ، رابط أو رقم deployment، نتيجة اختبار staging، نتيجة اختبار production غير تدميري، ولقطة مراقبة منزوعة البيانات. يجب إرفاق evidence في مساحة وصول مقيدة، وليس في Git إذا احتوت على headers أو identifiers حساسة.

يبقى القرار **NO-GO** إذا ظل أي سر تاريخي فعالاً، أو تعذر التحقق من DNS/TLS للـAPI، أو فشل login/MFA/RBAC/IDOR في staging، أو لم تظهر ترويسات الحماية بعد نشر Vercel، أو بقيت مفاتيح توقيع التطبيقات معرضة دون خطة إصدار معتمدة.

## References

[1]: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html "OWASP Secrets Management Cheat Sheet"
[2]: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html "OWASP Session Management Cheat Sheet"
[3]: https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html "OWASP Content Security Policy Cheat Sheet"
[4]: https://github.com/samertts/gula-platform/security/dependabot "Gula Platform Dependabot alerts"
