import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { purgeLegacyWorkboxQueue } from '@gula/ui-platform';

async function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
      if (registration.active) {
        console.info('[GULA Ministry] Service Worker registered');
      }
    } catch (error) {
      console.warn('[GULA Ministry] Service Worker registration failed:', error);
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
