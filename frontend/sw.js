// GULA Platform Service Worker - Offline Support
const CACHE_NAME = 'gula-v2';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/login.html',
  '/assets/gula.css',
  '/assets/gula.js',
  '/manifest.json'
];

// Install: cache static assets
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate: clean old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Fetch strategy:
// - API calls: network only (never cache medical data)
// - JS/CSS: network-first (always get latest, fall back to cache offline)
// - Other static: stale-while-revalidate
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // API calls & non-GET: pass through to network
  if (url.pathname.startsWith('/api/') || e.request.method !== 'GET') return;

  // JS/CSS: network-first to prevent stale code
  if (url.pathname.endsWith('.js') || url.pathname.endsWith('.css')) {
    e.respondWith(
      fetch(e.request).then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
        }
        return response;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  // Other static assets: stale-while-revalidate
  e.respondWith(
    caches.match(e.request).then(cached => {
      const fetchPromise = fetch(e.request).then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
        }
        return response;
      }).catch(() => cached);

      return cached || fetchPromise;
    })
  );
});
