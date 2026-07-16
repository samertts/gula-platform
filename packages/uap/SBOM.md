# Software Bill of Materials — @gula/uap v1.0.0

## Package Metadata
- Name: @gula/uap
- Version: 1.0.0
- License: PROPRIETARY
- Author: GULA Platform Team

## Runtime Dependencies
| Package | Version | License |
|---------|---------|---------|
| clsx | ^2.1.1 | MIT |
| tailwind-merge | ^3.0.0 | MIT |
| idb | ^8.0.0 | ISC |
| zod | ^3.23.0 | MIT |
| react | ^19.0.0 | MIT |
| react-dom | ^19.0.0 | MIT |
| react-router-dom | ^7.0.0 | MIT |
| lucide-react | ^0.546.0 | ISC |
| zustand | ^5.0.0 | MIT |
| date-fns | ^4.0.0 | MIT |
| zustand-persist | ^0.4.0 | MIT |

## Dev Dependencies
| Package | Version | License |
|---------|---------|---------|
| typescript | ^5.5.0 | Apache-2.0 |
| vite | ^6.0.0 | MIT |
| vitest | ^2.0.0 | MIT |
| @vitejs/plugin-react | ^4.0.0 | MIT |

## Subpath Exports
- `@gula/uap/tokens` — Design tokens
- `@gula/uap/components` — UI components
- `@gula/uap/runtime` — Application runtime
- `@gula/uap/offline` — Offline platform
- `@gula/uap/device` — Device platform
- `@gula/uap/update` — Update platform
- `@gula/uap/marketplace` — Marketplace
- `@gula/uap/notifications` — Notification platform
- `@gula/uap/printing` — Printing platform
- `@gula/uap/telemetry` — Telemetry
- `@gula/uap/sdk` — Developer SDK
- `@gula/uap/quality` — Quality gates

## Security
- No known CVEs in dependency tree (as of build date)
- All dependencies audited via `pnpm audit`
- Minimum Node.js version: 20
