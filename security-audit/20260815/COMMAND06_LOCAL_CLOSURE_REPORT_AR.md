# تقرير الإغلاق المحلي — Command 06

**المشروع:** GULA Platform — نظام العيادات الطبية الشعبية ومنصة GULA
**تاريخ التقرير:** 16 آب 2026
**الفرع:** `security/p0-bootstrap-alembic`
**HEAD قبل هذه الدفعة:** `b2b90972`
**نطاق العمل:** المعالجة المحلية للأمن، الصلاحيات، عزل البيانات، UTC timestamps، والتحقق البرمجي. لم يُنفذ push أو merge أو deployment أو production migration.

## الخلاصة التنفيذية

أُنجزت دفعة المعالجة المحلية المطلوبة على الفرع الحالي. أُغلقت residuals الزمنية في نطاق `backend/app` و`shared` بالكامل، وأصبح عدد الاستخدامات النصية لـ`datetime.utcnow` **صفراً**. شمل ذلك الاستدعاءات المباشرة، وحقول `dataclass` ذات `default_factory`، وSQLAlchemy `default/onupdate`، والقوالب التي كانت ستعيد إنتاج الكود deprecated مستقبلاً.

كما تم فصل صلاحيات المسارات المالية في `backend/app/financial/routes.py` إلى صلاحيات قراءة وكتابة وإدارة orchestration وقراءة الاشتراكات. وتمت مواءمة `frontend-v3` مع سجل الصلاحيات canonical، بحيث يستخدم edge platform صلاحية `runtime:operate` وتستخدم واجهة financial صلاحية `payments:read` بدلاً من التفويض العام أو الصلاحيات غير المطابقة. أُبقي محرك التحصيل المالي خلف feature flag المغلق افتراضياً، لأن تشغيله الحكومي الفعلي يحتاج بيئة staging وربطاً رسمياً ومراجعة بشرية.

> النتيجة المحلية: **صفر residual معروف ضمن نطاق UTC، وصفر regression في بوابة backend الواسعة، ونجاح بوابة frontend.** النتيجة التشغيلية: **SAFE_STOP ما زال سارياً** لأن بعض الأدلة المطلوبة لا يمكن إثباتها داخل البيئة المحلية.

## الحالة والفرع

| المؤشر | النتيجة |
|---|---|
| الفرع الحالي | `security/p0-bootstrap-alembic` |
| HEAD المرصود | `b2b90972` |
| push أو merge | لم يُنفذ |
| deployment أو production migration | لم يُنفذ |
| working tree | يحتوي تغييرات محلية مقصودة، ولم تُعتمد خارجياً |
| عدد الملفات المتأثرة | 124 ملفاً وفق diffstat، وتشمل دفعة UTC والصلاحيات والاختبارات والتوثيق |

## الإصلاحات المنفذة

### الصلاحيات المالية وRBAC

تمت إضافة guards صريحة إلى مسارات billing وinvoices وpayments وreceivables وpayables وpricing وtransactions وreports وsubscriptions. أصبحت عمليات القراءة تستخدم `payments:read`، والعمليات الإنشائية أو التحصيلية تستخدم `payments:write`، وتشغيل دورة الفوترة يستخدم `payments:orchestration:manage`، وقراءة الاشتراكات تستخدم `subscriptions:read`. هذا يمنع اعتماد المسار على `get_current_user` وحده، ويقلل احتمال أن يحصل الطبيب أو المختبر على صلاحيات التحصيل لمجرد امتلاكه جلسة صحيحة.

تمت مواءمة خرائط الأدوار في `shared/rbac/permissions.py` و`frontend-v3/src/permissions/index.ts` مع هذه scopes. كما استُبدلت صلاحية `system:admin` في رابط edge بــ`runtime:operate`، واستُبدلت صلاحية `lab:manage` في رابط financial بــ`payments:read`.

### UTC والعمر الزمني للبيانات

تم تحويل كل استخدامات `datetime.utcnow` في `backend/app` و`shared` إلى UTC-aware alternatives. وتمت معالجة الحالات الحساسة زمنياً بحيث لا يُقيّم timestamp عند import؛ فحقول `default_factory` وSQLAlchemy defaults تستخدم callables lazy مثل `lambda: datetime.now(UTC)`. كما عُدلت قوالب generators وfixtures حتى لا تعيد إنتاج النمط القديم مستقبلاً.

### العقود والخصوصية والتكاملات

بقيت الإصلاحات السابقة فعالة، ومنها contract exposure gate، fail-closed Redis، تغطية `refresh_token` في CSRF، تشديد CORS، حماية health diagnostics، server-side tenant filtering للبيانات الصحية، redaction لبيانات التعريف في ecosystem audit، وتقليص TTL لروابط نتائج المختبر العامة. هذه البنود موثقة أيضاً في سجل المخاطر المحدث [1].

## نتائج التحقق

| البوابة | النتيجة |
|---|---:|
| Backend full non-integration gate | **2654 passed، 42 deselected، 20 warnings** خلال 212.75 ثانية |
| Contract/performance/route gate | **53 passed، 1 warning** |
| Side-door وroute registration بعد financial split | **67 passed، 1 warning** |
| Backend compileall | ناجح على `backend/app` و`shared` |
| UTC residual scan | `datetime.utcnow` files = **0**، occurrences = **0** |
| Frontend tests/build | ناجحان؛ تم توليد build وPWA service worker دون خطأ |
| Ruff على الملفات الأخيرة | ناجح مع استثناءات Unicode المعروفة في المشروع |

التحذيرات المسجلة ليست فشلاً في الاختبارات، لكنها ليست صفراً مطلقاً: توجد تحذيرات deprecation من Starlette وSQLite datetime adapter وSentry integration. لذلك لا يصح وصف البوابة بأنها warning-free حتى تُعالج تلك التحذيرات في دفعة مستقلة.

## ما أُغلق محلياً وما بقي SAFE_STOP

| النطاق | القرار | سبب القرار |
|---|---|---|
| UTC residuals | مغلق محلياً | scan وcompileall ناجحان، ولا توجد occurrences متبقية |
| Financial RBAC alignment | مغلق محلياً | guards واختبارات regression والبناء ناجحة |
| Frontend granular scopes | مغلق محلياً | role maps والبناء ناجحان |
| Redis fail-closed | مغلق محلياً على مستوى source/tests | يلزم outage وmulti-worker staging لإثبات السلوك التشغيلي |
| Official Identity Provider | مفتوح — SAFE_STOP | لا توجد credentials/provider sandbox أو contract evidence موثقة محلياً |
| Browser CSRF/CORS | مفتوح — SAFE_STOP جزئياً | الاختبارات المحلية لا تعادل browser matrix حقيقية مع credentials |
| PostgreSQL/Redis staging | مفتوح — SAFE_STOP | لا توجد بيئة staging متعددة العمال لإثبات race وTLS وACL |
| MQTT/AMQP/TLS/egress | مفتوح — SAFE_STOP | يلزم اختبار موصلات حقيقي، allowlist، شهادات، وdelivery receipts |
| Flutter/Android/offline | مفتوح — SAFE_STOP | SDK وADB وTalkBack/Orca غير متاحة في هذه البيئة |
| Pentest | مفتوح — SAFE_STOP | يلزم فريق مرخص أو تفويض موثق وفحص staging معزول، وليس الموقع الحي |
| warnings/deprecations | مفتوح P2 | التحذيرات لا تفشل الاختبارات لكنها تمنع ادعاء warning-free |

## قرار التشغيل

لا أوصي بتفعيل التسجيل العام، موفر الهوية الرسمي، Redis degraded fallback، محرك التحصيل الحكومي، أو أي deployment حكومي اعتماداً على هذه النتائج المحلية وحدها. القرار الآمن هو إبقاء الحالة `AUTHENTICATION_RUNTIME_PARTIAL` و`SAFE_STOP` حتى تُنفذ اختبارات staging المحددة، ثم تُراجع النتائج بشرياً، ويُنتج rollback path واضح لكل تغيير حساس.

لا توجد حاجة إلى تغيير `main` أو `develop` أو حماية الفروع أو حذف فرع. ولا ينبغي تنفيذ merge أو push تلقائي؛ تبقى كل التغييرات في working tree المحلي حتى موافقة بشرية صريحة وفق حوكمة المستودع.

## الملفات الأساسية المتأثرة

| الملف | الغرض |
|---|---|
| `backend/app/financial/routes.py` | فصل صلاحيات financial routes وإصلاح UTC transaction timestamp |
| `frontend-v3/src/permissions/index.ts` | مواءمة role maps وnavigation مع granular scopes |
| `shared/rbac/permissions.py` | السجل canonical للصلاحيات الموسعة والأدوار |
| `backend/app/contracts/routes.py` | حماية contract metadata وinternal export |
| `backend/app/routes/ai.py` | privacy وTTL وcache bounding لمسارات AI العامة |
| `backend/app/national/ecosystem/routes.py` | least privilege وaudit redaction للتكاملات |
| `backend/app/models/lab_result.py` | hash/TTL/error minimization لروابط النتائج العامة |
| `security-audit/20260815/COMPREHENSIVE_RISK_INVENTORY_AND_REMEDIATION_PLAN_AR.md` | سجل المخاطر مع ملحق الحالة الحالية |
| `scripts/convert_utcnow.py` | أداة deterministic محلية قابلة للمراجعة لتحويل residuals الزمنية |

## المراجع

[1]: `COMPREHENSIVE_RISK_INVENTORY_AND_REMEDIATION_PLAN_AR.md` — سجل المخاطر الشامل وملحق التحقق المحلي.

[2]: `../../backend/app/financial/routes.py` — مسارات المحرك المالي وصلاحياتها الجديدة.

[3]: `../../shared/rbac/permissions.py` — سجل الصلاحيات canonical وخرائط الأدوار.

[4]: `../../frontend-v3/src/permissions/index.ts` — مواءمة صلاحيات وواجهة frontend-v3.

[5]: `../../backend/tests/test_security_regression.py` — اختبارات regression الأمنية.

[6]: `../../backend/tests/test_side_door_hardening.py` — اختبارات منع المسارات الجانبية.
