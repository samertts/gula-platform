# GULA Design System

## Overview

**GULA Platform** is an Arabic-first, medical laboratory management SaaS targeting the Iraqi and MENA healthcare markets. It provides comprehensive LIMS (Laboratory Information Management System) capabilities: patient registration, sample tracking, result management, reporting, billing, and advanced security/audit features. Built for multi-tenant, multi-lab deployments with strict data-integrity and compliance requirements.

**Tagline:** "Transforming Healthcare, One Lab at a Time"

### Sources

- **Codebase:** `samertts/gula-platform` (private GitHub repo) — FastAPI backend monolith + React 19 / Tailwind CSS 4 frontend
- No Figma designs were provided; design system is derived from codebase inspection and brand documentation

---

## Products

| Product | Description |
|---------|-------------|
| **Web App (Dashboard)** | Primary SaaS interface for lab staff — patients, samples, results, reports, billing |
| **API Backend** | FastAPI monolith; RESTful JSON; multi-tenant by `lab_id` |
| **(Planned) Mobile App** | Planned for Phase 2; not yet in codebase |

---

## Technology Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, Tailwind CSS 4, Lucide React icons, Framer Motion, Recharts |
| Backend | FastAPI (Python), Gunicorn + Uvicorn, SQLAlchemy |
| Database | PostgreSQL 16 (Supabase), Redis 7 |
| Infra | Docker, Render, HAProxy, Prometheus + Grafana |

---

## Content Fundamentals

### Language & Audience
- **Primary language:** Arabic (RTL). The platform is explicitly Arabic-first; all UI copy should be in Arabic for the primary audience.
- **Secondary language:** English for technical documentation and international expansion.
- **Target users:** Lab managers, technicians, administrative staff, government health officials in Iraq and the MENA region.

### Tone & Voice
- **Professional & trustworthy** — this is a clinical, patient-data system. Copy must feel authoritative and reliable.
- **Approachable** — not cold or bureaucratic; designed to be accessible to non-technical lab staff.
- **Security-forward** — frequently references safety, encryption, audit, and compliance. Trust is central.
- **Local-aware** — references Iraqi context, Iraqi dinar pricing, integration with Iraqi National ID.

### Casing & Style
- **Sentence case** for UI labels and headings (Arabic convention; English UI follows same).
- **No exclamation marks** in serious/clinical contexts. Used sparingly in onboarding/success states.
- **Numbers:** use Arabic-Indic numerals (٠١٢٣...) in the Arabic UI; Western numerals in English.
- **Emoji:** Used sparingly in marketing/onboarding (👋 in welcome header, ✅ in checklists). Not used in clinical data screens.

### Copy Examples
- `"مرحباً بعودتك!"` — Welcome back (with wave emoji in dashboard header)
- `"إدارة شاملة وآمنة"` — Comprehensive and secure management
- `"بيانات المرضى محمية بأعلى معايير الأمان"` — Patient data protected by the highest security standards
- `"Transforming Healthcare, One Lab at a Time"` — English tagline; measured, specific, mission-driven

---

## Visual Foundations

### Colors
- **Primary:** `#2563EB` — Professional Blue (brand anchor; buttons, links, nav highlights)
- **Secondary:** `#F59E0B` — Warm Gold (accents, badges, secondary CTAs)
- **Success:** `#10B981` — Emerald green (completed states, positive indicators)
- **Warning:** `#F59E0B` — Amber (pending states, caution)
- **Danger:** `#EF4444` — Red (failed states, critical alerts)
- **Neutral Light BG:** `from-slate-50 to-slate-100` gradient
- **Neutral Dark BG:** `from-slate-900 to-slate-800` gradient
- **Text primary:** `#111827` (gray-900) light mode; `#F9FAFB` (gray-50) dark mode
- **Text secondary:** `#4B5563` (gray-600) light; `#9CA3AF` (gray-400) dark
- **Borders:** `#E5E7EB` (gray-200) light; `#374151` (gray-700) dark

### Typography
- **Font:** Poppins (Google Fonts) — modern, geometric, highly legible
- **Arabic Font:** Cairo or Tajawal (Google Fonts) — best Arabic pairing for Poppins aesthetics
- **Type scale:** Standard Tailwind scale (text-xs through text-4xl); dashboard header at `text-4xl font-bold`
- **Weight range:** 400 (body), 500 (labels), 600 (subheadings), 700 (headings)

### Layout
- **Padding:** `p-8` (32px) for page-level padding; `p-6` for card content
- **Grid:** CSS Grid — `grid-cols-4` for stat cards, `grid-cols-3` for chart area
- **Gap:** `gap-6` (24px) standard component gap
- **Max-width:** Full viewport; no fixed max-width on the dashboard container

### Backgrounds
- Light mode: subtle diagonal gradient `from-slate-50 to-slate-100`; no textures or patterns
- Dark mode: deep `from-slate-900 to-slate-800`
- Cards: solid white (light) / slate-800 (dark) with `hover:shadow-lg` transition

### Cards
- **Border radius:** `rounded-lg` (~8px)
- **Shadow:** `shadow` default, `hover:shadow-lg` on hover — soft, multi-layer shadow
- **Border:** none by default; border appears via `border border-gray-200` in some variants
- **Padding:** `pt-6` top + `p-6` content area

### Icons
- **Library:** Lucide React (stroke-based, consistent 2px stroke weight, rounded caps)
- **Sizes:** `w-4 h-4` inline, `w-5 h-5` list items, `w-6 h-6` stat card icons
- **Icon backgrounds in stat cards:** solid color rounded squares (`p-3 rounded-lg bg-blue-500`)

### Animations
- **Library:** Framer Motion
- **Entry animations:** `opacity: 0 → 1` + `y: 20 → 0` with `duration: 0.3s`
- **Stagger:** `delay: 0.1` between sequential items
- **Hover states:** `hover:shadow-lg transition-shadow` — shadow elevation on cards
- **No bounces** — easing is smooth/ease; clinical feel, not playful

### Corner Radii
- `rounded-lg` (8px) — cards, buttons, icon containers
- `rounded-full` — pill badges, avatar circles

### Buttons
- **Default:** solid primary blue background, white text
- **Outline:** transparent bg, border + colored text
- **Ghost:** no border, subtle hover bg
- **Destructive:** red background
- **Size:** padding `px-4 py-2` (md), full-width in action lists

### Charts
- **Library:** Recharts
- **Colors:** Blue `#3B82F6`, Purple `#8B5CF6`, Green `#10B981`, Amber `#F59E0B`, Red `#EF4444`
- **Grid:** `strokeDasharray="3 3"` light dotted grid lines
- **Tooltip:** default Recharts; no custom styling in codebase

### Imagery
- No custom illustrations or photography found in codebase
- Placeholder-friendly: icon-only approach for empty states
- Brand imagery is implied to be medical/clinical photography (not yet in codebase)

---

## Iconography

- **System:** Lucide React — open-source, MIT, consistent stroke-based icon library
- **CDN:** `https://unpkg.com/lucide-react` or `https://unpkg.com/lucide@latest`
- **Style:** 2px stroke, rounded line caps/joins, 24×24 viewBox
- **No icon font** — SVG-based only
- **No emoji used** in data-heavy screens; only in welcome/marketing contexts
- **Key icons used in codebase:**
  - `Users`, `Beaker`, `FileText`, `TrendingUp`, `Clock`, `AlertCircle`
  - `CheckCircle`, `Activity`, `Download`, `Plus`, `BarChart`, `LineChart`

---

## File Index

```
README.md                  ← This file; brand overview & guidelines
SKILL.md                   ← Agent skill definition
colors_and_type.css        ← CSS custom properties for colors, type, spacing
assets/                    ← Logos, icons, visual assets
preview/                   ← Design System card previews (registered in DS tab)
ui_kits/
  dashboard/               ← Web app UI kit (index.html + JSX components)
```

---

## UI Kits

| Kit | Path | Description |
|-----|------|-------------|
| Dashboard | `ui_kits/dashboard/index.html` | Main lab management web app — login, dashboard, patients, samples |
