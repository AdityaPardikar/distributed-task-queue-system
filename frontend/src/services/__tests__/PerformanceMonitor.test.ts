import PerformanceMonitor, {
  withPerformanceTracking,
} from "../PerformanceMonitor";

describe("PerformanceMonitor", () => {
  beforeEach(() => {
    // Clear metrics and reset state
    PerformanceMonitor.clear();
    PerformanceMonitor.setEnabled(true);
  });

  describe("Basic Operations", () => {
    it("should track custom metrics", () => {
      PerformanceMonitor.trackCustom("test-metric", 100, { test: true });

      const metrics = PerformanceMonitor.getMetricsByName("test-metric");
      expect(metrics).toHaveLength(1);
      expect(metrics[0].name).toBe("test-metric");
      expect(metrics[0].duration).toBe(100);
      expect(metrics[0].type).toBe("custom");
      expect(metrics[0].metadata?.test).toBe(true);
    });

    it("should track render metrics", () => {
      PerformanceMonitor.trackRender("MyComponent", 50, { renders: 1 });

      const metrics = PerformanceMonitor.getMetricsByType("render");
      expect(metrics).toHaveLength(1);
      expect(metrics[0].name).toBe("MyComponent");
      expect(metrics[0].duration).toBe(50);
    });

    it("should track API call metrics", async () => {
      const mockFetch = jest.fn().mockResolvedValue({ data: "test" });

      const result = await PerformanceMonitor.trackApiCall(
        "fetchUsers",
        mockFetch,
        { endpoint: "/api/users" }
      );

      expect(result).toEqual({ data: "test" });
      expect(mockFetch).toHaveBeenCalledTimes(1);

      const metrics = PerformanceMonitor.getMetricsByType("api");
      expect(metrics).toHaveLength(1);
      expect(metrics[0].name).toBe("fetchUsers");
      expect(metrics[0].metadata?.success).toBe(true);
      expect(metrics[0].metadata?.endpoint).toBe("/api/users");
    });

    it("should track failed API calls", async () => {
      const mockFetch = jest.fn().mockRejectedValue(new Error("Network error"));

      await expect(
        PerformanceMonitor.trackApiCall("failingFetch", mockFetch)
      ).rejects.toThrow("Network error");

      const metrics = PerformanceMonitor.getMetricsByName("failingFetch");
      expect(metrics).toHaveLength(1);
      expect(metrics[0].metadata?.success).toBe(false);
      expect(metrics[0].metadata?.error).toBe("Network error");
    });
  });

  describe("Timer Functionality", () => {
    it("should start and stop timer", async () => {
      const stopTimer = PerformanceMonitor.startTimer("timer-test", "custom");

      // Simulate some work
      await new Promise((resolve) => setTimeout(resolve, 10));

      stopTimer({ extraMeta: "value" });

      const metrics = PerformanceMonitor.getMetricsByName("timer-test");
      expect(metrics).toHaveLength(1);
      expect(metrics[0].duration).toBeGreaterThanOrEqual(10);
      expect(metrics[0].metadata?.extraMeta).toBe("value");
    });
  });

  describe("Enable/Disable", () => {
    it("should not track metrics when disabled", () => {
      PerformanceMonitor.setEnabled(false);
      PerformanceMonitor.trackCustom("disabled-metric", 100);

      const metrics = PerformanceMonitor.getMetricsByName("disabled-metric");
      expect(metrics).toHaveLength(0);
    });

    it("should resume tracking when re-enabled", () => {
      PerformanceMonitor.setEnabled(false);
      PerformanceMonitor.trackCustom("disabled-metric", 100);
      
      PerformanceMonitor.setEnabled(true);
      PerformanceMonitor.trackCustom("enabled-metric", 100);

      expect(PerformanceMonitor.getMetricsByName("disabled-metric")).toHaveLength(0);
      expect(PerformanceMonitor.getMetricsByName("enabled-metric")).toHaveLength(1);
    });

    it("should still execute API calls when disabled", async () => {
      PerformanceMonitor.setEnabled(false);
      const mockFetch = jest.fn().mockResolvedValue("result");

      const result = await PerformanceMonitor.trackApiCall("disabled-api", mockFetch);

      expect(result).toBe("result");
      expect(mockFetch).toHaveBeenCalled();
      expect(PerformanceMonitor.getMetricsByType("api")).toHaveLength(0);
    });
  });

  describe("Query Methods", () => {
    beforeEach(() => {
      // Add some test metrics
      PerformanceMonitor.trackCustom("metric-a", 100);
      PerformanceMonitor.trackCustom("metric-b", 200);
      PerformanceMonitor.trackRender("ComponentA", 50);
      PerformanceMonitor.trackRender("ComponentB", 75);
    });

    it("should get metrics by name", () => {
      const metrics = PerformanceMonitor.getMetricsByName("metric-a");
      expect(metrics).toHaveLength(1);
      expect(metrics[0].duration).toBe(100);
    });

    it("should get metrics by type", () => {
      const customMetrics = PerformanceMonitor.getMetricsByType("custom");
      expect(customMetrics).toHaveLength(2);

      const renderMetrics = PerformanceMonitor.getMetricsByType("render");
      expect(renderMetrics).toHaveLength(2);
    });

    it("should get metrics in time range", () => {
      const now = Date.now();
      const metrics = PerformanceMonitor.getMetricsInRange(now - 1000, now + 1000);
      expect(metrics.length).toBeGreaterThan(0);
    });
  });

  describe("Statistics Calculation", () => {
    it("should calculate stats correctly", () => {
      // Add metrics with known durations
      PerformanceMonitor.trackCustom("stats-test", 10);
      PerformanceMonitor.trackCustom("stats-test", 20);
      PerformanceMonitor.trackCustom("stats-test", 30);
      PerformanceMonitor.trackCustom("stats-test", 40);
      PerformanceMonitor.trackCustom("stats-test", 50);

      const metrics = PerformanceMonitor.getMetricsByName("stats-test");
      const stats = PerformanceMonitor.calculateStats(metrics);

      expect(stats.count).toBe(5);
      expect(stats.totalDuration).toBe(150);
      expect(stats.avgDuration).toBe(30);
      expect(stats.minDuration).toBe(10);
      expect(stats.maxDuration).toBe(50);
      expect(stats.p50).toBe(30);
    });

    it("should return empty stats for empty metrics", () => {
      const stats = PerformanceMonitor.calculateStats([]);

      expect(stats.count).toBe(0);
      expect(stats.totalDuration).toBe(0);
      expect(stats.avgDuration).toBe(0);
    });
  });

  describe("Subscriptions", () => {
    it("should notify subscribers when metric is added", () => {
      const callback = jest.fn();
      const unsubscribe = PerformanceMonitor.subscribe(callback);

      PerformanceMonitor.trackCustom("subscribed-metric", 100);

      expect(callback).toHaveBeenCalledTimes(1);
      expect(callback).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "subscribed-metric",
          duration: 100,
        })
      );

      unsubscribe();
    });

    it("should stop notifying after unsubscribe", () => {
      const callback = jest.fn();
      const unsubscribe = PerformanceMonitor.subscribe(callback);

      PerformanceMonitor.trackCustom("before-unsub", 100);
      expect(callback).toHaveBeenCalledTimes(1);

      unsubscribe();

      PerformanceMonitor.trackCustom("after-unsub", 100);
      expect(callback).toHaveBeenCalledTimes(1); // Still 1
    });
  });

  describe("Report Generation", () => {
    it("should generate performance report", () => {
      PerformanceMonitor.trackCustom("custom-1", 100);
      PerformanceMonitor.trackRender("Component", 50);

      const report = PerformanceMonitor.generateReport();

      expect(report).toHaveProperty("startTime");
      expect(report).toHaveProperty("endTime");
      expect(report).toHaveProperty("totalMetrics");
      expect(report).toHaveProperty("apiMetrics");
      expect(report).toHaveProperty("renderMetrics");
      expect(report).toHaveProperty("customMetrics");
      expect(report.totalMetrics).toBeGreaterThanOrEqual(2);
    });
  });

  describe("Clear Metrics", () => {
    it("should clear all metrics", () => {
      PerformanceMonitor.trackCustom("to-clear", 100);
      expect(PerformanceMonitor.getMetricsByName("to-clear")).toHaveLength(1);

      PerformanceMonitor.clear();
      expect(PerformanceMonitor.getMetricsByName("to-clear")).toHaveLength(0);
    });
  });
});

describe("withPerformanceTracking HOF", () => {
  beforeEach(() => {
    PerformanceMonitor.clear();
  });

  it("should wrap async function with tracking", async () => {
    const originalFn = jest.fn().mockResolvedValue("result");
    const wrappedFn = withPerformanceTracking("wrapped-fn", originalFn, "api");

    const result = await wrappedFn();

    expect(result).toBe("result");
    expect(originalFn).toHaveBeenCalled();

    const metrics = PerformanceMonitor.getMetricsByName("wrapped-fn");
    expect(metrics).toHaveLength(1);
    expect(metrics[0].type).toBe("api");
  });

  it("should pass arguments through", async () => {
    const originalFn = jest.fn().mockImplementation((a, b) => Promise.resolve(a + b));
    const wrappedFn = withPerformanceTracking("add-fn", originalFn);

    const result = await wrappedFn(1, 2);

    expect(result).toBe(3);
    expect(originalFn).toHaveBeenCalledWith(1, 2);
  });

  it("should track failed requests", async () => {
    const originalFn = jest.fn().mockRejectedValue(new Error("Error"));
    const wrappedFn = withPerformanceTracking("failing-fn", originalFn, "api");

    await expect(wrappedFn()).rejects.toThrow("Error");

    const metrics = PerformanceMonitor.getMetricsByName("failing-fn");
    expect(metrics).toHaveLength(1);
    expect(metrics[0].metadata?.success).toBe(false);
  });
});
