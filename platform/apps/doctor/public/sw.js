const CACHE_NAME = 'gula-doctor-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS)),
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))),
    ),
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const { url } = event.request;

  if (url.includes('/api/')) {
    event.respondWith(networkFirstWithQueue(event.request));
    return;
  }

  if (url.match(/\.(png|jpg|jpeg|svg|gif|webp|dcm)$/)) {
    event.respondWith(cacheFirst(event.request));
    return;
  }

  event.respondWith(networkFirst(event.request));
});

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, response.clone());
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response('Offline', { status: 503 });
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, response.clone());
    return response;
  } catch {
    return new Response('Offline', { status: 503 });
  }
}

async function networkFirstWithQueue(request) {
  try {
    const response = await fetch(request);
    const cache = await caches.open('gula-doctor-api');
    cache.put(request, response.clone());
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;

    if (request.method !== 'GET') {
      const queue = await getQueue();
      queue.push({
        url: request.url,
        method: request.method,
        headers: Array.from(request.headers.entries()),
        body: await request.clone().text(),
        timestamp: Date.now(),
      });
      await saveQueue(queue);

      return new Response(JSON.stringify({ queued: true }), {
        status: 202,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ error: 'offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

async function getQueue() {
  try {
    const cache = await caches.open('gula-doctor-queue');
    const response = await cache.match('/sync-queue');
    if (response) {
      return await response.json();
    }
  } catch {}
  return [];
}

async function saveQueue(queue) {
  const cache = await caches.open('gula-doctor-queue');
  const response = new Response(JSON.stringify(queue), {
    headers: { 'Content-Type': 'application/json' },
  });
  await cache.put('/sync-queue', response);
}

self.addEventListener('sync', (event) => {
  if (event.tag === 'gula-doctor-sync' || event.tag === 'sync-offline-queue') {
    event.waitUntil(processQueue());
  }
});

async function processQueue() {
  const queue = await getQueue();
  const remaining = [];

  for (const item of queue) {
    try {
      const response = await fetch(item.url, {
        method: item.method,
        headers: item.headers.reduce((acc, [k, v]) => {
          acc[k] = v;
          return acc;
        }, {}),
        body: item.body,
      });

      if (!response.ok && item.retryCount < 5) {
        remaining.push({ ...item, retryCount: (item.retryCount || 0) + 1 });
      }
    } catch {
      if (item.retryCount < 5) {
        remaining.push({ ...item, retryCount: (item.retryCount || 0) + 1 });
      }
    }
  }

  await saveQueue(remaining);

  if (remaining.length > 0) {
    const registration = await self.registration;
    await registration.sync.register('sync-offline-queue');
  }
}

self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'sync-clinical-data') {
    event.waitUntil(processQueue());
  }
});
