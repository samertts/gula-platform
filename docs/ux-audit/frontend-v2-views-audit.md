# GULA Platform frontend-v2 — UX/UI Audit of 35 View Files

> Generated: 2026-07-20

**Brand:** GULA — multi-stakeholder healthcare platform (citizen, doctor, lab, admin, ministry, researcher)
**Tech stack:** React + TypeScript, Firebase (Auth + Firestore), Tailwind CSS, Lucide icons, Framer Motion / motion/react, Recharts
**Shared patterns:** `motion` animations, `cn()` utility, `rounded-3xl` cards, editorial headers (label + h1 + subtext), stat grids, skeleton screens, indigo/emerald/amber palette, sonner toasts for errors.

---

## Table of Contents

1. [General Views](#1-general-views)
2. [Lab Views](#2-lab-views)
3. [Doctor Views](#3-doctor-views)
4. [Citizen Views](#4-citizen-views)
5. [Admin Views](#5-admin-views)
6. [Ministry Views](#6-ministry-views)
7. [Research Views](#7-research-views)
8. [Cross-cutting Issues](#8-cross-cutting-issues)

---

## 1. General Views

### 1.1 DashboardView
**File:** `views/DashboardView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header (`label="Dashboard"`, `h1="Welcome back"`, subtext) + 4 stat cards (Total Patients, Appointments Today, Pending Results, Critical Alerts) + Recent Activity feed. Uses `max-w-7xl mx-auto`. |
| **Information hierarchy** | Good — KPIs first, then activity feed. Critical alerts get red/amber badges. |
| **Form patterns** | None present. |
| **Table patterns** | No table. Activity feed is a vertical list with avatar + text + timestamp. |
| **Error handling** | Uses `try/catch` with `toast.error` for Firestore fetches. Generic messages like "Failed to load" — no user guidance on next steps. |
| **Empty states** | Hardcoded mock data — no empty state ever visible. |
| **Loading states** | Uses `DashboardSkeleton` (pulsing stat cards + list). Adequate. |
| **Accessibility** | No ARIA labels, `role`, or keyboard navigation. Stat cards are `<div>` elements with `onClick` — not focusable. |
| **Mobile responsiveness** | `p-4 md:p-8`, stat grid `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`. Touch targets unverified (likely small stat cards). |
| **Clinical safety** | Critical alerts are visually highlighted (red badges). No confirmation on alert dismissal (none exists). No undo. |
| **Workflow clicks/steps** | N/A (dashboard overview). |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | None within view. Clicks on stat cards navigate elsewhere — no visual feedback that cards are clickable. |

---

### 1.2 RecordsView
**File:** `views/RecordsView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + search bar + filter chips (All, Labs, Imaging, etc.) + results table. |
| **Information hierarchy** | Good — search/filter first, then results. |
| **Form patterns** | Search input with real-time filtering. Validates on change. |
| **Table patterns** | Table with columns: Patient, Type, Date, Status, Actions. Has `StatusPill`, overflow menu, row click expands detail. No sticky headers, no column sorting controls, no bulk selection. |
| **Error handling** | Catch block wraps Firestore query — generic `toast.error("Failed to load records")`. No retry button. |
| **Empty states** | Has explicit `<EmptyState>` component with icon + message + action button. Well-implemented. |
| **Loading states** | `TableSkeleton` for initial load. Adequate. |
| **Accessibility** | No `aria-*` on search input, no `role="table"`, no keyboard navigation for overflow menu. |
| **Mobile responsiveness** | Table likely horizontal-scrolls on mobile (no responsive table wrapper mentioned). |
| **Clinical safety** | No confirmation on actions triggered from overflow menu. No audit trail visible to user. |
| **Workflow clicks/steps** | ~2 clicks to reach a record detail. Reasonable. |
| **Keyboard shortcuts** | None (e.g., `/` to focus search). |
| **Dead ends/confusion** | Overflow menu items may navigate to pages that don't exist yet (partial Firestore integration). |

---

### 1.3 AppointmentsView
**File:** `views/AppointmentsView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + tabs (Upcoming, Past, All) + appointment cards. |
| **Information hierarchy** | Tab-switching for temporal grouping is clear. |
| **Form patterns** | None (display-only). |
| **Table patterns** | Uses card-based layout (not table). Each card has date, patient, type, status badge, action buttons. |
| **Error handling** | Mock data — no error handling visible. |
| **Empty states** | Falls through to empty list if no appointments — no `<EmptyState>` component. |
| **Loading states** | No skeleton — likely shows nothing during load. |
| **Accessibility** | No ARIA for tablist/tabpanel roles. Tabs are `<button>` elements — good base but missing `aria-selected` / `aria-controls`. |
| **Mobile responsiveness** | Cards stack vertically naturally. `p-4 md:p-8`. Adequate. |
| **Clinical safety** | No confirmation on cancel/reschedule actions. |
| **Workflow clicks/steps** | ~2 clicks to view details, ~2 clicks to cancel/reschedule. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | Cancel/reschedule buttons may lead to unimplemented/mock flows. |

---

### 1.4 LabResultsView
**File:** `views/LabResultsView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + filters (date range, test type, status) + results list. |
| **Information hierarchy** | Filters prominent, results below. Good. |
| **Form patterns** | Date pickers and select dropdowns for filtering. No inline validation needed. |
| **Table patterns** | List with expandable items showing test details. Status pills for normal/abnormal/critical. Abnormal values highlighted with icon + color. |
| **Error handling** | Generic error boundary — no retry. |
| **Empty states** | None visible (mock data). |
| **Loading states** | `Loader2` spinner. No skeleton. |
| **Accessibility** | No `aria-*` on expand/collapse. Expanded state may not be announced by screen readers. |
| **Mobile responsiveness** | `p-4 md:p-8`, list items stack well. |
| **Clinical safety** | **Good:** Abnormal values get visual flagging (red/warning icon). Critical values get prominent badging. No mechanism to mark reviewed/acknowledged. |
| **Workflow clicks/steps** | 2-3 clicks to see full result details. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No way to compare with previous results side-by-side. No trend sparklines. |

---

### 1.5 LandingAuthView
**File:** `views/LandingAuthView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Full-screen landing with hero section + role-based sign-in cards + authentication forms. |
| **Information hierarchy** | Clear: GULA branding → value proposition → role selection → auth form. |
| **Form patterns** | Email/password, OTP, biometric login forms. Inline validation on blur + change. Password strength indicator. Good validation UX. |
| **Table patterns** | None. |
| **Error handling** | Toast-based for auth failures (wrong password, network error). Firebase error messages are technical (e.g., "auth/user-not-found") — not user-friendly. No contextual recovery suggestions. |
| **Empty states** | N/A (auth flow always has content). |
| **Loading states** | Button spinner on submit. Adequate. |
| **Accessibility** | Forms have labels (implied by Tailwind placeholder styling). No explicit `<label>` or `aria-label`. No `aria-describedby` for error messages. |
| **Mobile responsiveness** | `min-h-screen`, centered layout. `p-4 md:p-8`. Scales reasonably. |
| **Clinical safety** | N/A (not clinical). Session timeout not handled. |
| **Workflow clicks/steps** | 3 steps: select role → enter credentials → submit. Reasonable. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No "forgot password" visible on all form variants. No SSO/SAML options despite healthcare context. |

---

### 1.6 SettingsView
**File:** `views/SettingsView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + tabbed settings sections (Profile, Notifications, Security, Billing). |
| **Information hierarchy** | Tab-based grouping is standard and clear. |
| **Form patterns** | Profile form (name, email, phone), notification toggles, password change, billing info. Inline validation on save. No auto-save. |
| **Table patterns** | None. |
| **Error handling** | Toast on save failure. Generic messages. |
| **Empty states** | N/A (form data always present or editable). |
| **Loading states** | `Loader2` on save button. No skeleton for initial load. |
| **Accessibility** | Toggle switches may lack `role="switch"` and `aria-checked`. |
| **Mobile responsiveness** | `p-4 md:p-8`. Forms stack vertically. Adequate. |
| **Clinical safety** | N/A. |
| **Workflow clicks/steps** | 1 click to navigate to section, 1-2 to edit, 1 to save. Reasonable. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | Billing section probably mock/not functional. No confirmation on destructive actions (delete account not present but could be added). |

---

### 1.7 LabIntelligenceView
**File:** `views/LabIntelligenceView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + image upload area + analysis results display + interpretation panel. |
| **Information hierarchy** | Upload → process → results. Linear flow makes sense. |
| **Form patterns** | File upload (drag-and-drop zone). No validation on file type/size before submission. |
| **Table patterns** | Results shown as structured report, not table. |
| **Error handling** | Toast on upload failure or analysis error. |
| **Empty states** | Good — upload zone is the empty state (illustration + prompt to upload). |
| **Loading states** | Spinner during analysis. Progress bar would be better for image processing. |
| **Accessibility** | Drag-and-drop zone may not be keyboard accessible. No `aria-label` on upload area. |
| **Mobile responsiveness** | Upload zone may overflow on small screens. |
| **Clinical safety** | Results are AI-generated — no disclaimer that AI output should be verified. No way to flag incorrect analysis. |
| **Workflow clicks/steps** | 2 clicks: select image → analyze. Efficient. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | **No way to delete upload history.** No way to compare multiple analyses side-by-side. |

---

### 1.8 ImagingLabView
**File:** `views/ImagingLabView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + upload panel + image gallery + study details. |
| **Information hierarchy** | Decent — upload area prominent, gallery below, details on selection. |
| **Form patterns** | Upload form with metadata fields (patient ID, study type, date). **No validation on DICOM/nifti format.** |
| **Table patterns** | Gallery grid (not table). |
| **Error handling** | Toast on upload failure. No validation feedback before upload. |
| **Empty states** | Gallery area empty when no images. No `<EmptyState>` component — just empty grid. |
| **Loading states** | Spinner during upload. No skeleton for gallery. |
| **Accessibility** | No `alt` text on images in gallery. No keyboard navigation for gallery items. |
| **Mobile responsiveness** | Gallery grid `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`. Reasonable. |
| **Clinical safety** | **No validation on uploads** — wrong patient ID, wrong study type could be submitted. No duplicate detection. No DICOM header validation. |
| **Workflow clicks/steps** | 3+ clicks to complete upload + metadata entry. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | **No way to edit metadata after upload.** No batch upload. No DICOM viewer — just image display. |

---

## 2. Lab Views

### 2.1 lab/LabDashboard
**File:** `views/lab/LabDashboard.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + KPI stat row (Samples Today, Pending, Completed, Critical) + workflow charts + recent activity. |
| **Information hierarchy** | Strong — KPIs first, then trends, then operational details. |
| **Form patterns** | None. |
| **Table patterns** | Recent activity as a compact list. |
| **Error handling** | Uses `try/catch` with Firestore — generic toasts. |
| **Empty states** | Mock data — no empty states tested. |
| **Loading states** | `DashboardSkeleton`. Adequate. |
| **Accessibility** | Charts from Recharts may not have accessible data tables. No `aria-label` on stat cards. |
| **Mobile responsiveness** | `p-4 md:p-8`, `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`. Adequate. |
| **Clinical safety** | Critical count highlighted with red badge. No drill-down to see which samples are critical. |
| **Workflow clicks/steps** | N/A (overview). |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | Stat cards are not clickable but look like they could be. Users may click expecting drill-down. |

---

### 2.2 lab/WorkQueue
**File:** `views/lab/WorkQueue.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + filter bar (status, priority, date, search) + work items table. |
| **Information hierarchy** | Filters above table — correct. |
| **Form patterns** | Search input, select dropdowns for status/priority, date picker. |
| **Table patterns** | Table with columns: Patient, Test, Priority, Status, Assigned To, Actions. Sort/filter/expand row supported. **No bulk actions**, no sticky headers, no column sorting controls. |
| **Error handling** | Toast on fetch failure. |
| **Empty states** | Not visible (mock data). |
| **Loading states** | `TableSkeleton`. Good. |
| **Accessibility** | No `aria-*` on sort indicators (if any). Expandable rows may not be accessible. |
| **Mobile responsiveness** | Table likely horizontal-scroll on mobile. Large number of columns problematic. |
| **Clinical safety** | **Priority flagging is good** (urgent/critical items highlighted). No auto-refresh for time-sensitive items. No confirmation when assigning/reassigning work items. |
| **Workflow clicks/steps** | 2 clicks to view details, 2-3 to process a work item. Could be optimized. |
| **Keyboard shortcuts** | None (would benefit from `n` for next item, `a` to assign). |
| **Dead ends/confusion** | Actions may navigate to incomplete flows. No batch assignment. |

---

### 2.3 lab/DeviceMonitoring
**File:** `views/lab/DeviceMonitoring.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + device cards (grid) + status overview + alerts panel. |
| **Information hierarchy** | Devices prominent, alerts below. Good. |
| **Form patterns** | None (display-only). |
| **Table patterns** | Uses cards (not table). Each card shows device name, type, status (Online/Offline/Error), last communication, metrics. |
| **Error handling** | Toast on Firestore fetch failure. No stale-data indicator if real-time connection drops. |
| **Empty states** | No devices → empty grid. No `<EmptyState>`. |
| **Loading states** | Skeleton cards. Adequate. |
| **Accessibility** | Status indicators may be color-only (red/green/amber). Need text labels for colorblind users. |
| **Mobile responsiveness** | `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`. Reasonable. |
| **Clinical safety** | Device status is critical for lab ops. **No indication of data staleness** — if real-time connection drops, device shows last known status without warning. |
| **Workflow clicks/steps** | 1 click to see device details. Reasonable. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | Device detail view may not exist or be mock. No way to trigger device reconnection from UI. No maintenance scheduling. |

---

### 2.4 lab/InventoryManagement
**File:** `views/lab/InventoryManagement.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + item category tabs + inventory table + low-stock alerts. |
| **Information hierarchy** | Alerts prominent (top), categories/tabs, then items. Good. |
| **Form patterns** | Add item form (modal or inline) with fields: name, category, quantity, threshold, expiry. |
| **Table patterns** | Table with columns: Item Name, Category, Quantity, Threshold, Expiry Date, Status, Actions. Status pill for In Stock / Low Stock / Expired. |
| **Error handling** | Toast on save/update failure. |
| **Empty states** | No items → empty table. No `<EmptyState>` with "Add your first item" CTA. |
| **Loading states** | `TableSkeleton`. Good. |
| **Accessibility** | Modal form may not trap focus. No `aria-*` on status pills. |
| **Mobile responsiveness** | Table horizontal-scroll on mobile. Modal may overflow. |
| **Clinical safety** | Low-stock alerts are highlighted. **No way to update quantity** (cannot decrement when item used). Expiry warnings present. |
| **Workflow clicks/steps** | ~2 clicks to add item. No quick-consume flow for daily usage. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | **No way to update quantity** — serious usability gap for lab workflow. No batch add. No barcode scanning. |

---

### 2.5 lab/SampleTracking
**File:** `views/lab/SampleTracking.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + search/filter + sample timeline + sample detail panel. |
| **Information hierarchy** | Search first, then list/timeline, then detail on selection. Good. |
| **Form patterns** | Search input, status filter, date range. |
| **Table patterns** | Timeline view (not table) with sample lifecycle stages: Collected → Received → Processing → Analyzed → Reviewed → Reported. Visual progress indicator. |
| **Error handling** | Toast on fetch failure. |
| **Empty states** | No samples found → empty state? Not implemented (uses mock data). |
| **Loading states** | Timeline skeleton. Adequate. |
| **Accessibility** | Timeline steps may not be announced as a progress bar. No `aria-valuenow` / `aria-valuemax`. |
| **Mobile responsiveness** | Timeline may compress poorly on mobile (horizontal timeline is problematic). |
| **Clinical safety** | **Good:** Sample chain of custody visible. Timestamps for each step. No flag for samples exceeding expected turnaround time. |
| **Workflow clicks/steps** | 2 clicks to see full sample detail. Reasonable. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No way to flag sample issues (hemolyzed, insufficient, etc.) from UI. No barcode scan for quick lookup. |

---

### 2.6 lab/QualityControl
**File:** `views/lab/QualityControl.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + QC overview stats + control charts + lot tracking + corrective actions log. |
| **Information hierarchy** | Stats → charts → lots → actions. Good clinical QC flow. |
| **Form patterns** | Add QC result form, corrective action form, lot registration. |
| **Table patterns** | Lots table, corrective actions table. Standard columns. |
| **Error handling** | Toast on save/analysis failure. |
| **Empty states** | Not visible (mock data). |
| **Loading states** | Skeleton for charts + tables. Good. |
| **Accessibility** | Recharts used — no accessible data table fallback for screen readers. |
| **Mobile responsiveness** | Charts may be small on mobile. Tables horizontal-scroll. |
| **Clinical safety** | **Good:** Westgard rules / control limits visualized. Failed controls are highlighted. Corrective actions logged. No auto-alert escalation when controls fail repeatedly. |
| **Workflow clicks/steps** | 2-3 clicks to add QC result and view trend. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No way to link corrective action to specific QC failure automatically. No predefined corrective action templates. |

---

## 3. Doctor Views

### 3.1 doctor/DoctorIntelligence
**File:** `views/doctor/DoctorIntelligence.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + patient search + AI insights panel + clinical recommendations + recent patients. |
| **Information hierarchy** | AI insights prominent (clinical decision support focus). Good. |
| **Form patterns** | Patient search input, clinical note entry (rich text likely). |
| **Table patterns** | Recent patients as compact list with status indicators. |
| **Error handling** | Toast on AI analysis failure. |
| **Empty states** | No patients → empty list. No `<EmptyState>`. |
| **Loading states** | Skeleton for AI insights panel (processing may be slow). Good. |
| **Accessibility** | AI insights may use color coding — need text labels. |
| **Mobile responsiveness** | `p-4 md:p-8`, `grid-cols-1 lg:grid-cols-2`. Acceptable. |
| **Clinical safety** | **Critical:** AI recommendations must be reviewed by clinician — no forced-review gate. No disclaimer that AI is assistive only. No way to dismiss/flag incorrect AI suggestion. |
| **Workflow clicks/steps** | 2 clicks to search patient and see insights. |
| **Keyboard shortcuts** | None (would benefit from `/` for search). |
| **Dead ends/confusion** | AI recommendations have no "apply" action — user must manually act on them elsewhere. |

---

### 3.2 doctor/PatientProfile
**File:** `views/doctor/PatientProfile.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header with patient name/MRN + tabs (Overview, History, Results, Medications, Visits) + content panels. |
| **Information hierarchy** | Excellent — patient identity persistent across top, tabs for logical grouping. |
| **Form patterns** | None (display of patient data). |
| **Table patterns** | Results history as table, medications list, visit timeline. |
| **Error handling** | Toast on fetch failure. |
| **Empty states** | Some sections may be empty (no medications) — no explicit empty state handling visible. |
| **Loading states** | `Loader2` on tab content load. No skeleton for table. |
| **Accessibility** | Tablist needs ARIA roles. |
| **Mobile responsiveness** | Tabs may overflow on mobile (horizontal scroll needed). |
| **Clinical safety** | **Good:** Comprehensive patient data in one place. **Concern:** No indication that displayed data is current. No last-refreshed timestamp. |
| **Workflow clicks/steps** | 1-2 clicks to navigate between sections. Efficient. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No "Add Note" or "Order Test" action within profile — doctor must navigate elsewhere for actions. |

---

## 4. Citizen Views

### 4.1 citizen/CitizenHealth
**File:** `views/citizen/CitizenHealth.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + health score card + vitals summary + recent activity + recommendations. |
| **Information hierarchy** | Health score (gamification) first, then vitals, then activity. Good for patient engagement. |
| **Form patterns** | None. |
| **Table patterns** | None. |
| **Error handling** | Mock data — no error handling. |
| **Empty states** | Gamified score always present — no empty state. |
| **Loading states** | `Loader2` spinner. |
| **Accessibility** | Health score may be purely visual/numeric — need accessible description. No ARIA. |
| **Mobile responsiveness** | `p-4 md:p-8`, stacked layout. Good. |
| **Clinical safety** | Health score could be misinterpreted as clinical diagnosis. **No disclaimer** that score is informational only. |
| **Workflow clicks/steps** | N/A (dashboard). |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No way to understand how health score is calculated. Recommendations may be generic/mock. |

---

### 4.2 citizen/CitizenDashboard
**File:** `views/citizen/CitizenDashboard.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + personalized greeting + quick actions (Book Appointment, View Results, etc.) + recent notifications + upcoming appointments. |
| **Information hierarchy** | Good — quick actions prominent, then upcoming events. |
| **Form patterns** | None. |
| **Table patterns** | None. |
| **Error handling** | Toast on data fetch failure. |
| **Empty states** | No upcoming appointments — empty state with CTA to book. Good. |
| **Loading states** | `DashboardSkeleton`. Good. |
| **Accessibility** | Quick action cards are `<div>` elements with `onClick` — not keyboard accessible. |
| **Mobile responsiveness** | `p-4 md:p-8`, action cards grid. Good. |
| **Clinical safety** | N/A. |
| **Workflow clicks/steps** | 1 click to reach all major actions. Efficient. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | Quick actions may navigate to mock/incomplete views. |

---

### 4.3 citizen/CitizenAssistant
**File:** `views/citizen/CitizenAssistant.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Full-screen chat interface with message history + input bar + suggested prompts. |
| **Information hierarchy** | Chat layout is standard (history scrolls, input fixed at bottom). |
| **Form patterns** | Chat input (text), suggested prompt buttons. |
| **Table patterns** | None. |
| **Error handling** | Toast on response failure. "Try again" may not resend the message — user may need to retype. |
| **Empty states** | Empty chat — welcome message with suggested prompts. **Good.** |
| **Loading states** | Typing indicator during AI response. Good. |
| **Accessibility** | Chat messages may not have `role="log"` or `aria-live` for dynamic updates. |
| **Mobile responsiveness** | Full-screen layout, input bar at bottom works well on mobile. |
| **Clinical safety** | **Critical:** AI health assistant must not give medical advice. No disclaimer visible in chat. No escalation to human agent. |
| **Workflow clicks/steps** | 1 click/tap to send message. |
| **Keyboard shortcuts** | Enter to send. No `/` commands. |
| **Dead ends/confusion** | No history search. No way to know if assistant is AI or human. No feedback mechanism for incorrect answers. |

---

### 4.4 citizen/PatientRegistration
**File:** `views/citizen/PatientRegistration.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Multi-step wizard with stepper (Step 1 of 4: Personal Info, Contact, Medical History, Review). |
| **Information hierarchy** | Step-based wizard is excellent for complex registration. Clear progress indicator. |
| **Form patterns** | Extensive form with all patient fields. **Inline validation on blur + change.** Good validation UX. Masked fields for phone/date. |
| **Table patterns** | None. |
| **Error handling** | Per-field error messages (red text below field). Good specificity. Summary error on submit. |
| **Empty states** | N/A (always form content). |
| **Loading states** | Button spinner on submit. |
| **Accessibility** | Step indicator needs `aria-current="step"`. Form fields need proper `<label>` elements (not just placeholder). |
| **Mobile responsiveness** | Steps may compress on mobile. Form fields stack well. |
| **Clinical safety** | Registration is data-entry — no clinical safety risk. **No validation of national ID format.** |
| **Workflow clicks/steps** | 4 steps × ~5 fields each. Reasonable for registration complexity. **No auto-save** — losing data on browser refresh is frustrating. |
| **Keyboard shortcuts** | None. Would benefit from `Ctrl+S` to save draft. |
| **Dead ends/confusion** | No way to go back without losing entered data (needs confirmation on back). No draft save. |

---

### 4.5 citizen/IdentityVerificationView
**File:** `views/citizen/IdentityVerificationView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + document upload area + verification status + instructions. |
| **Information hierarchy** | Clear: instructions → upload → status. |
| **Form patterns** | File upload (document images), potentially webcam capture. |
| **Table patterns** | None. |
| **Error handling** | Toast on upload failure. File type/size validation before upload. |
| **Empty states** | Upload zone is the empty state (illustration + prompt). Good. |
| **Loading states** | Spinner during upload + processing. |
| **Accessibility** | Upload zone may not be keyboard accessible. No ARIA for file upload. |
| **Mobile responsiveness** | `p-4 md:p-8`. Upload zone should work on mobile camera too. |
| **Clinical safety** | N/A. |
| **Workflow clicks/steps** | 1-2 clicks to upload documents. Efficient. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No way to check verification status after submission (no pending status page). No estimated processing time shown. |

---

### 4.6 citizen/ConsentManagementView
**File:** `views/citizen/ConsentManagementView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + consent categories toggle list + audit log of consent changes. |
| **Information hierarchy** | Clear — categories prominent, history secondary. |
| **Form patterns** | Toggle switches for each consent category (Data Sharing, Research Use, Marketing, etc.). |
| **Table patterns** | Consent change history as compact table/timeline. |
| **Error handling** | Toast on save failure. |
| **Empty states** | No audit log entries yet — empty state? Not implemented. |
| **Loading states** | `Loader2` on initial load. |
| **Accessibility** | Toggles need `role="switch"` and `aria-checked`. Color-only indicators for on/off are problematic. |
| **Mobile responsiveness** | `p-4 md:p-8`. Toggle list stacks well. |
| **Clinical safety** | **Important:** Consent changes should have confirmation dialog (especially revoking critical consents like emergency data access). No confirmation present. |
| **Workflow clicks/steps** | 1 click to toggle consent. **Too easy to accidentally revoke consent** — needs confirmation. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No explanation of what each consent category means (tooltip or expandable description needed). |

---

### 4.7 citizen/MedicalHistoryView
**File:** `views/citizen/MedicalHistoryView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + timeline view + filter by type (All, Conditions, Surgeries, Allergies, Medications) + detail panel. |
| **Information hierarchy** | Timeline-first with filter — good for chronological understanding. |
| **Form patterns** | None (display only). |
| **Table patterns** | Timeline (not table). Each entry has date, type icon, title, description, provider. |
| **Error handling** | Toast on fetch failure. |
| **Empty states** | No medical history → empty timeline. Should have CTA to add first entry. |
| **Loading states** | Timeline skeleton. Adequate. |
| **Accessibility** | Timeline items need ARIA for expand/collapse. Type icons need text labels. |
| **Mobile responsiveness** | Timeline may compress poorly on mobile (date placement). |
| **Clinical safety** | **Good:** Full medical history viewable. **No way to flag incorrect entries.** No way to see data source/attribution. |
| **Workflow clicks/steps** | 1 click to expand entry, 1-2 to filter. Reasonable. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No way to add history entries from this view (read-only). No way to dispute incorrect data. |

---

### 4.8 citizen/SmartResultsView
**File:** `views/citizen/SmartResultsView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + results list + AI-powered interpretation panel + trend charts. |
| **Information hierarchy** | Results → interpretation → trends. Good for patient understanding. |
| **Form patterns** | None. |
| **Table patterns** | Results list with expandable items showing detailed values. |
| **Error handling** | Toast on fetch failure. |
| **Empty states** | No results → empty state with illustration. Good. |
| **Loading states** | Skeleton for results list. Trend chart skeleton also needed. |
| **Accessibility** | Charts from Recharts need accessible data tables. |
| **Mobile responsiveness** | `p-4 md:p-8`. Charts may be small on mobile. |
| **Clinical safety** | **Critical:** AI interpretation is presented to patient directly. **No disclaimer** that interpretation is AI-generated and should be discussed with doctor. Abnormal values could cause unnecessary anxiety. |
| **Workflow clicks/steps** | 1-2 clicks to see interpretation and trends. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No way to share results with doctor from this view. "Ask AI" feature may give misleading answers. |

---

### 4.9 citizen/FamilyManagement
**File:** `views/citizen/FamilyManagement.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + family member cards + add member button + consent/access management per member. |
| **Information hierarchy** | Clear — members as cards, actions per member. |
| **Form patterns** | Add family member form (name, relationship, date of birth, access level). |
| **Table patterns** | Card grid (not table). |
| **Error handling** | Toast on save failure. |
| **Empty states** | No family members → empty state with CTA to add first member. Good. |
| **Loading states** | Skeleton cards. Adequate. |
| **Accessibility** | Cards with actions need keyboard accessibility. |
| **Mobile responsiveness** | Card grid `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`. Reasonable. |
| **Clinical safety** | **Important:** Access to family member health data must be granularly controlled. Consent management present. **No way to remove member** or revoke access. |
| **Workflow clicks/steps** | 2-3 clicks to add family member and configure access. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | **No edit or remove flow** for family members. No way to change access level after initial setup. |

---

### 4.10 citizen/MedicationCenter
**File:** `views/citizen/MedicationCenter.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + medication list + add medication form + adherence tracking + refill reminders. |
| **Information hierarchy** | Active medications prominent, then adherence, then refills. Good. |
| **Form patterns** | Add medication form (name, dosage, frequency, start date, prescriber, notes). |
| **Table patterns** | Medication list as cards/table with dosage, frequency, last taken, adherence %. |
| **Error handling** | Toast on save failure. |
| **Empty states** | No medications → empty state with CTA to add first medication. Good. |
| **Loading states** | Skeleton for medication list. Adequate. |
| **Accessibility** | Adherence percentage may be color-coded only. Need text labels. |
| **Mobile responsiveness** | `p-4 md:p-8`. Medication cards stack well. |
| **Clinical safety** | **Important:** Drug interaction checking not mentioned. **No way to set medication end date.** No allergy conflict warnings. No duplicate medication detection. |
| **Workflow clicks/steps** | 2 clicks to add medication. 1 click to log dose taken. |
| **Keyboard shortcuts** | None. Would benefit from quick-log shortcuts. |
| **Dead ends/confusion** | No way to edit or discontinue medication (can only add). No refill request integration with pharmacy. No medication history (past medications). |

---

## 5. Admin Views

### 5.1 admin/AuditLog
**File:** `views/admin/AuditLog.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + advanced filters (date range, user, action type, resource) + audit trail table. |
| **Information hierarchy** | Filters above table — needed for large audit datasets. |
| **Form patterns** | Date picker, user select, action type select, search input. |
| **Table patterns** | Table with columns: Timestamp, User, Action, Resource, Details, IP Address. **No bulk export**, no column sorting controls. |
| **Error handling** | Toast on fetch failure. |
| **Empty states** | No matching entries → empty state? Not implemented. |
| **Loading states** | `TableSkeleton`. Good. |
| **Accessibility** | Large table needs ARIA for row selection. |
| **Mobile responsiveness** | Wide table with many columns — problematic on mobile. Horizontal scroll likely. |
| **Clinical safety** | Audit log is read-only — no safety risk. |
| **Workflow clicks/steps** | 2-3 clicks to filter and review logs. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | **No row detail expansion** — truncating long messages in a column is problematic. No export for compliance reporting. |

---

### 5.2 admin/SystemsArchitectureView
**File:** `views/admin/SystemsArchitectureView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + interactive architecture diagram + component cards + dependency graph. |
| **Information hierarchy** | Visual diagram first, details below. Good for system understanding. |
| **Form patterns** | None. |
| **Table patterns** | Component cards (not table). |
| **Error handling** | Toast on fetch failure (if data-driven). |
| **Empty states** | N/A (diagram always present). |
| **Loading states** | Skeleton for diagram. Adequate. |
| **Accessibility** | Interactive diagram not accessible to screen readers. Need text alternative. |
| **Mobile responsiveness** | Large diagram may be unscrollable on mobile. |
| **Clinical safety** | N/A (admin tool). |
| **Workflow clicks/steps** | 1 click to select component and see details. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | Diagram is likely static/mock — no real system data. Text alternative for diagram not provided. |

---

### 5.3 admin/InfrastructureView
**File:** `views/admin/InfrastructureView.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + server status cards + resource utilization charts + health check results. |
| **Information hierarchy** | Status first, then resources, then health checks. Good ops layout. |
| **Form patterns** | None (monitoring display). |
| **Table patterns** | Health check results as table with pass/fail status. |
| **Error handling** | Toast on monitoring fetch failure. |
| **Empty states** | No servers → empty state. Not implemented (mock data). |
| **Loading states** | Skeleton for charts + cards. Adequate. |
| **Accessibility** | Recharts need accessible fallback. Status indicators color-only. |
| **Mobile responsiveness** | `p-4 md:p-8`, charts may be small on mobile. |
| **Clinical safety** | N/A (infrastructure monitoring). |
| **Workflow clicks/steps** | N/A (monitoring overview). |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No way to trigger actions from monitoring (restart service, clear cache, etc.). |

---

### 5.4 admin/IntegrationHub
**File:** `views/admin/IntegrationHub.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + integration cards (LIS, EHR, HIS, etc.) + connection status + configuration panel. |
| **Information hierarchy** | Integrations listed as cards, status per integration. |
| **Form patterns** | Connection configuration forms (API URL, API key, authentication type). |
| **Table patterns** | None (card layout). |
| **Error handling** | Toast on connection test/update failure. |
| **Empty states** | No integrations configured → empty state with CTA to add first. Good. |
| **Loading states** | Skeleton cards. Adequate. |
| **Accessibility** | Connection status is color-coded — needs text label. |
| **Mobile responsiveness** | Card grid `grid-cols-1 md:grid-cols-2`. Reasonable. |
| **Clinical safety** | Integration configuration affects data flow — **no confirmation before changing production connection**. No "test connection" before save for all integration types. |
| **Workflow clicks/steps** | 2-3 clicks to configure integration. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No way to see integration activity log (last sync, errors). No way to trigger manual sync. |

---

## 6. Ministry Views

### 6.1 ministry/NationalHealthGrid
**File:** `views/ministry/NationalHealthGrid.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + map visualization + regional statistics + national KPIs + data quality indicators. |
| **Information hierarchy** | Map (geographic) first, then stats, then quality. Good for national view. |
| **Form patterns** | Region filter, date range, metric selector. |
| **Table patterns** | Regional stats as table. |
| **Error handling** | Toast on data fetch failure. |
| **Empty states** | Map with no data — unrecoverable empty state (just blank map). |
| **Loading states** | Map skeleton. Adequate. |
| **Accessibility** | Map is not accessible to screen readers. Need tabular alternative for all map data. |
| **Mobile responsiveness** | Map likely unusable on small screens. Tables horizontal-scroll. |
| **Clinical safety** | Population-level data — no individual patient safety risk. |
| **Workflow clicks/steps** | 1-2 clicks to drill into region statistics. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | Map is likely static/mock — no real geographic data. No way to export regional reports. |

---

### 6.2 ministry/EpidemiologicalIntelligence
**File:** `views/ministry/EpidemiologicalIntelligence.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + disease surveillance dashboard + outbreak detection alerts + trend charts + heat maps. |
| **Information hierarchy** | Alerts first (time-critical), then trends, then maps. Good for public health. |
| **Form patterns** | Disease type filter, region filter, date range. |
| **Table patterns** | Outbreak alerts as priority-sorted list. |
| **Error handling** | Toast on fetch failure. |
| **Empty states** | No alerts → empty state with "No current outbreaks." Good. |
| **Loading states** | Dashboard skeleton. Adequate. |
| **Accessibility** | Recharts + maps not accessible. Alert severity color-only. |
| **Mobile responsiveness** | Complex dashboard likely difficult on mobile. |
| **Clinical safety** | **Critical:** Outbreak detection reliability is a public health safety issue. No indication of data confidence/accuracy. |
| **Workflow clicks/steps** | 1 click to see outbreak details, 2+ to access response actions. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No way to trigger public health response from dashboard. Alert acknowledgement/action tracking missing. |

---

### 6.3 ministry/DataSovereigntyAudit
**File:** `views/ministry/DataSovereigntyAudit.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + data location map + cross-border transfer log + compliance status + audit timeline. |
| **Information hierarchy** | Location map + compliance status first, then transfer log. Good for sovereignty concerns. |
| **Form patterns** | Date range filter, data type filter, region filter. |
| **Table patterns** | Cross-border transfer log as table with columns: Timestamp, Data Type, Origin, Destination, Status, Approver. |
| **Error handling** | Toast on fetch failure. |
| **Empty states** | No transfers → empty state. Good. |
| **Loading states** | Table skeleton. Adequate. |
| **Accessibility** | Map not accessible. Data location markers color-only. |
| **Mobile responsiveness** | Map problematic on mobile. Table horizontal-scroll. |
| **Clinical safety** | Data sovereignty is regulatory, not directly clinical. |
| **Workflow clicks/steps** | 1-2 clicks to filter and review transfers. |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | No way to approve/pending transfers from UI (read-only). No export for regulatory reporting. |

---

### 6.4 ministry/MinistryDashboard
**File:** `views/ministry/MinistryDashboard.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + national KPIs (Hospitals, Labs, Active Cases, Vaccination Rate) + trends + regional breakdown + alerts. |
| **Information hierarchy** | KPIs → trends → regions → alerts. Standard executive dashboard. |
| **Form patterns** | Region filter, date range, metric selector. |
| **Table patterns** | Regional breakdown as table with sortable columns. |
| **Error handling** | Toast on fetch failure. |
| **Empty states** | Mock data — no empty states tested. |
| **Loading states** | `DashboardSkeleton`. Good. |
| **Accessibility** | Recharts need accessible data tables. |
| **Mobile responsiveness** | `p-4 md:p-8`. Complex layout may need simplification for mobile. |
| **Clinical safety** | Population-level only. |
| **Workflow clicks/steps** | N/A (executive overview). |
| **Keyboard shortcuts** | None. |
| **Dead ends/confusion** | Stat cards not clickable (no drill-down). Alerts don't link to action pages. |

---

## 7. Research Views

### 7.1 research/ResearcherDashboard
**File:** `views/research/ResearcherDashboard.tsx`

| Category | Findings |
|----------|----------|
| **Screen structure** | Editorial header + study overview cards + patient cohort builder + data query interface + publication tracker. |
| **Information hierarchy** | Studies → cohorts → queries → publications. Logical researcher flow. |
| **Form patterns** | Cohort builder (multiple filters: age, gender, diagnosis, lab values, date range), data query builder. |
| **Table patterns** | Study list as cards, cohort results as table. |
| **Error handling** | Toast on query/build failure. |
| **Empty states** | No studies → empty state with CTA to create first study. Good. |
| **Loading states** | Skeleton for studies + tables. Adequate. |
| **Accessibility** | Complex filter builder may not be keyboard-accessible. |
| **Mobile responsiveness** | Cohort builder with many filters likely unusable on mobile. |
| **Clinical safety** | **Critical:** Research access to patient data must be de-identified. No visible indication of de-identification status. Query builder may allow PII access. |
| **Workflow clicks/steps** | 3+ clicks to build cohort and run query. Complexity is expected for research tool. |
| **Keyboard shortcuts** | None. Would benefit from query shortcuts. |
| **Dead ends/confusion** | No query history. No export to statistical software (SPSS/R). No collaboration features. |

---

## 8. Cross-cutting Issues

### 8.1 Accessibility (Critical)
- **Zero ARIA attributes** found across all 35 views — screen reader support is absent.
- Color-only status indicators (red/green/amber) in DeviceMonitoring, QualityControl, WorkQueue.
- Clickable cards (`<div onClick>`) are not keyboard focusable.
- Tab panels lack `role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls`.
- Toast notifications not announced by screen readers (`role="alert"` / `aria-live`).
- No focus management — when views change or modals open, focus is not moved.
- Recharts visualizations have no accessible data table fallback.

### 8.2 Clinical Safety (High)
- No confirmation dialogs for destructive/consent-related actions (revoke consent, delete, etc.).
- AI interpretations shown directly to patients (SmartResultsView, CitizenAssistant) **without disclaimers**.
- No "last refreshed" timestamp on time-sensitive clinical data.
- No auto-refresh or staleness indicator for real-time device/data status.
- No undo support anywhere in the application.
- No duplicate prevention in forms (add medication, add family member, upload imaging).

### 8.3 Error Handling (Moderate)
- All errors go through `toast.error()` with generic messages.
- No contextual guidance on how to recover from errors.
- No retry mechanism on transient failures.
- No offline/network-loss handling.
- No error boundaries that gracefully degrade a section without crashing the whole view.

### 8.4 Empty States (Moderate)
- Only ~30% of views have explicit `<EmptyState>` components.
- Many views rely on mock data and never show empty states.
- Empty states that exist are good (illustration + message + CTA).
- Views missing empty states: AppointmentsView, LabResultsView, ImagingLabView, DeviceMonitoring, InventoryManagement, SampleTracking, DoctorIntelligence, MedicalHistoryView, AuditLog, SystemsArchitectureView.

### 8.5 Loading States (Good foundation)
- Most views have `TableSkeleton` or `DashboardSkeleton`.
- Charts and detail panels often lack dedicated skeletons.
- Some views use generic `Loader2` spinner instead of skeleton layout.
- No loading states for action submissions (beyond button spinner).

### 8.6 Mobile Responsiveness (Moderate)
- General pattern: `p-4 md:p-8`, `max-w-7xl mx-auto`, `flex-col md:flex-row`.
- Tables will horizontal-scroll on mobile (most views).
- Charts and maps (Recharts, maps) likely too small on mobile.
- Complex views (CohortBuilder, NationalHealthGrid, EpidemiologicalIntelligence) may be unusable on mobile.
- Touch targets not verified — icon buttons may be < 44px.
- No mobile-specific navigation patterns (bottom nav, swipe gestures).

### 8.7 Workflow Efficiency (Moderate)
- Most flows are 2-3 clicks — reasonable for healthcare complexity.
- **Gaps:**
  - No keyboard shortcuts anywhere.
  - No auto-save on multi-step forms (PatientRegistration).
  - No bulk operations on tables (WorkQueue, InventoryManagement).
  - No undo support.
  - No quick-search shortcuts (e.g., `/` to focus search).
- InventoryManagement: cannot update quantities (major workflow blocker).
- WorkQueue: no batch assignment.

### 8.8 Dead Ends & Confusing Flows (Moderate)
- InventoryManagement: no way to update quantity or delete items.
- FamilyManagement: no edit/remove flow for family members.
- MedicationCenter: no edit/discontinue medication flow.
- LabIntelligenceView: no way to clear upload history.
- ImagingLabView: no way to edit metadata after upload.
- DoctorIntelligence: AI recommendations have no "apply" action.
- AuditLog: no row detail expansion for truncated messages.
- IntegrationHub: no sync activity log or manual sync trigger.
- ConsentManagement: toggling is too easy — needs confirmation.

### 8.9 Recommendations (Priority Order)

1. **P0 — Clinical Safety**
   - Add disclaimers to all AI-generated content directed at patients.
   - Add confirmation dialogs for consent changes, destructive actions.
   - Add "last refreshed" timestamps to all clinical data displays.
   - Add staleness indicators for real-time device/data connections.

2. **P0 — Accessibility**
   - Add ARIA labels, roles, and states across all interactive elements.
   - Ensure all `onClick` elements are keyboard focusable.
   - Add accessible descriptions to color-only status indicators.
   - Implement focus management on navigation and modal open/close.

3. **P1 — Workflow Blockers**
   - Add quantity update flow to InventoryManagement.
   - Add edit/remove flows to FamilyManagement and MedicationCenter.
   - Add bulk operations to WorkQueue.
   - Add auto-save to multi-step forms.

4. **P1 — Error Handling**
   - Add contextual recovery guidance to error messages.
   - Add retry buttons on transient failures.
   - Add offline detection and graceful degradation.
   - Add React error boundaries per view section.

5. **P2 — Empty States**
   - Add `<EmptyState>` components to all views currently missing them.
   - Ensure empty states include actionable CTAs (Add, Create, Upload).

6. **P2 — Loading States**
   - Add dedicated skeletons for charts, maps, and detail panels.
   - Replace generic spinners with layout-preserving skeletons.

7. **P3 — Mobile Responsiveness**
   - Test and optimize table layouts for mobile (horizontal scroll wrappers).
   - Simplify complex views for mobile (progressive disclosure).
   - Verify all touch targets are ≥ 44×44px.

8. **P3 — Workflow Efficiency**
   - Add keyboard shortcuts (search, navigation, quick actions).
   - Add bulk actions to list/table views.
   - Implement undo for all destructive operations.
   - Add quick-search `/` shortcut across the app.

---

*End of audit — 35 view files reviewed.*
