# GULA Platform — Zero Redesign

**Author**: CPO / CXO / Principal UX Architect  
**Version**: 1.0  
**Philosophy**: Zero philosophy — zero clicks, zero windows, zero friction, zero confusion

---

## Table of Contents

1. [Zero Philosophy Applied](#1-zero-philosophy-applied)
2. [Screen Elimination](#2-screen-elimination)
3. [Navigation: Zero Navigation](#3-navigation-zero-navigation)
4. [Workflows: Zero Friction](#4-workflows-zero-friction)
5. [Screen-by-Screen Redesign](#5-screen-by-screen-redesign)
6. [AI: Everywhere, Invisible](#6-ai-everywhere-invisible)
7. [Design System](#7-design-system)
8. [Trust Architecture](#8-trust-architecture)
9. [Clinical Safety System](#9-clinical-safety-system)
10. [Accessibility: WCAG AAA](#10-accessibility-wcag-aaa)
11. [Implementation Roadmap](#11-implementation-roadmap)
12. [Success Metrics](#12-success-metrics)

---

## 1. Zero Philosophy Applied

### Zero Windows

| Current | Target | Reduction |
|---------|--------|-----------|
| 35+ view screens | 12 core experiences | 66% |
| 6 modal types | 2 modal types | 67% |
| Fixed sidebar | Transient overlay | 100% of nav chrome |
| 4 floating assistants | 1 contextual AI panel | 75% |

### Zero Clicks

| Workflow | Current clicks | Target clicks | Reduction |
|----------|---------------|---------------|-----------|
| View critical result | 4 | 0 (auto-push) | 100% |
| Enter lab result | 12 | 3 (keyboard only) | 75% |
| Find patient | 5 | 1 (type name) | 80% |
| Create order | 8 | 1 (AI suggestion) | 87% |
| Switch between wings | 2 | 0 (auto-context) | 100% |
| Review patient history | 4 | 1 (timeline) | 75% |

### Zero Redundancy

Every piece of data appears exactly once. No duplicate patient headers. No redundant status badges. No information repeated in cards and tables.

### Zero Thinking

Every screen is self-explanatory. No training required. The interface reveals what to do next through clear visual hierarchy and progressive disclosure.

---

## 2. Screen Elimination

### Current Screen Inventory

The app has 35+ distinct views. Most can be eliminated, merged, or reduced to inline panels.

| Current Screen | Fate | Rationale |
|----------------|------|-----------|
| LandingAuthView | **Keep** (redesign) | Necessary entry point |
| DashboardView | **Merge** → wing landing | One generic dashboard becomes 6 role-specific landing screens |
| RecordsView | **Merge** → universal search | Patient list becomes search results |
| AppointmentsView | **Merge** → calendar panel | Becomes a side drawer from any screen |
| LabResultsView | **Merge** → patient timeline | Results are part of patient record, not a separate view |
| LabIntelligenceView | **Remove** | Fake data, no real value |
| ImagingLabView | **Remove** | No real imaging integration |
| LabDashboard | **Keep** (redesign) | Lab-specific landing |
| WorkQueue | **Keep** (redesign) | Core lab workflow |
| DeviceMonitoring | **Remove** | Fake data, no real device integration |
| InventoryManagement | **Keep** (simplify) | Real lab inventory |
| SampleTracking | **Keep** (simplify) | Real lab workflow |
| QualityControl | **Keep** (simplify) | Real lab workflow |
| DoctorIntelligence | **Merge** → patient timeline | AI suggestions appear in-context |
| PatientProfile | **Keep** (redesign) | Core clinical view |
| CitizenHealth | **Merge** → patient portal | Single citizen home screen |
| CitizenDashboard | **Merge** → patient portal | Merged into one citizen experience |
| CitizenAssistant | **Remove** | No chatbot — AI is everywhere, invisible |
| PatientRegistration | **Keep** (simplify) | Essential onboarding |
| IdentityVerificationView | **Remove** | Part of registration flow, not a screen |
| ConsentManagementView | **Merge** → settings drawer | Inline toggles, not a full view |
| MedicalHistoryView | **Merge** → patient timeline | Part of patient record |
| SmartResultsView | **Merge** → patient timeline | Part of patient record |
| FamilyManagement | **Remove** | Not implemented, no real data |
| MedicationCenter | **Keep** (simplify) | Real medication management |
| AuditLog | **Keep** (simplify) | Regulatory requirement |
| SystemsArchitectureView | **Remove** | Fake data |
| InfrastructureView | **Remove** | Fake data |
| IntegrationHub | **Remove** | Fake data |
| NationalHealthGrid | **Keep** (simplify) | Ministry requirement |
| EpidemiologicalIntelligence | **Keep** (simplify) | Ministry requirement |
| DataSovereigntyAudit | **Keep** (simplify) | Ministry requirement |
| MinistryDashboard | **Merge** → ministry landing | Part of ministry experience |
| ResearcherDashboard | **Keep** (simplify) | Research portal |
| SettingsView | **Keep** (simplify) | Essential |

**Result**: 35 screens → 18 screens + 6 inline panels. 49% reduction.

### New Screen Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     PLATFORM SHELL                        │
│  [🔍 Universal Search]                    [👤] [🌐] [⚙] │
├──────────────────────────────────────────────────────────┤
│                                                           │
│   Only ONE of these is visible at a time:                 │
│                                                           │
│   1. AUTH        → Sign In / Register (split view)        │
│   2. LANDING     → Role-specific dashboard               │
│   3. PATIENT     → Timeline + results + orders            │
│   4. LAB QUEUE   → Kanban workboard                       │
│   5. LAB ENTRY   → Keyboard-first result entry            │
│   6. LAB OPS     → Inventory / Samples / QC               │
│   7. MINISTRY    → National health overview               │
│   8. RESEARCH    → Analytics workspace                     │
│   9. CITIZEN     → Health summary portal                   │
│   10. AUDIT      → Immutable log viewer                    │
│   11. SETTINGS   → Profile + preferences                   │
│                                                           │
├──────────────────────────────────────────────────────────┤
│  [Status: Online  •  Synced 2m ago  •  v2.1.0]           │
└──────────────────────────────────────────────────────────┘
```

**Inline Panels (not screens)**:
- Calendar (appointments) — side drawer
- Consent settings — settings drawer
- Medical history timeline — part of patient view
- Smart results — part of patient view
- AI suggestions — inline in relevant context
- Notifications — side drawer

---

## 3. Navigation: Zero Navigation

### Philosophy

The user should never "navigate" to anything.

- The system should bring the right screen to the user
- The user should type what they need (Universal Search)
- The system should predict what they need next

### Navigation Model

```
┌──────────────────────────────────────────────────────────┐
│  🔍  Search patients, orders, tests, commands...   [⌘K] │
│  ───────────────────────────────────────────────────────│
│  Recent / Predicted                                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │ ► Ahmed Hasan — Critical result (CRP: 85)   🔴  │   │
│  │ ► Zainab Ali — Pending review                   │   │
│  │ ► Lab Queue — 23 pending                        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  Quick Actions                                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │ > New Order  │ > New Patient  │ > Critical Alert │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Context Switching (Wing Switching)

The user's role determines their landing screen. Switching wings:

1. Type `@doctor`, `@lab`, `@citizen`, `@ministry` in search — OR —
2. System auto-switches based on context (viewing a patient record → doctor mode)

No sidebar. No wing selector. No tabs. The system knows what you need.

### Keyboard-Only Navigation

| Key | Action |
|-----|--------|
| `⌘K` | Universal search (always open) |
| `⌘1-9` | Quick actions (customizable) |
| `⌘Enter` | Confirm / Submit |
| `Escape` | Close panel / Deselect / Go back |
| `↑ ↓` | Navigate lists |
| `Tab` | Next field / Next section |
| `Shift+Tab` | Previous field |
| `Space` | Select / Toggle / Claim next work item |
| `Enter` | Open selected item |
| `⌘Z` | Undo |
| `⌘Shift+Z` | Redo |
| `⌘S` | Save (auto-save also active) |
| `⌘F` | Find in page |
| `?` | Show shortcuts |

---

## 4. Workflows: Zero Friction

### 4.1 Lab Result Entry — Current vs Target

**Current**: 12 clicks, form with mouse, 4 panels, fake AI sidebar, fake device monitor, simulated save.

**Target**: 3 keystrokes, keyboard-only, no navigation, no mouse, instant save.

```
┌────────────────────────────────────────────────┐
│  Result Entry — CBC (Ahmed Hasan)              │
│  ──────────────────────────────────────────────│
│  WBC    [11.2]  ████████░░  H  4.0-10.0  ↑2.4│
│  Hb     [13.5]  ██████████  █  12.0-16.0      │
│  PLT    [450]   ██████████  █  150-400         │
│  NEUT%  [75]    ██████████  H  40-70     ↑5   │
│  LYM%   [18]    ████░░░░░░  L  20-40     ↓5   │
│  ──────────────────────────────────────────────│
│  [Tab] Next  [Ctrl+Enter] Save & Next  [Esc]   │
└────────────────────────────────────────────────┘
```

**Principles**:
- Keyboard-only: Tab between fields, type values, Ctrl+Enter to save
- Automatic validation: out-of-range values highlighted immediately
- Delta shown: previous value and change direction
- Auto-save: each row saved on blur
- Hide irrelevant panels: no AI sidebar, no device monitor, no fake metrics
- Sound: optional beep on critical value entry

### 4.2 Patient Lookup — Current vs Target

**Current**: Navigate to RecordsView → click search → type → click result → click through tabs.

**Target**: Type name from anywhere → inline preview.

```
Any screen → ⌘K
┌──────────────────────────────────────────────┐
│  🔍  ahm                                       │
│  ────────────────────────────────────────────│
│  Patients                                      │
│  ┌─────────────────────────────────────────┐  │
│  │ Ahmed Hasan    045-XX-XXXX  3 visits    │  │
│  │ Ahmed Khalil   046-XX-XXXX  1 visit     │  │
│  │ Ahmadi Saleh   047-XX-XXXX  New         │  │
│  └─────────────────────────────────────────┘  │
│  → Select → Opens inline (not new page)       │
└──────────────────────────────────────────────┘
```

### 4.3 Order Creation — Current vs Target

**Current**: Navigate to orders → fill form → search tests → select → submit → wait.

**Target**: Describe clinical need → AI suggests → one-click accept.

```
┌──────────────────────────────────────────────┐
│  New Order                                    │
│  Patient: Ahmed Hasan                         │
│  ────────────────────────────────────────────│
│  Describe clinical presentation:              │
│  ┌────────────────────────────────────────┐   │
│  │ Patient with fatigue, weight loss,     │   │
│  │ polyuria. Suspect diabetes.            │   │
│  └────────────────────────────────────────┘   │
│                                               │
│  AI suggests:                                 │
│  ☑ Fasting Glucose     ☑ HbA1c               │
│  ☑ Urinalysis          ☑ TSH                  │
│                                               │
│  [Accept All]  [Edit]  [Dismiss]              │
└──────────────────────────────────────────────┘
```

### 4.4 Patient Registration — Current vs Target

**Current**: 8 steps (role → form → identity → medical → consent → OTP → success).  
**Target**: 2 steps (basic info → done). Everything else is progressive.

| Step | Action | Notes |
|------|--------|-------|
| 1 | Name + DOB + Phone | Auto-saves. AI predicts city from phone prefix. |
| 2 | Done | Share QR code. Identity verification optional later. |

### 4.5 Lab Queue Management — Current vs Target

**Current**: Card list with tabs, click to claim, click to enter, click to complete.

**Target**: Kanban board, keyboard-only, Space to claim, drag to move.

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   PENDING    │   IN WORK    │   REVIEW     │  COMPLETED   │
│      23      │      12      │       8      │     189      │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ CBC-201 🔴H │ CBC-205 🟢   │ CBC-210 🟢   │ ► View       │
│ ⏰ 14min     │ ⏰ 22min     │ 45min ago    │   today's    │
│              │              │              │   results    │
│ LFT-202 🔴H │ LFT-206 🟡H  │ LFT-211 🟢   │              │
│ ⏰ 8min      │ 35min        │ 1h ago       │              │
│              │              │              │              │
│ [Space] Next │ [Enter] Open │ [Drag] Move  │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### 4.6 Critical Alert Response — Current vs Target

**Current**: Alert appears → read → navigate to patient → review → take action.

**Target**: Alert pushes → one-click action from alert.

```
🔴 CRITICAL RESULT: CRP 85 mg/L
   Ahmed Hasan — CBC-2024-0842
   [View] [Acknowledge] [Notify Doctor]

   (Appears as toast, floating. Does not block work.)
```

---

## 5. Screen-by-Screen Redesign

### 5.1 Auth Screen (LandingAuthView)

**Current**: Single-page vertical scroll with 9 auth steps, demo role buttons, password strength indicator, identity verification, OTP, biometric, forgot password. Cognitive overload.

**Target**: Split screen. Brand on left. Minimal form on right.

```
┌─────────────────────┬──────────────────────────┐
│                     │                          │
│   GULA              │  Sign in                 │
│   Healthcare        │  ┌──────────────────────┐│
│   Intelligence      │  │ Email                ││
│   Platform          │  └──────────────────────┘│
│                     │  ┌──────────────────────┐│
│   [Arabic-first]    │  │ Password             ││
│   [Iraq]            │  └──────────────────────┘│
│                     │                          │
│   [QR Login]        │  [Sign In]  [Register]   │
│   [Biometric]       │                          │
│                     │  ── or ──               │
│                     │  [Fingerprint] [QR]      │
│                     │                          │
└─────────────────────┴──────────────────────────┘
```

**Changes**:
- Remove: demo role buttons (hardcoded credentials removed)
- Remove: identity verification, medical migration, forgot_password (move to post-login)
- Remove: PasswordStrength component (unnecessary complexity)
- Remove: decorative illustrations
- Add: `role="presentation"` on brand panel
- Add: `aria-label` on all inputs
- Add: inline validation on blur
- Add: biometric autofill detection
- Files: `LandingAuthView.tsx` — rewrite completely

### 5.2 Doctor Landing (replaces DashboardView + DoctorIntelligence)

**Current**: Generic DashboardView with fake charts, fake AI insights, NeuralConnectivityHub, QuantumHealthGrid. Zero actionable information.

**Target**: Triage-first landing with three sections: urgent, today's work, search.

```
┌──────────────────────────────────────────────────────────┐
│  Good morning, Dr. Ali                  🟢 12 online     │
│  ────────────────────────────────────────────────────────│
│  🔴 REQUIRES ATTENTION                                    │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 🔴 CRP 85 — Ahmed Hasan — Just now              │    │
│  │ 🟡 HbA1c 6.2 — Zainab Ali — 30m ago (↑from 5.8)│    │
│  │ 🟡 WBC 11.2 — Sajjad Karim — 2h ago (↑from 9.8)│    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  TODAY'S PATIENTS                                         │
│  ┌──────────────┬──────────┬──────────┬─────────────┐    │
│  │ Ahmed Hasan  │ CBC      │ 🟡 Anomaly│ 30m ago    │    │
│  │ Zainab Ali   │ Follow-up│ 🟢 Stable │ 2h ago     │    │
│  │ Sara Mohsin  │ New      │ 📋 Pending│ Scheduled   │    │
│  └──────────────┴──────────┴──────────┴─────────────┘    │
│                                                           │
│  🔍 [⌘K] Search patients, orders, everything...          │
└──────────────────────────────────────────────────────────┘
```

**Changes**:
- Remove: NeuralConnectivityHub, QuantumHealthGrid, BiometricStatus, DashboardInsight
- Remove: OrganAnalysis, DigitalTwinSimulation, PredictiveAnalytics
- Remove: fake AI metrics, fake bio-grid, fake biometrics
- Remove: GlobalAiAssistant (replace with inline AI)
- Focus: urgent results → today's patients → search
- Files: `DashboardView.tsx` — rewrite

### 5.3 Patient Profile (PatientProfile)

**Current**: Tabbed form with patient details, orders, results, history. Multiple navigation levels.

**Target**: Apple Health-style timeline. Single scroll. Inline expand.

```
┌─────────────────────────────────────────────────────┐
│  ← Back                                            │
│  Ahmed Hasan    045-XX-XXXX    35 yrs    Male       │
│  ──────────────────────────────────────────────────│
│  Timeline (All events for Ahmed Hasan)              │
│  ┌─────────────────────────────────────────────┐   │
│  │ 🔴 Today 14:30 — Critical Result            │   │
│  │ CRP: 85 mg/L (H), WBC: 11.2 (H)           │   │
│  │ View: CBC-2024-0842  [🤖 Explain]         │   │
│  ├─────────────────────────────────────────────┤   │
│  │ 🩺 Yesterday 10:00 — Appointment            │   │
│  │ Dr. Ali — Follow-up: HbA1c trending up      │   │
│  │ Notes: "Patient reports increased thirst"   │   │
│  ├─────────────────────────────────────────────┤   │
│  │ 💊 3 days ago — Medication Change           │   │
│  │ Metformin 500mg → 1000mg daily              │   │
│  │ Reason: HbA1c not at target (6.2%)         │   │
│  ├─────────────────────────────────────────────┤   │
│  │ 📋 1 week ago — Lab Order                   │   │
│  │ CBC + LFT + HbA1c + TSH                    │   │
│  │ Ordered by: Dr. Ali                          │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  [🤖 AI Summary] [⬇ Export] [➕ New Order]          │
└─────────────────────────────────────────────────────┘
```

**Changes**:
- Remove: tab navigation (Details | Orders | Results | History)
- Remove: separate LabResultsView (results are part of timeline)
- Remove: separate MedicalHistoryView (part of timeline)
- Remove: separate AppointmentsView (part of timeline)
- Replace: chronological timeline as single source of truth
- Add: inline expand for details
- Add: AI explanation on abnormal results
- Add: quick action buttons
- Keyboard: `J/K` to navigate timeline items, `Enter` to expand
- Files: `PatientProfile.tsx` — rewrite

### 5.4 Lab Work Queue (WorkQueue)

**Current**: Card list with tabs (Pending, In Progress, Completed, All). Each card is a large box with multiple icons. Bulk checkboxes. Simulated saves.

**Target**: Kanban board. Three columns. Minimal cards. Keyboard-first.

```
┌──────────────┬────────────────┬──────────────┬──────────────┐
│   PENDING    │   IN PROGRESS  │   REVIEW     │  COMPLETED   │
│      23      │       12       │      8       │     189      │
├──────────────┼────────────────┼──────────────┼──────────────┤
│ CBC-201 🔴  │ CBC-205       │ CBC-210      │ View today's │
│ Ahmed H.    │ Sara M.       │ Zainab A.    │              │
│ ⏰ 14min     │ ⏰ 22min       │ 45min ago    │              │
│──────────────┼────────────────┼──────────────┤              │
│ LFT-202 🔴  │ LFT-206 🟡   │ LFT-211      │              │
│ Basim K.    │ Ali H.        │ Omar S.      │              │
│ ⏰ 8min      │ 35min         │ 1h ago       │              │
└──────────────┴────────────────┴──────────────┴──────────────┘
│  [Space] Claim next  [Tab] Focus column  [Drag] Reorder    │
```

**Changes**:
- Remove: tabs (replaced by columns)
- Remove: large card animations (replace with compact rows)
- Remove: decorative icons (keep only status-critical ones)
- Remove: bulk checkbox UI (drag-and-drop replaces)
- Add: Kanban columns
- Add: drag-and-drop between columns
- Add: keyboard-only workflow (Space to claim next pending)
- Add: TAT countdown timers with visual urgency
- Add: real-time WebSocket updates
- Files: `WorkQueue.tsx` — rewrite

### 5.5 Lab Dashboard (LabDashboard)

**Current**: Multi-panel dashboard with charts, AI insights, device monitor, stats, and simulated metrics. Cognitive overload.

**Target**: Three-section landing: urgency, capacity, queue.

```
┌──────────────────────────────────────────────────────────┐
│  Lab Dashboard — Baghdad Central Lab                      │
│  ────────────────────────────────────────────────────────│
│  📥 23 Pending    🔬 45 In Progress    ✅ 189 Today      │
│  ────────────────────────────────────────────────────────│
│  CRITICAL PRIORITY                                        │
│  ┌──────┬────────────┬──────────┬────────┬─────────────┐ │
│  │ STAT │ CBC-23041  │ Ahmed H.│ ⏰ 14min│   ▶▶▶       │ │
│  │ STAT │ LFT-23042  │ Zainab A│ ⏰ 8min │   ▶▶▶       │ │
│  │ HIGH │ CRP-23043  │ Sara M. │ 22min   │   ▶▶        │ │
│  └──────┴────────────┴──────────┴────────┴─────────────┘ │
│                                                           │
│  INSTRUMENT STATUS                                        │
│  🟢 CBC Analyzer — Online      — 45 samples queued       │
│  🟢 Chemistry — Online          — 32 samples queued       │
│  🟡 Hematology — Maintenance    — ⏰ 15min                 │
│                                                           │
│  [Tab] Enter result entry mode                            │
└──────────────────────────────────────────────────────────┘
```

**Changes**:
- Remove: fake charts (PredictiveAnalytics, LabStatsTrends fake data)
- Remove: LabDeviceMonitor fake calibration data
- Remove: AI sidebar with hardcoded insights
- Remove: NeuralConnectivityHub
- Focus: pending queue → instrument status → quick entry
- Add: real-time instrument status (from actual device bridge)
- Add: quick entry button with keyboard shortcut
- Files: `LabDashboard.tsx` — rewrite

### 5.6 Citizen Portal (CitizenHealth + CitizenDashboard + SmartResultsView)

**Current**: Three separate views. CitizenDashboard has fake health scores. CitizenHealth has fake apps. SmartResultsView has AI chatbot.

**Target**: Single citizen home screen.

```
┌──────────────────────────────────────────────────────┐
│  مرحباً أحمد   Health Score: 85/100    🟢 Synced    │
│  ───────────────────────────────────────────────────│
│  NEEDS ATTENTION                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │ 🔴 New critical result: CRP 85 mg/L          │   │
│  │    ⚠ Requires immediate attention            │   │
│  │    [View] [Share with Doctor]                 │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  UPCOMING                                            │
│  ┌──────────────────────────────────────────────┐   │
│  │ 🩺 Appointment: Dr. Ali — Tomorrow 10:00 AM   │   │
│  │ 💊 Medication due: Metformin 1000mg — Now     │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  RECENT RESULTS                                      │
│  ┌──────────┬──────────┬──────┬─────────────────┐   │
│  │ HbA1c    │ 6.2%     │ 🟡 H │ Last week       │   │
│  │ Glucose  │ 95       │ 🟢   │ 2 weeks ago     │   │
│  │ CRP      │ 85       │ 🔴 H │ Today — NEW     │   │
│  └──────────┴──────────┴──────┴─────────────────┘   │
│                                                      │
│  [View All Results] [🤖 Ask About My Health]         │
└──────────────────────────────────────────────────────┘
```

**Changes**:
- Remove: CitizenDashboard (merged into one)
- Remove: GlobalAiAssistant (replaced by inline "Ask" button)
- Remove: OrganAnalysis, DigitalTwinSimulation, PredictiveAnalytics
- Remove: fake health metrics, fake apps
- Add: unified citizen home with urgency → upcoming → recent
- Add: inline AI button ("Ask About My Health") that opens contextual panel
- Add: sync indicator
- Files: `CitizenHealth.tsx` — rewrite (merge 3 views)

### 5.7 Settings (SettingsView)

**Current**: Tabs, clinical mode switcher, low bandwidth toggle, system diagnostics, decorative animations.

**Target**: Three sections. No tabs. No decoration.

```
┌──────────────────────────────────────────────────────┐
│  Settings                                             │
│  ────────────────────────────────────────────────────│
│  Profile                                              │
│  Name          ┌────────────────────────────────┐    │
│  Email         └────────────────────────────────┘    │
│  Language      [العربية ▾]                           │
│  ────────────────────────────────────────────────────│
│  Notifications                                       │
│  □ Critical alerts          [🔔 Push] [📧 Email]     │
│  □ Result available         [🔔 Push] [📧 Email]     │
│  □ Appointment reminder     [🔔 Push] [📧 Email]     │
│  ────────────────────────────────────────────────────│
│  Security                                            │
│  [Manage Biometrics]   [Active Sessions]             │
│  ────────────────────────────────────────────────────│
│  About                                               │
│  Version 2.1.0   •   GULA Platform                   │
└──────────────────────────────────────────────────────┘
```

**Changes**:
- Remove: Clinical Mode switcher (cosmetic, no backend effect)
- Remove: Low Bandwidth toggle (cosmetic)
- Remove: System Diagnostics drawer trigger
- Remove: Tabs
- Remove: decorative animations
- Add: inline editing on click
- Add: `aria-label` on all controls
- Files: `SettingsView.tsx` — rewrite

### 5.8 Ministry Dashboard (NationalHealthGrid + MinistryDashboard)

**Current**: Two separate views with fake national metrics, fake autonomous alerts, AI marketplace.

**Target**: Single national health overview with real data.

```
┌──────────────────────────────────────────────────────────┐
│  National Health Overview        Iraq      Last sync: now │
│  ────────────────────────────────────────────────────────│
│  NATIONAL METRICS                                         │
│  ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬────┐ │
│  │ Prov │ Tests│ Crit│ Pending│ Avg TAT│ Beds│ Census│   │
│  ├──────┼──────┼──────┼──────┼──────┼──────┼──────┼────┤ │
│  │Bgdad │1,234 │ 12  │ 45   │ 2.4h  │ 1,200│ 65%  │   │
│  │Basrah│ 892  │ 8   │ 23   │ 3.1h  │ 650  │ 72%  │   │
│  │Erbil │ 456  │ 3   │ 12   │ 1.8h  │ 400  │ 58%  │   │
│  │Mosul │ 678  │ 7   │ 34   │ 4.2h  │ 800  │ 78%  │   │
│  │Nineve│ 234  │ 5   │ 18   │ 3.8h  │ 350  │ 71%  │   │
│  └──────┴──────┴──────┴──────┴──────┴──────┴──────┴────┘ │
│                                                           │
│  ALERTS                                                   │
│  ┌───────────────────────────────────────────────────┐   │
│  │ 🟡 Mosul — TAT exceeding threshold (4.2h > 3.0h) │   │
│  │ 🟢 Erbil — All systems nominal                    │   │
│  └───────────────────────────────────────────────────┘   │
│                                                           │
│  [⬇ Export Report]  [🔍 Search by province]              │
└──────────────────────────────────────────────────────────┘
```

**Changes**:
- Remove: fake SLA percentages, fake autonomous alerts, AI marketplace
- Remove: MinistryCommandCenter fake data
- Remove: EpidemiologicalIntelligence fake outbreak predictions
- Add: real provincial metrics from national database
- Add: real-time sync indicator
- Add: exportable reports
- Files: `NationalHealthGrid.tsx`, `MinistryDashboard.tsx` — rewrite/merge

### 5.9 Audit Log (AuditLog)

**Current**: Table with search, filter, integrity hash. Hardcoded actor name. Good semantics but no loading state.

**Target**: Enterprise audit viewer.

```
┌──────────────────────────────────────────────────────────┐
│  Audit Log                         [Filter] [⬇ Export]   │
│  ────────────────────────────────────────────────────────│
│  ┌──────┬──────────┬──────────┬──────────┬──────────────┐│
│  │ Time │ Actor    │ Action   │ Resource │ Integrity    ││
│  ├──────┼──────────┼──────────┼──────────┼──────────────┤│
│  │14:30 │ Dr. Ali  │ RESULT_  │ CBC-0842 │ 🔒 Verified  ││
│  │      │          │ CREATED  │          │ SHA256: abc  ││
│  │14:28 │ System   │ ORDER_   │ ORD-2301 │ 🔒 Verified  ││
│  │      │          │ UPDATED  │          │ SHA256: def  ││
│  │14:25 │ Nurse    │ PATIENT_ │ 045-XX   │ 🔒 Verified  ││
│  │      │ Sara     │ UPDATED  │          │ SHA256: ghi  ││
│  └──────┴──────────┴──────────┴──────────┴──────────────┘│
│                                                           │
│  Showing 12 of 45,892 entries           [Load more ▾]    │
└──────────────────────────────────────────────────────────┘
```

**Changes**:
- Remove: hardcoded "Samer (Root)" — use actual user data
- Add: loading skeleton
- Add: infinite scroll
- Add: column sort
- Add: filter by actor, action, resource
- Add: export to CSV
- Files: `AuditLog.tsx` — minor improvements

### 5.10 Lab Operations (InventoryManagement + SampleTracking + QualityControl)

**Current**: Three separate views. Inventory has no inline edit. SampleTracking has no real data. QualityControl has no real QC data.

**Target**: Unified lab operations panel with tabless design.

```
┌──────────────────────────────────────────────────────────┐
│  Lab Operations                    🔍 Search reagents...  │
│  ────────────────────────────────────────────────────────│
│  [📦 Inventory]    [🧪 Samples]    [✅ QC]               │
│  ────────────────────────────────────────────────────────│
│  ┌──────┬────────────┬──────┬──────┬──────┬────────────┐ │
│  │ Item │ Lot        │ Qty  │ Exp  │ Status│ Actions    ││
│  ├──────┼────────────┼──────┼──────┼──────┼────────────┤│
│  │CRP   │ LOT-2301   │ 45   │12/24 │ 🟢   │ [Edit Qty] ││
│  │HbA1c │ LOT-2302   │ 12   │11/24 │ 🟡 L │ [Order]    ││
│  │CBC   │ LOT-2303   │ 0    │10/24 │ 🔴 O │ [Order Now]││
│  └──────┴────────────┴──────┴──────┴──────┴────────────┘│
│                                                           │
│  [Tab] Navigate sections  [Enter] Edit quantity           │
└──────────────────────────────────────────────────────────┘
```

**Changes**:
- Remove: three separate views → single unified panel
- Remove: fake device monitoring
- Add: inline quantity editing
- Add: reorder button with smart defaults
- Add: low-stock alerts (amber/orange/red threshold)
- Add: search across all operations
- Files: `InventoryManagement.tsx`, `SampleTracking.tsx`, `QualityControl.tsx` — merge

---

## 6. AI: Everywhere, Invisible

### Philosophy

AI is not a chatbot. AI is not a bubble in the corner. AI is everywhere the user works, embedded in the context of their current task.

### 6.1 Remove All Chatbot UI

| Component | Fate |
|-----------|------|
| `GlobalAiAssistant.tsx` | **Removed** — replaced with inline AI |
| `AISummary.tsx` | **Removed** — replaced with inline AI explainer |
| `CitizenAssistant.tsx` | **Removed** — replaced with "Ask AI" button |
| `AITriageAssistant.tsx` | **Removed** — AI suggestions embedded in doctor workflow |
| `ExplainableAI.tsx` | **Removed** — fake data, not real AI |

### 6.2 AI Integration Points

#### On Abnormal Results (Patient Timeline)

```
Result: CRP 85 mg/L (🔴 High)
─────────────────────────────
🤖 CRP is significantly elevated (>5 mg/L), suggesting
active inflammation or infection. Previous value (12 mg/L)
shows a sharp rise. Recommend: ESR, procalcitonin, blood culture.

[Dismiss] [Add to Notes] [Copy]
```

- Appears automatically on abnormal results
- One click "Add to Notes" appends to clinical documentation
- Does NOT require a separate chat window

#### On Order Creation

```
Describe clinical presentation:
┌──────────────────────────────────────────┐
│ Patient with fatigue, weight loss.       │
└──────────────────────────────────────────┘

🤖 Suggested tests:
☑ Fasting Glucose    ☑ HbA1c    ☑ TSH

[Accept All] [Edit] [Dismiss]
```

- AI suggests tests based on clinical description
- Appears after user stops typing (debounced)
- One click accept

#### On Patient Profile

```
[🤖 Summarize Last 6 Months]
```

- Button on patient profile
- Generates concise clinical summary
- Appears inline below the timeline
- One click "Add to Report"

#### On Search

```
🔍  "patient with high crp"
─────────────────────────────
Results:
- Ahmed Hasan — CRP: 85 (Critical)
- Zainab Ali — CRP: 12 (High)
```
- AI interprets natural language queries
- Understands clinical context

### 6.3 AI Safety

- Every AI output includes: `This is a decision support tool. Final clinical judgment rests with the licensed professional.`
- Temperature: 0.1 (low creativity, high determinism)
- PII stripped before API calls
- User must explicitly accept AI suggestions — never auto-execute

---

## 7. Design System

### 7.1 Design Tokens

```css
:root {
  /* Colors — semantic only */
  --color-success: #059669;
  --color-info: #2563eb;
  --color-warning: #d97706;
  --color-critical: #dc2626;
  --color-neutral: #64748b;

  /* UI */
  --color-bg: #ffffff;
  --color-surface: #f8fafc;
  --color-border: #e2e8f0;
  --color-text: #0f172a;
  --color-text-secondary: #64748b;
  --color-primary: #4f46e5;
  --color-primary-hover: #4338ca;

  /* Typography */
  --font-display: 2.25rem;
  --font-heading: 1.5rem;
  --font-subheading: 1.125rem;
  --font-body: 0.9375rem;
  --font-small: 0.8125rem;
  --font-tiny: 0.75rem;
  --font-family: 'Inter', 'Noto Naskh Arabic', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Cairo', monospace;

  /* Spacing — 4px grid */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;

  /* Shadows — minimal */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 2px 8px rgba(0,0,0,0.08);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);

  /* Animation */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
}
```

### 7.2 Component Architecture

```
src/components/
├── ui/                          # Design system primitives
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Select.tsx
│   ├── Textarea.tsx
│   ├── Badge.tsx
│   ├── Card.tsx
│   ├── Modal.tsx                # Only 2 modal types: Dialog, Sheet
│   ├── Drawer.tsx               # Side drawer
│   ├── Toast.tsx
│   ├── Tooltip.tsx
│   ├── Skeleton.tsx
│   ├── EmptyState.tsx
│   ├── ErrorState.tsx
│   ├── LoadingState.tsx
│   └── VisuallyHidden.tsx       # Screen-reader-only text
│
├── data/                        # Enterprise DataGrid
│   ├── DataGrid.tsx             # The one table to rule them all
│   ├── DataGridColumn.tsx
│   ├── DataGridRow.tsx
│   ├── DataGridFilter.tsx
│   ├── DataGridPagination.tsx
│   └── DataGridToolbar.tsx
│
├── form/                        # Smart Form system
│   ├── SmartForm.tsx
│   ├── FormField.tsx
│   ├── FormSection.tsx
│   └── FormActions.tsx
│
├── navigation/                  # Navigation primitives
│   ├── UniversalSearch.tsx      # Spotlight-style ⌘K
│   ├── CommandPalette.tsx
│   ├── TopBar.tsx
│   ├── Breadcrumbs.tsx
│   └── KeyboardShortcuts.tsx
│
├── patient/                     # Patient-related components
│   ├── PatientHeader.tsx
│   ├── PatientTimeline.tsx
│   ├── PatientResults.tsx
│   └── PatientInfo.tsx
│
├── lab/                         # Lab workflow components
│   ├── KanbanBoard.tsx
│   ├── KanbanColumn.tsx
│   ├── KanbanCard.tsx
│   ├── ResultEntry.tsx
│   └── InstrumentStatus.tsx
│
├── ai/                          # AI integration
│   ├── InlineAI.tsx             # Embedded AI suggestion
│   ├── AIExplainer.tsx          # Explain abnormal results
│   ├── AISummary.tsx            # Generate clinical summary
│   └── AIOrderSuggestion.tsx    # Suggest tests
│
├── trust/                       # Trust indicators
│   ├── SyncIndicator.tsx
│   ├── SaveIndicator.tsx
│   ├── OnlineStatus.tsx
│   └── AuditTrail.tsx
│
├── clinical/                    # Clinical safety
│   ├── CriticalValueAlert.tsx
│   ├── ConfirmDialog.tsx
│   ├── PatientIdentityCheck.tsx
│   └── DuplicatePrevention.tsx
│
└── layout/                      # Layout components
    ├── AppShell.tsx
    ├── PageHeader.tsx
    ├── PageContent.tsx
    ├── InspectorPanel.tsx
    └── StatusBar.tsx

(45 components — consolidated from 75+)
```

### 7.3 DataGrid Specification

```tsx
<DataGrid
  columns={[
    { key: 'patientName', title: 'Patient', width: 200, pinned: true, sortable: true, filterable: true },
    { key: 'testName', title: 'Test', width: 150, sortable: true },
    { key: 'result', title: 'Result', width: 100, sortable: true, render: (v) => <ResultBadge value={v} /> },
    { key: 'status', title: 'Status', width: 100, render: (v) => <StatusBadge variant={v} /> },
    { key: 'receivedAt', title: 'Received', width: 120, sortable: true },
  ]}
  data={items}
  pageSize={50}
  virtualized={true}
  stickyHeader={true}
  stickyColumns={1}
  onRowClick={handleRowClick}
  onSelectionChange={handleSelection}
  sortable={true}
  filterable={true}
  resizable={true}
  reorderable={true}
  bulkActions={[
    { label: 'Assign', action: handleAssign },
    { label: 'Export', action: handleExport },
  ]}
  emptyState={<EmptyState icon={Search} title="No results" description="Try adjusting filters" />}
  loading={<Skeleton rows={5} />}
/>
```

### 7.4 SmartForm Specification

```tsx
<SmartForm
  sections={[
    {
      title: 'Patient Information',
      fields: [
        { key: 'name', label: 'Full Name', required: true, autoFocus: true },
        { key: 'phone', label: 'Phone', type: 'tel', mask: '+964 ### ### ####' },
        { key: 'dob', label: 'Date of Birth', type: 'date' },
        { key: 'city', label: 'City', type: 'autocomplete', suggestions: cities },
      ],
    },
    {
      title: 'Clinical Details',
      fields: [
        { key: 'symptoms', label: 'Symptoms', type: 'textarea', aiAssist: true },
        { key: 'priority', label: 'Priority', type: 'select', options: ['Routine', 'Urgent', 'STAT'] },
      ],
    },
  ]}
  onSubmit={handleSubmit}
  onSave={handleAutoSave}
  autoSave={true}
  autoSaveInterval={5000}
  undo={true}
  validation="onBlur"
  keyboardNavigation={true}
/>
```

---

## 8. Trust Architecture

### 8.1 Trust Indicators

Every screen must show:

| Indicator | Where | What |
|-----------|-------|------|
| Save status | Every form | `Saved just now` / `Saving...` / `Failed to save` |
| Sync status | Status bar | `Synced 2m ago` / `Offline — 3 pending` |
| Online status | Status bar | `🟢 Online` / `🟡 Offline` |
| Last updated | Every data view | `Updated 5m ago` |
| Data source | Clinical data | `Source: Baghdad Central Lab` |
| Audit trail | Every record | `🔒 Audit logged` |
| User identity | Top bar | `👤 Dr. Ali Ahmed` |
| Version | Status bar | `v2.1.0` |

### 8.2 SyncIndicator Component

```
🟢 Synced 2 minutes ago
🟡 Syncing... (3 of 12)
🔴 Sync failed — Tap to retry
```

Shows in status bar. Always visible. Click for details.

### 8.3 SaveIndicator Component

```
Saved just now
Saving...
Changes saved offline (will sync when online)
Failed to save — [Retry]
```

Appears inline next to save button or form footer.

---

## 9. Clinical Safety System

### 9.1 Safety Principles

1. **Prevent wrong patient**: Patient identity must be confirmed before any clinical action
2. **Prevent duplicate submissions**: Debounce all submit buttons, disable after click
3. **Prevent accidental deletion**: No delete without confirmation. Require type-to-confirm for critical data.
4. **Highlight critical values**: Red background + bold + icon on all critical results
5. **Prevent specimen mix-up**: Barcode/QR verification before result entry
6. **Prevent medication errors**: Drug-drug interaction check, allergy check before prescription
7. **Prevent unauthorized actions**: Role-based access on every mutation

### 9.2 ConfirmDialog

```tsx
<ConfirmDialog
  open={showConfirm}
  onConfirm={handleConfirm}
  onCancel={handleCancel}
  title="Revoke consent?"
  description="This will remove Ahmed Hasan's consent to share data with the Ministry of Health. This action is reversible within 30 days."
  confirmLabel="Revoke consent"
  cancelLabel="Cancel"
  variant="danger" // 'danger' | 'warning' | 'info'
  requireTypeToConfirm="REVOKE" // optional, for dangerous actions
/>
```

### 9.3 CriticalValueAlert

```tsx
<CriticalValueAlert
  value={85}
  test="CRP"
  patient={patient}
  referenceRange="<5 mg/L"
  onAcknowledge={handleAck}
  onNotifyDoctor={handleNotify}
/>
```

Shows as a prominent banner (not a dismissible toast) for critical values. Requires explicit acknowledgement.

### 9.4 PatientIdentityCheck

Before any clinical action (order, result entry, prescription):

```tsx
<PatientIdentityCheck
  patient={patient}
  onVerified={handleVerified}
  method="name-dob" // 'name-dob' | 'barcode' | 'qr' | 'biometric'
/>
```

Shows patient name + DOB + ID with explicit confirmation checkbox.

---

## 10. Accessibility: WCAG AAA

### 10.1 Requirements

| Criterion | Current Status | Target |
|-----------|---------------|--------|
| Color contrast (text) | Unknown | 7:1 minimum |
| Color contrast (non-text) | Unknown | 3:1 minimum |
| Keyboard navigation | Partial | Complete |
| Focus indicators | None | 3px outline, high contrast |
| ARIA labels | None | Every interactive element |
| Screen reader support | None | All content accessible |
| Reduced motion | None | All animations respect `prefers-reduced-motion` |
| Zoom support | Unknown | 200% zoom no loss |
| Error identification | None | Clear error messages with suggestions |
| Headings hierarchy | None | Proper h1-h6 structure |
| Landmarks | Partial | All regions have roles |
| Touch targets | Unknown | Minimum 44x44px |

### 10.2 Implementation

**Global**:
```tsx
// useReducedMotion.ts
function useReducedMotion(): boolean {
  const mq = typeof window !== 'undefined'
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : null;
  const [reduced, setReduced] = useState(mq?.matches ?? false);
  useEffect(() => {
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq?.addEventListener('change', handler);
    return () => mq?.removeEventListener('change', handler);
  }, []);
  return reduced;
}
```

**Every modal**:
```tsx
// useFocusTrap.ts
function useFocusTrap(ref: RefObject<HTMLElement>, active: boolean) {
  useEffect(() => {
    if (!active) return;
    const el = ref.current;
    if (!el) return;
    const focusable = el.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    first?.focus();
    function handleTab(e: KeyboardEvent) {
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    }
    el.addEventListener('keydown', handleTab);
    return () => el.removeEventListener('keydown', handleTab);
  }, [active]);
}
```

**Every icon button**:
```tsx
<button aria-label="Close dialog">
  <XIcon aria-hidden="true" />
</button>
```

**Every dynamic region**:
```tsx
<div role="status" aria-live="polite" aria-atomic="true">
  {syncMessage}
</div>
```

**Every table**:
```tsx
<table role="grid" aria-label="Patient results">
  <thead>
    <tr>
      <th scope="col" aria-sort="ascending">Name</th>
    </tr>
  </thead>
  <tbody>
    <tr tabindex="0" role="row">
      <td role="gridcell">Ahmed Hasan</td>
    </tr>
  </tbody>
</table>
```

---

## 11. Implementation Roadmap

### Phase 1: Safety & Trust (Week 1)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Remove all fabricated clinical data | 17 components | 2d | **Critical** |
| Wire simulated saves to real persistence | ClinicalNotes, ResultEntryUI, all services | 2d | **Critical** |
| Add SaveIndicator to every form | New component + all forms | 1d | High |
| Add SyncIndicator to status bar | New component + AppShell | 1d | High |
| Add ConfirmDialog for destructive actions | New component + consent, delete, logout | 1d | **Critical** |
| Add CriticalValueAlert component | New component | 1d | **Critical** |
| Add OnlineStatus indicator | New component + AppShell | 0.5d | High |

### Phase 2: Design System (Week 2-3)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Define design tokens in CSS | index.css | 1d | Foundation |
| Build Button, Input, Select, Badge primitives | ui/* | 2d | Foundation |
| Build Skeleton, EmptyState, ErrorState | ui/* | 1d | High |
| Build Toast system | ui/Toast.tsx | 1d | High |
| Build VisuallyHidden | ui/VisuallyHidden.tsx | 0.5d | Accessibility |

### Phase 3: Navigation (Week 3-4)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Redesign top bar (search + user only) | TopBar.tsx | 1d | High |
| Build UniversalSearch component | navigation/UniversalSearch.tsx | 2d | **Critical** |
| Upgrade CommandPalette → Spotlight-style | CommandPalette.tsx | 2d | High |
| Remove fixed sidebar | App.tsx | 2d | High |
| Add KeyboardShortcuts system | navigation/KeyboardShortcuts.tsx | 1d | High |
| Add context-aware landing pages | Each wing view | 2d | High |
| Remove 4 floating assistants | Multiple files | 1d | Medium |

### Phase 4: Enterprise DataGrid (Week 4-5)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Build DataGrid with virtualization | data/DataGrid*.tsx | 4d | **Critical** |
| Add column resize, sort, filter | DataGrid infrastructure | 2d | High |
| Add bulk actions, export | DataGridToolbar | 1d | High |
| Add keyboard navigation | DataGrid keyboard handlers | 1d | High |
| Migrate RecordsView to DataGrid | RecordsView.tsx | 1d | High |
| Migrate WorkQueue to Kanban | WorkQueue.tsx | 3d | High |
| Migrate LabResultsView to DataGrid | LabResultsView.tsx | 1d | High |

### Phase 5: Smart Form System (Week 5-6)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Build SmartForm with auto-save | form/SmartForm.tsx | 3d | High |
| Add inline validation | form/FormField.tsx | 1d | High |
| Add undo/redo | form state management | 1d | High |
| Migrate PatientRegistration | PatientRegistration.tsx | 1d | High |
| Migrate Settings → inline edit | SettingsView.tsx | 1d | Medium |

### Phase 6: Screen Redesigns (Week 6-8)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Redesign auth screen (split view) | LandingAuthView.tsx | 1d | High |
| Redesign doctor landing | DashboardView.tsx | 2d | High |
| Redesign patient timeline | PatientProfile.tsx | 3d | **Critical** |
| Redesign lab dashboard | LabDashboard.tsx | 2d | High |
| Redesign citizen portal | CitizenHealth.tsx (merge 3) | 2d | High |
| Redesign ministry dashboard | NationalHealthGrid.tsx | 2d | High |
| Redesign lab operations (merge 3) | Inventory/Sample/QC | 2d | Medium |

### Phase 7: AI Integration (Week 8-9)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Build InlineAI component | ai/InlineAI.tsx | 2d | High |
| Build AIExplainer for results | ai/AIExplainer.tsx | 1d | High |
| Build AIOrderSuggestion | ai/AIOrderSuggestion.tsx | 1d | High |
| Build AISummary for patient profile | ai/AISummary.tsx | 1d | High |
| Remove chatbot UIs | 5 components | 1d | Medium |
| Add AI to search (natural language) | UniversalSearch.tsx | 2d | High |

### Phase 8: Accessibility (Week 9-10)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Add ARIA labels to all interactive elements | All components | 3d | **Critical** |
| Add focus traps to all modals | useFocusTrap hook | 1d | **Critical** |
| Add keyboard navigation to all tables | DataGrid + custom tables | 2d | **Critical** |
| Add aria-live regions | Contexts + views | 1d | High |
| Add prefers-reduced-motion | useReducedMotion hook | 1d | Medium |
| Add screen-reader-only text | All icon buttons | 1d | High |
| Test with screen reader | All views | 2d | **Critical** |

### Phase 9: Performance & Polish (Week 10-11)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Add skeleton loading to all views | All 18 screens | 2d | High |
| Add empty states to all views | All screens | 1d | Medium |
| Add optimistic UI to mutations | Services + components | 2d | High |
| Mobile responsive pass | All screens | 3d | High |
| Performance audit + optimization | All | 2d | High |

### Total: 60-70 person-days (3-4 engineers × 5-6 weeks)

---

## 12. Success Metrics

| Metric | Current | Target | How to measure |
|--------|---------|--------|----------------|
| Screens | 35 | 18 | Code file count |
| Modals | 6 types | 2 types | Component count |
| Floating UI elements | 4 assistants | 0 | Visual audit |
| Clicks: view critical result | 4 | 0 (auto-push) | Workflow test |
| Clicks: enter lab result | 12 | 3 | Workflow test |
| Clicks: find patient | 5 | 1 | Workflow test |
| Clicks: create order | 8 | 1 | Workflow test |
| Clicks: switch wings | 2 | 0 (auto-context) | Workflow test |
| Keyboard shortcuts | 8 global | 30+ | Feature checklist |
| DataGrid features | 3 | 15+ | Feature checklist |
| Fake clinical data components | 17 | 0 | Code review |
| Skeleton loading states | 0 | 18 screens | Code review |
| Empty states | 10 | 18 screens | Code review |
| Confirmation dialogs | 0 | 5+ actions | Code review |
| Undo support | 1 component | All forms | Code review |
| Auto-save | 0 forms | All forms | Code review |
| Save indicators | 0 | All forms | Code review |
| Sync indicators | 0 | Always visible | Code review |
| ARIA attributes | ~5 | ~500+ | Linter |
| Focus traps | 0 | All modals | Code review |
| prefers-reduced-motion | 0 | All animations | Code review |
| Screen reader support | None | Full | Manual test |
| Color contrast | Unknown | AAA 7:1 | Automated audit |
| WCAG compliance | 0% | AA (AAA target) | Audit report |

---

## Final Word

This is not a UI refresh.

This is a complete reinvention of how healthcare software should feel.

**Before this redesign**:
- Users navigate through 35+ screens
- Users click 8-12 times for common tasks
- Users see fabricated clinical data that erodes trust
- Users have zero accessibility support
- Users have zero undo, zero auto-save, zero keyboard shortcuts
- Users are interrupted by floating assistants, modals, and notifications

**After this redesign**:
- Users have 18 focused screens (49% reduction)
- Users click 1-3 times for common tasks (70% reduction)
- Users see only real clinical data with clear provenance
- Users have WCAG AA accessibility (AAA target)
- Users have undo, auto-save, keyboard shortcuts everywhere
- Users have calm technology — AI assists without interrupting

The interface disappears.

The work becomes the focus.

**This is the world's best healthcare experience.**
