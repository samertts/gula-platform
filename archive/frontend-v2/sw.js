const CACHE_VERSION = 'v3';
const STATIC_CACHE = `gula-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `gula-dynamic-${CACHE_VERSION}`;
const API_CACHE = `gula-api-${CACHE_VERSION}`;
const ASSET_CACHE = `gula-assets-${CACHE_VERSION}`;

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
];

const API_CACHE_PATTERNS = [
  /\/api\/v1\/(patients|orders|samples|results)(\?|\/|$)/,
  /\/api\/v1\/labs/,
  /\/api\/v1\/dashboard/,
  /\/api\/v1\/stats/,
];

const MUTATION_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => {
            return name.startsWith('gula-') && !name.includes(CACHE_VERSION);
          })
          .map((name) => caches.delete(name))
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method === 'POST' && url.pathname === '/api/v1/sync/register') {
    return;
  }

  if (MUTATION_METHODS.includes(request.method)) {
    return handleMutationRequest(event);
  }

  if (isAPIRequest(url)) {
    return handleAPIRequest(event);
  }

  if (isStaticAsset(request)) {
    return handleStaticRequest(event);
  }

  if (isImageRequest(url)) {
    return handleImageRequest(event);
  }

  event.respondWith(networkFirstWithFallback(request));
});

function isAPIRequest(url) {
  return url.pathname.startsWith('/api/v1/') || API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
}

function isStaticAsset(request) {
  const url = new URL(request.url);
  return STATIC_ASSETS.includes(url.pathname) ||
    /\.[0-9a-f]{8}\.(js|css|woff2?)$/.test(url.pathname) ||
    url.pathname.startsWith('/assets/') ||
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'font';
}

function isImageRequest(url) {
  return /\.(png|jpg|jpeg|gif|svg|webp|ico|avif)$/i.test(url.pathname);
}

function isHTMLRequest(request) {
  return request.headers.get('Accept')?.includes('text/html') || request.mode === 'navigate';
}

async function handleStaticRequest(event) {
  const { request } = event;
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(STATIC_CACHE).then((cache) => cache.put(request, clone));
        }
        return response;
      }).catch(() => {
        return caches.match('/offline.html') || new Response('Offline', { status: 503 });
      });
    })
  );
}

async function handleAPIRequest(event) {
  const { request } = event;
  event.respondWith(
    fetch(request).then((response) => {
      if (response.ok && response.status < 400) {
        const clone = response.clone();
        caches.open(API_CACHE).then((cache) => {
          cache.put(request, clone);
        });
      }
      return response;
    }).catch(() => {
      return caches.match(request).then((cached) => {
        if (cached) return cached;
        return new Response(JSON.stringify({
          error: 'offline',
          message: 'You are offline. This data will sync when you reconnect.',
          offline: true,
        }), {
          status: 503,
          headers: { 'Content-Type': 'application/json', 'X-Offline': 'true' },
        });
      });
    })
  );
}

async function handleImageRequest(event) {
  const { request } = event;
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(ASSET_CACHE).then((cache) => {
            cache.put(request, clone);
          });
        }
        return response;
      }).catch(() => {
        return caches.match('/fallback-image.png') || new Response('', { status: 404 });
      });
    })
  );
}

async function networkFirstWithFallback(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const clone = response.clone();
      caches.open(DYNAMIC_CACHE).then((cache) => cache.put(request, clone));
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (isHTMLRequest(request)) {
      return caches.match('/offline.html') || new Response('Offline', { status: 503 });
    }
    return new Response('Offline', { status: 503 });
  }
}

function handleMutationRequest(event) {
  const { request } = event;
  event.respondWith(
    fetch(request.clone()).then((response) => {
      return response;
    }).catch(() => {
      return serializeRequest(request).then((serialized) => {
        return saveToSyncQueue(serialized).then(() => {
          return new Response(JSON.stringify({
            queued: true,
            message: 'Request queued for sync when online',
          }), {
            status: 202,
            headers: { 'Content-Type': 'application/json', 'X-Queued': 'true' },
          });
        });
      });
    })
  );
}

async function serializeRequest(request) {
  const body = request.body ? await request.clone().text() : null;
  const headers = {};
  request.headers.forEach((value, key) => {
    if (!['authorization', 'cookie', 'set-cookie'].includes(key.toLowerCase())) {
      headers[key] = value;
    }
  });
  return {
    url: request.url,
    method: request.method,
    headers,
    body,
    timestamp: Date.now(),
  };
}

async function saveToSyncQueue(serialized) {
  const db = await openSyncDB();
  const tx = db.transaction('sync_queue', 'readwrite');
  await tx.store.add({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    ...serialized,
    retryCount: 0,
    maxRetries: 5,
  });
  await tx.done;

  if ('syncManager' in self.registration) {
    try {
      await self.registration.sync.register('gula-sync');
    } catch {
      console.log('Background sync registration failed');
    }
  }
}

function openSyncDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('gula-sw-sync', 1);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('sync_queue')) {
        db.createObjectStore('sync_queue', { keyPath: 'id' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

self.addEventListener('sync', (event) => {
  if (event.tag === 'gula-sync') {
    event.waitUntil(processSyncQueue());
  }
});

async function processSyncQueue() {
  const db = await openSyncDB();
  const tx = db.transaction('sync_queue', 'readonly');
  const items = await tx.store.getAll();
  await tx.done;

  for (const item of items) {
    try {
      const response = await fetch(item.url, {
        method: item.method,
        headers: item.headers,
        body: item.body || undefined,
      });
      if (response.ok) {
        const deleteTx = db.transaction('sync_queue', 'readwrite');
        await deleteTx.store.delete(item.id);
        await deleteTx.done;

        const clients = await self.clients.matchAll();
        for (const client of clients) {
          client.postMessage({ type: 'SYNC_COMPLETE', id: item.id, url: item.url });
        }
      } else {
        item.retryCount++;
        if (item.retryCount >= item.maxRetries) {
          const deleteTx = db.transaction('sync_queue', 'readwrite');
          await deleteTx.store.delete(item.id);
          await deleteTx.done;
        } else {
          const updateTx = db.transaction('sync_queue', 'readwrite');
          await updateTx.store.put(item);
          await updateTx.done;
        }
      }
    } catch {
      item.retryCount++;
      if (item.retryCount < item.maxRetries) {
        const updateTx = db.transaction('sync_queue', 'readwrite');
        await updateTx.store.put(item);
        await updateTx.done;
      }
    }
  }
}

self.addEventListener('push', (event) => {
  if (!event.data) return;
  try {
    const data = event.data.json();
    const options = {
      body: data.body || '',
      icon: data.icon || '/pwa-192x192.png',
      badge: data.badge || '/badge-icon.png',
      vibrate: data.vibrate || [200, 100, 200],
      data: {
        url: data.url || '/',
        action: data.action || 'open',
        id: data.id || null,
      },
      tag: data.tag || 'default',
      renotify: data.renotify || false,
      requireInteraction: data.requireInteraction || false,
      actions: data.actions || [
        { action: 'open', title: 'Open' },
        { action: 'dismiss', title: 'Dismiss' },
      ],
    };
    event.waitUntil(self.registration.showNotification(data.title || 'GULA Platform', options));
  } catch {
    event.waitUntil(self.registration.showNotification('GULA Platform', { body: event.data.text() }));
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  const action = event.action;
  if (action === 'dismiss') return;
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(self.location.host) && 'focus' in client) {
          return client.focus().then(() => {
            client.postMessage({
              type: 'NOTIFICATION_CLICKED',
              notificationId: event.notification.data?.id,
              action,
            });
            return client.navigate(url);
          });
        }
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});

self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (event.data?.type === 'PURGE_CACHE') {
    const maxAge = event.data.maxAge || 30 * 24 * 60 * 60 * 1000;
    const cutoff = Date.now() - maxAge;
    caches.open(API_CACHE).then((cache) => {
      cache.keys().then((keys) => {
        keys.forEach((key) => {
          cache.match(key).then((response) => {
            const date = response?.headers.get('date');
            if (date && new Date(date).getTime() < cutoff) {
              cache.delete(key);
            }
          });
        });
      });
    });
  }
});

self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'gula-data-refresh') {
    event.waitUntil(refreshCachedData());
  }
  if (event.tag === 'gula-sync-queue') {
    event.waitUntil(processSyncQueue());
  }
});

async function refreshCachedData() {
  const cache = await caches.open(API_CACHE);
  const keys = await cache.keys();
  for (const request of keys) {
    try {
      const response = await fetch(request);
      if (response.ok) {
        cache.put(request, response);
      }
    } catch {
      // keep stale cache on refresh failure
    }
  }
}

function broadcast(type, data) {
  self.clients.matchAll().then((clients) => {
    for (const client of clients) {
      client.postMessage({ type, ...data });
    }
  });
}
