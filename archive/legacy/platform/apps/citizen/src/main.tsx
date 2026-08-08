import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

async function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      });

      if (registration.active) {
        console.info('Service Worker registered');
      }

      if ('SyncManager' in window) {
        const status = await (navigator as any).permissions.query({
          name: 'periodic-background-sync',
        });
        if (status.state === 'granted') {
          try {
            await (registration as any).periodicSync.register('sync-health-data', {
              minInterval: 12 * 60 * 60 * 1000,
            });
          } catch {}
        }
      }
    } catch (error) {
      console.warn('Service Worker registration failed:', error);
    }
  }
}

async function initializeApp() {
  await registerServiceWorker();

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
