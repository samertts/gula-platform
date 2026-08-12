import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { purgeLegacyWorkboxQueue } from '@gula/ui-platform';

async function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      });

      if (registration.active) {
        console.info('[GULA Lab] Service Worker registered');
      }

      if ('SyncManager' in window) {
        try {
          const status = await (navigator as any).permissions.query({
            name: 'periodic-background-sync',
          });
          if (status.state === 'granted') {
            await (registration as any).periodicSync.register('gula-lab-sync', {
              minInterval: 6 * 60 * 60 * 1000,
            });
          }
        } catch { /* ignore */ }
      }
    } catch (error) {
      console.warn('[GULA Lab] Service Worker registration failed:', error);
    }
  }
}

async function initializeApp() {
  try {
    await purgeLegacyWorkboxQueue();
    await registerServiceWorker();
  } catch { /* ignore */ }

  const rootElement = document.getElementById('root');
  if (!rootElement) throw new Error('Root element not found');

  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}

initializeApp();

declare global {
  interface Window {
    deferredPrompt?: Event;
  }
}
