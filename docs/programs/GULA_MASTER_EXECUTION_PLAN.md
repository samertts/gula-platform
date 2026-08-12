# GULA — Master Execution Plan

## طريقة التنفيذ

كل Wave تمر بالتسلسل: Inspect، تحديد النطاق، dependency analysis، أصغر وحدة آمنة، tests، security checks، architecture checks، integration checks، documentation، evidence، commit مقصود، Git verification، ثم wave report. لا تُجمع إصلاحات غير مرتبطة في Wave واحدة، ولا تُعلن capability مكتملة دون دليل.

## Waves

| Wave | النطاق | المخرجات | بوابة الخروج |
|---:|---|---|---|
| 0 | Repository recovery | current state، branches/tags/worktrees، work protection | لا تعديل تدميري، state document |
| 1 | Current-state and gap analysis | seven first-deliverable docs، gap matrix، risk register، dependency graph | STOP ومراجعة Program Director |
| 2 | Architecture reconciliation | ADRs، ownership map، duplicate/legacy decisions، contract map | architecture/security review |
| 3 | Identity/account/org/auth stabilization | unified account، MFA، sessions، RBAC/ABAC، tenant/object auth | security + negative tests + migration proof |
| 4 | Unified application shell/workspaces | shell، workspace/context، inbox/tasks، consent/privacy، design system | UX/accessibility/security/E2E |
| 5 | Citizen + Clinical foundation | patient summary/timeline، consent، clinical safety workflows | clinical safety review |
| 6 | Laboratory + Radiology + Pharmacy | analyzer/integration، imaging contracts، pharmacy workflows | domain owner and integration tests |
| 7 | Hospital + EMS + Blood | admissions/beds/emergency/transfusion | clinical safety and outage tests |
| 8 | Public Health + Workforce | surveillance، workforce/employee boundaries | privacy/legal/security review |
| 9 | Patient Flow + Appointment + Referral + Resource | reusable national engines | capacity/queue/reconciliation tests |
| 10 | Integration Hub + Terminology | FHIR/HL7/DICOM/LIS/RIS/PACS mapping | interoperability contract certification |
| 11 | Offline/resilience/DR | encrypted offline queues، reconciliation، backup/restore | recovery drill with RTO/RPO |
| 12 | National Control Plane + Analytics | ministry dashboards، national capacity/analytics | governance and data-quality review |
| 13 | AI governance | versioning/provenance/evals/human oversight/kill switch | AI safety certification |
| 14 | Entitlements/commercial | free base tier، centralized entitlements، paid extensions | product/security/data review |
| 15 | Scale/security certification | production-like load، HA، SLOs، supply chain | release gate |
| 16 | Pilot deployment | controlled facility pilot and monitoring | pilot approval |
| 17 | Production expansion | staged national expansion with rollback | operational approval |

## Immediate safe scope after Wave 1

يمكن تنفيذ إصلاحات صغيرة غير تدميرية مثل security regressions، dependency patches، test contract fixes، observability، migration compatibility، and documentation. أي تعديل يغير workflow السريري أو authorization architecture أو deployment behavior يحتاج Change Control وADR واعتماداً.

## بوابات عامة

لا يجوز تجاوز أي بوابة إذا بقي P0 مفتوحاً، أو فشل اختبار غير مفسر، أو لم تثبت migrations على PostgreSQL، أو لم تُختبر الاستعادة، أو لم يتوفر load evidence على بنية مماثلة للإنتاج. الأداء لا يبرر تخطي validation أو audit أو authorization.

## Wave 4 HARD STOP

B-5 branch pruning، B-6 version synchronization إن كان تدميرياً، B-7 root JSON cleanup، B-8 frontend-v3 rename، GitHub Release، وتغيير deployment behavior تبقى `AWAITING APPROVAL`. لا تُنفذ تلقائياً ضمن هذه الخطة.
