import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles.css'

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/service-worker.js').catch(() => {
    console.log('Service worker registration skipped (offline mode optional)')
  })
}

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Root element #root not found. Ensure index.html has <div id="root"></div>')
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
