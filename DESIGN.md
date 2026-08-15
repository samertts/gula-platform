# GULA Design System for Stitch

## Product context

GULA is a unified, Arabic-first platform for representing and serving Iraqi and non-Iraqi people, organizations, institutions, ministries, professional bodies, private entities, and future health-related services without restricting the domain model to one sector. The interface must make the distinction between **entity type**, **verification status**, **membership**, **role**, **permission**, **entitlement**, and **workspace** visible and understandable. No user or organization receives authority merely from a name, type, sector, or visual label.

The visual system is designed for high-trust public services and clinical-adjacent workflows. It should feel calm, precise, inclusive, and operational rather than promotional. The product is Arabic-first and RTL by default, with English, Kurdish, Turkmen, and Syriac as supported directions or locales where available.

## Design principles

1. **Arabic first and direction-aware.** All layouts, forms, navigation, tables, empty states, alerts, and dialog actions must work in RTL. Do not mirror meaning incorrectly: status icons, medical symbols, charts, and progress indicators must preserve semantic direction.
2. **Authority is explicit.** Display verification and access state as separate status surfaces. Never imply that an organization type or job title grants a clinical or administrative permission.
3. **Calm operational hierarchy.** Use a quiet light surface, strong navy for primary structure, teal for confirmed progress, amber for attention, and red only for errors or dangerous actions.
4. **Progressive disclosure.** Citizens see simple next steps; institutional and ministry users see workspace context, verification state, and scoped actions without exposing irrelevant administration.
5. **Accessible by construction.** Target WCAG 2.2 AA. Every interactive element needs keyboard focus, a visible focus ring, an accessible name, and a touch target of at least 44×44 CSS pixels. Dynamic status changes must use semantic status or alert regions.
6. **Safety before speed.** Loading and optimistic visual feedback must never imply that a server-authoritative action succeeded before the backend confirms it. No design may hide audit, verification, conflict, or read-only states.

## Visual tokens

Use the following existing GULA tokens as the source of truth. Stitch variations may explore composition, but must not invent a competing palette.

| Token | Value | Use |
|---|---|---|
| Primary | `#0B3658` | Main actions, headings, navigation anchors, trusted structure |
| Primary container | `#124C74` | Selected navigation, high-emphasis surfaces |
| Primary light | `#EAF4FB` | Informational background and selected-but-safe states |
| Secondary | `#6E8090` | Supporting text and neutral controls |
| Background | `#F5F8FA` | Application canvas |
| Surface | `#FFFFFF` | Cards, forms, dialogs, table containers |
| Surface container | `#EDF4F7` | Grouped sections and low-emphasis panels |
| On-surface | `#17324A` | Primary text |
| On-surface variant | `#6E8090` | Secondary text |
| Outline | `#D8E4E9` | Borders and dividers |
| Success | `#258B76` | Verified, ready, completed, healthy |
| Success container | `#EAF7F2` | Non-blocking success background |
| Warning | `#F59E0B` | Pending verification, attention required |
| Warning container | `#FFFBEB` | Warning background |
| Error | `#EF4444` | Failed request, invalid transition, destructive risk |
| Error container | `#FEF2F2` | Error background |

Typography uses **Tajawal** for Arabic and Latin interface text where available, with `Noto Naskh Arabic` and system sans-serif fallbacks. Use `JetBrains Mono` only for IDs, request references, timestamps, and technical values. Avoid all-caps Arabic and avoid dense small text in clinical or government workflows.

## Layout and responsive behavior

Use a 4px base spacing rhythm with 8px as the dominant step. Desktop authenticated views use a persistent right-side navigation rail in RTL, a sticky top bar for identity and workspace context, and a fluid content area constrained to a readable maximum width. On mobile, replace the rail with a bottom navigation bar for the highest-frequency actions and a dismissible drawer for the complete navigation set.

Use surface cards with 12–24px radii and restrained shadows. Prefer borders plus subtle elevation over large gradients. Keep primary action placement consistent: in RTL, the primary action is on the right side of a horizontal action group unless the task has an explicit destructive or cancellation hierarchy. Preserve a visible skip link and keep sticky elements from obscuring focused controls.

## Component language

The Stitch project should generate and reuse the following component families rather than creating one-off visual patterns:

| Component family | Required states |
|---|---|
| App shell | Authenticated, demo read-only, offline/degraded, loading, error |
| Workspace header | Active workspace, pending workspace, switching, denied, server rejection |
| Navigation item | Default, hover, keyboard focus, active, disabled, unauthorized/hidden |
| Status badge | Pending verification, verified, restricted, read-only, failed, expired |
| Card and metric | Loading skeleton, populated, empty, stale, error |
| Data table | Loading, empty, filtered, paginated, row conflict, permission-limited |
| Form field | Default, focused, invalid, server error, disabled, read-only, autocomplete |
| Alert and toast | Polite status, assertive error, persistent critical notice, dismissible notice |
| Dialog and drawer | Open, focus-trapped, confirmation, rejection, network retry |
| Empty state | No data, no access, not configured, offline, action available |
| Timeline/audit item | Actor, timestamp, action, before/after summary, immutable indicator |

Use icons from the existing Lucide icon language. Icons support text and must not be the only carrier of meaning. Do not use decorative biometric, national-ID, camera, NFC, or government-registry imagery in current-phase screens.

## Screen map for Stitch exploration

Create the following screens as separate frames or connected prototype states. Each screen must include desktop and mobile variants where the workflow is relevant.

### Public access

- **GULA landing and access choice:** explain the platform in neutral language, distinguish citizen and institutional access, show language selection, and provide a clear route to sign in. Do not present citizen registration as active in the current phase.
- **Login:** show email/phone and password fields, secure-access messaging, demo mode as read-only and clearly labelled, server error state, and an accessible loading state.
- **Account request information:** describe that account requests are governed and reviewed; do not display a self-service activation promise.

### Authenticated shell

- **Dashboard:** show server-confirmed workspace, verification status, high-level operational summaries, recent activity, alerts, and an explicit read-only/demo banner where applicable.
- **Workspace switcher:** show only server-provided workspaces. Include loading, switching, denied, pending, and error states. Never show a client-controlled membership or workspace status control.
- **Notification center:** separate informational, warning, and critical notifications with accessible live-region behavior.

### Citizen workspace

- **Citizen home:** show personal services and requests without exposing institutional administration or speculative clinical permissions. Include empty, offline, and pending-review states.
- **Request/status detail:** present a clear timeline and next action while preserving backend authority and audit traceability.

### Institution workspace

- **Institution overview:** represent organization type, sector, jurisdiction, authority level, verification level, parent organization, and relationships as separate fields. Use pending verification as the default unverified state.
- **Members and roles:** show memberships, roles, permissions, and entitlements as separate, scoped concepts. Include a denial state for self-escalation attempts.
- **Facilities/departments/workspaces:** show hierarchy and server-confirmed access without allowing the frontend to mutate status directly.

### Ministry and national operations views

- **Ministry operations dashboard:** show authorized workspaces and aggregate operational information, not fabricated ministry integrations or legal approvals.
- **Verification queue:** show pending, approved, rejected, and needs-more-information states. Design the workflow for review, not automatic activation.
- **Audit and governance:** show immutable audit entries, actor, timestamp, operation, before/after summary, and request correlation ID.

## Motion and feedback

Motion must be short and purposeful: 120–240ms for hover and navigation feedback, up to 300ms for drawers and dialogs, with no animation that blocks keyboard use. All non-essential animation must be disabled or reduced when `prefers-reduced-motion: reduce` is active. Never use optimistic feedback for authorization, workspace switching, verification, clinical writes, or other server-authoritative operations.

Every screen must define what happens when loading takes longer than 200ms, when the request fails, when the user has no permission, when the data is empty, and when the device is offline. A skeleton indicates structure only; it must not contain fake patients, results, orders, organizations, or government data.

## Content and localization

Use plain Arabic suitable for citizens and institutional operators. Avoid unexplained acronyms, legal claims, or statements that imply Ministry of Health approval. Provide English fallback copy for every new message and preserve semantic meaning across Kurdish, Turkmen, and Syriac translations. Dates and numbers follow locale settings; identifiers remain copyable technical strings.

## Stitch guardrails

Stitch-generated output is a visual hypothesis, not production authority. Do not paste generated code directly into production. Before implementation, map each visual component to an existing GULA component or create a reviewed shared component. Remove fabricated data and replace it with typed API states. Preserve the current route guards, server-authoritative authorization, demo read-only boundary, clinical gateway OFF default, and P4/P5 release gates.

The first Stitch exploration should produce a coherent visual direction and screen map, not a full production replacement. Each accepted screen becomes a scoped GitHub PR with tests, accessibility checks, responsive verification, and human review before merge or deployment.
