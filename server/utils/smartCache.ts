import { structuredLogger } from './structuredLogger';

interface CacheEntry<T> {
  value: T;
  expiresAt: number;
  tags: string[];
  hits: number;
  lastAccessed: number;
}

type CacheInvalidationStrategy = 'ttl' | 'lru' | 'smart';

class SmartCache {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private tagIndex: Map<string, Set<string>> = new Map();
  private strategy: CacheInvalidationStrategy = 'smart';
  private maxSize: number = 1000;
  private defaultTTL: number = 3600000; // 1 hour

  constructor(strategy: CacheInvalidationStrategy = 'smart', maxSize: number = 1000) {
    this.strategy = strategy;
    this.maxSize = maxSize;

    // Cleanup expired entries every 5 minutes
    setInterval(() => this.cleanup(), 5 * 60 * 1000);
  }

  set<T>(key: string, value: T, ttl: number = this.defaultTTL, tags: string[] = []): void {
    const now = Date.now();

    // Check cache size and evict if necessary
    if (this.cache.size >= this.maxSize) {
      this.evict();
    }

    const entry: CacheEntry<T> = {
      value,
      expiresAt: now + ttl,
      tags,
      hits: 0,
      lastAccessed: now,
    };

    this.cache.set(key, entry);

    // Update tag index
    tags.forEach(tag => {
      if (!this.tagIndex.has(tag)) {
        this.tagIndex.set(tag, new Set());
      }
      this.tagIndex.get(tag)!.add(key);
    });

    structuredLogger.logCacheOperation('set', key, false, 0);
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      structuredLogger.logCacheOperation('get', key, false, 0);
      return null;
    }

    const now = Date.now();

    // Check if expired
    if (now > entry.expiresAt) {
      this.cache.delete(key);
      this.removeFromTagIndex(key);
      structuredLogger.logCacheOperation('get', key, false, 0);
      return null;
    }

    // Update hit count and last accessed time
    entry.hits++;
    entry.lastAccessed = now;

    structuredLogger.logCacheOperation('get', key, true, 0);
    return entry.value as T;
  }

  delete(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;

    this.cache.delete(key);
    this.removeFromTagIndex(key);

    structuredLogger.logCacheOperation('delete', key, false, 0);
    return true;
  }

  invalidateByTag(tag: string): number {
    const keys = this.tagIndex.get(tag);
    if (!keys) return 0;

    let count = 0;
    keys.forEach(key => {
      this.cache.delete(key);
      count++;
    });

    this.tagIndex.delete(tag);
    structuredLogger.debug(`Invalidated ${count} cache entries by tag: ${tag}`);
    return count;
  }

  invalidateByPattern(pattern: RegExp): number {
    let count = 0;
    const keysToDelete: string[] = [];

    this.cache.forEach((_, key) => {
      if (pattern.test(key)) {
        keysToDelete.push(key);
      }
    });

    keysToDelete.forEach(key => {
      this.cache.delete(key);
      this.removeFromTagIndex(key);
      count++;
    });

    structuredLogger.debug(`Invalidated ${count} cache entries by pattern: ${pattern}`);
    return count;
  }

  clear(): void {
    this.cache.clear();
    this.tagIndex.clear();
    structuredLogger.info('Cache cleared');
  }

  private removeFromTagIndex(key: string): void {
    const entry = this.cache.get(key);
    if (!entry) return;

    entry.tags.forEach(tag => {
      const keys = this.tagIndex.get(tag);
      if (keys) {
        keys.delete(key);
        if (keys.size === 0) {
          this.tagIndex.delete(tag);
        }
      }
    });
  }

  private cleanup(): void {
    const now = Date.now();
    const keysToDelete: string[] = [];

    this.cache.forEach((entry, key) => {
      if (now > entry.expiresAt) {
        keysToDelete.push(key);
      }
    });

    keysToDelete.forEach(key => {
      this.cache.delete(key);
      this.removeFromTagIndex(key);
    });

    if (keysToDelete.length > 0) {
      structuredLogger.debug(`Cleaned up ${keysToDelete.length} expired cache entries`);
    }
  }

  private evict(): void {
    if (this.strategy === 'ttl') {
      this.evictByTTL();
    } else if (this.strategy === 'lru') {
      this.evictByLRU();
    } else {
      this.evictSmart();
    }
  }

  private evictByTTL(): void {
    const now = Date.now();
    const entries = Array.from(this.cache.entries())
      .filter(([_, entry]) => now <= entry.expiresAt)
      .sort((a, b) => a[1].expiresAt - b[1].expiresAt);

    if (entries.length > 0) {
      const keyToDelete = entries[0][0];
      this.delete(keyToDelete);
    }
  }

  private evictByLRU(): void {
    let lruKey: string | null = null;
    let lruTime = Infinity;

    this.cache.forEach((entry, key) => {
      if (entry.lastAccessed < lruTime) {
        lruTime = entry.lastAccessed;
        lruKey = key;
      }
    });

    if (lruKey) {
      this.delete(lruKey);
    }
  }

  private evictSmart(): void {
    // Combine TTL and LRU: prioritize expired entries, then evict LRU
    const now = Date.now();
    const expiredEntries = Array.from(this.cache.entries()).filter(
      ([_, entry]) => now > entry.expiresAt
    );

    if (expiredEntries.length > 0) {
      this.delete(expiredEntries[0][0]);
    } else {
      this.evictByLRU();
    }
  }

  getStats(): {
    size: number;
    maxSize: number;
    hitRate: number;
    avgHits: number;
  } {
    let totalHits = 0;
    let count = 0;

    this.cache.forEach(entry => {
      totalHits += entry.hits;
      count++;
    });

    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      hitRate: count > 0 ? totalHits / count : 0,
      avgHits: count > 0 ? totalHits / count : 0,
    };
  }
}

export const smartCache = new SmartCache('smart', 1000);
