import React from 'react';
import ReactDOM from 'react-dom/client';

async function initializeApp() {
  try {
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
      if (registration.active) {
        console.info('[GULA Hospital] Service Worker registered');
      }
    }
  } catch {}

  const rootElement = document.getElementById('root');
  if (!rootElement) throw new Error('Root element not found');

  const { default: App } = await import('./App');

  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}

initializeApp();
