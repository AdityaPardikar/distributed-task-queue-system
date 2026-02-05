/**
 * CacheService - Frontend caching service with TTL support
 * Provides a unified interface for caching data with automatic expiration
 */

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  key: string;
}

export interface CacheOptions {
  ttl?: number; // Time to live in milliseconds (default: 5 minutes)
  storage?: "memory" | "session" | "local"; // Storage type
  namespace?: string; // Key namespace for scoping
}

const DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes
const DEFAULT_NAMESPACE = "dtqs_cache";

class CacheServiceClass {
  private memoryCache: Map<string, CacheEntry<unknown>> = new Map();
  private cleanupInterval: number | null = null;

  constructor() {
    // Start cleanup interval
    this.startCleanup();
  }

  /**
   * Get the full cache key with namespace
   */
  private getFullKey(key: string, namespace: string = DEFAULT_NAMESPACE): string {
    return `${namespace}:${key}`;
  }

  /**
   * Check if a cache entry is still valid
   */
  private isValid<T>(entry: CacheEntry<T>): boolean {
    return Date.now() - entry.timestamp < entry.ttl;
  }

  /**
   * Get item from cache
   */
  get<T>(key: string, options: CacheOptions = {}): T | null {
    const { storage = "memory", namespace = DEFAULT_NAMESPACE } = options;
    const fullKey = this.getFullKey(key, namespace);

    try {
      let entry: CacheEntry<T> | null = null;

      switch (storage) {
        case "memory":
          entry = this.memoryCache.get(fullKey) as CacheEntry<T> | undefined ?? null;
          break;
        case "session":
          const sessionData = sessionStorage.getItem(fullKey);
          entry = sessionData ? JSON.parse(sessionData) : null;
          break;
        case "local":
          const localData = localStorage.getItem(fullKey);
          entry = localData ? JSON.parse(localData) : null;
          break;
      }

      if (entry && this.isValid(entry)) {
        return entry.data;
      }

      // Remove expired entry
      if (entry) {
        this.remove(key, options);
      }

      return null;
    } catch (error) {
      console.error("CacheService get error:", error);
      return null;
    }
  }

  /**
   * Set item in cache
   */
  set<T>(key: string, data: T, options: CacheOptions = {}): void {
    const {
      ttl = DEFAULT_TTL,
      storage = "memory",
      namespace = DEFAULT_NAMESPACE,
    } = options;
    const fullKey = this.getFullKey(key, namespace);

    try {
      const entry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        ttl,
        key: fullKey,
      };

      switch (storage) {
        case "memory":
          this.memoryCache.set(fullKey, entry as CacheEntry<unknown>);
          break;
        case "session":
          sessionStorage.setItem(fullKey, JSON.stringify(entry));
          break;
        case "local":
          localStorage.setItem(fullKey, JSON.stringify(entry));
          break;
      }
    } catch (error) {
      console.error("CacheService set error:", error);
      // Handle quota exceeded for storage
      if (error instanceof DOMException && error.name === "QuotaExceededError") {
        this.clearExpired(options);
      }
    }
  }

  /**
   * Remove item from cache
   */
  remove(key: string, options: CacheOptions = {}): void {
    const { storage = "memory", namespace = DEFAULT_NAMESPACE } = options;
    const fullKey = this.getFullKey(key, namespace);

    try {
      switch (storage) {
        case "memory":
          this.memoryCache.delete(fullKey);
          break;
        case "session":
          sessionStorage.removeItem(fullKey);
          break;
        case "local":
          localStorage.removeItem(fullKey);
          break;
      }
    } catch (error) {
      console.error("CacheService remove error:", error);
    }
  }

  /**
   * Check if item exists and is valid
   */
  has(key: string, options: CacheOptions = {}): boolean {
    return this.get(key, options) !== null;
  }

  /**
   * Get or fetch - Returns cached data or fetches new data if not cached
   */
  async getOrFetch<T>(
    key: string,
    fetcher: () => Promise<T>,
    options: CacheOptions = {}
  ): Promise<T> {
    const cached = this.get<T>(key, options);
    if (cached !== null) {
      return cached;
    }

    const data = await fetcher();
    this.set(key, data, options);
    return data;
  }

  /**
   * Invalidate cache by key pattern
   */
  invalidate(pattern: string | RegExp, options: CacheOptions = {}): void {
    const { storage = "memory", namespace = DEFAULT_NAMESPACE } = options;
    const regex = pattern instanceof RegExp ? pattern : new RegExp(pattern);

    try {
      switch (storage) {
        case "memory":
          for (const key of this.memoryCache.keys()) {
            if (key.startsWith(namespace) && regex.test(key)) {
              this.memoryCache.delete(key);
            }
          }
          break;
        case "session":
          for (let i = sessionStorage.length - 1; i >= 0; i--) {
            const key = sessionStorage.key(i);
            if (key && key.startsWith(namespace) && regex.test(key)) {
              sessionStorage.removeItem(key);
            }
          }
          break;
        case "local":
          for (let i = localStorage.length - 1; i >= 0; i--) {
            const key = localStorage.key(i);
            if (key && key.startsWith(namespace) && regex.test(key)) {
              localStorage.removeItem(key);
            }
          }
          break;
      }
    } catch (error) {
      console.error("CacheService invalidate error:", error);
    }
  }

  /**
   * Clear all expired entries
   */
  clearExpired(options: CacheOptions = {}): number {
    const { storage = "memory", namespace = DEFAULT_NAMESPACE } = options;
    let cleared = 0;

    try {
      switch (storage) {
        case "memory":
          for (const [key, entry] of this.memoryCache.entries()) {
            if (key.startsWith(namespace) && !this.isValid(entry)) {
              this.memoryCache.delete(key);
              cleared++;
            }
          }
          break;
        case "session":
          for (let i = sessionStorage.length - 1; i >= 0; i--) {
            const key = sessionStorage.key(i);
            if (key && key.startsWith(namespace)) {
              const data = sessionStorage.getItem(key);
              if (data) {
                const entry = JSON.parse(data) as CacheEntry<unknown>;
                if (!this.isValid(entry)) {
                  sessionStorage.removeItem(key);
                  cleared++;
                }
              }
            }
          }
          break;
        case "local":
          for (let i = localStorage.length - 1; i >= 0; i--) {
            const key = localStorage.key(i);
            if (key && key.startsWith(namespace)) {
              const data = localStorage.getItem(key);
              if (data) {
                const entry = JSON.parse(data) as CacheEntry<unknown>;
                if (!this.isValid(entry)) {
                  localStorage.removeItem(key);
                  cleared++;
                }
              }
            }
          }
          break;
      }
    } catch (error) {
      console.error("CacheService clearExpired error:", error);
    }

    return cleared;
  }

  /**
   * Clear all cache entries in a namespace
   */
  clearNamespace(namespace: string = DEFAULT_NAMESPACE): void {
    // Clear memory
    for (const key of this.memoryCache.keys()) {
      if (key.startsWith(namespace)) {
        this.memoryCache.delete(key);
      }
    }

    // Clear session storage
    for (let i = sessionStorage.length - 1; i >= 0; i--) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith(namespace)) {
        sessionStorage.removeItem(key);
      }
    }

    // Clear local storage
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i);
      if (key && key.startsWith(namespace)) {
        localStorage.removeItem(key);
      }
    }
  }

  /**
   * Get cache statistics
   */
  getStats(): {
    memorySize: number;
    memoryEntries: number;
    sessionEntries: number;
    localEntries: number;
  } {
    let sessionEntries = 0;
    let localEntries = 0;

    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith(DEFAULT_NAMESPACE)) {
        sessionEntries++;
      }
    }

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(DEFAULT_NAMESPACE)) {
        localEntries++;
      }
    }

    return {
      memorySize: this.memoryCache.size,
      memoryEntries: this.memoryCache.size,
      sessionEntries,
      localEntries,
    };
  }

  /**
   * Start periodic cleanup of expired entries
   */
  private startCleanup(): void {
    // Clear expired entries every minute
    this.cleanupInterval = window.setInterval(() => {
      this.clearExpired({ storage: "memory" });
      this.clearExpired({ storage: "session" });
      this.clearExpired({ storage: "local" });
    }, 60000);
  }

  /**
   * Stop cleanup interval
   */
  stopCleanup(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
  }
}

// Export singleton instance
const CacheService = new CacheServiceClass();
export default CacheService;

// Export cache presets
export const CachePresets = {
  // Short-lived cache for frequently changing data
  SHORT: { ttl: 30 * 1000 }, // 30 seconds

  // Default cache for general data
  DEFAULT: { ttl: 5 * 60 * 1000 }, // 5 minutes

  // Medium cache for moderately static data
  MEDIUM: { ttl: 15 * 60 * 1000 }, // 15 minutes

  // Long cache for static data
  LONG: { ttl: 60 * 60 * 1000 }, // 1 hour

  // Persistent cache stored in localStorage
  PERSISTENT: { ttl: 24 * 60 * 60 * 1000, storage: "local" as const }, // 24 hours

  // Session cache that persists for the browser session
  SESSION: { ttl: 30 * 60 * 1000, storage: "session" as const }, // 30 minutes
};
