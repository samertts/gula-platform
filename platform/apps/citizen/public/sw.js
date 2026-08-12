const CACHE_NAME = 'gula-citizen-v2';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
];

const API_CACHE = 'gula-api-v1';
const OFFLINE_QUEUE = 'gula-offline-queue';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      caches.keys().then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
      ),
      purgeLegacyOfflineQueue(),
    ])
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Mutation queues are owned by the authenticated application client. The
  // legacy worker must never persist or replay authenticated mutations.
  if (request.method !== 'GET') return;

  if (url.origin === self.location.origin && request.destination === 'document') {
    event.respondWith(networkFirstWithFallback(request, '/index.html'));
    return;
  }

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstWithTimeout(request, 5000, API_CACHE));
    return;
  }

  if (request.destination === 'style' || request.destination === 'script' || request.destination === 'font') {
    event.respondWith(cacheFirst(request));
    return;
  }

  if (request.destination === 'image') {
    event.respondWith(cacheFirstWithFallback(request, '/icons/icon-192x192.png'));
    return;
  }

  event.respondWith(networkFirst(request));
});

async function networkFirstWithFallback(request, fallbackUrl) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    return caches.match(fallbackUrl);
  }
}

async function networkFirstWithTimeout(request, timeout, cacheName) {
  const timeoutPromise = new Promise((_, reject) =>
    setTimeout(() => reject(new Error('timeout')), timeout)
  );
  try {
    const response = await Promise.race([fetch(request), timeoutPromise]);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(JSON.stringify({ error: 'offline', cached: false }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) {
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, response.clone());
  }
  return response;
}

async function cacheFirstWithFallback(request, fallbackUrl) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return caches.match(fallbackUrl);
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return caches.match(request);
  }
}

async function purgeLegacyOfflineQueue() {
  try {
    const db = await new Promise((resolve, reject) => {
      const request = indexedDB.open('gula-offline', 2);
      request.onupgradeneeded = () => {
        if (!request.result.objectStoreNames.contains(OFFLINE_QUEUE)) {
          request.result.createObjectStore(OFFLINE_QUEUE, { keyPath: 'id', autoIncrement: true });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    if (!db.objectStoreNames.contains(OFFLINE_QUEUE)) return;
    const tx = db.transaction(OFFLINE_QUEUE, 'readwrite');
    tx.objectStore(OFFLINE_QUEUE).clear();
    await tx.done;
    db.close();
  } catch (error) {
    console.error('Failed to purge legacy offline queue:', error);
  }
}
