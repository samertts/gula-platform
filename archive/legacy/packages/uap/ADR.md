# ADR-001: Unified Application Platform Architecture

## Status
Accepted

## Context
Multiple frontend applications (frontend-v2, client) shared no common runtime, causing:
- Duplicated authentication, routing, state management patterns
- Inconsistent UI/UX across applications
- No shared offline or sync capabilities
- No centralized device management or update system
- Separate i18n implementations

## Decision
Build `@gula/uap` — a single Unified Application Platform package that:
1. Provides all cross-cutting concerns as a single dependency
2. Follows the existing monorepo structure
3. Reuses the existing `shared/` Python design system specs as TypeScript types
4. Uses Zustand for state (lightweight, TypeScript-first, works with React 18/19)
5. Uses IndexedDB for offline storage (ubiquitous, no additional dependencies)
6. Exports via subpath imports for tree-shaking
7. Supports both ESM and CJS consumers

## Consequences
Positive:
- Single source of truth for all application infrastructure
- Future apps depend only on `@gula/uap`
- Consistent UX across all GULA applications
- Reduced bundle sizes through shared dependencies
- Backward compatible — existing apps continue working

Negative:
- Existing apps must migrate to consume from `@gula/uap` (phased approach)
- New team members must learn the UAP conventions

## Compliance
- Every future GULA application MUST import from `@gula/uap`
- No application MAY duplicate UAP-provided functionality
- The `packages/uap/` directory is frozen after v1.0
- Changes require ADR and committee approval
