# تقرير Command 06 — تقوية Membership وWorkspace وAuthorization Context

**المؤلف:** Manus AI
**التاريخ:** 2026-08-17
**المستودع:** `samertts/gula-platform`
**الفرع:** `chore/security-ddos-hardening-clean`
**النطاق:** `Account → Membership → Organization → Facility → Workspace → Role/Permission → Policy → Authorized Resource`

## 1. القرار التنفيذي

النتيجة النهائية هي **`AUTHORIZATION_CONTEXT_PARTIAL`**. تم تنفيذ الإصلاحات الآمنة ذات الدليل المحلي، ولم يظهر في الاختبارات أي تسريب cross-tenant أو cross-organization أو stale privilege بعد revocation أو authorization bypass. ومع ذلك لا يمكن رفع الحالة إلى `AUTHORIZATION_CONTEXT_REMEDIATED` بسبب بقاء بعض الحدود غير القابلة للإثبات محلياً: لا يوجد NIAM Entitlement aggregate مستقل، لا تزال legacy authorization surfaces موجودة بوصفها compatibility paths، native Android/iOS/Flutter CI غير متاحة، والتحقق من PostgreSQL الفعلية وruntime production غير متاح.

> لم يُنفذ أي production deployment أو production database modification أو automatic merge أو privilege bypass. أي بند لا يملك دليلاً محلياً صريحاً صُنّف `PARTIAL` أو `UNVERIFIED` بدلاً من اعتباره مكتملًا.

## 2. ملخص التغييرات المنفذة

| المجال | المشكلة الجذرية | الإصلاح المنفذ | الدليل الأمني |
|---|---|---|---|
| Membership lifecycle | كانت بعض آثار revoke/suspend محصورة في تغيير status والتدقيق، مع احتمال بقاء session/context قديم. | إضافة `revoke_account_access()` لتعطيل كل الجلسات النشطة وسياقات workspace في نفس transaction، مع audit `session_revoked`. | اختبار يثبت تعطيل جلستين وسياق واحد بثلاثة DB round-trips ثابتة، وfull suite أخضر. |
| Organization/Facility context | كانت صحة organization/facility/workspace تعتمد جزئياً على service checks، مع قبول بعض السياقات الأضيق دون إثبات الحالة الفعالة. | Membership context يرفض workspace غير النشط أو غير المتوافق مع facility؛ workspace discovery يستبعد organization/facility غير النشطة؛ role assignment يتحقق من organization/facility الفعالة. | اختبارات scope mismatch وcross-organization وworkspace hardening ناجحة. |
| Workspace selection | كان frontend ينفذ auto-switch عند وجود workspace واحد، دون قرار policy صريح. | إزالة implicit auto-switch؛ يبقى المستخدم `WORKSPACE_REQUIRED` حتى ينفذ switch server-authoritative. | اختبار auth state جديد، وPlaywright auth/recovery `8/8`. |
| Workspace switch | كان permission reflection مخزناً بمفتاح organization فقط، ما قد يبقي صلاحيات workspace السابق في الذاكرة. | بعد switch يعاد تحميل memberships وتنعكس permissions للسياق الحالي فقط؛ عند عدم وجود context تُمسح permissions. | Vitest `62/62` وtypecheck/build ناجحان، واختبار server trusted scope يرفض mismatch. |
| Effective permissions | كان endpoint يقبل facility/department/unit/workspace من query كمدخلات يمكن أن تؤثر في النتيجة. | endpoint يستخرج `WorkspaceSessionContext` من session/account، يشتق scope من workspace، ويرفض أي mismatch؛ `unit_id` غير المشتق من Workspace لا يُقبل من العميل. | اختبارات cross-workspace وcross-organization ناجحة، وauthorization يبقى default-deny. |
| Global permission fallback | legacy service كان يستطيع استخدام role أو shared RBAC fallback كمصدر عالمي للصلاحية. | إزالة `shared.rbac` fallback؛ permission لا تُقبل إلا من RoleAssignment/RolePermission المسندة صراحة. | لا توجد global role/org-type permission path في legacy checker بعد الإصلاح، وfull backend suite ناجح. |
| Legacy delegation | create/revoke لم يثبتا delegator authority أو scope ownership أو maximum privilege. | management authority server-side، explicit organization scope، active role assignment، active organization/facility، tenant boundary، delegatable role، duplicate active delegation، expiry bound، وaudit deny/allow. | المسارات تعيد 403 عند فشل الإثبات، دون كشف تفاصيل حساسة أو نجاح صوري. |
| Legacy role mutations | role assignment/revoke كان يمكن أن يمر دون management gate موحد. | `LegacyAuthorizationDenied` وmanagement authority checks مع target/role/tenant/expiry validation، وربط routes بنتيجة 403 آمنة. | route boundary لا يعتمد على body وحده؛ full suite وRuff وBandit ناجحة. |
| Client-controlled resource scope | `/authz/check` وbatch كانا يقبلان resource scope authoritative من client. | رفض `tenant_id`, `organization_id`, `facility_id`, `department_id`, `unit_id`, `workspace_id`, و`resource_id` من `resource_attrs/environment`؛ المصدر الموثوق هو server resolver. | اختبار server trusted scope وstatic review؛ لا يُنفذ query/mutation عند رفض boundary. |
| Audit context | أعمدة facility/workspace/decision/reason/request/correlation كانت موجودة في model لكن لا تُملأ بشكل موحد. | توسيع `AuditService.record/record_event`، إدراج الحقول في hash عند وجودها مع الحفاظ على hash compatibility للسجلات القديمة، وربط IDs بسياق request middleware. | اختبار يتحقق من كل الحقول وسلامة chain؛ Bandit ناجح ولا تُسجل secrets أو patient payloads. |

## 3. Membership وOrganization وFacility وWorkspace

يُفصل النظام الآن بوضوح بين **Account** و**Membership** و**Role** و**Permission**. لا يمنح membership وحده permission عالمية، ولا تستخدم الواجهة hidden guards كمصدر أمني. حالات membership الموجودة تشمل `invited`, `pending`, `active`, `suspended`, `expired`, `revoked`, `rejected`, و`deactivated` حيثما كان ذلك جزءاً من النموذج القائم. الانتقالات القانونية ما زالت محكومة في service layer، و`membership_key` يمنع duplicate membership في المسار canonical.

تتحقق خدمات membership من أن organization فعالة، وأن facility تتبع organization وفعالة، وأن department/unit ضمن التسلسل الإداري، وأن workspace يتبع organization وحالته `active` عند استخدامه كسياق membership. ويظل `Workspace.facility_id` بلا foreign key صريح في النموذج الحالي؛ لم تتم إضافة migration تلقائية لأن إثبات existing-data compatibility يحتاج PostgreSQL staging وdata audit قبل أي تغيير schema.

يستخرج `WorkspaceService.list_eligible()` workspaces من memberships الفعالة وغير المنتهية، ويستبعد organization/facility غير النشطة. لا يساوي organization ownership تلقائياً وصولاً إلى workspace. ويُستبدل `WorkspaceSessionContext` عند switch، ثم يعاد حساب permission reflection فقط للسياق الجديد. عند revoke/suspend/role removal تُبطل كل sessions وcontexts للحساب المتأثر، وهو قرار محافظ يمنع stale privilege حتى عندما يكون نطاق التغيير أضيق من كل جلسات الحساب.

## 4. Authorization وObject-level boundaries

يعتمد NIAM authorization decision على actor/session/account state، membership، scope، permission catalog، role assignments، policies، purpose، assurance/step-up، وserver-resolved resource context. عند فشل أي من هذه الشروط تكون النتيجة deny. لا تُعتبر Assurance Level permission بحد ذاتها، ولا تُستخدم Organization Type أو Sector كبديل عن assignment صريح.

في legacy `/authz` تم إغلاق مدخل client scope authoritative. هذا لا يحذف legacy surface، لكنه يمنع استخدامه للحصول على قرار قائم على `organization_id` أو `facility_id` أو `workspace_id` أرسله العميل وحده. أما object-level authorization للموارد السريرية فيبقى مرتبطاً بعقود resource-specific القائمة؛ أي endpoint جديد يجب أن يمرر resource context بعد server resolution، وإلا فقرار `resource_unresolved` هو النتيجة الآمنة.

| اختبار boundary | النتيجة |
|---|---|
| Organization A → Organization B | **DENY** |
| Workspace A → Workspace B في trusted scope | **DENY** |
| Facility mismatch في membership context | **DENY** |
| Client-provided resource scope في legacy `/authz` | **DENY** |
| Role assignment بدون management authority | **DENY** |
| Self-escalation أو role غير قابل للتفويض | **DENY** |
| Expired/suspended membership أو organization/facility غير نشطة | **DENY** |
| Reuse لصلاحيات workspace السابق بعد switch/revocation | **DENY / cache cleared** |

## 5. Delegation وInvitation

تتطلب legacy delegation الآن delegator فعالاً، delegate فعالاً، role فعالاً وقابلاً للتفويض، organization scope صريحاً، management authority مثبتة من RoleAssignment/RolePermission، source role داخل نفس organization، tenant/facility boundary، مدة مستقبلية ضمن maximum duration، وسبباً محفوظاً. لا تتجاوز delegation مصدر privilege ولا تعبر tenant أو organization. revoke لا يسمح به إلا delegator أو manager مثبت لنفس scope، وتُسجل محاولات الرفض والنجاح في `AuthorizationAudit`.

أما invitation canonical فتظل token-hashed وsingle-use وexpiring وscoped، وأضيف row lock عبر `with_for_update()` عند acceptance، مع تصحيح audit invalid token وrecipient mismatch إلى `invitation_rejected`. لا يُعاد token hash أو raw token في serialization العادي، ولا يُسجل token في logs.

## 6. Audit وحماية البيانات

تحتوي أحداث identity الآن على حقول actor وorganization وfacility وworkspace وaction وdecision وreason وrequest ID وcorrelation ID وtimestamp عندما يكون السياق متاحاً. request/correlation IDs يستمدان من middleware server-side؛ إذا لم يوجد correlation header يُستخدم request ID كـcorrelation key بدلاً من اختراع معرف غير مرتبط بالطلب.

أُدرجت حقول السياق الجديدة في audit chain hash للسجلات الجديدة التي تحتويها، مع إبقاء hash compatibility للسجلات القديمة التي لا تحتوي هذه الحقول. لا تُضاف passwords أو tokens أو OTPs أو session secrets أو patient payloads إلى metadata. اختبار Command 06 يتحقق من chain integrity بعد تسجيل context كامل.

## 7. Performance evidence

لا يوجد authorization cache دائم في المسار الجديد يحتاج TTL أو invalidation؛ frontend permission reflection محدود بالسياق الحالي ويمسح عند عدم وجود workspace. `revoke_account_access()` ينفذ bulk update للجلسات، وbulk update للسياق، وaudit flush، ولذلك يثبت الاختبار ثلاث round-trips ثابتة بدلاً من N+1 لكل session/context. Workspace discovery يستخدم queries مجمعة للم memberships/workspaces ولا ينفذ permission query لكل workspace.

| القياس/الحاجز | النتيجة |
|---|---|
| Revocation DB calls في اختبار helper | **3 ثابتة**: sessions، contexts، audit lookup/flush path |
| Permission reflection بعد switch | **سياق workspace الحالي فقط** |
| N+1 في session invalidation | **غير موجود في helper؛ bulk updates** |
| Authorization cache stale privilege | **لا يوجد server cache؛ frontend map يُمسح ويُعاد بناؤه** |
| Load/latency benchmark على PostgreSQL production-like | **UNVERIFIED**؛ لا توجد PostgreSQL/staging متاحة محلياً |

## 8. Frontend/UX parity

| المنصة | التصنيف | الدليل | المخاطر المتبقية |
|---|---|---|---|
| Web/PWA | **PASS للـcontracts المعدلة / PARTIAL للـnative-like parity** | AuthContext، WorkspaceSelector، MembershipsPage، typed API، Vitest، typecheck، build، Playwright. | لا توجد صفحة مستقلة لكل `/organizations`, `/invitations`, `/access`, ولا يعرض membership contract role/entitlement مستقلاً؛ لا يجوز اختراعها من client. |
| Android | **UNVERIFIED** | Command 05 recovery contracts موجودة؛ لا يوجد native Command 06 compile evidence. | Android SDK/CI غير متاح محلياً. |
| iOS | **UNVERIFIED** | Command 05 recovery contracts موجودة؛ لا يوجد native Command 06 compile evidence. | Xcode/CI غير متاح محلياً. |
| Flutter/Desktop | **UNVERIFIED** | Command 05 recovery contracts موجودة؛ لا يوجد native Command 06 compile evidence. | Flutter/Dart toolchain غير متاح محلياً. |

تعرض الواجهة الحالية current organization وfacility وworkspace وaccess status في `WorkspaceSelector` عندما يكون context معتمداً، وتعرض `MembershipsPage` جميع lifecycle states المعروفة. لا تعرض Role/Entitlement كأنه membership؛ عندما لا يوفر backend role assignment في contract يُعرض ذلك كـ`غير معروض` بدلاً من تحويل scope إلى permission.

## 9. الاختبارات وبوابات الجودة

| البوابة | النتيجة |
|---|---:|
| Backend full suite | **2719 passed، 4 skipped، 0 failed** من 2723 |
| Command 06 backend regressions | **5/5 passed** |
| Identity role/workspace/audit regression group | **ناجحة**؛ المجموعة الأخيرة 29/29 |
| Frontend TypeScript | **0 errors** |
| Frontend ESLint للملفات المتأثرة | **0 errors/warnings** |
| Frontend Vitest unit (استبعاد Playwright files) | **62/62 passed، 17 test files** |
| Frontend production build/PWA | **PASS**؛ `built in` وSW generated |
| Playwright `e2e/auth.spec.ts` | **8/8 passed** |
| Ruff الكامل على ملفات Command 06 | **All checks passed** |
| Bandit على ملفات security/authorization | **PASS** |
| mypy المحدود | **PARTIAL/UNVERIFIED** بسبب legacy FastAPI decorator/BaseModel typing وgeneric legacy annotations؛ لم تستخدم broad suppressions |
| `git diff --check` | **PASS** |
| Alembic heads | **single head: `20260816_0023`** |
| Alembic offline upgrade | **PASS** من `20260815_0022` إلى `20260816_0023` |
| Alembic offline downgrade | **PASS** من `20260816_0023` إلى `20260815_0022` |

تحذيرات pytest الموجودة ليست failures: تشمل warning من Starlette/httpx، deprecation في datetime، وSAWarning قديم متعلق بدورة foreign keys في نماذج غير مرتبطة مباشرة بتعديلات Command 06.

## 10. Production safety gates

لم تُجرَ أي كتابة إلى production. الحالة الموروثة من Commands 01–05 تشير إلى أن feature flags الأمنية ما زالت fail-closed، وأن public self-registration معطل، وAPI docs معطل، وrecovery email غير مفعل حتى يتوفر provider حقيقي. Vercel ما زال محمياً بـSSO، وآخر deployment مصنف blocked بسبب حماية خارجية، ولم يتم تجاوز SSO أو تغيير runtime production.

| بوابة الإنتاج | التصنيف | الملاحظة |
|---|---|---|
| Runtime production configuration | **UNVERIFIED/READ-ONLY** | لا توجد كتابة أو تعديل؛ التحقق المحلي ليس بديلاً عن production inspection. |
| Production PostgreSQL state | **UNVERIFIED** | لا توجد staging/PostgreSQL متاحة؛ rehearsal كان offline SQL فقط. |
| Vercel deployment | **BLOCKED_EXTERNAL** | SSO Protection يمنع الوصول/التحقق الكامل؛ لم يتم التحايل عليه. |
| Feature flags/public registration | **SAFE** وفق الحالة الموروثة | لا تفعيل لتسجيل عام أو provider وهمي. |
| Migration safety | **PASS offline / production UNVERIFIED** | لا migration جديدة في Command 06؛ chain الحالية single-head وupgrade/downgrade offline ناجحان. |

## 11. Remaining risks وقرار SAFE_STOP

يبقى Entitlement ككيان NIAM مستقل **MISSING**؛ تم الإبقاء على role/permission server-authoritative دون fake provider أو model غير مطلوب. كما تبقى legacy authorization surfaces بحاجة إلى migration لاحقة، رغم أن mutation وclient-scope boundaries أصبحت fail-closed. لا يوجد endpoint lifecycle واضح لإزالة workspace أو تعليق organization/facility بشكل كامل؛ لذلك لا يمكن الادعاء بأن كل mutation المستقبلية ترث revocation propagation تلقائياً.

تظل native parity وPostgreSQL staging وruntime production unverified. إذا أظهر أي تحقق لاحق cross-tenant leakage أو IDOR/BOLA أو privilege escalation أو stale privilege بعد revocation أو audit failure أو unsafe migration، يجب تفعيل **SAFE_STOP** وعدم بدء Command 07 قبل العزل والإصلاح.

## 12. المراجع الداخلية

[1]: `command06-baseline-inventory.md` — baseline inventory الفعلي قبل الإصلاح.
[2]: `command06-gap-analysis.md` — تحليل الفجوات وترتيب المعالجة الآمنة.
[3]: `../backend/app/identity/services/access_revocation.py` — revocation propagation المركزي.
[4]: `../backend/app/identity/services/audit_service.py` — audit context وchain hashing.
[5]: `../backend/app/identity/api/roles.py` — trusted workspace scope في effective permissions.
[6]: `../backend/app/routes/authorization.py` — legacy client-scope وadmin mutation boundaries.
[7]: `../frontend-v3/src/contexts/AuthContext.tsx` — explicit workspace selection وpermission invalidation.
[8]: `../backend/tests/identity/test_authorization_context_command06.py` — اختبارات Command 06 الجديدة.
