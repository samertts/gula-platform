# GULA Command 09 — P4 Acceptance Matrix

**المرجع:** متطلبات `pasted_content.txt`، Commands 01–08، وbaseline الحالي `478bad1f927543323236c98da5cbb6e0a123dc40`.
**القرار:** **`P4_PARTIAL / UNVERIFIED` — ليس `P4_COMPLETE`**.

> نجاح local tests لا يكفي لإغلاق P4 عندما تكون طبقة PostgreSQL/Redis أو production runtime أو native CI أو governance غير مثبتة. لا تُحوّل هذه المصفوفة `PARTIAL` أو `UNVERIFIED` إلى `PASS` بالاستنتاج.

| # | Requirement | Evidence الحالي | Current Status | Blocker | Required Action | Owner | Human Approval |
|---:|---|---|---|---|---|---|---|
| 1 | Account Request ليس Public Registration ويقبل human فقط | `AccountRequestService` وRegisterPage وdefault flag `PUBLIC_SELF_REGISTRATION_ENABLED=false`؛ لا session من intake | **PASS للحد الأمني / PARTIAL للدورة** | لا توجد رحلة request→review→approval→activation كاملة على Staging | تنفيذ governed lifecycle E2E ببيانات synthetic مع صلاحيات ومراجعة | Identity/Security | Security + Product + Legal |
| 2 | Verification state server-authoritative | OTP digest/TTL/attempt/cooldown/consume وprovider failure tests | **PASS محلياً / PARTIAL كتكامل رسمي** | official Government/Professional/Organization provider غير متصل؛ legacy Contact منفصل عن NIAM | Staging provider contract أو إبقاء fail-closed؛ لا fake verification | Identity/Security | Security + Legal + Government Integration |
| 3 | Authentication bypass resistance | lockout، account-kind claim، normalization، cookie/native boundary، auth tests | **PASS محلياً / PARTIAL للإغلاق** | legacy `/login` وNIAM `/niam/auth/*` split؛ current-head CI blocked | اعتماد compatibility/cutover plan ثم CI/Staging | Security Architecture | Security + API/Release |
| 4 | Session integrity and replay | refresh rotation، family revocation، idle timeout، account-scoped logout، local tests | **PASS محلياً / UNVERIFIED خارجياً** | PostgreSQL/Redis multi-worker and row-lock behavior | concurrent staging rehearsal على PostgreSQL/Redis | Platform/Security | Security + Production + Database |
| 5 | Recovery safe lifecycle | recovery aggregate، 45 targeted tests، recovery security 10/10 | **PASS للـpassword flow / PARTIAL ككل** | email provider off؛ high-risk flows `PENDING_REVIEW` | إبقاء fail-closed؛ اعتماد manual review/provider قبل التفعيل | Identity/Security | Security + Legal + Operations |
| 6 | Membership lifecycle and revocation | membership/role/workspace tests وrevocation helper | **PARTIAL** | current-head CI/Staging integration unavailable؛ legacy paths remain | staging lifecycle test and role/membership audit review | IAM Owner | Security + Production |
| 7 | Workspace context isolation | server-derived context، explicit switch، stale permission clearing، mismatch denial | **PASS محلياً / PARTIAL parity** | native/device and live DB/runtime evidence missing | native CI/device E2E and staging revocation check | IAM/Frontend/Mobile | Security + Release |
| 8 | Authorization default-deny and no client scope | legacy `/authz` client-scope rejection، trusted scope، cross-tenant tests | **PASS محلياً / PARTIAL architecture** | legacy surfaces and missing independent Entitlement aggregate | migration plan; do not delete or bypass legacy surface | Security Architecture | Security + Product |
| 9 | Audit integrity and redaction | context fields، chain hash compatibility، tamper/redaction tests | **PASS محلياً / PARTIAL live sink** | PostgreSQL sink/retention/SIEM not verified | staging persistence/retention/chain verification | Security/Observability | Security + Production + Legal |
| 10 | Web/PWA identity UX | TypeScript 0، ESLint 0، Vitest 68/68، Playwright 55/55، build/PWA pass | **PASS محلياً / PARTIAL release** | Vercel HEAD deployment `BLOCKED`؛ live backend unavailable | resolve Vercel external block via owner, then read-only recheck | Frontend/Release | Deployment + Security |
| 11 | Error matrix and recovery UX | tests for 401/403/409/422/429/5xx/offline and deep-link sanitization | **PASS local contract** | controlled live responses and screen-reader/device QA absent | run browser accessibility and staging error matrix | Frontend/QA | Security + Accessibility |
| 12 | Localization and RTL/LTR | seven locale contract، direction declarations، Web RTL tests | **PARTIAL** | Persian independent resources and native visual QA incomplete | complete locale/resource audit and device visual QA | Frontend/Localization | Product + Accessibility |
| 13 | Android parity | native source contracts exist; no current successful build artifact | **UNVERIFIED / NOT_BUILT** | Android SDK/current-head CI unavailable; CI runner failure | run Gradle compile/unit/device E2E on current SHA | Android Owner | Security + Release |
| 14 | iOS parity | API/Auth source contracts exist; no current successful Xcode artifact | **UNVERIFIED / NOT_BUILT** | Xcode/current-head CI unavailable; CI runner failure | run Xcode build/Simulator/device session/recovery tests | iOS Owner | Security + Release |
| 15 | Flutter/Desktop parity | source contracts and state enum exist; no current artifact | **UNVERIFIED / NOT_BUILT** | Flutter/Dart/current-head CI unavailable | run Dart analyze/test/build and desktop E2E | Desktop Owner | Security + Release |
| 16 | CI security/quality gates | 17 runs failed pre-step with `runner_id=0`, zero steps | **BLOCKED_EXTERNAL** | GitHub runner/policy/billing/access outside sandbox | human infra repair and re-run checks on exact SHA | Repository/CI Owner | Deployment + Security |
| 17 | Alembic topology and rollback | single head `20260816_0023`; offline upgrade/downgrade pass | **PASS offline / UNVERIFIED PostgreSQL** | no live/staging PostgreSQL or existing-data rehearsal | PostgreSQL staging apply/rollback/lock/index validation | Database Owner | Database + Production |
| 18 | Production alignment chain | `origin/main` differs from HEAD; Vercel HEAD deployment BLOCKED; Railway/DB absent | **BLOCKED_EXTERNAL / UNVERIFIED** | no Railway connector/runtime/DB/env read-only evidence | inspect exact chain `main→CI→Vercel/Railway→runtime→DB→flags` | Release/Platform | Production + Deployment |
| 19 | Performance and N+1 | revocation helper bulk updates; local query/performance smoke pass | **PASS local / UNVERIFIED production profile** | no PostgreSQL p50/p95/p99 or multi-worker load | staging latency/query/load measurement | Platform/DB | Performance + Production |
| 20 | Quality debt | targeted Ruff passes; backend full tests pass; repository debt documented | **PARTIAL** | full Ruff/MyPy/Bandit/pip-audit/gitleaks not clean/available | separate scoped debt wave; preserve changed-files gate | Maintainers/Security | Security + Engineering |
| 21 | Human governance | no current approval record for Security/Production/DB/Legal/Government/Deployment | **PENDING_HUMAN** | approvals cannot be inferred from CI/merge | record named approvers, scope, date, decision, expiry | Governance Owner | Required for each domain |
| 22 | P5 protection | P5 not started; no P5 migrations/adapters/activation | **P5_BLOCKED_BY_PREREQUISITE** | P4 not complete and governance absent | keep P5 blocked; no Command 10 auto-start | Program Owner | Governance Authorization |

## P4 decision rule

لا يحقق المشروع `P4_COMPLETE` لأن الصفوف 3–5 و13–21 تحتوي `PARTIAL` أو `UNVERIFIED` أو `BLOCKED_EXTERNAL` أو `PENDING_HUMAN`. ولا يثبت `P4_COMPLETE` إلا بعد إغلاق كل blockers وإرفاق artifacts قابلة للتحقق على current head، ثم تسجيل الموافقات البشرية المطلوبة.

## Exact acceptance sequence

الخطوة التالية المسموح بها هي إصلاح GitHub runner infrastructure خارج الكود، ثم تشغيل native CI وPostgreSQL/Redis staging ببيانات synthetic، ثم قراءة Railway/Vercel/runtime flags read-only، ثم مراجعة الأدلة والموافقات. لا يُنفذ production deployment أو production DB change أو public registration أو National ID/OCR/NFC/biometrics activation من هذه المهمة.

## References

[1]: `command09-baseline.md` — baseline السلطوي الحالي.
[2]: `command09-p0-reconciliation.md` — P0 domain and blocker reconciliation.
[3]: `command08-final-qa-report.md` — consolidated prior QA and release gate.
[4]: `QUALITY_CHANGED_FILES_GATE.md` — changed-files quality gate and separation from P4 closure.
[5]: `../backend/app/config.py` — source defaults and production/staging guards.
