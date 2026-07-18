import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './src/styles/theme.css'
import './src/styles/components.css'

// Load Cairo font for Arabic support
const fontLink = document.createElement('link')
fontLink.href = 'https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap'
fontLink.rel = 'stylesheet'
document.head.appendChild(fontLink)

// Set initial theme
const storedTheme = localStorage.getItem('gula_radiology_theme')
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
const initialTheme = storedTheme || (prefersDark ? 'dark' : 'light')
document.documentElement.setAttribute('data-theme', initialTheme)

// Set initial direction
const storedDir = localStorage.getItem('gula_radiology_dir')
document.documentElement.dir = storedDir || 'rtl'

const root = document.getElementById('root')
if (!root) {
  throw new Error('Root element not found. Ensure index.html has <div id="root"></div>')
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)

// Enable service worker for PWA
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      // Service worker registration failed - non-critical
    })
  })
}
