import CacheService, { CachePresets } from "../CacheService";

describe("CacheService", () => {
  beforeEach(() => {
    // Clear all caches before each test
    CacheService.clearNamespace();
    localStorage.clear();
    sessionStorage.clear();
  });

  describe("Memory Cache", () => {
    it("should set and get values from memory cache", () => {
      CacheService.set("test-key", { value: "test-data" });
      const result = CacheService.get("test-key");
      
      expect(result).toEqual({ value: "test-data" });
    });

    it("should return null for non-existent keys", () => {
      const result = CacheService.get("non-existent-key");
      
      expect(result).toBeNull();
    });

    it("should return null for expired entries", async () => {
      CacheService.set("expired-key", "data", { ttl: 1 }); // 1ms TTL
      
      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 10));
      
      const result = CacheService.get("expired-key");
      expect(result).toBeNull();
    });

    it("should check if key exists with has()", () => {
      CacheService.set("exists-key", "data");
      
      expect(CacheService.has("exists-key")).toBe(true);
      expect(CacheService.has("not-exists-key")).toBe(false);
    });

    it("should remove items from cache", () => {
      CacheService.set("remove-key", "data");
      expect(CacheService.get("remove-key")).toBe("data");
      
      CacheService.remove("remove-key");
      expect(CacheService.get("remove-key")).toBeNull();
    });
  });

  describe("Session Storage Cache", () => {
    it("should set and get values from session storage", () => {
      CacheService.set("session-key", { value: "session-data" }, { storage: "session" });
      const result = CacheService.get("session-key", { storage: "session" });
      
      expect(result).toEqual({ value: "session-data" });
    });

    it("should store in sessionStorage", () => {
      CacheService.set("session-test", "data", { storage: "session" });
      
      const keys = Object.keys(sessionStorage);
      expect(keys.some(k => k.includes("session-test"))).toBe(true);
    });
  });

  describe("Local Storage Cache", () => {
    it("should set and get values from local storage", () => {
      CacheService.set("local-key", { value: "local-data" }, { storage: "local" });
      const result = CacheService.get("local-key", { storage: "local" });
      
      expect(result).toEqual({ value: "local-data" });
    });

    it("should store in localStorage", () => {
      CacheService.set("local-test", "data", { storage: "local" });
      
      const keys = Object.keys(localStorage);
      expect(keys.some(k => k.includes("local-test"))).toBe(true);
    });
  });

  describe("getOrFetch", () => {
    it("should return cached value if available", async () => {
      CacheService.set("fetch-key", "cached-value");
      const fetcher = jest.fn().mockResolvedValue("fetched-value");
      
      const result = await CacheService.getOrFetch("fetch-key", fetcher);
      
      expect(result).toBe("cached-value");
      expect(fetcher).not.toHaveBeenCalled();
    });

    it("should fetch and cache if not available", async () => {
      const fetcher = jest.fn().mockResolvedValue("fetched-value");
      
      const result = await CacheService.getOrFetch("new-key", fetcher);
      
      expect(result).toBe("fetched-value");
      expect(fetcher).toHaveBeenCalledTimes(1);
      expect(CacheService.get("new-key")).toBe("fetched-value");
    });
  });

  describe("invalidate", () => {
    it("should invalidate cache entries by pattern", () => {
      CacheService.set("user-1", "data1");
      CacheService.set("user-2", "data2");
      CacheService.set("task-1", "task-data");
      
      CacheService.invalidate(/user/);
      
      expect(CacheService.get("user-1")).toBeNull();
      expect(CacheService.get("user-2")).toBeNull();
      expect(CacheService.get("task-1")).toBe("task-data");
    });

    it("should invalidate with string pattern", () => {
      CacheService.set("api-tasks", "data1");
      CacheService.set("api-users", "data2");
      
      CacheService.invalidate("api-");
      
      expect(CacheService.get("api-tasks")).toBeNull();
      expect(CacheService.get("api-users")).toBeNull();
    });
  });

  describe("clearExpired", () => {
    it("should clear expired entries", async () => {
      CacheService.set("valid-key", "valid", { ttl: 60000 });
      CacheService.set("expired-key", "expired", { ttl: 1 });
      
      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 10));
      
      const cleared = CacheService.clearExpired();
      
      expect(cleared).toBeGreaterThanOrEqual(1);
      expect(CacheService.get("valid-key")).toBe("valid");
    });
  });

  describe("clearNamespace", () => {
    it("should clear all entries in namespace", () => {
      CacheService.set("key1", "data1");
      CacheService.set("key2", "data2");
      CacheService.set("key1", "session-data", { storage: "session" });
      CacheService.set("key1", "local-data", { storage: "local" });
      
      CacheService.clearNamespace();
      
      expect(CacheService.get("key1")).toBeNull();
      expect(CacheService.get("key2")).toBeNull();
      expect(CacheService.get("key1", { storage: "session" })).toBeNull();
      expect(CacheService.get("key1", { storage: "local" })).toBeNull();
    });
  });

  describe("getStats", () => {
    it("should return cache statistics", () => {
      CacheService.set("key1", "data1");
      CacheService.set("key2", "data2");
      CacheService.set("key3", "data3", { storage: "session" });
      CacheService.set("key4", "data4", { storage: "local" });
      
      const stats = CacheService.getStats();
      
      expect(stats.memoryEntries).toBe(2);
      expect(stats.sessionEntries).toBe(1);
      expect(stats.localEntries).toBe(1);
    });
  });

  describe("Namespace Support", () => {
    it("should isolate data by namespace", () => {
      CacheService.set("key", "value1", { namespace: "namespace1" });
      CacheService.set("key", "value2", { namespace: "namespace2" });
      
      expect(CacheService.get("key", { namespace: "namespace1" })).toBe("value1");
      expect(CacheService.get("key", { namespace: "namespace2" })).toBe("value2");
    });
  });

  describe("Cache Presets", () => {
    it("should have SHORT preset with 30 seconds TTL", () => {
      expect(CachePresets.SHORT.ttl).toBe(30000);
    });

    it("should have DEFAULT preset with 5 minutes TTL", () => {
      expect(CachePresets.DEFAULT.ttl).toBe(300000);
    });

    it("should have MEDIUM preset with 15 minutes TTL", () => {
      expect(CachePresets.MEDIUM.ttl).toBe(900000);
    });

    it("should have LONG preset with 1 hour TTL", () => {
      expect(CachePresets.LONG.ttl).toBe(3600000);
    });

    it("should have PERSISTENT preset with local storage", () => {
      expect(CachePresets.PERSISTENT.storage).toBe("local");
      expect(CachePresets.PERSISTENT.ttl).toBe(86400000);
    });

    it("should have SESSION preset with session storage", () => {
      expect(CachePresets.SESSION.storage).toBe("session");
      expect(CachePresets.SESSION.ttl).toBe(1800000);
    });
  });

  describe("Error Handling", () => {
    it("should handle JSON parse errors gracefully", () => {
      // Manually set invalid JSON in storage
      sessionStorage.setItem("dtqs_cache:bad-json", "invalid json {");
      
      const result = CacheService.get("bad-json", { storage: "session" });
      expect(result).toBeNull();
    });
  });
});
