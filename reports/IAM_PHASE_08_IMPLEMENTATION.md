# تقرير تنفيذ IAM Phase 8 — Authorization Decision Engine

**المشروع:** GULA Platform
**المستودع:** `samertts/gula-platform`
**فرع Phase 8:** `feat/iam-phase8-authorization-engine`
**خط الأساس السابق:** `feat/iam-phase6-memberships`
**التاريخ:** 2026-08-14
**المنفذ:** Manus AI

## الملخص التنفيذي

تم تنفيذ Phase 8 فوق المصدر الفعلي لـPhases 0–7، دون إنشاء نظام حسابات ثانٍ أو قاعدة بيانات مشتركة أو نقطة تفويض خارج GULA. أصبح لدى NIAM محرك قرار مركزي يستهلك actor/session الموثوق، العضوية، RBAC من Phase 7، policy registry الموجود، العلاقات الصريحة، التحقق المهني، وحالة المورد، ثم يصدر قرارًا حتميًا `allow` أو `deny`.

> **القاعدة الأساسية:** عدم حل السياق أو فشل policy evaluation لا يتحول إلى سماح. القرار يكون `DENY`، والواجهة الأمامية والموبايل لا يملكان صلاحية اعتماد القرار.

## ما تم تنفيذه

| المجال | التنفيذ |
|---|---|
| نموذج الطلب | إضافة `AuthorizationRequest` داخلي يحتوي actor/resource/action والنطاق التنظيمي والعضوية والعلاقة والغرض والحساسية وحالة المورد والبيئة وbreak-glass. معرف الحساب لا يُستمد من body في المسارات المحمية. |
| نموذج القرار | إضافة `AuthorizationDecision` مع `ALLOW/DENY` وreason code ثابت وpolicy id/version وrequired assurance وaudit reference، مع public response محدود لا يكشف شروط السياسة الداخلية. |
| ترتيب القرار | Authentication → account → session → break-glass → purpose → resource state → management authority/membership → scope → resource resolution → relationship → professional verification → step-up → RBAC permission → explicit policy conflict → audit/final decision. |
| RBAC | استهلاك `RolePermissionService.effective_permissions` وcatalog status وassignment scope من Phase 7، مع رفض permission غير المعروف أو المفقود. |
| العضويات | اختيار العضوية النشطة المطابقة للنطاق، واختيار النطاق الأشد تحديدًا، ورفض الغموض المتساوي بدل اختيار سجل عشوائي. |
| boundaries | رفض cross-tenant، workspace crossing، facility/department/unit mismatch، وعدم قبول claims أو role names كحقائق. |
| organization authority | عمليات role assignment/revoke وmembership approve/invite/revoke/suspend/reactivate تتطلب ownership أو active representative authority من المصدر الموجود في `MembershipService`. |
| relationships | استخدام `CitizenRelationship` فقط للعلاقات الصريحة النشطة وغير المنتهية وغير الملغاة، مع exact purpose وresource scope؛ لا يوجد استنتاج من الهاتف أو الرقم الوطني أو القرابة غير الموثقة. |
| verification | اشتراط `VerificationRecord` مهني نشط ومتحقق وغير منتهٍ عند طلب `professional_verification_required`. |
| policy conflicts | قراءة `IdentityPolicy` الفعالة، والـexplicit `deny` يتغلب على `allow`، مع احترام priority/version/time window. |
| step-up | العمليات الحساسة وhigh/critical clinical/export/security paths تتطلب MFA عندما يحدد السياق ذلك؛ لم تُخترع مستويات AAL غير موجودة في architecture الحالية. |
| break-glass | لا يوجد `admin=true` bypass. الطلب يحتاج authorization صريحًا، reason، expiry، وMFA، وإلا يُرفض. لا توجد delegated impersonation غير مقيدة. |
| audit | إضافة أحداث `AUTHZ_ALLOW_SENSITIVE`, `AUTHZ_DENY`, `AUTHZ_POLICY_FAILURE`, `AUTHZ_CROSS_TENANT_ATTEMPT`, `AUTHZ_PRIVILEGE_ESCALATION_ATTEMPT`, `AUTHZ_ROLE_MANIPULATION_ATTEMPT`, `AUTHZ_RESOURCE_ENUMERATION_ATTEMPT`, `BREAK_GLASS_USED`, `STEP_UP_REQUIRED`, و`STEP_UP_FAILED` إلى `AuditAction`. القرارات الحساسة والرفض الأمني تُسجل عبر hash-chained `AuditService` دون payload سريري زائد. |
| API integration | ربط `roles/effective`, role assign/revoke، وmembership management routes بالمحرك المركزي قبل استدعاء خدمات Phase 6/7، مع تحميل target resource من الخادم لمنع IDOR/BOLA. |
| compatibility | استبدال `app/identity/policy_engine.py` placeholder الذي كان يسمح افتراضيًا، بواجهة fail-closed فوق المحرك المركزي؛ اختبار التوافق القديم عُدّل ليؤكد الرفض عند غياب actor/session موثوقين. |
| frontend | `AuthContext` يجلب memberships وeffective permissions من الخادم لكل organization. `Sidebar` و`usePermissions` يستخدمانها لقرارات UX فقط؛ static role map يعمل في demo فقط. `RoleGuard` لا يمنع live routes بناءً على role name. |
| mobile | إضافة قراءة server-reflected effective capabilities إلى Desktop AuthManager، مع عدم تضمين master permissions أو اعتبار الحالة المحلية مصدرًا للأمان. Flutter/Dart غير متاح في sandbox، لذلك التنفيذ mobile source-only وغير منفذ محليًا. |

## الاختبارات والبوابات

| البوابة | النتيجة الفعلية |
|---|---|
| Ruff للملفات المتأثرة | **PASS — All checks passed** |
| Python compileall للملفات المتأثرة | **PASS** |
| Backend identity regression غير التكاملية | **152 passed, 2 deselected** |
| `tests/test_niam.py` | **44 passed** |
| Phase 8 tests | مشمولة ضمن identity regression، وتغطي 19 حالة تشمل fail-closed، actor mismatch، session/account، resource resolution، scope، unknown/missing permission، explicit deny precedence، purpose، MFA، break-glass، DB failure، relationship، وIDOR. |
| Alembic heads | **PASS — `20260814_0005` هو head** |
| Frontend test suite | **10 files passed, 34 tests passed** |
| Frontend typecheck | **PASS** |
| Frontend production build | **PASS — built in 493ms** |
| Flutter/Dart formatter | **غير متاح في sandbox**؛ mobile source موجود ويجب تشغيل `dart format` وFlutter analyzer في CI/بيئة Flutter. |

## حدود مقصودة وعدم ادعاءات زائفة

لم تتم إضافة صلاحيات سريرية تخمينية أو اعتماد provider/government integrations غير موجودة. لم يُسمح للمحرك بالموافقة على نتائج سريرية، ولا يزال GULA هو clinical system of record ونقطة enforcement الوحيدة. لم يتم تفعيل organization تلقائيًا، ولم تُقبل membership status/account/actor_id من client body، ولم يُسمح self-escalation.

Break-glass وdelegation وimpersonation تم تمثيل حدودها ورفض bypass غير المصرح به، لكن workflows التشغيلية الكاملة لهذه القدرات تتطلب موافقة وسياسة منفصلة، وموفر step-up فعلي، وسجل review بعد الحدث؛ لم يتم اختراعها في Phase 8.

المواصفات المرفقة تنتهي مبتورة في قسم Security Event Categories عند عبارة `Avoid logging every trivial read if this creates unacceptable v...`. تم تنفيذ الجزء المكتمل فقط، ولم تُستنتج متطلبات غير موجودة من نهاية مبتورة.

## الملفات الرئيسية

| الملف | الغرض |
|---|---|
| `backend/app/identity/services/authorization_decision.py` | المحرك المركزي ونماذج request/decision والسياسات والـaudit. |
| `backend/app/identity/policy_engine.py` | compatibility facade fail-closed. |
| `backend/app/identity/api/memberships.py` | ربط Phase 6 management routes بالمحرك. |
| `backend/app/identity/api/roles.py` | ربط Phase 7 effective/assignment routes بالمحرك. |
| `backend/app/identity/models/audit.py` | event categories الجديدة. |
| `backend/tests/identity/test_authorization_phase8.py` | اختبارات القرار والأمن والعزل وIDOR. |
| `docs/architecture/IAM_PHASE_08_AUTHORIZATION_DECISION_ENGINE.md` | وثيقة التصميم وترتيب التقييم. |
| `reports/IAM_PHASE_08_PREFLIGHT_SOURCE_FINDINGS.md` | تدقيق المصدر الفعلي قبل التنفيذ. |

## القرار النهائي

Phase 8 **مكتمل على مستوى المصدر والاختبارات المحلية المذكورة أعلاه** وجاهز للمراجعة في Pull Request. لا يوجد merge أو deployment تلقائي ضمن هذا التنفيذ، ولا ينبغي وضع completion tag قبل انتهاء CI البعيد ومراجعة بشرية صريحة.
