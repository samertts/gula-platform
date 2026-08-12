# GULA Preview Environment — Developer Guide

## Architecture

```
frontend-v2/
├── src/
│   ├── mock/           # Mock backend services
│   │   ├── config.ts        # Feature flags & environment
│   │   ├── dataStore.ts     # Synthetic data store
│   │   ├── demoData.ts      # Data generators
│   │   ├── handlers.ts      # API route handlers
│   │   └── mockService.ts   # Fetch interceptor
│   ├── demo/           # Demo/preview UI components
│   │   ├── demoAuth.tsx      # Role-based authentication
│   │   ├── featureFlags.tsx  # Feature flag system
│   │   ├── demoBanner.tsx    # DEMO banner overlay
│   │   ├── roleSwitcher.tsx  # Role switching dropdown
│   │   ├── demoDataPanel.tsx # Data management widget
│   │   └── experienceCenter.tsx # App launcher
```

## Mock Service Architecture

The mock service intercepts `window.fetch` calls and routes them to in-memory handlers:

```typescript
// Initialization
import { MockService } from './mock';

const mock = MockService.getInstance();
await mock.initialize();  // Generates 1000+ synthetic records
```

### Adding New Mock Endpoints

Edit `handlers.ts` and add a new route handler:

```typescript
if (path.startsWith('/api/new-endpoint')) {
  return {
    status: 200,
    body: { data: store.get('collection'), total: store.get('collection').length }
  };
}
```

### Feature Flags

```typescript
import { getConfig, setFeatureFlag, isFeatureEnabled } from './mock';

// Check if feature is enabled
if (isFeatureEnabled('ai')) {
  // Show AI features
}

// Toggle feature
setFeatureFlag('experimental', true);
```

## Demo Authentication

```typescript
import { DemoAuthProvider, useDemoAuth } from './demo';

// In your component
const { user, login, switchRole, isDemoMode } = useDemoAuth();

// Login as a specific role
login('lab_manager');
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_USE_MOCK` | `false` | Enable mock backend |
| `VITE_DEMO_MODE` | `false` | Enable demo features |
| `VITE_FEATURE_AI` | `true` | AI feature flag |
| `VITE_FEATURE_OCR` | `true` | OCR feature flag |
| `VITE_FEATURE_FHIR` | `true` | FHIR feature flag |
| `VITE_DEMO_BANNER` | `true` | Show demo banner |

## Synthetic Data

The `DemoDataGenerator` creates realistic healthcare data:

```typescript
import { DemoDataGenerator } from './mock';

const generator = new DemoDataGenerator();
const patients = generator.generatePatients(1000);  // Arabic/English
const results = generator.generateLabResults(5000); // Medical results
```

## Building

```bash
# Production build (mock disabled)
cd frontend-v2 && npm run build

# Preview build (mock enabled)
VITE_USE_MOCK=true VITE_DEMO_MODE=true npm run build

# Development with mock
VITE_USE_MOCK=true VITE_DEMO_MODE=true npm run dev
```
