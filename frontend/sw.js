// GULA Platform Service Worker - Offline Support + Background Sync
const CACHE_NAME = 'gula-v3';
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

// ── Background Sync ────────────────────────────────────────────────────────
// When the browser regains connectivity it fires the 'sync' event.
// We notify all open tabs to flush their IndexedDB offline queue.
// Medical data queued while offline is replayed exactly once in order.
self.addEventListener('sync', e => {
  if (e.tag === 'gula-queue') {
    e.waitUntil(
      self.clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then(clients => {
          clients.forEach(c => c.postMessage({ type: 'FLUSH_QUEUE' }));
        })
    );
  }
});

// ── Push Notifications (critical results) ─────────────────────────────────
// The backend can push a Web Push notification for critical lab results.
// The SW shows it here so it works even when the tab is closed.
self.addEventListener('push', e => {
  if (!e.data) return;
  let payload;
  try { payload = e.data.json(); } catch { return; }

  const title   = payload.title   || 'GULA — تنبيه';
  const body    = payload.body    || '';
  const icon    = payload.icon    || '/assets/icon-192.svg';
  const badge   = '/assets/icon-192.svg';
  const tag     = payload.tag     || 'gula-alert';
  const data    = payload.data    || {};

  e.waitUntil(
    self.registration.showNotification(title, { body, icon, badge, tag, data,
      dir: 'rtl', lang: 'ar', requireInteraction: payload.critical || false })
  );
});

// Clicking a notification opens the relevant order page
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = e.notification.data?.url || '/';
  e.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(clients => {
        const existing = clients.find(c => c.url.includes(self.location.origin));
        if (existing) { existing.focus(); existing.postMessage({ type: 'NAVIGATE', url }); }
        else self.clients.openWindow(url);
      })
  );
});
