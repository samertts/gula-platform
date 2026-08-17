# تقرير جرد مسارات GULA وتحليل الحماية

**تاريخ الفحص:** 17 آب/أغسطس 2026

**المستودع:** [`samertts/gula-platform`](https://github.com/samertts/gula-platform)

**الفرع:** `chore/security-ddos-hardening-clean`

**نطاق الفحص:** مسارات FastAPI المركبة محلياً، تعريفات AST، OpenAPI، مسارات React Router، ومسارات GoRouter في تطبيق desktop/mobile.

**حدود الفحص:** جرد وتحليل ساكن ومحلي فقط؛ لم تُرسل طلبات هجومية إلى الإنتاج، ولم تُجرَ محاولات تجاوز مصادقة، ولم تُعدّل قاعدة بيانات أو بيئة إنتاج.

## القرار التنفيذي

تم اكتشاف **2,029 عملية OpenAPI فعلية** في الوضع المحلي، و**2,034 مساراً runtime** بعد flattening للـrouters، و**2,353 decorator ثابتاً** في `backend/app`. كما جرى جرد **95 تعريف مسار في React/PWA** و**37 تعريف مسار في GoRouter desktop/mobile**. لم تظهر duplicate operation IDs في OpenAPI، لكن ظهرت **ثلاث مجموعات runtime مكررة لنفس method/path**، وهي مشكلة جودة وتحتاج إزالة أو توحيداً قبل اعتماد الجرد النهائي.

أهم نتيجة أمنية هي وجود مسارات تسجيل عامة تتعارض مع قاعدة المشروع المعلنة: **No Public Registration؛ Account Request فقط؛ human type فقط**. كما يوجد مسار عام لسجل المريض يعتمد على الهاتف والاسم، إضافة إلى مسارات مشاركة نتائج تعتمد على token عام. لا يعني هذا التقرير أن كل هذه المسارات مستغلة حالياً، لكنه يثبت أنها تحتاج قراراً أمنياً/حوكمياً واضحاً ولا يجوز إعلانها PASS تلقائياً.

> **الحكم الحالي:** جرد المسارات مكتمل محلياً، لكن المسارات العامة الحساسة وازدواجية runtime تحتاج معالجة ومراجعة أمنية قبل إعلان P4 كاملاً أو بدء P5. لا يغيّر هذا التقرير حالة `P4 SECURITY_BLOCKED — AUTHENTICATION_PARTIAL` ولا حالة `P5_BLOCKED_BY_PREREQUISITE`.

## 1. منهجية الجرد

استخدم الفحص ثلاث طبقات مستقلة. الطبقة الأولى حللت AST لجميع ملفات Python في `backend/app` دون استيراد التطبيق، لاستخراج `APIRouter` وdecorators و`include_router`. الطبقة الثانية شغّلت التطبيق محلياً في `RUNTIME_MODE=openapi` و`OPENAPI_EXPORT=true`، ثم صدّرت OpenAPI وflattened مسارات `APIRoute` وdependencies الفعلية. الطبقة الثالثة جردت تعريفات `createBrowserRouter` و`GoRoute` من مصادر الواجهات فقط. لا تُعد نتائج الواجهة دليلاً على التفويض الخادمي؛ فالـserver-authoritative authorization هو المرجع.

## 2. الإحصاءات الرئيسية

| السطح | العدد | طريقة القياس | التفسير |
|---|---:|---|---|
| ملفات backend/app Python | 1,883 | AST scan | دون parse errors |
| تعريفات APIRouter | 201 | AST scan | تشمل routers المضمّنة أو الشرطية |
| decorators ثابتة | 2,353 | AST scan | قد تشمل تعريفات غير مركبة runtime |
| include_router calls | 147 | AST scan | تشمل factory والـcomposition |
| OpenAPI operations | 2,029 | local OpenAPI export | المسارات المركبة والقابلة للتصدير |
| runtime APIRoute entries | 2,034 | runtime flattening | يشمل التكرار المضمّن |
| OpenAPI operations مع security metadata | 1,885 | OpenAPI | metadata ليست بديلاً عن فحص dependencies |
| OpenAPI operations بلا security metadata | 144 | OpenAPI | بعضها محمي داخلياً أو router-level |
| runtime routes مع dependencies | 1,980 | runtime dependency tree | يشمل DB وBearer وactor وغيرها |
| runtime routes بلا dependencies | 54 | runtime dependency tree | أعلى مجموعة تحتاج مراجعة |
| React/PWA route declarations | 95 | `frontend-v3/src/routes/index.tsx` | جرد client-side فقط |
| GoRouter desktop/mobile declarations | 37 | `mobile/desktop/lib/app_router.dart` | لا يثبت native build parity |
| duplicate OpenAPI operation IDs | 0 | OpenAPI analysis | PASS لهذا الفحص المحدد |
| duplicate runtime method/path groups | 3 | runtime analysis | finding مفتوح |

توزيع عمليات OpenAPI هو: **986 GET، 866 POST، 123 PUT، 49 DELETE، و5 PATCH**. مجموع هذه القيم يساوي 2,029 عملية.

## 3. خريطة العائلات الرئيسية

تظهر عائلات المسارات في OpenAPI على شكل مجالات كبيرة للهوية والطب والمختبر والصيدلة والحوكمة. الجدول التالي يلخص أكبر مجموعات tags، بينما توجد القائمة الكاملة في ملف [`api-operations.json`](./api-operations.json).

| العائلة | عدد العمليات |
|---|---:|
| NIAM | 228 |
| EHR | 86 |
| Care continuum | 74 |
| Governance | 70 |
| LIMS | 69 |
| Nursing | 66 |
| Clinical | 63 |
| NHDW | 61 |
| Pharmacy | 59 |
| Radiology | 58 |
| Document Intelligence | 50 |
| Research Platform | 49 |
| AI Fabric | 42 |
| NIAM Lifecycle | 42 |
| Hospital | 39 |
| NIAM Trust | 31 |
| National Task Engine | 29 |
| FHIR | 29 |
| National Scheduling Platform | 28 |
| Authorization | 27 |
| National EMS Platform | 26 |
| Device integration | 26 |

هذه المجموعات وصفية وليست بديلاً عن تحليل permission لكل endpoint. قد يحمل endpoint أكثر من tag، لذلك لا ينبغي جمع أعداد tags للحصول على إجمالي العمليات.

## 4. نتائج الحماية

### 4.1 مسارات لا تملك runtime dependencies

وجد الفحص 54 مساراً بلا dependencies مباشرة في `APIRoute`. وتشمل `/health*` و`/test-types` و`/test-profiles` و`/app-updates` و`/tiers` وmetadata الخاصة بـOAuth2/SAML/FHIR، إضافة إلى `/contracts/*` و`/certification/*` وبعض health/metadata وAI/public-result endpoints. القائمة الكاملة موجودة في [`runtime-no-deps.tsv`](./runtime-no-deps.tsv).

غياب dependency لا يثبت وحده أن المسار غير محمي؛ بعض الوظائف تستدعي helper داخلياً أو تعتمد على توقيع webhook أو token logic. لكن وفق قاعدة **Default Deny** يجب أن تكون الحماية قابلة للإثبات في endpoint نفسه أو في router dependency موثق ومختبر، لا أن تعتمد على افتراضات من اسم المسار.

### 4.2 التسجيل العام — finding حرج بالنسبة لسياسة المشروع

| المسار | الدليل المصدر | السلوك المرصود | التقييم |
|---|---|---|---|
| `POST /register` | `backend/app/routes/register.py:194-258` | ينشئ Lab وLabUser في حالة inactive/pending approval بعد كتابة قاعدة البيانات؛ لا يصدر token | **Public onboarding؛ تعارض مع Account Request-only policy** |
| `POST /register/citizen` | `backend/app/routes/register.py:308-399` | ينشئ `User(role="citizen", is_active=True, is_verified=False)` ويمتد إلى mint citizen identity | **Public self-registration؛ تعارض مباشر مع No Public Registration** |
| `POST /register/doctor` | `backend/app/routes/register.py:564-650` | موثق صراحةً `no auth required` وينشئ doctor فعالاً مع `is_verified=False` | **Public self-registration؛ تعارض مباشر مع السياسة** |
| `POST /register/staff` | `backend/app/routes/register.py:439-504` | يعتمد على `get_current_user` ويتطلب role admin | **محمي مبدئياً؛ يحتاج اختبار tenant/role** |

هذه ليست ملاحظة شكلية. حتى عندما تكون بعض الحسابات pending أو غير verified، فإن المسار العام يكتب سجلات هوية ويخلق حسابات جديدة، بينما متطلب المشروع ينص على أن التسجيل العام غير مسموح وأن المسار المقبول هو Account Request لشخص بشري فقط. يجب أن يكون القرار إما إزالة/تعطيل المسارات العامة أو تحويلها إلى account-request intake لا ينشئ حساباً قابلاً للدخول ولا يفعّل هوية مباشرة.

### 4.3 سجلات المواطنين والنتائج العامة

`GET /history/{phone}` موثق في `backend/app/routes/results.py:282-302` بأنه public وrate-limited، ويتطلب `name` query parameter. ويظهر من `backend/app/services/order_service.py` أن التنفيذ يبحث عن phone مطابقاً تماماً ويقارن الاسم باستخدام HMAC ثم يجمع history عبر المختبرات. هذا يقلل بعض مخاطر التخمين لكنه لا يساوي مصادقة قوية، ويظل مساراً عاماً يعيد بيانات طبية حساسة.

المساران `GET /r/{token}` و`GET /r/{token}/pdf` يستخدمان token للمشاركة العامة، مع expiry وtoken hash وفق الخدمة المقروءة. يجب مراجعة entropy، وone-time/revocation behavior، وعدم تسجيل token، وسياسة الحد من إعادة المشاركة، لأن حامل token يستطيع الوصول إلى النتيجة دون جلسة مستخدم تقليدية.

مسارات `/citizen/profile` و`/citizen/results` و`/citizen/orders` و`/citizen/health-record` لا تعرض `Depends` في signature، لكنها تستدعي `_current_citizen(request, db)` داخلياً. هذه الدالة تستخدم `get_current_user` وتفرض `role == "citizen"`، كما أن الاستعلامات تُقيد server-side بهاتف المواطن أو national-id hash وpatient IDs. النتيجة هي **حماية داخلية موجودة، لكن metadata لا تعكسها بوضوح**؛ يجب إضافة regression test يثبت 401/403 بلا cookie وبهوية غير citizen، وربط dependency صريح إن كان ذلك لا يغيّر contract، حتى لا يُساء فهمها أو تُنسى عند إعادة البناء.

### 4.4 NIAM

يُركّب `backend/app/identity/api/router.py` المسارات الأساسية `/niam/persons` و`/niam/account-requests` و`/niam/accounts` و`/niam/auth` و`/niam/sessions` و`/niam/workspaces` و`/niam/memberships` و`/niam/roles` و`/niam/audit` و`/niam/consents` و`/niam/security` و`/niam/devices` دون `_AUTH_REQUIRED` على مستوى المجموعة. أما governance/trust/lifecycle/federation/certificates/workflows/notifications/adaptive-auth/admin/compliance فتُضمّن مع `Depends(get_current_niam_actor)`.

`/niam/accounts/` و`/niam/accounts/{account_uuid}/lock` و`/niam/accounts/{account_uuid}/unlock` تظهر كمسارات بلا dependencies، لكن `backend/app/identity/api/accounts.py` يجعلها fail-closed بإرجاع **HTTP 410 Gone** وتعطيل الإنشاء والتعديل المباشر. هذه المسارات ليست دليلاً على public account creation فعّال، لكنها ينبغي أن تبقى مغطاة باختبار يمنع عودتها إلى سلوك قابل للتنفيذ.

### 4.5 مسارات operational/metadata

المسارات `/health/deep` و`/health/status` و`/health/kernel` و`/edge/health` و`/governance/health` و`/national/*/health` و`/contracts/*` و`/oauth2/.well-known/*` و`/auth/saml/metadata` و`/fhir-interoperability/metadata` تبدو مصممة للتشغيل أو metadata. مع ذلك، `/health/deep` يصف database/Redis latency وqueue backlog وmemory/circuit state؛ ينبغي وضعه خلف شبكة مراقبة أو حماية مناسبة إذا كانت هذه المؤشرات تعتبر معلومات تشغيلية حساسة.

مسارات `POST /api/v1/telegram/webhook` و`POST /edge/agent/*` و`POST /contracts/export` و`POST /certification/*` لا ينبغي اعتبارها آمنة لمجرد أنها لا تحمل Bearer metadata. يجب إثبات signature/API-key verification أو جعلها محمية بـactor/permission، ثم إضافة test contract لكل مسار.

## 5. التكرارات المكتشفة

لم توجد duplicate operation IDs في OpenAPI، لكن runtime flattening وجد التكرارات التالية:

| Method | Path | Implementations | Modules |
|---|---|---:|---|
| GET | `/clinical/quality/benchmarks` | 2 | `app.routes.clinical`, `app.routes.clinical_quality` |
| POST | `/clinical/quality/measurements` | 2 | `app.routes.clinical`, `app.routes.clinical_quality` |
| GET | `/integration/connectors` | 2 | `app.integration.routes`, `app.integration.connectors.routes` |

جميع النسخ المرصودة تحمل dependencies Bearer/`get_current_user`، وبعضها يحمل `require_permission`. لذلك لا يوجد من هذا الجرد وحده إثبات BOLA، لكن duplicate registration قد يجعل FastAPI يختار implementation بحسب ترتيب التسجيل، فينتج contract غير واضح أو authorization drift. يجب توحيد كل مجموعة إلى implementation واحد وإضافة OpenAPI/runtime uniqueness test.

## 6. واجهات الويب وdesktop/mobile

يحتوي `frontend-v3/src/routes/index.tsx` على **95 تعريف route**. الصفحات العامة الظاهرة تشمل `/login` و`/register` و`/recover` و`/verify` والوثائق القانونية. معظم صفحات العمل محاطة بـ`RoleGuard`، ويستخدم `/device-integration` أيضاً `InstitutionalOnlyRoute`. هذا مفيد كحاجز تجربة مستخدم، لكنه لا يثبت التفويض الخادمي ولا يبرر فتح API.

يحتوي `mobile/desktop/lib/app_router.dart` على **37 تعريف GoRoute**، بما في ذلك `/login` و`/mfa` و`/forgot-password` و`/account-request` ومساحات dashboard/patients/orders/samples/results/reports/memberships. هذا جرد مصدر فقط؛ لا يُعلن نجاح native build أو parity كاملة بين Web/PWA وdesktop/mobile.

## 7. الأولويات والتوصيات

| الأولوية | finding | المعالجة المطلوبة | معيار الإغلاق |
|---|---|---|---|
| P0 | Public citizen/doctor registration conflicts with project policy | تعطيل المسارات العامة أو تحويلها إلى Account Request لا ينشئ حساباً فعالاً ولا يمسح public registration policy | 401/403 أو intake-only behavior مثبت باختبارات، ولا public account creation |
| P0 | Public `/history/{phone}` returns medical history | نقل الوصول إلى citizen session أو short-lived consented share token قوي؛ إزالة phone+name كحد مصادقة | tests تثبت deny بلا session/share authorization وtenant isolation |
| P1 | Token result sharing `/r/{token}` وPDF | مراجعة entropy/expiry/revocation/logging/rate-limit وعدم كشف token | threat-model وtests للانتهاء والإلغاء وإعادة الاستخدام |
| P1 | Runtime duplicate routes | توحيد implementations الثلاثة وإزالة duplicate registration | uniqueness test يمر في runtime وOpenAPI |
| P1 | No-dependency writes/operational endpoints | إثبات signature/actor/permission لكل webhook/export/certification/policy endpoint | dependency/security contract tests لكل endpoint |
| P2 | Citizen endpoints use internal auth helper only | جعل server dependency صريحاً أو توثيق helper مع tests وعدم الاعتماد على client guard | OpenAPI/security metadata و401/403 tests متطابقة |
| P2 | Public health/metadata exposure | تحديد public/private policy لكل health/contract/metadata path وتقييد operational detail | allowlist موثقة واختبارات response contract |
| P2 | Cross-platform route parity | إنشاء matrix مستقلة لـWeb/PWA/desktop/mobile مع build evidence | لا تُصنّف NOT_BUILT/UNVERIFIED كـPASS |

## 8. حدود التقرير

هذا التقرير لا يثبت قابلية استغلال خارجية ولا يمثل penetration test. القياسات ناتجة عن source inspection وOpenAPI export محلي، ولم تُنفّذ طلبات production أو brute force أو token guessing أو تجاوز مصادقة. كما أن غياب dependency في AST أو runtime لا يكفي وحده للحكم على مسار يستخدم authorization helper داخلياً؛ لذلك صُنفت هذه الحالات على أنها **Needs proof** حيث لا يوجد دليل كافٍ.

لم يُجرَ أي تغيير كودي بسبب طلب المستخدم الحالي الذي اقتصر على الاكتشاف والتقرير. تبقى findings أعلاه مفتوحة حتى اعتماد معالجة منفصلة وفق SAFE_STOP، ولا يجوز بدء P5 أو إعلان P4 PASS استناداً إلى هذا الجرد وحده.

## 9. الملفات والأدلة

| الملف | المحتوى |
|---|---|
| [`api-openapi.json`](./api-openapi.json) | OpenAPI المحلي الكامل |
| [`api-operations.json`](./api-operations.json) | عمليات OpenAPI المنقحة مع method/path/security/tags |
| [`runtime-routes.json`](./runtime-routes.json) | runtime routes وdependencies الفعلية |
| [`backend-static-routes.csv`](./backend-static-routes.csv) | AST route decorators |
| [`router-declarations.csv`](./router-declarations.csv) | APIRouter declarations |
| [`router-includes.csv`](./router-includes.csv) | include_router calls |
| [`runtime-no-deps.tsv`](./runtime-no-deps.tsv) | 54 runtime routes بلا dependencies مباشرة |
| [`runtime-duplicates.tsv`](./runtime-duplicates.tsv) | مجموعات التكرار الثلاث |
| [`runtime-duplicate-details.txt`](./runtime-duplicate-details.txt) | modules/dependencies لكل تكرار |
| [`frontend-routes.tsv`](./frontend-routes.tsv) | 95 React route declarations |
| [`mobile-desktop-routes.tsv`](./mobile-desktop-routes.tsv) | 37 GoRoute declarations |
| [`no-security-openapi.tsv`](./no-security-openapi.tsv) | 144 عملية بلا OpenAPI security metadata |
| [`summary.json`](./summary.json) | counts الأساسية |

## References

[1]: ../../command04-authentication-hardening-report.md "Command 04 authentication hardening report"
[2]: ../../../backend/app/routes/register.py "Registration routes source"
[3]: ../../../backend/app/routes/citizen_portal.py "Citizen portal routes source"
[4]: ../../../backend/app/routes/results.py "Result and history routes source"
[5]: ../../../backend/app/services/order_service.py "Public result/history service source"
[6]: ../../../backend/app/identity/api/router.py "NIAM router composition"
[7]: ../../../backend/app/identity/api/accounts.py "Disabled direct account mutation source"
[8]: ../../../frontend-v3/src/routes/index.tsx "Web/PWA route declarations"
[9]: ../../../mobile/desktop/lib/app_router.dart "Desktop/mobile GoRouter declarations"
