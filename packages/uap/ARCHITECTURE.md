# GULA Unified Application Platform - Architecture Guide

## Overview
The UAP (`@gula/uap`) is the single application runtime for all GULA applications.
It provides every cross-cutting concern as importable modules.

## Package Structure

```
packages/uap/
├── src/
│   ├── index.ts              # Main entry — re-exports everything
│   ├── tokens/               # Design tokens (colors, typography, spacing)
│   ├── components/           # UI components
│   │   ├── ui/               # Button, Card, Dialog, Input, Table, etc.
│   │   ├── charts/           # Chart components
│   │   ├── layout/           # Layout components
│   │   └── utils.ts          # cn(), rtl(), isRtl()
│   ├── runtime/              # Application runtime
│   │   ├── i18n/             # Internationalization
│   │   ├── auth/             # Authentication & authorization
│   │   ├── config/           # Application configuration
│   │   ├── plugins/          # Plugin loader
│   │   ├── features/         # Feature flags
│   │   ├── errors/           # Error handling
│   │   ├── recovery/         # Crash recovery
│   │   ├── shell/            # App shell & layout
│   │   └── state/            # Global state management
│   ├── offline/              # Offline platform
│   │   ├── db/               # Encrypted IndexedDB storage
│   │   ├── sync/             # Sync queue & engine
│   │   ├── conflict/         # Conflict resolution
│   │   └── queue/            # Compression, delta, retry
│   ├── device/               # Device platform
│   ├── update/               # Update platform
│   ├── marketplace/          # App marketplace
│   ├── notifications/        # Notification platform
│   ├── printing/             # Printing platform
│   ├── telemetry/            # Application telemetry
│   ├── sdk/                  # Developer SDK
│   └── quality/              # Quality gates
```

## Import Paths

```typescript
// Main
import { Button, Card, useAuth, useI18n } from '@gula/uap'

// Subpath (for tree-shaking)
import { Button } from '@gula/uap/components'
import { useAuth } from '@gula/uap/runtime'
import { useSyncQueue } from '@gula/uap/offline'
```

## Key Design Decisions

### State Management
- Zustand for all state (runtime, UI, offline)
- Persistence middleware for app state and config
- No Redux — keeping dependency lightweight

### Offline Storage
- IndexedDB via `idb` wrapper
- XOR encryption at rest (key from config)
- Sync queue with configurable backoff and retry

### Theming
- CSS custom properties via Tailwind
- Dark mode via class strategy
- RTL via `dir` attribute on root
- High contrast via separate stylesheet

### Internationalization
- Stores translations per locale as key-value maps
- Runtime locale switching updates `dir` attribute
- Pluralization and parameter interpolation supported

## Future Applications
Every new GULA application:
1. Adds `@gula/uap` as dependency
2. Imports components from `@gula/uap/components`
3. Uses `useAuth` for authentication
4. Uses `useI18n` for translations
5. Implements offline with `@gula/uap/offline`
