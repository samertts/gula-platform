# خريطة أسطح GULA لتصميم Stitch

> **الغرض:** هذه الخريطة هي backlog تصميمي شامل لـ Google Stitch وللتنفيذ داخل `frontend-v3`. إنها تصف الواجهة والحالات البصرية فقط؛ لا تمنح صلاحية جديدة، ولا تغيّر مسارًا سريريًا، ولا تستبدل أي عقد API أو تدقيق أو عزل مؤسسة.

## قواعد لا تقبل التفاوض

كل prompt أو تصميم أو screenshot في Stitch يستخدم بيانات اصطناعية غير قابلة للتعرف على أشخاص. لا تُرفع ملفات مرضى أو لقطات من الإنتاج أو tokens أو مفاتيح. جميع الواجهات العربية تعمل `RTL`، وجميع الإجراءات السريرية تبقى مرتبطة بالحالة والصلاحية والعقد الموجودة في GULA.

| قاعدة | تطبيق بصري إلزامي |
|---|---|
| RBAC وTenant Isolation | يوضّح التصميم نطاق مساحة العمل والدور، ولا يعرض إجراءً غير مصرح به كأنه متاح |
| State machine | كل مرحلة عينة/طلب/نتيجة تعرض الحالة الحالية والانتقال المسموح فقط |
| Auditability | كل إجراء مؤثر يعرض سببًا أو تأكيدًا أو أثرًا تدقيقيًا عندما يطلبه السلوك القائم |
| Demo isolation | شريط ثابت وواضح يعلن أن البيانات اصطناعية والكتابة والتكاملات محظورة |
| Accessibility | تركيز واضح، keyboard flow، labels للأيقونات، نص بجانب اللون، وتباين كافٍ |
| Mobile parity | نفس حدود الصلاحيات ومنع الكتابة في الويب والجوال؛ يختلف الترتيب لا السلوك |

## 1. Design System ومكوّنات التطبيق المشتركة

| الحزمة | أسطح Stitch المطلوبة | حالات التنفيذ |
|---|---|---|
| App shell | Sidebar RTL/LTR، top bar، workspace، profile، notifications، search، theme، language | desktop، compact desktop، tablet، mobile header، mobile bottom nav |
| Navigation | active item، collapsed sidebar، group labels، permission-hidden item، legacy bridge | default، hover، focus، active، forbidden، loading |
| Cards and KPI | operational card، clinical metric، status summary، safety banner | loading، zero، unavailable، demo، critical |
| Forms | inputs، select، date/time، file placeholder، inline validation | pristine، focus، valid، invalid، disabled، saving، server error |
| Dialogs | confirmation، reason capture، privileged action، destructive action، session timeout | modal desktop، mobile sheet، loading، success، error, cancel |
| Data views | table، stacked mobile card، timeline، audit event، filter panel، pagination | loading، empty، error، filtered empty، bulk selection |
| System states | skeleton، offline/degraded، 401/403، 404، 409 conflict، 422 validation، 429 retry، 5xx | Arabic and English, light and dark |

## 2. الهوية والوصول والواجهات العامة

| Route / surface | شاشة Stitch المطلوبة | نوافذ وحالات لا بد من تصميمها |
|---|---|---|
| `/login` | Arabic-first institutional access، citizen access، trust cues | show/hide password، validation، bad credentials، locked/throttled، demo persona picker |
| `/register` | onboarding stepper وشرح الخصوصية | validation، duplicate identity، consent، success، pending verification |
| `/profile` | profile summary وsession/device awareness | edit fields، password/credential change، unsaved changes |
| `/settings` | grouped settings and preferences | save/rollback، locale/theme، notification settings، permission-limited field |
| `/security` | security posture and controls | confirmation dialog، session revoke، audit drill-down، privilege denied |
| Public and citizen | citizen home، result entry point، notices | unauthenticated، verified view، consent wall، empty results |

## 3. المختبر وسير العمل السريري

| Route / surface | شاشة Stitch المطلوبة | نوافذ وحالات لا بد من تصميمها |
|---|---|---|
| `/dashboard` | operations dashboard desktop + mobile | healthy system، demo read-only، integration unconfigured، critical alert panel |
| `/patients` | patient list with scoped search and filters | loading، no patients، filter-empty، patient card preview، permission boundary |
| `/patient-card` | patient snapshot and clinical context | sensitive data warning، restricted field، timeline، no active record |
| `/orders` | worklist and order detail | create/route action only where existing permissions permit، invalid state transition، sample pending |
| `/samples` | sample collection/receipt/verification queue | barcode placeholder، verification state، chain of custody، reject reason dialog |
| `/results` | results review/verification workspace | result draft، reviewer state، conflict/version mismatch، authorised validation only |
| `/qc` | quality control dashboard | run status، out-of-range cue، escalation panel، review only |
| `/alerts` | critical alert queue | critical/non-critical views، acknowledgement where contract permits، empty and escalation state |
| `/notifications` | notification inbox | read/unread، priority, empty, retry, preference redirect |
| `/reports` and `/stats` | analytic reports and trends | filters، generated/empty/error, export permission state |
| `/labs` | laboratory directory/status | workspace selector، empty directory، facility status |

## 4. الإدارة والحوكمة والتكاملات

| Route / surface | شاشة Stitch المطلوبة | نوافذ وحالات لا بد من تصميمها |
|---|---|---|
| `/admin/labs` | facility administration | create/edit if permitted، archive confirmation، validation |
| `/admin/users` | users and role assignment | invite, role change confirmation, deactivation, audit reason |
| `/admin/audit` | immutable audit explorer | filters, event detail drawer, no results, export permission state |
| `/identity` and `/niam/*` | trust, lifecycle, federation, certificates, workflows | credential states، review queues، expired certificate، policy conflict |
| `/compliance` and `/certification` | compliance evidence and readiness | checklist, nonconformity, attachment placeholder, read-only evidence |
| `/integration` and `/integration/connectors` | connector catalog and health | unconfigured connector, token rotation path, connection test, failure/retry, approval boundary |
| `/fhir`, `/health-data`, `/health-ecosystem` | data exchange and interoperability | endpoint health, schema validation, consent boundary, response inspector |
| `/edge`, `/kernel`, `/control-plane`, `/platform` | platform operations | node health, degraded mode, change review, control boundary |

## 5. التطبيقات التخصصية والقطاعية

| Surface family | Routes to group in Stitch | Visual intent |
|---|---|---|
| Hospital / pharmacy / biomedical / blood bank | `/hospital`, `/pharmacy`, `/biomedical`, `/blood-bank` | Workspace-specific operations, safe queues, inventory or service status without exposing unscoped data |
| Critical and emergency | `/critical-care`, `/ems`, `/command-center`, `/command-intelligence` | High-priority information hierarchy, rapid scan, explicit urgency, no accidental action |
| AI and intelligence | `/ai`, `/ai-platform`, `/ai-fabric` | Assistant boundaries, citation/uncertainty panel, no autonomous clinical assertion, safe handoff |
| Finance and tiers | `/financial`, `/tiers`, `/lifecycle-platform`, `/pilot-platform` | Account status, entitlements, billing/plan boundaries, admin confirmation states |
| National and public health | `/national-data`, `/public-health`, `/national/*`, `/command-center` | Jurisdiction-aware dashboards, broad data density, clear scope labels and export restrictions |
| Capabilities | `/capabilities/*` | Consistent catalog/detail pages with service state, contracts, access summary, and empty/error modes |

## 6. الجسور والواجهات غير المفعلة بالكامل

| Entry point | Design treatment | Behavior boundary |
|---|---|---|
| `/legacy`, `/web-suite` | calm migration/bridge page with a clear supported destination | Do not imitate full legacy features before contracts are approved |
| `/doctor`, `/nurse`, `/radiology` | specialty gateway with scoped status and safe next steps | No hidden data, DICOM, orders, or writes when the current contract is incomplete |
| Unconfigured integrations | empty-state plus requirements checklist | Never show a false-connected state or accept secrets in client-side UI |

## 7. Stitch project and prompt batches

| Stitch project | Batch | Target surfaces | Definition of done |
|---|---|---|---|
| **GULA Clinical Clarity System** | A | Shell, cards, fields, dialogs, data states, mobile navigation | DESIGN.md tokens and reusable component references approved |
| **GULA Lab Operations** | B | Dashboard, patients, orders, samples, results, QC, alerts | Desktop and mobile references for workflow, empty/error/demo states |
| **GULA Trust & Administration** | C | Login, profile, settings, security, users, audit, compliance, identity | Privileged and confirmation flows visually explicit |
| **GULA Data & Ecosystem** | D | Reports, FHIR, health data, integrations, platform/edge | Dense data layouts, connector state, degraded/retry behavior |
| **GULA National & Specialty** | E | Hospital, pharmacy, critical care, AI, national/public-health, specialty bridges | Jurisdiction and specialty scopes visually distinct but consistent |
| **GULA Responsive States** | F | All modal, drawer, sheet, empty, error, offline, conflict, loading states | Same rules validated at desktop, tablet, and mobile widths |

## 8. Implementation waves

| Wave | Code scope | Quality gate |
|---|---|---|
| 1 | Shared tokens, App Shell, Workspace selector, mobile navigation, cards, dialogs, empty/error states | Typecheck, unit tests, keyboard and responsive smoke tests |
| 2 | Dashboard, patients, orders, samples, results, alerts, reports | Existing API contracts, demo write barrier, route permissions |
| 3 | Admin, audit, settings, security, compliance, integrations, FHIR | Role guard tests, confirmation states, no client-side secret entry |
| 4 | Citizen, hospital, pharmacy, intelligence, national and capability modules | Responsive visual checks and scope labels |
| 5 | Legacy/specialty bridges and documentation | No accidental feature activation; clear supported destinations |

## Acceptance checklist for every surface

1. The screen is designed in RTL and responsive variants before implementation.
2. Every state can be understood without relying on color alone.
3. Demo and read-only modes are explicit and do not expose an interactive-looking clinical write path.
4. Existing `RoleGuard`, navigation permissions, workspace scope, API client read/write barriers, and audit expectations remain unchanged.
5. Loading, empty, validation, conflict, permission, network, and degraded states are specified before the page is considered complete.
6. The production bundle, relevant tests, and an in-browser smoke test pass before the change is pushed.
