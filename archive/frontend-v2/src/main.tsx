import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import {initTelemetry} from './lib/telemetry';

// Fire-and-forget — telemetry init must NEVER block first paint.
// Failures inside initTelemetry are caught and logged structurally;
// the app still renders even if PostHog / Sentry are unavailable.
initTelemetry();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
