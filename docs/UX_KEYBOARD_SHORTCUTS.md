# GULA Platform — Keyboard Shortcuts

A user-facing reference. Press **`?`** anywhere in the app to open the same
list as a popup overlay.

> Shortcuts are automatically suspended while focus is in any text input,
> textarea, select, or `contenteditable` region — typing in those fields will
> never trigger a navigation hotkey.

---

## Global

| Keys              | Action                                |
|-------------------|---------------------------------------|
| `Cmd K` / `Ctrl K`| Open the command palette              |
| `/`               | Focus the command-palette search      |
| `?`               | Open this shortcuts overlay           |
| `Esc`             | Close any open modal / cancel action  |

## Navigation (Vim-style chords)

Press the keys in sequence within ~1.5 s of each other.

| Keys  | Goes to                    | Route |
|-------|----------------------------|-------|
| `g d` | Dashboard                  | `/`   |
| `g p` | Patients (Health Records)  | `/patients` |
| `g a` | Appointments               | `/appointments` |
| `g i` | Medical Intelligence       | `/intelligence` |
| `g l` | Laboratory                 | `/lab/dashboard` |
| `g q` | Lab Work Queue             | `/lab/queue` |
| `g s` | Settings                   | `/settings` |
| `g h` | Open this shortcuts page   | — |

> Wing-restricted destinations (e.g. `/lab/queue`) follow the same RBAC the
> sidebar enforces. If your role lacks permission, the palette hides the
> command and the chord becomes a no-op.

## Inside the command palette

| Keys      | Action                       |
|-----------|------------------------------|
| `↑` / `↓` | Move selection               |
| `Home`    | Jump to first result         |
| `End`     | Jump to last result          |
| `Enter`   | Run the highlighted command  |
| `Esc`     | Close (focus returns to opener) |

## Lists & tables

| Keys           | Action                                    |
|----------------|-------------------------------------------|
| `Tab`          | Move focus across rows / form controls    |
| `Enter`/`Space`| Activate the focused row (open record)    |

---

## Adding shortcuts

To register a new chord, edit
`frontend-v2/src/App.tsx` → `GlobalShortcuts`:

```ts
useKeySequence({
  // existing entries…
  'g x': () => navigate('/some/path'),
});
```

To register a single keystroke (with optional modifiers):

```ts
import { useShortcut } from '@/lib/useShortcut';

useShortcut('s', save, { modifiers: ['mod'] }); // ⌘S / Ctrl+S
useShortcut('Escape', close);
```

The hook automatically:
- ignores keystrokes inside editable fields,
- normalises `mod` to ⌘ on macOS and Ctrl on Windows/Linux,
- calls `e.preventDefault()` on a match (override with `preventDefault: false`).

To add a command to the palette, edit
`frontend-v2/src/lib/commandRegistry.ts`:

```ts
{
  id: 'nav.example',
  label: (t) => 'Example',
  category: 'tools',
  icon: SomeLucideIcon,
  shortcut: ['G', 'X'],          // optional — visual hint only
  wings: ['lab', 'admin'],       // optional — RBAC gate
  keywords: ['demo', 'sample'],  // optional — fuzzy search
  run: ({ navigate }) => navigate('/some/path'),
},
```

Then update `ShortcutsModal.tsx` if the new shortcut deserves to appear in
the help overlay.
