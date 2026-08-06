---
id: FRONTEND-000001
type: frontend
title: "Frontend Knowledge Bridge"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 85%
tags: [frontend, react, typescript, bridge]
---

# Frontend Knowledge — Bridge Reference

## Stack
- React 18+ with TypeScript
- Vite (build tool, ~3.5s build)
- TailwindCSS (styling)
- Vitest (testing, 54 tests)
- ESLint + Prettier (linting)

## Structure
```
frontend-v3/
├── src/
│   ├── components/    # Reusable UI components
│   ├── pages/         # Page components (9 workflow pages)
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utility functions
│   ├── services/      # API service layer
│   └── test/          # Test setup (vitest)
├── vite.config.ts     # Vite + Vitest config
├── tsconfig.json      # TypeScript config
└── package.json
```

## Key Files
- `src/lib/utils.ts` — 46 utility function tests
- `src/hooks/useDebounce.ts` — Debounce hook
- `src/hooks/useToast.ts` — Toast notification hook
- `src/test/setup.ts` — Vitest setup (@testing-library/jest-dom)

## Quality Gates
- `npx tsc --noEmit` — 0 TypeScript errors
- `npx eslint src/` — 0 ESLint errors
- `npx vitest run` — 54/54 tests pass
- `npx vite build` — Production build succeeds

## Patterns
- Arabic-first (dir="rtl" in index.html)
- RTL layout throughout
- Role-based access (RBAC)
- Multi-tenant support
- API services use typed responses (no `as any`)

## Related
- `.ai/core/memory/PROJECT_MEMORY.md` — Frontend decisions
- `docs/frontend/UI_COMPONENT_CATALOG.md` — Component catalog
