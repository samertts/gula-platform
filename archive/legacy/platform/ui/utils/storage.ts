const STORAGE_PREFIX = 'gula_';

export class StorageError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'StorageError';
  }
}

function getStorage(): Storage | null {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function setItem<T>(key: string, value: T): void {
  const storage = getStorage();
  if (!storage) return;
  try {
    storage.setItem(`${STORAGE_PREFIX}${key}`, JSON.stringify(value));
  } catch (e) {
    throw new StorageError(`Failed to set item "${key}": ${e}`);
  }
}

export function getItem<T>(key: string, defaultValue?: T): T | undefined {
  const storage = getStorage();
  if (!storage) return defaultValue;
  try {
    const raw = storage.getItem(`${STORAGE_PREFIX}${key}`);
    if (raw === null) return defaultValue;
    return JSON.parse(raw) as T;
  } catch {
    return defaultValue;
  }
}

export function removeItem(key: string): void {
  const storage = getStorage();
  if (!storage) return;
  try {
    storage.removeItem(`${STORAGE_PREFIX}${key}`);
  } catch (e) {
    throw new StorageError(`Failed to remove item "${key}": ${e}`);
  }
}

export function clearAll(): void {
  const storage = getStorage();
  if (!storage) return;
  try {
    const keysToRemove: string[] = [];
    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i);
      if (key && key.startsWith(STORAGE_PREFIX)) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach(key => storage.removeItem(key));
  } catch (e) {
    throw new StorageError(`Failed to clear storage: ${e}`);
  }
}

export function getKeys(): string[] {
  const storage = getStorage();
  if (!storage) return [];
  const keys: string[] = [];
  for (let i = 0; i < storage.length; i++) {
    const key = storage.key(i);
    if (key && key.startsWith(STORAGE_PREFIX)) {
      keys.push(key.slice(STORAGE_PREFIX.length));
    }
  }
  return keys;
}

export function exists(key: string): boolean {
  const storage = getStorage();
  if (!storage) return false;
  return storage.getItem(`${STORAGE_PREFIX}${key}`) !== null;
}

export const storage = {
  set: setItem,
  get: getItem,
  remove: removeItem,
  clear: clearAll,
  keys: getKeys,
  exists,
};
