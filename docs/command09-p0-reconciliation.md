# GULA Command 09 — P0 Reconciliation

**Baseline:** `478bad1f927543323236c98da5cbb6e0a123dc40` على `chore/security-ddos-hardening-clean`
**قاعدة القرار:** `PASS` لا يُمنح إلا لدليل قابل لإعادة الإنتاج على نفس commit وفي الطبقة المطلوبة. `PARTIAL` و`UNVERIFIED` لا يُرفعان إلى PASS بالاستنتاج أو بنجاح اختبارات طبقة أخرى.

## 1. ملخص القرار

الحالة الموحدة لـP0 هي **`PARTIAL / NOT CANDIDATE FOR CLOSURE`**. لا يوجد في الأدلة المحلية المنفذة حتى الآن فشل Critical يثبت authentication bypass أو cross-tenant access أو token replay ناجحاً أو privilege escalation. لكن الإغلاق الكامل محجوب بسبب فجوة legacy/NIAM المعمارية، وعدم وجود رحلة account request→verification→approval→activation كاملة على Staging، وعدم إثبات PostgreSQL/Redis، وفشل current-head CI قبل تنفيذ أي خطوة، وعدم إثبات native/device parity، وحظر Vercel الخارجي، وعدم توفر provider رسمي لـverification/recovery.

| مجال P0 | التصنيف الحالي | ما يثبت محلياً | ما يمنع `PASS` الكامل |
|---|---|---|---|
| Account | **PARTIAL** | Account Request human-only، idempotency، encryption/redaction، state transitions، لا session أو activation من intake | لا توجد رحلة governed كاملة تربط intake بالـapproval/activation، وlegacy/NIAM source-of-truth split |
| Verification | **PARTIAL** | OTP/Contact Verification: digest، TTL، atomic resend/consume، attempt bound، enumeration resistance، provider failure fail-closed | Government/Professional/Organization providers غير متصلة؛ لا live provider أو Staging E2E؛ Contact legacy منفصل عن NIAM VerificationRecord |
| Authentication | **PARTIAL** | lockout، phone/email normalization، account namespace claim، cookie-only Web، native contract، CSRF/rate-limit guards، local security suites | legacy `/login` مقابل canonical `/niam/auth/*` لم يُحسم؛ PostgreSQL/Redis multi-worker وCI/native current-head غير مثبتة |
| Session | **PARTIAL** | account-bound sessions، idle/absolute expiry، refresh rotation، family revocation، account-scoped logout، perm_version propagation محلياً | PostgreSQL row locks/transaction isolation وRedis atomicity تحت عدة workers غير مثبتة؛ native runtime غير مثبت |
| Recovery | **PARTIAL** | canonical recovery aggregate، 10/10 security tests، single-use digest، cross-account isolation، enumeration-resistant response، revocation on completion | email provider مغلق (`false`)؛ high-risk operations `PENDING_REVIEW`؛ PostgreSQL concurrency وdelivery/observability غير مثبتة |
| Membership | **PARTIAL** | active/suspended/revoked checks، management authority، duplicate invitation/replay controls، revocation propagation محلياً | full lifecycle integration على Staging وcurrent-head CI غير مثبتان؛ بعض compatibility/legacy paths باقية |
| Workspace | **PARTIAL** | server-derived context، active org/facility filtering، explicit switch، stale permission clearing، mismatch denial | native UX/runtime غير مبني؛ production session/context persistence وPostgreSQL غير مقروءة |
| Authorization | **PARTIAL** | default-deny، trusted server scope، client-controlled scope rejection، cross-org/facility/workspace deny، role/management gates | legacy authorization surfaces لا تزال compatibility paths؛ NIAM Entitlement aggregate غير موجود؛ production object-level coverage غير مثبتة |
| Audit | **PARTIAL** | context fields، chain hashing compatibility، allow/deny events، redaction وغياب secrets في الأدلة المحلية | PostgreSQL sink/retention/stream وlive observability غير مثبتة؛ existing-data chain compatibility غير مجرّبة على DB حقيقية |
| Frontend | **PARTIAL** | Web/PWA TypeScript/ESLint/Vitest/Playwright/build محلية؛ error mapping وURL sanitization و7 locales وserver-authoritative UX | Vercel deployment محجوب؛ controlled backend error matrix وscreen-reader/device visual evidence غير مكتملة؛ native surfaces خارج Web/PWA |
| Cross-platform | **PARTIAL** | Web/PWA evidence قابلة لإعادة الإنتاج؛ native API/source contracts موجودة جزئياً | Android/iOS/Flutter/Desktop current-head builds/device E2E غير متحققة؛ CI الخارجي blocked؛ `NOT_BUILT` ليس PASS |

## 2. Domain reconciliation بالتفصيل

### 2.1 Account

الحد الأمني الخاص بطلب الحساب مضبوط: الطلب بشري فقط، لا يخلق جلسة ولا يفعّل صلاحيات، ويستخدم idempotency وblind-index/encrypted contact handling وaudit redaction. كذلك توجد transitions منضبطة للحسابات وتمنع بعض المسارات المباشرة عبر fail-closed responses. مع ذلك، لا توجد في الدليل الحالي رحلة واحدة على Staging تثبت المراجعة والموافقة والإنشاء والتفعيل ثم login/workspace/authorization. كما أن وجود مسارين legacy وNIAM يجعل توحيد source of truth قراراً معمارياً يتطلب موافقة بشرية، وليس patchاً آمناً تخمينياً.

**الحكم:** `PARTIAL`.
**الإجراء الآمن:** إبقاء public registration مغلقاً، وإبقاء approval/activation governed وserver-side، وتصميم compatibility/cutover على Staging قبل أي إعادة توجيه للمسارات.

### 2.2 Verification

Contact Verification وOTP موثقان محلياً: digest فقط، TTL، محاولات محدودة، atomic resend/consume، رسائل غير كاشفة، وفشل provider لا يتحول إلى نجاح. وفي المقابل، Government/Professional/Organization/Trust paths إما fail-closed أو provider-dependent؛ National ID لا يقبل STUB/SHADOW كإثبات. لذلك لا يمكن اعتبار الهوية الرسمية أو المهنية أو المؤسسية مكتملة، ولا يجوز تفعيل OCR/NFC/biometrics أو national identity.

**الحكم:** `PARTIAL`.
**الإجراء الآمن:** إبقاء المزودات غير المتصلة fail-closed، وعدم رفع assurance أو إنشاء VerificationRecord موثوق من نتيجة client/provider غير مثبتة.

### 2.3 Authentication

الاختبارات المحلية تثبت hardening مهماً: منع فتح manual lock بالمحاولة، تطبيع phone/email، account-kind claim، web cookie-only، native token boundary، CSRF وglobal rate-limit registration، ومراقبة replay. لكن التقارير السابقة وثقت بقاء route split بين legacy callers وNIAM canonical routes، إضافة إلى عدم إثبات جميع async identity paths على DB boundary موحدة. هذا يجعل الجاهزية التشغيلية أوسع من نطاق اختبارات unit المحلية.

**الحكم:** `PARTIAL`.
**الإجراء الآمن:** عدم تنفيذ cutover أو إعادة توجيه frontend/native إلى `/niam/auth/*` دون API compatibility contract وStaging migration وقرار Security Architecture.

### 2.4 Session

Session lifecycle المحلي يتضمن expiry وtouch وrotation وaccount-scoped logout وfamily revocation بعد refresh replay، مع انتشار `perm_version` في مسارات الاستعادة/التغيير/الإبطال. حدود الإثبات المتبقية هي PostgreSQL row-lock/transaction isolation، Redis shared atomicity، وmulti-worker behavior، إضافة إلى native runtime. لا توجد أدلة على replay ناجح في الاختبارات الحالية، لكن غياب الاختبار الخارجي يمنع closure الكامل.

**الحكم:** `PARTIAL`.
**الإجراء الآمن:** تشغيل concurrency rehearsal على PostgreSQL/Redis staging ببيانات synthetic قبل release؛ عدم إضافة cache يسمح بـstale authorization.

### 2.5 Recovery

`AccountRecoveryRequest` canonical ويخزن digest لا token، ويضع حدود TTL والمحاولات، ويمنع replay ويؤكد account/request binding ويُبطل الجلسات عند completion. المجموعة الأمنية المركزة 10/10، وتبقى الرسائل مقاومة للتعداد. لكن `ACCOUNT_RECOVERY_EMAIL_ENABLED=false`، وعمليات contact change/lost device/MFA reset/passkey recovery/unlock تتوقف عند `PENDING_REVIEW`. لا يوجد دليل delivery حقيقي أو concurrency PostgreSQL أو provider outage drill.

**الحكم:** `PARTIAL` و`BLOCKED/FAIL-CLOSED` لطبقة email/provider.
**الإجراء الآمن:** عدم تفعيل provider أو تحويل delivery failure إلى success، وإبقاء high-risk recovery manual review فقط.

### 2.6 Membership

Membership وrole management وinvitation boundaries تستخدم authority وscope وactive organization/facility checks، وتمت إضافة revocation propagation للجلسات وworkspace contexts. الاختبارات المحلية تثبت deny عند mismatch وexpired/revoked membership وself-escalation. إلا أن Staging lifecycle integration وCI current-head غير مثبتين، وبعض legacy compatibility paths لم تُزل.

**الحكم:** `PARTIAL`.
**الإجراء الآمن:** إبقاء كل mutation على management authority server-side، وعدم حذف legacy routes أو اختراع entitlement layer دون design/approval.

### 2.7 Workspace

Workspace context مشتق من الخادم، ولا يعتمد اختيار المستخدم وحده كمصدر صلاحية؛ التبديل صريح، والسياق القديم والصلاحيات القديمة يمسحان قبل قبول response الجديد، وتُرفض mismatches في organization/facility/workspace. هذا يعطي evidence محلياً قوياً، لكنه لا يثبت native UI/device behavior أو live session context بعد deployment.

**الحكم:** `PARTIAL`.
**الإجراء الآمن:** عدم إضافة auto-select أو frontend permission cache؛ إجراء native/staging tests قبل ادعاء parity.

### 2.8 Authorization

الخدمة الحديثة default-deny وتقرأ actor/session/membership/scope/policy/purpose/step-up من مصادر خادمية. Legacy `/authz` يرفض client-provided authoritative scope، وتوجد اختبارات cross-org/cross-workspace وrole-management denial. مع ذلك، legacy surfaces ما زالت موجودة بوصفها compatibility paths، وEntitlement aggregate المستقل غير موجود، لذلك لا يجوز إعلان authorization architecture موحدة كاملة.

**الحكم:** `PARTIAL`.
**الإجراء الآمن:** إبقاء legacy mutators fail-closed عند غياب authority، وعدم حذفها أو إعادة بناء NIAM/Entitlement دون migration/compatibility approval.

### 2.9 Audit

تمت إضافة context fields الخاصة بـorganization/facility/workspace/decision/reason/request/correlation إلى audit service مع الحفاظ على hash compatibility للسجلات القديمة، وتُختبر chain integrity وsecret redaction. غير أن sink الفعلي وretention وPostgreSQL chain continuity وSIEM mapping في بيئة حية غير مقروءة.

**الحكم:** `PARTIAL`.
**الإجراء الآمن:** عدم تسجيل secrets أو patient payloads، وإجراء staging audit persistence/retention verification قبل closure.

### 2.10 Frontend

Web/PWA local evidence يشمل 0 TypeScript errors و0 ESLint warnings وVitest 68/68 وPlaywright 55/55 وPWA build ناجحاً، إضافة إلى client write barrier وerror matrix وrecovery deep-link sanitization وserver-derived workspace UX. هذه النتائج لا تثبت Vercel deployment أو backend runtime الحقيقي أو screen-reader/device visual parity. كما أن current PWA workflow deployment steps skipped/blocked خارجياً.

**الحكم:** `PARTIAL` على مستوى P0 الكلي، مع `PASS` محلي لنطاق Web/PWA المحدد.
**الإجراء الآمن:** إبقاء frontend guards UX-only، وعدم التعامل مع local mocks أو Vercel project metadata كدليل server readiness.

### 2.11 Cross-platform

الـWeb وPWA يستخدمان bundle واحداً ولهما evidence محلية. أما Android وiOS وFlutter/Desktop فمصادر العقود موجودة في أجزاء محددة، لكن current-head build/device evidence غير متاحة، وGitHub jobs تفشل قبل steps، كما لا توجد Android SDK/Xcode/Flutter محلياً.

**الحكم:** `PARTIAL`.
**الإجراء الآمن:** تصنيف native capabilities `UNVERIFIED` أو `NOT_BUILT` حتى تمر compilers وdevice/desktop E2E على current HEAD؛ لا تُستخدم historical CI commits كإغلاق current HEAD.

## 3. Blocker ledger

| Blocker | Root cause | Impact | Dependency | Safe fix/next action | Regression risk |
|---|---|---|---|---|---|
| CI execution | GitHub jobs لها `runner_id=0` وzero steps | لا يمكن فصل source result عن infrastructure أو الحصول على artifacts | GitHub Actions runner/policy/billing/repository access | Human infra owner يصلح runner ثم يعيد checks على نفس SHA؛ لا suppressions | إعادة تشغيل على بيئة مختلفة قد يكشف code failures؛ يجب مراجعة artifacts كاملة |
| PostgreSQL/Redis staging | لا runtime أو connector أو credentials مقروءة | لا proof للlocks/isolation/multi-worker/rollback/live audit | Security/release owner وsynthetic staging | توفير staging مع read-only inspection ثم rehearsal؛ لا production DDL | Data/transaction behavior قد يختلف عن SQLite |
| Legacy↔NIAM split | مساران identity/session/contracts متوازيان | احتمال operational drift إن جرى cutover تخمينياً | Security Architecture + API compatibility approval | تصميم bridge/cutover/rollback ثم تنفيذ محدود واختباره | breaking login/cookie/mobile/workspace behavior |
| Account approval E2E | لا canonical governed review/activation journey كاملة | P0 lifecycle يبقى PARTIAL | Product/Security/Legal/Operations | تصميم workflow وصلاحياته ثم staging E2E | privilege activation or audit gaps |
| Provider dependency | email وofficial identity providers مغلقة/غير متصلة | recovery/verification الرسميان غير قابلين للإثبات | Provider, Legal, Security, Operations | إبقاء fail-closed وmanual review؛ لا fake success | false verification أو account enumeration |
| Native parity | SDK/toolchains غير متاحة وCI blocked | لا binaries/device/runtime proof | Mobile/Desktop owners وGitHub infra | تشغيل current-head CI/device tests بعد إصلاح runner | platform-specific auth/session regressions |
| Vercel protection | SSO يحجب deployments وlatest deployment BLOCKED | لا live frontend/headers/runtime verification | Vercel project owner | human read-only/project review ثم recheck؛ لا تعطيل protection | exposure of protected deployment if weakened |
| Quality debt | legacy full Ruff/MyPy/Bandit/pip-audit/gitleaks debt | repository-wide quality not green | Maintainers/security tooling | changed-files/critical-scope gate؛ separate debt wave | broad refactor scope and unrelated behavior changes |

## 4. SAFE_STOP decision

لا يثبت evidence المحلي الحالي Critical security failure، لذلك لا يتم تفعيل SAFE_STOP بسبب bypass مكتشف. لكن **Release Stop** وP0 closure stop قائمان بسبب نقص الأدلة الخارجية والحواجز أعلاه. إذا كشف أي subsequent staging/CI test authentication bypass أو session compromise أو token replay ناجح أو cross-tenant access أو privilege escalation أو audit tampering أو unsafe migration، يتوقف التنفيذ فوراً ولا تُدمج أي remediation مرتبطة بالمسار قبل العزل والتحليل والإصلاح.

## References

[1]: `command01-authoritative-audit-report.md` — account namespace، legacy/NIAM split، baseline and security fixes.
[2]: `command02-account-lifecycle-report.md` — account request/idempotency/approval gap.
[3]: `command03-verification-hardening-report.md` — OTP/provider trust boundaries and fail-closed behavior.
[4]: `command04-authentication-hardening-report.md` — auth/session/CSRF/rate-limit/replay evidence.
[5]: `command05-account-recovery-hardening-report.md` — recovery state machine and provider boundary.
[6]: `command06-authorization-context-hardening-report.md` — membership/workspace/authorization/audit evidence.
[7]: `command07-08-identity-lifecycle-closure-report.md` — Web/PWA/native/production limits.
[8]: `command08-final-qa-report.md` — consolidated P0/P4/P5 gate and current evidence.
[9]: `command09-baseline.md` — current authoritative Git/CI/Vercel/Railway/PostgreSQL/flags baseline.
