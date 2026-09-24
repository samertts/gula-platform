---
name: gula-design
description: Use this skill to generate well-branded interfaces and assets for GULA Platform, an Arabic-first medical laboratory SaaS for Iraq and the MENA region. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping. Reference only — this is NOT the theme frontend-v3 ships; see the scope boundary below before touching production code.
user-invocable: true
---

# GULA Design System (reference kit)

## SCOPE BOUNDARY — read this before writing any code

**This skill is a reference kit. It is not the design system `frontend-v3` runs on.**

`frontend-v3` ships a different, governed design system called **Clinical Clarity**,
documented in `frontend-v3/DESIGN.md` and implemented as Tailwind 4 `@theme` tokens
in `frontend-v3/src/styles/index.css`. The two disagree on nearly every foundational
token:

| | Clinical Clarity (what the app runs) | This kit |
|---|---|---|
| Primary | `#0b3658` navy / `#0d9488` teal | `#2563EB` blue |
| Font | Tajawal / Noto Naskh Arabic | Poppins / Cairo |
| Radius (md) | `0.75rem` (12px) | `8px` |
| Success | `#258b76` | `#10B981` |
| Critical | `#E11D48` | `#EF4444` |

Measured 2026-09-24: this kit's palette and fonts appear in **0** files under
`frontend-v3/src/`; Clinical Clarity's teal appears in **18**. 95 pages and 27
components are built on Clinical Clarity.

**Therefore:**

- ✅ **DO** use this kit for standalone mockups, throwaway prototypes, slides,
  marketing pages, and anything that is not `frontend-v3`.
- ✅ **DO** read `README.md` here for brand voice, Arabic copy conventions, and
  product context — that guidance is accurate and not in conflict with anything.
- ❌ **DO NOT** apply these colors, fonts or radii to `frontend-v3`. Re-skinning it
  is a decision its owner makes explicitly, not a side effect of loading a skill.
- ❌ **DO NOT** apply `_adherence.oxlintrc.json` repo-wide. It restricts fonts to
  "Poppins, Cairo" and would flag every existing `frontend-v3` file. It describes
  *this kit's* internal rules only.
- ❌ **DO NOT** copy the `ui_kits/dashboard/` views into `frontend-v3` pages. They
  carry hard-coded mock data, and `verify:contracts` / `verify:data-sources` exist
  to block exactly that.

If a task seems to need this kit applied to production code, stop and ask the user.

`DESIGN.md` also carries clinical-safety rules this kit does not: do not encode
clinical status with color alone, and red must never imply a clinical action
succeeded. Those rules win wherever the two overlap.

## What is here

Read `README.md` first — brand overview, Arabic-first copy conventions, visual
foundations and the file index. Then explore:

| Path | What it is |
|---|---|
| `colors_and_type.css` | CSS custom properties: color, type scale, spacing, radii, shadows. Light + dark. |
| `assets/` | Logo (horizontal, mark), brand lockup, icon system sheet. |
| `preview/` | 14 self-contained HTML specimens — colors, type (Latin + Arabic), buttons, badges, forms, tables, stat cards, charts, nav, spacing. Open in a browser. |
| `ui_kits/dashboard/` | Interactive prototype: 10 screens, 5 languages, dark mode. React 18 UMD + Babel-in-browser. Open `index.html` directly — no build step. |
| `uploads/` | Source reference imagery the design was derived from. |
| `_ds_bundle.js`, `_ds_manifest.json` | Claude Design tooling artifacts; carried for fidelity, not used at runtime. |

## How to use it

If creating visual artifacts (slides, mocks, throwaway prototypes), copy assets out
and create static HTML files for the user to view.

If the user invokes this skill without other guidance, ask them what they want to
build or design, ask some questions, and act as an expert designer — but respect the
scope boundary above when the target is `frontend-v3`.

## Provenance

Exported from Claude Design project `019dd3a9-da6d-7dcc-8db6-a6943033825b`
("GULA Design System") and vendored here on 2026-09-24. Its README states it was
derived from codebase inspection of an earlier frontend tree (`frontend-v2/`), which
no longer exists in this repository — which is why it does not match what ships.
See `PROVENANCE.md` for the full import record and the defects found on import.
