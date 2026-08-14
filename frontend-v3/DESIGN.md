# GULA Clinical Clarity Design System

## Scope and safety boundary

This document is the visual source of truth for GULA web and mobile surfaces. It translates the **Clinical Clarity** design direction generated in the GULA Stitch project into implementation rules for `frontend-v3`. It governs presentation only. It must never add, remove, hide, or bypass clinical validation, role-based access control, tenant isolation, audit logging, read-only demo boundaries, or API contracts.

All design prototypes and UI examples must use **synthetic data only**. A visual state may never imply that an action succeeded unless the existing backend contract confirms it. Clinical writes must remain visibly distinct from navigation, preview, and read-only states.

## Brand and color tokens

| Role | Token | Value | Intended use |
|---|---|---:|---|
| Clinical navy | `--gula-navy` | `#0F172A` | Application shell, high-emphasis headings, secure workspace surfaces |
| Clinical teal | `--gula-teal` | `#0D9488` | Primary positive action, focus, active navigation, operational health |
| Slate neutral | `--gula-slate` | `#64748B` | Secondary copy, metadata, muted icons |
| Warm sand | `--gula-sand` | `#231500` | Restrained neutral accent; never a primary clinical status |
| Success | `--gula-success` | `#059669` | Confirmed non-clinical success and healthy system status |
| Warning | `--gula-warning` | `#D97706` | Delayed, incomplete, or attention-required states |
| Critical | `--gula-critical` | `#E11D48` | Critical alert display only; never use as a destructive-action default |
| Surface | `--gula-surface` | `#FFFFFF` | Cards, modals, forms, and elevated content |
| Canvas | `--gula-canvas` | `#F8FAFC` | Main page background and spacious layout canvas |

Use restrained color. Teal communicates safe progress or an approved primary interaction. Red signals attention and never automatically performs a clinical action. Do not encode clinical status with color alone; pair it with readable text and an icon.

## Typography and direction

GULA is Arabic-first and must render with `dir="rtl"` for Arabic sessions. Use an Arabic-capable sans-serif stack such as `IBM Plex Sans, Noto Sans Arabic, system-ui, sans-serif`; keep readable line height, visible focus rings, and no font size below 12 px for operational data.

| Element | Desktop | Mobile | Rule |
|---|---:|---:|---|
| Page title | 30–36 px | 26–30 px | One clear task or operational context per screen |
| Section title | 16–18 px | 16 px | Use concise Arabic labels |
| Body | 14–16 px | 14–16 px | Minimum 1.6 line height for Arabic copy |
| Metadata | 12 px | 12 px | Never the only carrier of a safety-critical state |
| KPI value | 28–32 px | 24–28 px | Use tabular numerals where available |

## Layout rules

The desktop shell uses a persistent RTL sidebar, a calm top bar with workspace and session context, and a maximum content width of 1280 px. The mobile shell uses a compact header and the existing role-aware bottom navigation. Preserve existing navigation visibility checks; styling may change, permissions may not.

Every operational page follows this hierarchy: page context, safety/read-only or workspace status, highest-priority clinical or operational information, primary task area, secondary activity, and empty/error/help states. Avoid dense tables above the fold on mobile; offer readable stacked cards or responsive table overflow without hiding data.

## Components and interactive states

| Component | Base treatment | Required states |
|---|---|---|
| Dashboard KPI | White card, 16–20 px padding, top accent line, icon in tinted square | loading, read-only, unavailable, critical |
| Primary action | Teal fill, white label, clear verb | default, hover, focus-visible, disabled, loading, permission denied |
| Secondary action | White or slate surface with border | default, hover, focus-visible, disabled |
| Clinical action | Clearly labelled, role-aware, confirmation path where existing workflow requires it | enabled only by existing state machine and permissions |
| Dialog / modal | Focus-trapped white surface, explicit title and reason, mobile bottom-sheet fallback | open, loading, validation error, server error, cancel |
| Table / list | Strong headers, compact but touch-safe rows, explicit empty state | loading, empty, error, filtered-empty, pagination |
| Alert | Icon + text + severity label; no color-only meaning | info, warning, critical, resolved |
| Demo badge | Amber, explicit read-only text | must be present wherever synthetic data could be mistaken for production data |

## Surface map

| Surface family | Required visual goal | Non-negotiable behavior |
|---|---|---|
| Authentication and onboarding | Reassuring, minimal, accessible, Arabic-first | Preserve access-path separation and credential handling |
| Dashboard and command center | Calm operational hierarchy with healthy/attention states | Preserve workspace scoping and demo isolation |
| Patients, orders, samples, results | Progressive disclosure and clear workflow stage | Preserve state machine, RBAC, and audit behavior |
| Alerts and critical care | High contrast prioritization without alarm fatigue | No automatic acknowledgement or resolution in UI-only work |
| Reports, analytics, and FHIR | Dense data made scannable with filters and readable empty states | Preserve read contracts and export permissions |
| Administration, settings, and integrations | Structured configuration with consequences visible | Preserve confirmation, encryption, and privileged-action boundaries |
| National and public-health modules | Consistent hierarchy for wide data surfaces | Preserve tenant, jurisdiction, and authorization controls |
| Mobile web and responsive states | Touch-safe, bottom navigation, concise cards | Preserve exactly the same permissions and write barriers as desktop |

## Accessibility acceptance criteria

All new visual work must maintain keyboard navigation, visible focus, semantic headings, labels for icon-only controls, contrast suitable for text and status chips, and reduced reliance on hover-only behavior. Do not remove the existing skip link, focus ring, or accessible names.

## Implementation sequence

1. Apply shared tokens, shell, card, button, dialog, and empty-state standards.
2. Apply the system to the dashboard, patient list/detail, orders, samples, results, and alerts.
3. Apply it to reports, settings, integrations, administration, national modules, and public surfaces.
4. Verify responsive layouts, role-aware navigation, demo isolation, API contracts, and production build after each batch.

## Stitch reference

Reference project: `GULA Medical Operations Dashboard` in Google Stitch. The project supplies the visual direction and synthetic layout examples; production code remains owned by GULA and must be reviewed against this document before merge.
