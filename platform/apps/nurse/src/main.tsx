import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { purgeLegacyWorkboxQueue } from '@gula/ui-platform';

if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    await purgeLegacyWorkboxQueue();
    await navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
