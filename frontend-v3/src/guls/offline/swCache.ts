/** Service Worker cache names are versioned so an activation can invalidate them atomically. */
export const GULS_SW_CACHE_VERSION = "v1";
export const GULS_LOCALIZATION_CACHE = `guls-localization-${GULS_SW_CACHE_VERSION}`;
export const GULS_PWA_OFFLINE_PAGE = "/offline.html";

/** Drop the versioned localization runtime cache. The next read repopulates it. */
export async function invalidateLocalizationCache(
  cacheName: string = GULS_LOCALIZATION_CACHE,
): Promise<boolean> {
  if (typeof caches === "undefined") return false;
  const existed = await caches.has(cacheName);
  if (existed) await caches.delete(cacheName);
  return existed;
}

/** Remove older GULS localization caches without touching unrelated caches. */
export async function purgeObsoleteLocalizationCaches(
  current: string = GULS_LOCALIZATION_CACHE,
): Promise<string[]> {
  if (typeof caches === "undefined") return [];
  const removed: string[] = [];
  const names = await caches.keys();
  for (const name of names) {
    if (
      name.startsWith("guls-localization-") &&
      name !== current &&
      (await caches.delete(name))
    )
      removed.push(name);
  }
  return removed;
}
