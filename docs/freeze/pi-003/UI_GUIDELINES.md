# UI/UX GUIDELINES — PI-003 National Applications Suite

## 1. One Design System

The GULA National Applications Suite uses a single design system defined in
`shared/design_system/`. All four form factors (Desktop, Mobile, Web, PWA) share
the same tokens, components, and RTL patterns.

### 1.1 Design Tokens (`shared/design_system/tokens.py`)

```python
@dataclass(frozen=True)
class Colors:
    primary: str = "#1B5E20"        # Deep green — authority, health
    primary_light: str = "#4C8C4A"
    primary_dark: str = "#003300"
    secondary: str = "#0277BD"       # Blue — trust, information
    accent: str = "#FF6F00"          # Amber — warnings, attention
    error: str = "#D32F2F"
    background: str = "#FAFAFA"
    surface: str = "#FFFFFF"
    text_primary: str = "#212121"
    text_secondary: str = "#757575"
```

### 1.2 Typography

```python
@dataclass(frozen=True)
class Typography:
    font_family_arabic = '"Noto Sans Arabic", "Cairo", sans-serif'
    font_family_latin  = '"Inter", "Roboto", sans-serif'
    h1_size = "2.25rem"   # 36px
    h2_size = "1.875rem"  # 30px
    h3_size = "1.5rem"    # 24px
    body_size = "1rem"    # 16px
```

### 1.3 Spacing & Breakpoints

```python
@dataclass(frozen=True)
class Breakpoints:
    xs: str = "480px"    # Phone portrait
    sm: str = "768px"    # Phone landscape / tablet
    md: str = "1024px"   # Tablet landscape
    lg: str = "1280px"   # Desktop
    xl: str = "1440px"   # Large desktop
```

## 2. RTL & Arabic-First Design

GULA is an Arabic-first platform. The design system enforces RTL at every level.

### 2.1 RTL Styles (`shared/design_system/rtl.py`)

```python
RTLStyles = {
    "direction": "rtl",
    "text_align": "right",
    "font_family": '"Noto Sans Arabic", "Cairo", sans-serif',
    "flex_direction": "row-reverse",
    "padding_start": "padding-right",
    "padding_end": "padding-left",
    "border_start": "border-right",
    "border_end": "border-left",
}
```

### 2.2 Arabic-First Principles

1. **Default layout:** RTL is the default. LTR is the exception.
2. **Bilingual content:** All labels, messages, and errors have `detail_ar` fields.
3. **Date format:** `YYYY/MM/DD` (ISO Iraqi standard) in Arabic numerals.
4. **Number format:** Arabic-Indic digits (٠-٩) in Arabic mode, Western digits in English mode.
5. **Font stack:** Noto Sans Arabic first, Cairo second, then system fallback.

### 2.3 Bilingual UI Pattern

Every API response includes both languages:
```json
{
  "detail": "Patient record not found",
  "detail_ar": "سجل المريض غير موجود"
}
```

The UI renders the appropriate field based on `lang` parameter in the PWA manifest
(`"lang": "ar"` by default).

## 3. Responsive Design Patterns

### 3.1 Layout Grids

| Breakpoint | Columns | Max Width | Target |
|-----------|---------|-----------|--------|
| xs (<480px) | 4 | 100% | Phone |
| sm (480-768px) | 8 | 720px | Tablet portrait |
| md (768-1024px) | 12 | 960px | Tablet landscape |
| lg (1024-1280px) | 12 | 1140px | Desktop |
| xl (>1280px) | 12 | 1320px | Large desktop |

### 3.2 Adaptive Component Patterns

| Component | Mobile | Tablet | Desktop |
|-----------|--------|--------|---------|
| Navigation | Bottom bar | Side rail | Full sidebar |
| Data tables | Card list | Horizontal scroll | Full table |
| Modals | Full-screen sheet | Centered modal | Centered modal |
| Search | Full-screen overlay | Dropdown | Inline |
| Patient list | Swipeable cards | Split view | Full list + detail |
| Forms | Single column | Single column | Multi-column |

### 3.3 Touch Targets

Minimum touch target size: **44×44px** (WCAG 2.2 guideline).
All interactive elements meet this across all breakpoints.

## 4. Component Library

### 4.1 Defined Components (`shared/design_system/components.py`)

```python
class ButtonVariant(Enum): PRIMARY, SECONDARY, OUTLINE, GHOST, DANGER
class ButtonSize(Enum):    SM, MD, LG
class InputType(Enum):     TEXT, EMAIL, PASSWORD, NUMBER, TEL, DATE, FILE, SELECT, TEXTAREA
class TableVariant(Enum):  STRIPED, BORDERED, HOVER, COMPACT
```

| Component | Spec Class | States | Notes |
|-----------|-----------|--------|-------|
| Button | `ButtonSpec` | default, hover, active, disabled, loading | Full-width variant for mobile |
| Card | `CardSpec` | elevated, bordered | Padding variants: sm/md/lg |
| Dialog | `DialogSpec` | open, closable, confirm/cancel | Sizes: sm/md/lg; RTL enabled |
| Form | `FormSpec` | vertical (default) | Real-time validation |
| Input | `InputSpec` | default, focus, error, disabled | 9 input types supported |
| Table | `TableSpec` | striped, bordered, hover, compact | Sortable, paginated, RTL |
| Icon | `IconSpec` | 24px default | Lucide icon set |

### 4.2 Dark Mode Tokens

Dark mode uses inverted token values:

```python
dark_colors = {
    "background": "#121212",
    "surface": "#1E1E1E",
    "text_primary": "#E0E0E0",
    "text_secondary": "#9E9E9E",
    "border": "#333333",
}
```

All components support automatic dark mode via CSS `prefers-color-scheme`
with manual override for user preference.

## 5. Accessibility Guidelines

### 5.1 WCAG 2.2 Compliance Targets

| Level | Target | Status |
|-------|--------|--------|
| AA | All public-facing interfaces | Mandatory |
| AAA | Ministry Command Centre | Target |
| AA | All clinical workflows | Mandatory |

### 5.2 Keyboard Navigation

All desktop and web applications support full keyboard navigation:

- **Tab** — move focus forward
- **Shift+Tab** — move focus backward
- **Enter/Space** — activate
- **Escape** — close modal/dropdown
- **Arrow keys** — navigate lists, tables, date pickers
- **Ctrl+F** — search within current view

### 5.3 Screen Reader Support

- All icons have `aria-label` attributes
- Form inputs have associated `<label>` elements in both Arabic and English
- Dynamic content updates announce via `aria-live` regions
- Error messages are linked to inputs via `aria-describedby`
- Skip-to-content link present on every page

### 5.4 Color Contrast

| Token | Light Mode | Dark Mode | Ratio |
|-------|-----------|-----------|-------|
| text_primary | #212121 on #FAFAFA | #E0E0E0 on #121212 | 13.9:1 ✓ |
| text_secondary | #757575 on #FAFAFA | #9E9E9E on #121212 | 4.5:1 ✓ |
| link | #0277BD on #FAFAFA | #58A5F0 on #121212 | 4.8:1 ✓ |
| error | #D32F2F on #FAFAFA | #EF5350 on #121212 | 4.5:1 ✓ |

### 5.5 Focus Indicators

All focusable elements must show a visible focus ring:
- **Desktop:** 2px solid `secondary` (#0277BD) with 2px offset
- **Mobile:** 3px solid `secondary_light` (#58A5F0)
- **Never** use `outline: none` without a replacement

### 5.6 Motion & Animation

- All animations respect `prefers-reduced-motion`
- Default animation duration: 200-300ms
- No auto-playing animations on critical care screens
- Skeleton loading states preferred over spinners

## 6. Form Patterns

### 6.1 Clinical Data Entry

- **Auto-save:** Forms save draft every 30s when connected
- **Offline queue:** Mutations queued locally when offline, synced on reconnect
- **Idempotency:** All mutations include `Idempotency-Key` header for safe retry
- **Validation:** Real-time client-side + server-side (Pydantic)
- **RTL-aware inputs:** `input_direction: "rtl"` for Arabic text input

### 6.2 Error Handling

```json
{
  "detail": "National ID is required",
  "detail_ar": "الرقم الوطني مطلوب",
  "field": "national_id",
  "code": "validation_required"
}
```

Field-level errors displayed inline below the input. Toast notifications for
system-level errors (network, timeout, server error).

## 7. Platform-Specific Guidelines

### 7.1 Desktop (PySide6)

- Full window management (minimize, maximize, close)
- Multi-monitor support
- System tray for background lab instrument monitoring
- Native file dialogs for report export
- Local printer integration for barcode/label printing
- Keyboard shortcuts documented in `docs/UX_KEYBOARD_SHORTCUTS.md`

### 7.2 Mobile (Flutter/Kotlin)

- Bottom navigation bar (max 5 items)
- Pull-to-refresh for data refresh
- Swipe gestures for common actions
- Biometric authentication (fingerprint, face)
- Haptic feedback on critical actions
- Orientation: portrait preferred

### 7.3 Web/PWA (React)

- URL-based routing for deep linking
- Responsive sidebar collapse on small screens
- Infinite scroll for long lists (patient list, results)
- Service worker update notification
- PWA install prompt
