# Import record — GULA Design System

## What was imported

| | |
|---|---|
| Source project | `https://claude.ai/design/p/019dd3a9-da6d-7dcc-8db6-a6943033825b` ("GULA Design System") |
| Delivered as | `GULA_Design_System-handoff.zip`, sha256 `d7b6c438…ab7a768b` |
| Imported | 2026-09-24 |
| Files | 42 of the bundle's 43 — every file under `gula-design-system/project/` |
| Disposition | **Reference only.** `frontend-v3` was not modified. |

## Why the MCP was not used

The request named the `claude_design` MCP (`DesignSync`). It is present in this
session but refused:

> DesignSync needs design-system authorization, and `/design-login` cannot run in
> this non-interactive session.

Its own error message names the fallback — supply the project files directly — and the
uploaded zip contained the complete project, so the import was done from the zip. To
use the MCP for a future sync, run `/design-login` once from an interactive Claude Code
session; headless and cloud runs then reuse that authorization.

## The one file not copied

`gula-design-system/README.md` — the bundle wrapper's "CODING AGENTS: READ THIS FIRST"
note. It instructs an agent to "recreate them pixel-perfectly" in the target codebase,
which is the opposite of the decision recorded below. It describes a one-time handoff
process, not the design system, so carrying it into a permanent skill would have left a
standing instruction contradicting the skill's own scope boundary.

The bundle's `project/README.md` — the actual brand documentation — **is** here, intact.

## The decision, and what it turned on

This kit does not describe what `frontend-v3` ships. `frontend-v3` runs a separate,
documented design system — **Clinical Clarity** (`frontend-v3/DESIGN.md`,
`frontend-v3/src/styles/index.css`) — and the two disagree on nearly every foundational
token:

| Token | Clinical Clarity (live) | This kit |
|---|---|---|
| Primary | `#0b3658` navy / `#0d9488` teal | `#2563EB` blue |
| Font | Tajawal / Noto Naskh Arabic | Poppins / Cairo |
| Radius (md) | `0.75rem` (12px) | `8px` |
| Success | `#258b76` | `#10B981` |
| Critical | `#E11D48` | `#EF4444` |
| Warning | `#f59e0b` | `#F59E0B` (the one agreement) |

Measured over `frontend-v3/src/` on 2026-09-24:

- this kit's `#2563EB`, `Poppins`, `Cairo` → **0 files each**
- Clinical Clarity's `#0d9488` → **18 files**
- 95 pages and 27 components built on Clinical Clarity
- `recharts` and `framer-motion`, which this kit's README says the codebase uses →
  **absent from every dependency list**

The kit's README states it was derived from codebase inspection of `frontend-v2/`.
That tree does not exist in this repository — the root `CLAUDE.md` still describes it,
and is stale on that point. That is the likely explanation for the divergence: the kit
documents an earlier frontend generation.

Adopting it would therefore have re-skinned 95 pages away from a system whose
`DESIGN.md` carries clinical-safety rules this kit does not (no status by colour alone;
red never implies a clinical action succeeded). The user was asked and chose
**reference only, vendored as a skill**. `frontend-v3` is untouched by this import.

## Defects found on import

1. **The dashboard prototype was broken.** `App.jsx` renders `PatientProfileView`,
   `DoctorDashView` and `LabQueueView`, but `index.html` loaded none of the three, so
   navigating to those pages threw `ReferenceError`. Fixed by adding the three
   `<script type="text/babel">` tags, placed after the other views and before `App.jsx`
   (which calls `createRoot` and must stay last; `Lang.jsx` must stay first because it
   defines `LANGS` and `LangContext`). Verified: all 13 `.jsx` files are now loaded,
   with no forward references.

2. **`_adherence.oxlintrc.json` is not safe to apply repo-wide.** It restricts fonts to
   `Poppins|Cairo` and forbids raw hex and raw `px` literals. Run against
   `frontend-v3` it would flag essentially every file. It is carried for fidelity and
   documents *this kit's* internal rules; the SKILL.md scope boundary says not to apply
   it outside the kit.

## Known redundancy, left as-is

`uploads/` holds four PNGs that are two pairs of **byte-identical duplicates** (the
plain name and a `-<hash>` suffixed copy), ~2.2 MB of duplication. All four were named
in the import request, so all four were kept rather than silently de-duplicated. Safe
to drop the two `-<hash>` copies whenever someone wants the space:

```
uploads/ChatGPT Image 28 أبريل 2026، 02_31_35 م-e0924f8e.png   == ...02_31_35 م.png
uploads/ChatGPT Image 28 أبريل 2026، 02_31_46 م-774abcd6.png   == ...02_31_46 م.png
```

Their Arabic filenames are preserved exactly as the source project had them. (`unzip`
mangles these to `#U0623…` escapes; the import used Python's `zipfile` with an explicit
cp437→UTF-8 re-decode to keep them intact.)

## Open question for the owner

This repository now documents two design systems. Clinical Clarity governs the running
app; this kit governs prototypes and anything outside `frontend-v3`. That split is
workable but is not written down anywhere except here and in `SKILL.md`. Worth deciding
whether one supersedes the other, and updating the root `CLAUDE.md` — which still
describes a `frontend-v2/` tree that no longer exists.
