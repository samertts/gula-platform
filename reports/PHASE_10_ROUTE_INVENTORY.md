# Phase 10 — جرد المسارات

المسارات أدناه مستخرجة من route registries الفعلية في frontend-v3 وfrontend-v2، مع تمييز الجسر والـlegacy.

| path | method | page | auth | role | permission | workspace | backend | status | source |
|---|---|---|---|---|---|---|---|---|---|
| /login | GET | LazyPage | NO | authenticated | public | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:112 |
| /register | GET | LazyPage | NO | authenticated | public | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:113 |
| /privacy-policy | GET | LazyPage | YES | authenticated | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:114 |
| /terms-of-service | GET | LazyPage | YES | authenticated | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:115 |
| /dashboard | GET | LazyPage | YES | authenticated | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:127 |
| /patients | GET | RoleGuard roles={staffRoles} | YES | staffRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:128 |
| /orders | GET | RoleGuard roles={staffRoles} | YES | staffRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:129 |
| /reports | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:130 |
| /results | GET | RoleGuard roles={staffRoles} | YES | staffRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:131 |
| /samples | GET | RoleGuard roles={labRoles} | YES | labRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:132 |
| /labs | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:133 |
| /alerts | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:134 |
| /notifications | GET | LazyPage | YES | authenticated | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:135 |
| /ai | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:136 |
| /ai-platform | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:137 |
| /stats | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:138 |
| /qc | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:139 |
| /patient-card | GET | RoleGuard roles={staffRoles} | YES | staffRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:140 |
| /identity | GET | RoleGuard roles={staffRoles} | YES | staffRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:141 |
| /tiers | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:142 |
| /compliance | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:143 |
| /settings | GET | LazyPage | YES | authenticated | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:144 |
| /profile | GET | LazyPage | YES | authenticated | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:145 |
| /security | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:146 |
| /admin/labs | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:147 |
| /admin/users | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:148 |
| /admin/audit | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:149 |
| /fhir | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:150 |
| /ehr | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | LEGACY_BRIDGE | frontend-v3/src/routes/index.tsx:151 |
| /hospital | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:152 |
| /edge | GET | RoleGuard roles={['master_admin', 'admin']} | YES | ['master_admin', 'admin'] | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:153 |
| /financial | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:154 |
| /national-data | GET | RoleGuard roles={['master_admin', 'ministry_admin', 'province_admin']} | YES | ['master_admin', 'ministry_admin', 'province_admin'] | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:155 |
| /niam/governance | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:156 |
| /niam/trust | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:157 |
| /niam/lifecycle | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:158 |
| /niam/federation | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:159 |
| /niam/certificates | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:160 |
| /niam/workflows | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:161 |
| /niam/adaptive-auth | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:162 |
| /ai-fabric | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:163 |
| /biomedical | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:164 |
| /blood-bank | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:165 |
| /capabilities/clinical-foundation | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:166 |
| /capabilities/document-management | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:167 |
| /capabilities/encounter-management | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:168 |
| /capabilities/healthcare-consent | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:169 |
| /capabilities/provider-management | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:170 |
| /capabilities/reporting-service | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:171 |
| /capabilities/search-service | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:172 |
| /capabilities/storage-service | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:173 |
| /capabilities/workflow-engine | GET | RoleGuard roles={readonlyRoles} | YES | readonlyRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:174 |
| /certification | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:175 |
| /citizen | GET | RoleGuard roles={["citizen"]} | YES | ['citizen'] | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:176 |
| /citizen-platform | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:177 |
| /command-center | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:178 |
| /command-intelligence | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:179 |
| /control-plane | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:180 |
| /critical-care | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:181 |
| /ems | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:182 |
| /health-data | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:183 |
| /integration | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:184 |
| /integration/connectors | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:185 |
| /kernel | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:186 |
| /lifecycle-platform | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:187 |
| /national/background-platform | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:188 |
| /national/document-platform | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:189 |
| /national/ecosystem | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:190 |
| /national/ecosystem/gateway | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:191 |
| /national/notification-platform | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:192 |
| /national/observability | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:193 |
| /national/rules-engine | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:194 |
| /national/scheduling-platform | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:195 |
| /national/search-platform | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:196 |
| /national/task-engine | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:197 |
| /national/workflow-runtime | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:198 |
| /pharmacy | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:199 |
| /pilot-platform | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:200 |
| /platform | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:201 |
| /public-health | GET | RoleGuard roles={adminRoles} | YES | adminRoles | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:202 |
| /admin | GET | Navigate to="/admin/labs" replace / | YES | authenticated | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:203 |
| /* | GET | LegacyRouteBridge / | YES | authenticated | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | LEGACY_BRIDGE | frontend-v3/src/routes/index.tsx:204 |
| /* | GET | Navigate to="/" replace / | YES | authenticated | UI role guard only; backend decision required | UNVERIFIED | UNVERIFIED | ROUTE_REGISTERED | frontend-v3/src/routes/index.tsx:207 |
| / | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:89 |
| /patients | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:90 |
| /patients/:id | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:91 |
| /appointments | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:92 |
| /intelligence | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:93 |
| /lab/dashboard | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:95 |
| /lab/queue | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:96 |
| /lab/devices | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:97 |
| /lab/inventory | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:98 |
| /lab/samples | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:99 |
| /lab/qc | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:100 |
| /lab/imaging | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:101 |
| /citizen/dashboard | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:103 |
| /citizen/profile | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:104 |
| /citizen/assistant | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:105 |
| /citizen/medications | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:106 |
| /citizen/appointments | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:107 |
| /citizen/family | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:108 |
| /citizen/results | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:109 |
| /citizen/history | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:110 |
| /citizen/security | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:111 |
| /citizen/verification | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:112 |
| /citizen/consent | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:113 |
| /citizen/register | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:114 |
| /admin/audit | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:116 |
| /admin/infrastructure | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:119 |
| /admin/architecture | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:122 |
| /admin/integrations | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:125 |
| /ministry/dashboard | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:129 |
| /ministry/epidemiology | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:132 |
| /ministry/audit | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:135 |
| /ministry/analytics | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:138 |
| /settings | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:142 |
| * | GET | legacy route element | OUTER SESSION GATE | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | LEGACY | frontend-v2/src/App.tsx:143 |

**Rows:** 117. All `UNVERIFIED` values require contract-level follow-up; they are not claims of functionality.
