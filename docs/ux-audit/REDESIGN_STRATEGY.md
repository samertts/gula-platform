# GULA Platform — Complete UX Redesign Strategy

**Author**: CXO / Chief Product Designer  
**Version**: 1.0  
**Target**: World-class healthcare experience (Apple, Stripe, Linear, Epic quality)

---

## Table of Contents

1. [Navigation Architecture](#1-navigation-architecture)
2. [Design System](#2-design-system)
3. [Screen-by-Screen Redesign](#3-screen-by-screen-redesign)
4. [Workflow Optimization](#4-workflow-optimization)
5. [AI Experience](#5-ai-experience)
6. [Component Library](#6-component-library)
7. [Implementation Roadmap](#7-implementation-roadmap)

---

## 1. Navigation Architecture

### Current Problems

- Wing-based sidebar with 9 roles creates navigation overload
- "Network Interlink" and fake bio-metrics add noise
- Multiple floating assistants (AI, Help, Command Palette) overlap at bottom-right
- No context-aware navigation
- Breadcrumbs are naive (URL path parsing only)

### Target Architecture

```
┌─────────────────────────────────────────────────┐
│  [☰]  [🔍 Global Search — Cmd+K]     [🌐] [👤] │  ← Universal Top Bar
├─────────────────────────────────────────────────┤
│                                                  │
│   CONTENT AREA (full width, no sidebar)          │
│                                                  │
│   ┌─────────────────────────────────────────┐    │
│   │  Page content — one primary purpose      │    │
│   │  One primary action                       │    │
│   │  Progressive disclosure for secondary     │    │
│   └─────────────────────────────────────────┘    │
│                                                  │
├─────────────────────────────────────────────────┤
│  [Status bar: last sync | offline | version]     │  ← Thin status footer
└─────────────────────────────────────────────────┘
```

### Key Decisions

| Decision | Why |
|----------|-----|
| **Remove fixed sidebar** | Consumes 288px of horizontal space. Navigation should be transient (Cmd+K or context menu). |
| **Single universal top bar** | Search + user menu. Everything else is one keystroke away. |
| **Cmd+K is primary navigation** | Type what you need. Fuzzy search wings, patients, orders, tests, commands. |
| **Role-based landing page** | Each wing gets a purpose-built dashboard on login. |
| **Breadcrumbs become navigation path** | Show actual navigation trail, not URL segments. Use wing > section > item format. |
| **Context sidebar (optional)** | Toggleable inspector panel for detail views. Not always visible. |

### Command Palette Redesign

Current: Modal with command list filtered by wing.  
Target: Spotlight-style overlay (like macOS Spotlight, Linear quick search).

```
┌─────────────────────────────────────────────┐
│  🔍  Search patients, orders, tests...       │  ← Autofocused
├─────────────────────────────────────────────┤
│  Recent                                       │
│  ┌─────────────────────────────────────────┐ │
│  │ Patient: Ahmed Hasan — HbA1c follow-up  │ │
│  │ Order: CBC + Diff — Lab-2024-0842       │ │
│  │ Doctor: Dr. Ali — Patient Profile       │ │
│  └─────────────────────────────────────────┘ │
│                                               │
│  Actions (>)                                   │
│  > Create Order                                │
│  > View Critical Alerts                        │
│  > New Patient Registration                    │
│                                               │
│  Patients                                      │
│  ┌─────────────────────────────────────────┐ │
│  │ Ahmed Hasan — 045-XX-XXXX               │ │
│  │ Zainab Ali — 046-XX-XXXX                │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+K` | Open command palette |
| `Cmd+1-9` | Quick switch wings |
| `g then d` | Go to dashboard |
| `g then p` | Go to patients |
| `g then l` | Go to lab |
| `g then o` | Go to orders |
| `g then s` | Go to settings |
| `?` | Show shortcuts |
| `Escape` | Close panel / Deselect |
| `Enter` | Confirm action |
| `↑ ↓` | Navigate lists |
| `Cmd+Enter` | Submit form / Save |
| `Cmd+Z` | Undo |
| `Cmd+Shift+Z` | Redo |
| `Cmd+S` | Save (auto-save also active) |

---

## 2. Design System

### Philosophy

Typography is the design. Color communicates meaning only. Space creates hierarchy.

### Color Palette

```css
/* Semantic — ONLY use for meaning */
--color-success:    #059669;  /* emerald-600 */
--color-info:      #2563eb;  /* blue-600 */
--color-warning:   #d97706;  /* amber-600 */
--color-critical:  #dc2626;  /* red-600 */
--color-neutral:   #64748b;  /* slate-500 */

/* UI — minimal, no decoration */
--color-bg:        #ffffff;
--color-surface:   #f8fafc;  /* slate-50 */
--color-border:    #e2e8f0;  /* slate-200 */
--color-text:      #0f172a;  /* slate-900 */
--color-text-secondary: #64748b;  /* slate-500 */

/* Brand — single accent */
--color-primary:   #4f46e5;  /* indigo-600 */
--color-primary-hover: #4338ca;  /* indigo-700 */
```

### Typography Scale

```css
--font-display: 2.25rem  /* 36px — page title */
--font-heading: 1.5rem   /* 24px — section title */
--font-subheading: 1.125rem /* 18px — card title */
--font-body: 0.9375rem   /* 15px — body text */
--font-small: 0.8125rem  /* 13px — labels, metadata */
--font-tiny: 0.75rem     /* 12px — badges, timestamps */

--font-family: 'Inter', 'Noto Naskh Arabic', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'Cairo', monospace;
```

- **Remove ALL `font-black` usage** except for display and heading
- **Remove ALL `text-[8px|9px|10px]`** — replace with scale values
- **Remove ALL uppercase on Arabic text**
- **Line-height**: 1.6 for body, 1.2 for headings

### Spacing Scale

```css
--space-1: 4px
--space-2: 8px
--space-3: 12px
--space-4: 16px
--space-5: 20px
--space-6: 24px
--space-8: 32px
--space-10: 40px
--space-12: 48px
--space-16: 64px
```

Every component uses this scale. No arbitrary values.

### Border Radius

```css
--radius-sm: 6px     /* inputs, buttons */
--radius-md: 10px    /* cards */
--radius-lg: 16px    /* modals, dialogs */
```

### Shadow System

```css
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 2px 8px rgba(0,0,0,0.08);
--shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
```

No multi-layered shadows. No blur. No glow.

### Animation

```css
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 400ms;
```

Only three timing values. Respect `prefers-reduced-motion`.

---

## 3. Screen-by-Screen Redesign

### 3.1 LandingAuthView → Split Authentication

**Current**: Single vertical scroll with all auth steps.  
**Target**: Split-screen with brand + form.

```
┌─────────────────────┬──────────────────────────┐
│                     │                          │
│   GULA              │  Sign in                 │
│                     │  ┌────────────────────┐  │
│   Healthcare        │  │ Email              │  │
│   Intelligence      │  └────────────────────┘  │
│   Platform          │  ┌────────────────────┐  │
│                     │  │ Password           │  │
│   [Arabic-first]    │  └────────────────────┘  │
│   [Iraq]            │                          │
│                     │  [Sign In]  [Register]   │
│   [QR login]        │                          │
│   [Biometric]       │  ─── or ───             │
│                     │  [Biometric] [QR Code]  │
│                     │                          │
└─────────────────────┴──────────────────────────┘
```

**Changes**:
- Left panel: brand, QR login option, biometric entry point
- Right panel: clean form with inline validation
- Remove: all identity verification, medical migration, forgot_password steps (move to flow after login)
- Remove: hardcoded demo role buttons
- Add: `role="presentation"` on brand panel

### 3.2 DashboardView → Wing-Specific Landing

**Current**: Generic dashboard with charts, stats, AI insights.  
**Target**: Each wing gets a purpose-built landing.

#### Doctor Dashboard
```
┌─────────────────────────────────────────────────┐
│  Good morning, Dr. Ali                          │
│  ───────────────────────────────────────────────│
│  ⚠ 3 Critical Results     ⏳ 12 Pending Review  │
│  🔴 1 Critical Alert       📋 8 Appointments    │
│  ───────────────────────────────────────────────│
│  Today's Patients                                │
│  ┌──────────────┬──────────┬────────┬─────────┐ │
│  │ Ahmed Hasan  │ CBC      │ 🟡 High │ 2h ago  │ │
│  │ Zainab Ali   │ HbA1c    │ 🟢 Norm │ 30m ago │ │
│  │ Sajjad Karim │ LFTs     │ 🔴 Crit │ Just now│ │
│  └──────────────┴──────────┴────────┴─────────┘ │
│                                                  │
│  [Cmd+K] Search patients and orders              │
└─────────────────────────────────────────────────┘
```

**Changes**:
- Remove: NeuralConnectivityHub, QuantumHealthGrid, DigitalTwinSimulation, BiometricStatus
- Remove: fake AI insights (DashboardInsight)
- Focus: urgent items first, then work queue, then schedule
- Add: patient search bar at bottom
- One primary action: "Review next pending result"

#### Lab Dashboard
```
┌─────────────────────────────────────────────────┐
│  Lab Dashboard — Baghdad Central Lab            │
│  ───────────────────────────────────────────────│
│  📥 23 Pending    🔬 45 In Progress    ✅ 189 Today│
│  ───────────────────────────────────────────────│
│  Critical Priority                               │
│  ┌──────┬────────────┬──────────┬────────┬─────┐ │
│  │ STAT │ CBC-23041  │ Ahmed H. │ ⏰ 14min│▶▶  │ │
│  │ STAT │ LFT-23042  │ Zainab A │ ⏰ 8min │▶▶  │ │
│  │ HIGH │ CRP-23043  │ Sara M.  │ 22min  │▶   │ │
│  └──────┴────────────┴──────────┴────────┴─────┘ │
│                                                  │
│  [Tab] Focus on next urgent item                  │
└─────────────────────────────────────────────────┘
```

**Changes**:
- Remove: LabDeviceMonitor (fake device data), NeuralConnectivityHub
- Remove: decorative animated metrics
- Focus: queue management, TAT tracking, urgent items
- Add: Quick entry mode (single-kes start)

#### Citizen Dashboard
```
┌─────────────────────────────────────────────────┐
│  مرحباً أحمد                                      │
│  ───────────────────────────────────────────────│
│  🟢 Health Score: 85/100    Last updated: today  │
│  ───────────────────────────────────────────────│
│  Pending Actions                                 │
│  □ Review HbA1c results (new)                    │
│  □ Confirm next appointment (tomorrow 10am)      │
│  □ Update medications                            │
│  ───────────────────────────────────────────────│
│  Quick Actions                                   │
│  [View Results] [Book Appointment] [Ask AI]      │
└─────────────────────────────────────────────────┘
```

**Changes**:
- Remove: GlobalAiAssistant (replace with inline AI panel)
- Remove: OrganAnalysis, DigitalTwinSimulation, PredictiveAnalytics
- Remove: fake health metrics
- Focus: actionable items, clear next steps, simple navigation

### 3.3 RecordsView → Enterprise Patient List

**Current**: Basic table with search and filters.  
**Target**: Enterprise-grade patient registry.

```
┌──────────────────────────────────────────────────────┐
│  Patients  [➕ New]                                  │
│  ┌──────────────────────────────────────────────┐   │
│  │ 🔍 Name, ID, phone...               [Filter] │   │
│  ├──────┬───────────┬──────┬──────┬──────┬──────┤   │
│  │ Name │ ID        │ DOB  │ Wing │ Last │ ⚠   │   │
│  ├──────┼───────────┼──────┼──────┼──────┼──────┤   │
│  │ Ahmed│ 045-XX-XX │ 1985 │ Lab  │ 2h   │ 🔴  │   │
│  │ Zaina│ 046-XX-XX │ 1990 │ Doc  │ 30m  │ 🟡  │   │
│  │ Sara │ 047-XX-XX │ 1978 │ Cit  │ 1d   │ 🟢  │   │
│  └──────┴───────────┴──────┴──────┴──────┴──────┘   │
│  Showing 12 of 1,234 patients          [Load more]   │
└──────────────────────────────────────────────────────┘
```

**Changes**:
- Replace custom table with Enterprise DataGrid
- Add: column resize, column visibility, sort by any column
- Add: inline row preview (sidebar)
- Add: bulk actions (assign, export, merge)
- Add: virtual scrolling for 10,000+ rows
- Remove: decorative icons, excess cards

### 3.4 WorkQueue → Linear-Style Task Board

**Current**: Card-based task list with tabs.  
**Target**: Kanban board with quick actions.

```
┌─────────────────────────────────────────────────────┐
│  Lab Queue                        [Filter] [View]   │
│  ┌──────────┬──────────┬──────────┬────────────────┐│
│  │ PENDING  │ IN WORK  │ REVIEW   │ COMPLETED      ││
│  │    23    │    12    │     8    │    189         ││
│  ├──────────┼──────────┼──────────┼────────────────┤│
│  │ CBC-201  │ CBC-205  │ CBC-210  │ Done today     ││
│  │ Ahmed H. │ Sara M.  │ Zainab A │                ││
│  │ ⏰ 14min │ ⏰ 22min │ 45min    │                ││
│  │ 🟡 High  │ 🟢 Norm  │ 🟢 Norm  │                ││
│  ├──────────┼──────────┼──────────┤                ││
│  │ LFT-202  │ LFT-206  │ LFT-211  │                ││
│  │ Basim K. │ Ali H.   │ Omar S.  │                ││
│  │ ⏰ 8min  │ 35min    │ 1h       │                ││
│  │ 🔴 Crit  │ 🟡 High  │ 🟢 Norm  │                ││
│  └──────────┴──────────┴──────────┴────────────────┘│
│  [Space] Quick claim   [Tab] Next column             │
└─────────────────────────────────────────────────────┘
```

**Changes**:
- Kanban board with drag-and-drop
- Quick actions: Space to claim next, Tab to navigate columns
- Remove: task cards expand animation (replace with inline)
- Remove: decorative status icons
- Add: real-time TAT countdown timers
- Add: keyboard navigation throughout

### 3.5 LabResultsView → Clinical Results Hub

**Current**: Single list of results with real-time subscription.  
**Target**: Multi-panel results viewer.

```
┌──────────────────────────────────────────────────────┐
│  Patient: Ahmed Hasan       DOB: 1985-03-15         │
│  ───────────────────────────────────────────────────│
│  ┌──────────┬──────────┬──────┬──────┬──────┬──────┐│
│  │ Test     │ Result   │ Flag │ Ref  │ Prev │ Unit ││
│  ├──────────┼──────────┼──────┼──────┼──────┼──────┤│
│  │ WBC      │ 11.2     │ 🟡 H │ 4-10 │ 9.8  │ K/uL ││
│  │ Hb       │ 13.5     │ 🟢   │12-16 │ 13.2 │ g/dL ││
│  │ Platelets│ 450      │ 🟢   │150-400│420  │ K/uL ││
│  │ CRP      │ 85       │ 🔴 H │ <5   │ 12   │ mg/L ││
│  │ Glucose  │ 142      │ 🔴 H │70-100│ 118  │ mg/dL││
│  └──────────┴──────────┴──────┴──────┴──────┴──────┘│
│  [⬇ Export] [🖨 Print] [🤖 AI Summary] [📊 Trends]  │
└──────────────────────────────────────────────────────┘
```

**Changes**:
- Proper data grid with semantic flag coloring
- Delta column (previous value) for trend awareness
- Critical values highlighted with red background + bold
- AI Summary opens inline panel (not modal)
- Quick actions: export, print, trend chart
- Remove: decorative loading animations

### 3.6 PatientProfile → Apple Health-Style Timeline

**Current**: Form-like layout with tabs.  
**Target**: Timeline-based patient record.

```
┌──────────────────────────────────────────────────────┐
│  ← Back to Patients                                  │
│  Ahmed Hasan    045-XX-XXXX    35 yrs    Male        │
│  ───────────────────────────────────────────────────│
│  Timeline                                            │
│  ┌──────────────────────────────────────────────┐   │
│  │ Today 2:30 PM              🔴 Critical        │   │
│  │ CRP: 85 mg/L (H) — New result                │   │
│  │ ────────────────────────────────────────     │   │
│  │  View details →                               │   │
│  ├──────────────────────────────────────────────┤   │
│  │ Yesterday 10:00 AM           🩺 Appointment   │   │
│  │ Follow-up: HbA1c trending up (5.8 → 6.2)    │   │
│  │ Dr. Ali — Baghdad Central                    │   │
│  ├──────────────────────────────────────────────┤   │
│  │ 3 days ago                   💊 Medication    │   │
│  │ Metformin 500mg — dose changed               │   │
│  │ ────────────────────────────────────────     │   │
│  │ Reason: HbA1c not at target                  │   │
│  ├──────────────────────────────────────────────┤   │
│  │ 1 week ago                   📋 Lab Order     │   │
│  │ CBC + LFT + HbA1c — Ordered by Dr. Ali      │   │
│  └──────────────────────────────────────────────┘   │
│  [Cmd+K] Quick actions                              │
└──────────────────────────────────────────────────────┘
```

**Changes**:
- Chronological timeline as primary view
- Each event type has distinct icon and color
- Critical results highlighted at top
- Inline expand for details (no page navigation)
- Remove: separate tabs for orders/results/history
- Remove: card-based layout with multiple panels

### 3.7 SettingsView → Minimal Settings

**Current**: Tabbed settings with multiple sections.  
**Target**: Single-page, grouped settings.

```
┌──────────────────────────────────────────────────┐
│  Settings                                         │
│  ────────────────────────────────────────────────│
│  Profile                                          │
│  Name     ┌────────────────────────────────┐     │
│  Email    └────────────────────────────────┘     │
│  Language ┌────────────────────────────────┐     │
│           │ Arabic (العربية)               │     │
│           └────────────────────────────────┘     │
│  ────────────────────────────────────────────────│
│  Notifications                                    │
│  □ Critical alerts         [Push] [Email] [SMS]  │
│  □ Result available        [Push] [Email]        │
│  □ Appointment reminder    [Push] [Email]        │
│  ────────────────────────────────────────────────│
│  Security                                         │
│  [Manage Biometrics] [Active Sessions]            │
│  ────────────────────────────────────────────────│
│  About                                            │
│  Version 2.1.0  •  GULA Platform                  │
└──────────────────────────────────────────────────┘
```

**Changes**:
- Remove: decorative mode toggles (Clinical Mode, Low Bandwidth)
- Remove: Theme customization
- Remove: System diagnostics drawer trigger
- Group settings by category with clear section headers
- Inline editing on click (no separate edit forms)

### 3.8 CitizenHealth → Patient Health Summary

**Current**: Dashboard with vitals, AI assistant, charts.  
**Target**: Apple Health-style summary.

```
┌──────────────────────────────────────────────────────┐
│  Health Summary                     Last sync: now   │
│  ───────────────────────────────────────────────────│
│  🟢 Health Score: 85/100                             │
│  ───────────────────────────────────────────────────│
│  Highlights                                          │
│  ┌──────────────────────────────────────────────┐   │
│  │ HbA1c   6.2%  ↑  ████████░░  Above target    │   │
│  │ BP      128/84      ██████░░░░  Normal        │   │
│  │ Glucose 95          ███████░░░  Normal        │   │
│  └──────────────────────────────────────────────┘   │
│  ───────────────────────────────────────────────────│
│  Recent Activity                                     │
│  • New lab result received (2h ago)                 │
│  • Medication reminder for Metformin (due now)      │
│  • Appointment with Dr. Ali tomorrow 10:00          │
│  ───────────────────────────────────────────────────│
│  [View All Results] [Manage Medications]            │
└──────────────────────────────────────────────────────┘
```

**Changes**:
- Remove: OrganAnalysis, DigitalTwinSimulation, PredictiveAnalytics
- Remove: GlobalAiAssistant (replace with inline "Ask AI" button)
- Remove: NeuralSparkline, QuantumHealthGrid
- Remove: fake telemetry and biometrics
- Focus: clear health summary, actionable items, recent activity
- Add: Apple Health-style metric bars with color-coding

### 3.9 AuthContext / Profile → Trust Indicators

**Current**: No save indicators, no sync feedback.  
**Target**: Visible trust signals.

```
Top bar:
  [👤 Ahmed Hasan  ▾]  [🟢 Synced 2m ago]  [🌐 Online]

Status bar:
  Last saved: just now  •  Encrypted  •  Audit logged
```

**Add throughout the app**:
- `Last saved` timestamp on every form
- `Synced X ago` on data views
- `🟢 Online` / `🟡 Offline — XX pending` indicator
- `🔒 Encrypted` badge on patient data
- Audit trail link on clinical records

---

## 4. Workflow Optimization

### 4.1 Patient Registration

**Current**: 8-step flow (role → form → identity → medical → consent → OTP → success).  
**Target**: 3-step flow.

| Step | What |
|------|------|
| 1 | Basic info (name, DOB, phone) — auto-saves, AI fills address |
| 2 | Identity verification (optional — skip for later) |
| 3 | Done — share QR code for follow-up |

**Savings**: 62% fewer steps.

### 4.2 Lab Result Entry

**Current**: Form with manual entry, AI sidebar, device panel.  
**Target**: Keyboard-first entry with auto-validation.

```
Result Entry Mode
─────────────────────────────────
Test: CBC
─────────────────────────────────
 WBC    [11.2]  🟡 H  (4-10)     ↓ prev: 9.8
 Hb     [13.5]  🟢     (12-16)    ↓ prev: 13.2
 PLT    [450]   🟢     (150-400)  ↓ prev: 420
─────────────────────────────────
[Tab] next field  [Shift+Tab] prev  [Ctrl+Enter] commit
```

**Changes**:
- Remove: AI sidebar (replace with inline suggestion after entry)
- Remove: Device status panel
- Remove: Fidelity Score (fabricated)
- Keyboard-only workflow (Tab, arrows, Ctrl+Enter)
- Auto-validate against reference ranges on blur
- Auto-save after each row

### 4.3 Order Creation

**Current**: Form with multiple fields.  
**Target**: AI-assisted order.

```
New Order for: Ahmed Hasan
─────────────────────────────────
🔍 Search tests or describe clinical need
┌──────────────────────────────────────┐
│ Patient presents with fatigue and    │
│ weight loss. Suspect diabetes.       │
└──────────────────────────────────────┘

AI suggests:
┌──────────────────────────────────────┐
│ ☑ Fasting Glucose                    │
│ ☑ HbA1c                              │
│ ☑ CBC with Differential              │
│ ☑ TSH                                 │
│                                      │
│ [Accept All] [Edit] [Dismiss]        │
└──────────────────────────────────────┘
```

**Changes**:
- Natural language input instead of form
- AI suggests tests based on clinical description
- One-click accept all
- Remove: multi-page order form

### 4.4 Consent Management

**Current**: List of consents with grant/revoke.  
**Target**: Inline consent toggle.

```
Consent Preferences
─────────────────────────────────
Share results with primary physician
  [Always] [Ask each time] [Never]

Share with Ministry of Health (anonymized)
  [Always] [Never]

Share with research partners
  [Always] [Ask each time] [Never]
```

**Changes**:
- Inline toggles (no modal)
- Granular opt-in levels
- Audit log shown inline
- Confirmation on "revoke" with ⚠️ warning

---

## 5. AI Experience

### Principles

1. **AI is invisible** — no chatbot UI, no "AI assistant" bubble, no typing indicator
2. **AI suggests, never decides** — user always has final say
3. **AI embeds in context** — suggestions appear where the user is working
4. **AI respects clinical authority** — always includes disclaimer
5. **AI respects privacy** — PII is stripped before API calls

### Implementation

#### Inline AI (replaces GlobalAiAssistant + AISummary)

```
┌──────────────────────────────────────────────┐
│  Results for Ahmed Hasan                      │
│  ────────────────────────────────────────────│
│  CRP: 85 mg/L (🔴 High)                      │
│                                               │
│  🤖 CRP is significantly elevated (>5 mg/L)  │
│  suggesting active inflammation or infection. │
│  Previous value (12 mg/L) shows sharp rise.  │
│  Consider: ESR, procalcitonin, blood culture. │
│                                               │
│  [Dismiss] [Add to Notes] [Copy]              │
└──────────────────────────────────────────────┘
```

- Appears as a small panel next to abnormal results
- One-tap "Add to Notes" appends to clinical documentation
- No full-screen chat, no typing, no waiting

#### AI Order Suggestions

- When doctor types clinical description, AI suggests tests
- Appears as a card below the search input
- One-tap "Accept All" or individual selection

#### AI Summary on Patient Profile

- "Summarize last 6 months" button on timeline
- Generates concise clinical summary
- One-tap "Add to Report"

#### What to Remove

- `GlobalAiAssistant.tsx` — replace with inline AI
- `AISummary.tsx` — replace with inline AI
- `ExplainableAI.tsx` — fake data, remove
- `DashboardInsight.tsx` — fake data, remove

---

## 6. Component Library

### Enterprise DataGrid

```tsx
<DataGrid
  columns={[
    { key: 'name', title: 'Name', width: 200, pinned: true },
    { key: 'id', title: 'ID', width: 120 },
    { key: 'status', title: 'Status', width: 100, render: StatusBadge },
  ]}
  data={patients}
  onRowClick={openPatient}
  sortable
  filterable
  resizable
  virtualized
  bulkActions={['assign', 'export', 'delete']}
/>
```

Features:
- Column resize, reorder, show/hide
- Multi-sort
- Text filter per column
- Row selection with Shift+click
- Bulk action bar
- Virtual scrolling
- Sticky header + pinned columns
- Inline row expansion
- Export to CSV/PDF
- Saved views

### Clinical Card

```tsx
<ClinicalCard
  patient={patient}
  variant="result" // result | order | alert | appointment
  status="critical"
  onClick={handleClick}
  actions={[<Button>Review</Button>]}
/>
```

### Status Badge

```tsx
<StatusBadge
  value="High"
  variant="warning" // success | info | warning | critical
/>
```

### Smart Form

```tsx
<SmartForm
  fields={[
    { key: 'name', label: 'Name', required, autoFocus },
    { key: 'phone', label: 'Phone', mask: '+964 ### ### ####' },
    { key: 'city', label: 'City', suggestions: ['Baghdad', 'Basrah', 'Erbil'] },
  ]}
  onSubmit={handleSubmit}
  autoSave
  undo
/>
```

### Toast

```tsx
<Toast
  message="Patient registered successfully"
  variant="success" // success | error | warning | info
  action={{ label: 'Undo', onClick: handleUndo }}
  duration={5000}
/>
```

### Empty State

```tsx
<EmptyState
  icon={SearchIcon}
  title="No results found"
  description="Try adjusting your search or filters"
  action={{ label: 'Clear filters', onClick: clearFilters }}
/>
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

| Task | Files | Effort |
|------|-------|--------|
| Remove all fabricated clinical data | 17 components | 2d |
| Wire simulated saves to real persistence | ClinicalNotes, ResultEntryUI | 2d |
| Remove TopBar fake telemetry | TopBar.tsx | 0.5d |
| Remove GlobalAiAssistant (replace with inline) | GlobalAiAssistant.tsx | 1d |
| Remove Sidebar "Network Interlink" panel | Sidebar.tsx | 0.5d |
| Remove BiometricStatus, DashboardInsight, OrganAnalysis | 3 components | 0.5d |
| Remove NeuralConnectivityHub, QuantumHealthGrid, DigitalTwinSimulation | 3 components | 0.5d |

### Phase 2: Design System (Week 3-4)

| Task | Files | Effort |
|------|-------|--------|
| Define design tokens in CSS | index.css | 1d |
| Build `DataGrid` component | New file | 3d |
| Build `ClinicalCard` component | New file | 1d |
| Build `StatusBadge` component | New file | 0.5d |
| Build `SmartForm` component | New file | 2d |
| Build `EmptyState` component | New file | 0.5d |
| Build `Skeleton` component | New file | 0.5d |
| Build `Toast` component (replace sonner) | New file | 1d |
| Build `ConfirmDialog` component | New file | 0.5d |
| Build `FocusTrap` hook | New file | 0.5d |
| Build `useReducedMotion` hook | New file | 0.5d |
| Build `useAriaLive` hook | New file | 0.5d |

### Phase 3: Navigation (Week 5)

| Task | Files | Effort |
|------|-------|--------|
| Redesign top bar (search + user menu only) | TopBar.tsx | 1d |
| Remove fixed sidebar, make transient | Sidebar.tsx, App.tsx | 2d |
| Upgrade CommandPalette to Spotlight-style | CommandPalette.tsx | 2d |
| Add context-aware navigation | App.tsx | 1d |
| Add recent items tracking | New service | 1d |

### Phase 4: Screen Redesigns (Week 6-8)

| Task | Files | Effort |
|------|-------|--------|
| Redesign DashboardView (wing-specific) | DashboardView.tsx + wing views | 3d |
| Redesign RecordsView (DataGrid) | RecordsView.tsx | 2d |
| Redesign WorkQueue (Kanban) | WorkQueue.tsx | 3d |
| Redesign LabResultsView (results grid) | LabResultsView.tsx | 2d |
| Redesign PatientProfile (timeline) | PatientProfile.tsx | 2d |
| Redesign LandingAuthView (split) | LandingAuthView.tsx | 1d |
| Redesign SettingsView | SettingsView.tsx | 1d |
| Redesign CitizenHealth | CitizenHealth.tsx | 2d |

### Phase 5: Accessibility (Week 9)

| Task | Files | Effort |
|------|-------|--------|
| Add ARIA labels to all interactive elements | All views | 3d |
| Add focus traps to all modals | 6 components | 1d |
| Add keyboard navigation to all tables | All table views | 2d |
| Add `aria-live` regions | Contexts, views | 1d |
| Add `prefers-reduced-motion` | All animated components | 1d |
| Add screen-reader-only text | All icon-only buttons | 1d |
| Add color-blind-friendly indicators | All status indicators | 1d |
| Test with screen reader | All views | 2d |

### Phase 6: Performance & Polish (Week 10)

| Task | Files | Effort |
|------|-------|--------|
| Add skeleton loading to all views | All views | 2d |
| Add empty states to all views | All views | 1d |
| Add optimistic UI to all mutations | Services + views | 2d |
| Add undo support | SmartForm, DataGrid | 1d |
| Add auto-save to all forms | SmartForm | 1d |
| Add keyboard shortcuts to all views | All views | 2d |
| Mobile responsive pass | All views | 2d |

### Total Estimated Effort: 60 person-days (3 engineers × 4 weeks)

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Visual complexity | High | Minimal | Designer review |
| Clicks per task | ~8 | ~3 | User testing |
| Form fields per task | ~12 | ~5 | Code review |
| Modal usage | ~15 screens | ~3 screens | Code review |
| WCAG compliance | 0% | AA (target AAA) | Automated audit |
| ARIA attributes | ~5 | ~500 | Linter |
| Keyboard shortcuts | 8 global | 30+ global + local | Code review |
| Fake clinical data components | 17 | 0 | Code review |
| Skeleton loading states | 0 | 35 views | Code review |
| Empty states | 10 | 35 views | Code review |
| Confirmation dialogs | 0 | 5+ dangerous actions | Code review |
| Undo support | 1 component | All forms + tables | Code review |
| Auto-save | 0 forms | All forms | Code review |
| DataGrid features | 3 | 15+ | Feature checklist |

---

## Final Word

This is not a UI refresh.

This is a fundamental experience redesign.

Every component, every screen, every workflow has been questioned from first principles.

The result will be a platform that:

- A doctor can review 200+ results in 5 minutes (not 20)
- A lab tech can enter results without touching a mouse
- A patient understands their health in 30 seconds
- A ministry official sees national trends instantly
- A new user is productive in 10 minutes (not 2 days)
- Every interaction feels instant, clear, and safe

The interface disappears.

The work becomes the focus.

**This is the world's best healthcare experience.**
