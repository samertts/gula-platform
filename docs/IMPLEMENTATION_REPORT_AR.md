# تقرير تنفيذ إصلاحات منصة العيادات الطبية الشعبية الحكومية

**المستودع:** `samertts/gula-platform`
**الفرع المحلي:** `security/p0-bootstrap-alembic`
**تاريخ التقرير:** 15 أغسطس 2026
**الحالة:** جاهز للمراجعة البشرية؛ لم يُنفذ `push` أو `merge` أو نشر إنتاجي.

## 1. الملخص التنفيذي

اكتملت حزمة الإصلاحات الأساسية لنظام العيادات الطبية الشعبية الحكومية المختصة بمرضى الأمراض المزمنة، بما في ذلك المجال الخلفي، واجهة مساحة العمل الحكومية، الصلاحيات، التحصيل المالي، دفتر الصرف الشهري، اختبارات P0، وتحديثات Offline-first الآمنة لتطبيقات Android وFlutter Desktop. كما أُغلقت إصلاحات P2 المستهدفة المتعلقة بسجلات الإشعارات، استعادة كلمات المرور، تباين واجهة الاستخدام، تشغيل CI على فرع `develop`، وبعض مخالفات Ruff القابلة للإصلاح الآلي.

توجد حدود تحقق يجب أن تمر عبر CI أو جهاز تطوير مجهز: لا يتوفر Android SDK ولا Flutter SDK في بيئة التنفيذ الحالية، كما أن أداة `offline_risk_audit.py` المصدرية المشار إليها في ملاحظات الجلسة غير موجودة في نسخة المستودع الحالية. لذلك تم تشغيل الاختبارات المتاحة، وفحص الأسرار الرسمي الموجود في المستودع، وفحص ساكن مباشر لعلامة قاعدة SQLite plaintext، مع توثيق هذه الحدود بدلاً من اعتبارها نجاحاً زائفاً.

## 2. commits المنفذة

| Commit | المضمون | الحالة |
|---|---|---|
| `8dd04d1d` | تشفير SQLite at rest في Android وFlutter، مفاتيح دائمة، تشفير طابور المزامنة، cursor، recovery، وقواعد release | منفذ محلياً |
| `4ab5a20d` | إغلاق P2 للخصوصية، password reset، WCAG، CI، واختبارات regression | منفذ محلياً |
| `16a197a3` | تحديث خريطة عقود مسارات الواجهة وإغلاق audit artifacts | منفذ محلياً |

وتبقى commits المجال الخلفي والواجهة الأساسية السابقة ضمن نفس الفرع، بما في ذلك `c7a1be25` و`d2d47581`.

## 3. نطاق التنفيذ الفني

### 3.1 نظام العيادات الشعبية

تم تثبيت نماذج المجال والعقود والخدمات والمسارات الخاصة بالعيادات الشعبية، مع فصل الصلاحيات بين الطبيب، الصيدلي، المختبر، الأشعة، السونار، الضماد، الاستقبال، وقاطع التذاكر والتحصيل. يتضمن المجال ملف المريض المزمن، خطة العلاج، الصرف الشهري، الخدمات، الزيارات، السجلات السريرية، التذاكر، والتحصيل الداخلي. ويُفرض عدم تكرار الصرف للمريض نفسه خلال الشهر مع التسعير الحكومي المعتمد: 3,250 ديناراً نقداً و3,000 دينار إلكترونياً.

### 3.2 Offline-first الآمن

في Android أضيفت طبقة تشفير SQLCipher لقاعدة Room، ومفتاح قاعدة مستقل محفوظ في `EncryptedPrefs`، وترحيل آمن من قاعدة SQLite plaintext إلى نسخة مشفرة، مع فحص integrity قبل استبدال الملف. كما أضيف تشفير AES-GCM لعناصر طابور المزامنة، وهوية جهاز ثابتة عبر `X-Sync-Device-ID`، وحفظ cursor، واسترداد عناصر `IN_PROGRESS`، وحالة `DEFERRED`، وإعادة المحاولة عبر WorkManager. ويحافظ `clearAll()` على مفاتيح قاعدة البيانات وهوية الجهاز ومفتاح payload حتى لا يؤدي تسجيل الخروج إلى فقدان القدرة على فتح البيانات المحلية المشفرة.

في Flutter Desktop تم استبدال `NativeDatabase(file)` بفتح SQLite3 Multiple Ciphers مع مفتاح محفوظ آمن، وترحيل plaintext، وحارس fail-closed يمنع التشغيل غير المشفر.

### 3.3 إصلاحات P2

أزيلت عناوين البريد وأرقام الهواتف ومقتطفات الرسائل من سجلات البريد وSMS وWhatsApp، مع إبقاء رسائل الحالة التشغيلية والأخطاء غير الحساسة. وأضيف اختبار regression يمنع عودة PII إلى logs.

وسّع تدفق استعادة كلمة المرور ليشمل حسابات `User` الأساسية إلى جانب `LabUser`. أضيفت حقول reset token إلى نموذج `User` وترحيل `20260815_0022_user_password_reset`، مع تحقق موحد من tokens المجزأة، واستجابة عامة لا تكشف وجود البريد الإلكتروني، واختبار تكاملي لحساب المنصة الأساسي.

رُفع تباين مؤشر التركيز `ring` في الوضع الفاتح إلى لون داكن قوي، ورُفع تباين success في `Badge` و`ToastContainer` إلى درجات `emerald` أغمق. كما أضيف `develop` إلى push وpull request triggers في CI.

شغّل Ruff الإصلاحات الآلية الآمنة للقواعد `F/B/S`؛ أزيلت تسعة imports غير مستخدمة دون تغيير سلوك الأعمال. أما baseline القديم على مستوى `backend/app` فما زال يحوي مخالفات واسعة، معظمها `E501` و`B008`، ولا يمكن اعتباره مغلقاً بالكامل من دون مشروع تنسيق ومراجعة مستقل؛ وقد جرى عزل هذه الحقيقة في قسم المتبقي أدناه.

## 4. نتائج بوابات التحقق

| البوابة | النتيجة | الدليل أو الملاحظة |
|---|---:|---|
| Backend P0 + offline + auth + notification privacy | ناجحة: **55/55** | `pytest` على الاختبارات المتاحة |
| Compile Python للموديلات والمسارات والترحيل | ناجح | `compileall` |
| Alembic head | ناجح: **0022 head واحد** | `alembic heads` |
| Public secrets audit | ناجح | `scripts/security/check_public_secrets.py` أعاد عدم وجود أسرار عامة محتملة |
| Offline plaintext static guard | ناجح | لا توجد مطابقة `NativeDatabase(file)` في mobile |
| Frontend typecheck | ناجح | `pnpm typecheck` |
| Frontend tests | ناجحة: **49/49** في **14** ملف اختبار | `pnpm test` |
| Frontend unification | ناجح | `pnpm verify:unification` |
| Contract governance | ناجح | `pnpm verify:contracts` |
| Integration boundary | ناجح | `pnpm verify:integration-boundary` |
| Data-source governance | ناجح: **93 سطحاً** | `pnpm verify:data-sources` |
| Audit artifacts | ناجح: **309 مساراً خلفياً و93 مدخل واجهة** | بعد تحديث route contract map في `16a197a3` |
| Frontend ESLint | ناجح | `pnpm lint` |
| Frontend build | ناجح | `pnpm build` |
| Bundle size | ناجح؛ لا violations | `pnpm check:bundle`، الإجمالي 1,475,720 bytes |
| Android Kotlin/Gradle | غير قابل للتحقق محلياً | فشل بسبب `SDK location not found` فقط؛ لا توجد نتيجة Kotlin قابلة للتقييم |
| Flutter analyze | غير قابل للتحقق محلياً | Flutter وDart SDK غير مثبتين |

## 5. المتبقي والمخاطر المعروفة

أولاً، الفرع المحلي لا يملك فرعاً بعيداً مقابلاً؛ `git ls-remote` لم يُظهر `origin/security/p0-bootstrap-alembic`، كما أن upstream المحلي يشير إلى `origin/main`. لذلك لا يمكن إنشاء PR قابل للمراجعة على GitHub من دون رفع الفرع أولاً، ورفع الفرع إجراء خارجي لم يُنفذ احتراماً لقاعدة عدم إجراء `push` أو `merge` دون موافقة بشرية صريحة.

ثانياً، الملفان `backend/tests/test_offline_sync_contract.py` و`backend/scripts/offline_risk_audit.py` المشار إليهما في ملاحظات الجلسة غير موجودين في الشجرة الحالية. الاختبارات المتاحة في `backend/tests/test_offline_sync.py` نجحت، كما استُخدم فحص الأسرار الفعلي الموجود في `scripts/security/check_public_secrets.py` وفحص ساكن مباشر لعلامة plaintext. ينبغي في CI إعادة تشغيل أدوات التدقيق الرسمية من مصدرها المعتمد أو إعادة إضافة ملفاتها إن كانت مطلوبة كجزء من العقد.

ثالثاً، ما زال في المستودع baseline واسع لـRuff عند تشغيل `ruff check --select E,F,B,S backend/app`: **8,869 مخالفة** في لقطة التحقق، منها 4,556 `E501` و3,710 `B008` و218 `S101`، إضافة إلى قواعد أمنية وتصميمية أخرى. أُصلحت المخالفات الآلية الآمنة التسع، وجميع الملفات الجديدة أو المعدلة في password reset والاختبارات تمر بفحص `E9,F`. لكن الإغلاق الكامل لهذا البند يتطلب حملة مستقلة لتقسيم الملفات، معالجة `B008` الخاص بتواقيع FastAPI، مراجعة قواعد `S`، وإعادة تنسيق `E501` تدريجياً، ولا ينبغي تنفيذ ذلك آلياً على كامل backend في نفس PR الحساس.

رابعاً، ظهرت تحذيرات غير حاجبة في الاختبارات، منها تحذير Starlette/httpx، استعمال `datetime.utcnow()` في مكوّن قديم، وتحذير SQLAlchemy متعلق بدورة Foreign Keys في teardown الاختبارات. هذه ليست فشل gates الحالي لكنها مرشحة لـP2 لاحق مستقل.

## 6. خطوات CI والنشر الآمنة

قبل فتح PR، يجب أن يرفع صاحب الصلاحية commits المحلية إلى فرع بعيد مؤقت باسم مطابق، ثم ينشئ PR إلى `develop` لا إلى `main`. يجب أن يشمل PR commits الثلاثة الجديدة والـcommits السابقة الخاصة بمجال العيادات الشعبية، مع ذكر أن Android وFlutter يحتاجان تحققاً على runners أو أجهزة مزودة بالـSDK. بعد فتح PR، يجب انتظار بوابات CI، ومراجعة migration `0022` وSQLCipher، وتشغيل `alembic upgrade head` على PostgreSQL اختبارية، ثم إجراء مراجعة بشرية أمنية قبل أي دمج.

لا توجد خطوة نشر أو merge منفذة في هذا التقرير. كما لا ينبغي حذف الفرع المؤقت إلا بعد التأكد من عدم وجود deployment أو PR أو عمل نشط مرتبط به.

## 7. الملفات المرجعية الرئيسية

| المجال | الملفات |
|---|---|
| مجال العيادات | [`backend/app/models/popular_clinic.py`](../backend/app/models/popular_clinic.py)، [`backend/app/routes/popular_clinics.py`](../backend/app/routes/popular_clinics.py)، [`backend/app/services/popular_clinics.py`](../backend/app/services/popular_clinics.py) |
| Offline-first Android | [`DatabaseModule.kt`](../mobile/android/app/src/main/java/io/gula/android/di/DatabaseModule.kt)، [`SyncRepositoryImpl.kt`](../mobile/android/app/src/main/java/io/gula/android/data/repository/SyncRepositoryImpl.kt)، [`SecurePayloadCodec.kt`](../mobile/android/app/src/main/java/io/gula/android/security/SecurePayloadCodec.kt) |
| Offline-first Flutter | [`database.dart`](../mobile/desktop/lib/core/offline/database.dart)، [`secure_config.dart`](../mobile/desktop/lib/core/security/secure_config.dart) |
| Password reset | [`password_reset.py`](../backend/app/routes/password_reset.py)، [`user.py`](../backend/app/models/user.py)، [`20260815_0022_user_password_reset.py`](../backend/migrations/versions/20260815_0022_user_password_reset.py) |
| الخصوصية | [`sender.py`](../shared/notifications/sender.py)، [`test_notification_sender_privacy.py`](../backend/tests/test_notification_sender_privacy.py) |
| WCAG وGovernance | [`theme.css`](../frontend-v3/src/styles/theme.css)، [`Badge.tsx`](../frontend-v3/src/components/ui/Badge.tsx)، [`FRONTEND_ROUTE_CONTRACT_MAP.md`](../docs/contract-audit/generated/FRONTEND_ROUTE_CONTRACT_MAP.md) |

## 8. القرار المطلوب من المراجع البشري

المطلوب الوحيد قبل الخطوة الخارجية التالية هو الموافقة الصريحة على رفع الفرع المحلي إلى GitHub وإنشاء PR إلى `develop`. لا يتضمن ذلك الموافقة على merge؛ فالدمج والنشر يجب أن يبقيا خاضعين للمراجعة البشرية ونتائج CI النهائية.

## References

[1]: https://github.com/samertts/gula-platform "Gula Platform repository"
[2]: https://github.com/samertts/gula-platform/blob/develop/.github/workflows/ci.yml "Gula Platform CI workflow"
[3]: https://github.com/samertts/gula-platform/tree/develop/backend/migrations/versions "Gula Platform database migrations"
