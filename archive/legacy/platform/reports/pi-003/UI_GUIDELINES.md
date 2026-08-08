# PI-003 — UI Guidelines

## National Applications Design System

**Version:** 1.0.0
**Package:** `@gula/ui-platform`

---

## 1. Color Palette

### 1.1 Brand Colors (Primary)

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| primary-500 | `#6366f1` | `#818cf8` | Primary buttons, links, active states |
| primary-600 | `#4f46e5` | `#6366f1` | Hover states |
| primary-700 | `#4338ca` | `#4f46e5` | Active/pressed states |

### 1.2 Semantic Colors

| Role | Light | Dark |
|------|-------|------|
| **success** | `#22c55e` | `#4ade80` |
| **warning** | `#f59e0b` | `#fbbf24` |
| **danger** | `#ef4444` | `#f87171` |
| **info** | `#3b82f6` | `#60a5fa` |

### 1.3 App-Specific Accent Colors

| App | Primary Hue | Token |
|-----|-------------|-------|
| Citizen | Indigo | `primary` |
| Doctor | Blue | `info` |
| Lab | Purple | `lab` |
| Radiology | Pink | `radiology` |
| Pharmacy | Teal | `pharmacy` |
| Hospital | Slate | `neutral` |
| Nurse | Sky | `info` |
| Ministry | Indigo | `primary` |
| Emergency | Orange | `emergency` |

### 1.4 Surface & Background (Light Mode)

| Token | Value | Usage |
|-------|-------|-------|
| `--gula-bg` | `#f8fafc` | Page background |
| `--gula-surface` | `#ffffff` | Cards, modals, dropdowns |
| `--gula-surface-secondary` | `#f1f5f9` | Secondary surfaces, hover states |
| `--gula-text` | `#1e293b` | Primary text |
| `--gula-text-secondary` | `#64748b` | Secondary text, labels |
| `--gula-border` | `#e2e8f0` | Borders, dividers |
| `--gula-border-light` | `#f1f5f9` | Subtle borders |

### 1.5 Surface & Background (Dark Mode)

| Token | Value | Usage |
|-------|-------|-------|
| `--gula-bg` | `#0f172a` | Page background |
| `--gula-surface` | `#1e293b` | Cards, modals, dropdowns |
| `--gula-surface-secondary` | `#334155` | Secondary surfaces, hover states |
| `--gula-text` | `#f1f5f9` | Primary text |
| `--gula-text-secondary` | `#94a3b8` | Secondary text, labels |
| `--gula-border` | `#334155` | Borders, dividers |
| `--gula-border-light` | `#1e293b` | Subtle borders |

### 1.6 Full Color Scale

Each semantic family has 11 shades (50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950) for fine-grained control.

---

## 2. Typography

### 2.1 Font Families

| Category | English | Arabic |
|----------|---------|--------|
| **Sans** (body) | Inter | Tajawal, Cairo |
| **Display** (headings) | Outfit, Inter | Noto Naskh Arabic, Tajawal |
| **Mono** (code) | JetBrains Mono | JetBrains Mono |

### 2.2 Type Scale

| Category | Size | Font Size | Line Height | Weight | Usage |
|----------|------|-----------|-------------|--------|-------|
| **Display** | xs | 1.875rem | 2.25rem | 800 | Hero text (mobile) |
| | sm | 2.25rem | 2.5rem | 800 | Hero text |
| | md | 3rem | 1 | 800 | Page title |
| | lg | 3.75rem | 1 | 900 | Large hero |
| | xl | 4.5rem | 1 | 900 | Marketing hero |
| **Heading** | xs | 1.25rem | 1.75rem | 700 | Section header |
| | sm | 1.5rem | 2rem | 700 | Card title |
| | md | 1.875rem | 2.25rem | 700 | Page section |
| | lg | 2.25rem | 2.5rem | 700 | Page header |
| **Body** | xs | 0.75rem | 1rem | 400 | Small text, captions |
| | sm | 0.875rem | 1.25rem | 400 | Body text (compact) |
| | md | 1rem | 1.5rem | 400 | Body text (default) |
| | lg | 1.125rem | 1.75rem | 400 | Body text (large) |
| **Label** | xs | 0.625rem | 0.875rem | 700 | Field label, badge |
| | sm | 0.75rem | 1rem | 700 | Small label |
| | md | 0.875rem | 1.25rem | 600 | Standard label |

### 2.3 Arabic Typography Notes

- Arabic text uses 10-15% larger font size at the same scale for readability
- Line height is increased by 0.125rem for Arabic text
- Font weight 700 for Arabic body text improves readability on screens
- All numbers are rendered in Eastern Arabic numerals (٠١٢٣٤٥٦٧٨٩) for Arabic locale

---

## 3. Spacing & Layout

### 3.1 Spacing Scale

| Token | Rem | Px (16px base) |
|-------|-----|----------------|
| 0 | 0 | 0 |
| 0.5 | 0.125rem | 2px |
| 1 | 0.25rem | 4px |
| 2 | 0.5rem | 8px |
| 3 | 0.75rem | 12px |
| 4 | 1rem | 16px |
| 5 | 1.25rem | 20px |
| 6 | 1.5rem | 24px |
| 8 | 2rem | 32px |
| 10 | 2.5rem | 40px |
| 12 | 3rem | 48px |
| 16 | 4rem | 64px |
| 20 | 5rem | 80px |
| 24 | 6rem | 96px |

### 3.2 Layout Grid

- **Max content width:** 1280px (xl breakpoint)
- **Content padding:** 16px mobile, 24px tablet, 32px desktop
- **Card grid:** 1 col mobile, 2 col tablet, 3 col desktop
- **Sidebar width:** 280px collapsed, 64px expanded

### 3.3 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `sm` | 0.125rem | Checkbox, tag |
| `md` | 0.375rem | Input field |
| `lg` | 0.5rem | Card, button |
| `xl` | 0.75rem | Modal, dropdown |
| `2xl` | 1rem | Large card, dialog |
| `full` | 9999px | Pill, badge, avatar |

---

## 4. Responsive Breakpoints

| Breakpoint | Min Width | Target |
|------------|-----------|--------|
| **xs** | 0px | Mobile phones (portrait) |
| **sm** | 640px | Mobile phones (landscape), small tablets |
| **md** | 768px | Tablets (portrait) |
| **lg** | 1024px | Tablets (landscape), small desktops |
| **xl** | 1280px | Desktops |
| **2xl** | 1536px | Large desktops, TVs |

**Container max-widths:**
- sm: 640px, md: 768px, lg: 1024px, xl: 1280px, 2xl: 1536px

---

## 5. Component Usage Guidelines

### 5.1 Button

| Variant | Usage |
|---------|-------|
| `primary` | Primary action (1 per view) |
| `secondary` | Secondary action, cancel |
| `outline` | Subtle action, alternative choice |
| `ghost` | Lowest emphasis, toolbar action |
| `danger` | Destructive action (delete, revoke) |

**Sizes:** xs (20px), sm (28px), md (36px), lg (44px), xl (52px)

### 5.2 Modal

- Always provides a close button (×) and ESC key handler
- Focus is trapped within modal when open
- Background is scrimmed at 50% opacity
- Return focus to trigger element on close
- Size variants: sm (384px), md (512px), lg (640px), xl (800px), full (viewport)

### 5.3 DataTable

- Sortable columns (click header to toggle sort)
- Configurable page sizes: 10, 20, 50, 100
- Row actions via action column with dropdown menu
- Bulk selection for batch operations
- Empty state shown when no data matches filters

### 5.4 Forms

- Labels above inputs (Arabic: right-aligned)
- Validation errors appear below input field
- Required fields marked with red asterisk (Arabic: right side)
- Submit button disabled until all required fields pass validation
- Autosave on field blur for long forms

---

## 6. Accessibility (WCAG 2.1 AA)

### 6.1 Compliance Targets

| Criterion | Target | Status |
|-----------|--------|--------|
| 1.1.1 Non-text Content | AA | Pass |
| 1.3.1 Info and Relationships | AA | Pass |
| 1.4.3 Contrast (Minimum) | AA (4.5:1) | Pass |
| 1.4.4 Resize text | AA (200%) | Pass |
| 2.1.1 Keyboard | AA | Pass |
| 2.4.3 Focus Order | AA | Pass |
| 2.4.7 Focus Visible | AA | Pass |
| 3.3.1 Error Identification | AA | Pass |
| 3.3.2 Labels or Instructions | AA | Pass |
| 4.1.2 Name, Role, Value | AA | Pass |

### 6.2 Implementation

- All interactive elements are keyboard accessible
- Focus indicators use 3px ring with offset (focus-visible)
- ARIA labels on all icon-only buttons
- Screen reader announcements for async updates
- Skip-to-content link at top of each page
- Color is never the sole indicator of meaning
- `prefers-reduced-motion` respected (animations disabled)
- Touch targets minimum 44×44px on mobile

---

## 7. RTL Layout Guidelines

- Mirror layout horizontally when direction switches to RTL
- Icons with directional meaning are flipped (arrows, chevrons)
- Text alignment follows direction (right-aligned in RTL)
- Padding/margin start/end used instead of left/right
- Form labels positioned to the right in RTL
- Button icon positions swap automatically (iconPosition flips)
- Sidebar navigation: items aligned to the right, expand chevron on left
- Breadcrumb separators flip
- Pagination: previous/next buttons swap sides

---

## 8. Iconography

- 60+ SVG icons in `@gula/ui-platform/icons`
- 24×24px default size
- strokeWidth: 2 (standard), 1.5 (dense), 2.5 (bold)
- Custom healthcare icons: lab, radiology, pharmacy, nurse, emergency
- Directional icons auto-flip with `transform: scaleX(-1)` in RTL mode
- Icon colors inherit from current text color via `currentColor`

---

## 9. Loading, Empty & Error State Patterns

### 9.1 Loading States

| Pattern | Usage |
|---------|-------|
| **Spinner** | Inline button loading, content refresh |
| **Skeleton** | Page/card loading (preferred for perceived performance) |
| **Progress bar** | File upload, multi-step form |
| **Shimmer** | List loading (rows fade in with animated gradient) |

### 9.2 Empty States

- Illustration + descriptive text + optional CTA
- Examples: "No results found", "No appointments scheduled", "No lab results yet"
- Contextual suggestions: "Try adjusting filters", "Schedule your first appointment"

### 9.3 Error States

- **ErrorBoundary** catches unhandled React errors, shows retry button
- **Alert** component for inline errors (dismissible)
- **Toast notifications** for transient errors (auto-dismiss 5s)
- **Network errors** show offline indicator + "Retry" when connection restores

---

## 10. Shadow Elevation

| Level | Shadow | Usage |
|-------|--------|-------|
| sm | `0 1px 2px 0 rgba(0,0,0,0.05)` | Subtle card |
| default | `0 1px 3px 0 rgba(0,0,0,0.1)` | Card default |
| md | `0 4px 6px -1px rgba(0,0,0,0.1)` | Dropdown, popover |
| lg | `0 10px 15px -3px rgba(0,0,0,0.1)` | Modal, drawer |
| xl | `0 20px 25px -5px rgba(0,0,0,0.1)` | Full-screen modal |
| 2xl | `0 25px 50px -12px rgba(0,0,0,0.25)` | Toast, notification |
| inner | `inset 0 2px 4px 0 rgba(0,0,0,0.05)` | Inset input |

---

## 11. Motion & Animation

- Duration: 200ms (micro-interactions), 300ms (transitions), 500ms (page transitions)
- Easing: `ease-out` for enter, `ease-in` for exit
- Page transitions: fade + subtle slide (100px)
- Respects `prefers-reduced-motion`: all animations reduced to opacity-only
- Button press: `scale(0.97)` with 150ms
- Modal enter: scale(0.95 → 1) + fade, 200ms
- Toast enter: slide in from top, 300ms
