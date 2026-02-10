/**
 * PerformanceMonitor - Service for tracking and reporting performance metrics
 * Tracks API response times, component render times, and custom metrics
 */

export interface PerformanceMetric {
  name: string;
  type: "api" | "render" | "custom";
  duration: number;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface PerformanceStats {
  count: number;
  totalDuration: number;
  avgDuration: number;
  minDuration: number;
  maxDuration: number;
  p50: number;
  p90: number;
  p99: number;
}

export interface PerformanceReport {
  startTime: number;
  endTime: number;
  metrics: Record<string, PerformanceStats>;
  apiMetrics: PerformanceStats;
  renderMetrics: PerformanceStats;
  customMetrics: PerformanceStats;
  totalMetrics: number;
}

class PerformanceMonitorClass {
  private metrics: PerformanceMetric[] = [];
  private maxMetrics: number = 1000;
  private isEnabled: boolean = true;
  private listeners: Set<(metric: PerformanceMetric) => void> = new Set();

  constructor() {
    // Setup performance observer for long tasks
    this.setupPerformanceObserver();
  }

  /**
   * Enable/disable performance monitoring
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }

  /**
   * Track API request performance
   */
  trackApiCall<T>(
    name: string,
    request: () => Promise<T>,
    metadata?: Record<string, unknown>,
  ): Promise<T> {
    return this.track(name, "api", request, metadata);
  }

  /**
   * Track component render performance
   */
  trackRender(
    componentName: string,
    duration: number,
    metadata?: Record<string, unknown>,
  ): void {
    if (!this.isEnabled) return;

    const metric: PerformanceMetric = {
      name: componentName,
      type: "render",
      duration,
      timestamp: Date.now(),
      metadata,
    };

    this.addMetric(metric);
  }

  /**
   * Track custom metric
   */
  trackCustom(
    name: string,
    duration: number,
    metadata?: Record<string, unknown>,
  ): void {
    if (!this.isEnabled) return;

    const metric: PerformanceMetric = {
      name,
      type: "custom",
      duration,
      timestamp: Date.now(),
      metadata,
    };

    this.addMetric(metric);
  }

  /**
   * Generic tracking function
   */
  async track<T>(
    name: string,
    type: PerformanceMetric["type"],
    operation: () => Promise<T>,
    metadata?: Record<string, unknown>,
  ): Promise<T> {
    if (!this.isEnabled) {
      return operation();
    }

    const startTime = performance.now();

    try {
      const result = await operation();
      const duration = performance.now() - startTime;

      const metric: PerformanceMetric = {
        name,
        type,
        duration,
        timestamp: Date.now(),
        metadata: {
          ...metadata,
          success: true,
        },
      };

      this.addMetric(metric);
      return result;
    } catch (error) {
      const duration = performance.now() - startTime;

      const metric: PerformanceMetric = {
        name,
        type,
        duration,
        timestamp: Date.now(),
        metadata: {
          ...metadata,
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
        },
      };

      this.addMetric(metric);
      throw error;
    }
  }

  /**
   * Start a timer and return a function to stop it
   */
  startTimer(
    name: string,
    type: PerformanceMetric["type"] = "custom",
  ): () => void {
    const startTime = performance.now();

    return (metadata?: Record<string, unknown>) => {
      const duration = performance.now() - startTime;
      const metric: PerformanceMetric = {
        name,
        type,
        duration,
        timestamp: Date.now(),
        metadata,
      };
      this.addMetric(metric);
    };
  }

  /**
   * Add a metric to the collection
   */
  private addMetric(metric: PerformanceMetric): void {
    this.metrics.push(metric);

    // Trim old metrics if exceeding max
    if (this.metrics.length > this.maxMetrics) {
      this.metrics = this.metrics.slice(-this.maxMetrics);
    }

    // Notify listeners
    this.listeners.forEach((listener) => listener(metric));
  }

  /**
   * Subscribe to new metrics
   */
  subscribe(callback: (metric: PerformanceMetric) => void): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * Get metrics by name
   */
  getMetricsByName(name: string): PerformanceMetric[] {
    return this.metrics.filter((m) => m.name === name);
  }

  /**
   * Get metrics by type
   */
  getMetricsByType(type: PerformanceMetric["type"]): PerformanceMetric[] {
    return this.metrics.filter((m) => m.type === type);
  }

  /**
   * Get metrics within a time range
   */
  getMetricsInRange(startTime: number, endTime: number): PerformanceMetric[] {
    return this.metrics.filter(
      (m) => m.timestamp >= startTime && m.timestamp <= endTime,
    );
  }

  /**
   * Calculate statistics for a set of metrics
   */
  calculateStats(metrics: PerformanceMetric[]): PerformanceStats {
    if (metrics.length === 0) {
      return {
        count: 0,
        totalDuration: 0,
        avgDuration: 0,
        minDuration: 0,
        maxDuration: 0,
        p50: 0,
        p90: 0,
        p99: 0,
      };
    }

    const durations = metrics.map((m) => m.duration).sort((a, b) => a - b);
    const total = durations.reduce((sum, d) => sum + d, 0);

    return {
      count: durations.length,
      totalDuration: total,
      avgDuration: total / durations.length,
      minDuration: durations[0],
      maxDuration: durations[durations.length - 1],
      p50: this.percentile(durations, 50),
      p90: this.percentile(durations, 90),
      p99: this.percentile(durations, 99),
    };
  }

  /**
   * Calculate percentile
   */
  private percentile(sortedValues: number[], percentile: number): number {
    if (sortedValues.length === 0) return 0;
    const index = Math.ceil((percentile / 100) * sortedValues.length) - 1;
    return sortedValues[Math.max(0, index)];
  }

  /**
   * Generate a performance report
   */
  generateReport(startTime?: number, endTime?: number): PerformanceReport {
    const now = Date.now();
    const start = startTime ?? now - 3600000; // Default: last hour
    const end = endTime ?? now;

    const metricsInRange = this.getMetricsInRange(start, end);

    // Group by name
    const byName: Record<string, PerformanceMetric[]> = {};
    metricsInRange.forEach((m) => {
      if (!byName[m.name]) {
        byName[m.name] = [];
      }
      byName[m.name].push(m);
    });

    const metricStats: Record<string, PerformanceStats> = {};
    Object.entries(byName).forEach(([name, metrics]) => {
      metricStats[name] = this.calculateStats(metrics);
    });

    return {
      startTime: start,
      endTime: end,
      metrics: metricStats,
      apiMetrics: this.calculateStats(
        metricsInRange.filter((m) => m.type === "api"),
      ),
      renderMetrics: this.calculateStats(
        metricsInRange.filter((m) => m.type === "render"),
      ),
      customMetrics: this.calculateStats(
        metricsInRange.filter((m) => m.type === "custom"),
      ),
      totalMetrics: metricsInRange.length,
    };
  }

  /**
   * Get recent slow metrics
   */
  getSlowMetrics(threshold: number = 1000): PerformanceMetric[] {
    return this.metrics
      .filter((m) => m.duration > threshold)
      .sort((a, b) => b.duration - a.duration);
  }

  /**
   * Clear all metrics
   */
  clear(): void {
    this.metrics = [];
  }

  /**
   * Export metrics as JSON
   */
  exportToJSON(): string {
    return JSON.stringify(
      {
        exportedAt: new Date().toISOString(),
        metrics: this.metrics,
        report: this.generateReport(),
      },
      null,
      2,
    );
  }

  /**
   * Setup performance observer for long tasks
   */
  private setupPerformanceObserver(): void {
    if (typeof window === "undefined" || !window.PerformanceObserver) {
      return;
    }

    try {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.duration > 50) {
            // Long task threshold
            this.trackCustom("long-task", entry.duration, {
              startTime: entry.startTime,
              entryType: entry.entryType,
            });
          }
        });
      });

      observer.observe({ entryTypes: ["longtask"] });
    } catch (error) {
      // PerformanceObserver not supported or longtask not available
      console.debug("PerformanceObserver for longtask not supported");
    }
  }

  /**
   * Get Web Vitals metrics
   */
  getWebVitals(): Record<string, number | null> {
    if (typeof window === "undefined" || !window.performance) {
      return {};
    }

    const navigation = performance.getEntriesByType("navigation")[0] as
      | PerformanceNavigationTiming
      | undefined;
    const paint = performance.getEntriesByType("paint");

    const fcp = paint.find((entry) => entry.name === "first-contentful-paint");
    const fp = paint.find((entry) => entry.name === "first-paint");

    return {
      // Time to First Byte
      ttfb: navigation?.responseStart ?? null,
      // First Paint
      fp: fp?.startTime ?? null,
      // First Contentful Paint
      fcp: fcp?.startTime ?? null,
      // DOM Content Loaded
      dcl: navigation?.domContentLoadedEventEnd ?? null,
      // Load Event
      load: navigation?.loadEventEnd ?? null,
      // DOM Interactive
      domInteractive: navigation?.domInteractive ?? null,
    };
  }
}

// Export singleton instance
const PerformanceMonitor = new PerformanceMonitorClass();
export default PerformanceMonitor;

// Export types and helper functions
export { PerformanceMonitorClass };

/**
 * Higher-order function to wrap API calls with performance tracking
 */
export function withPerformanceTracking<
  T extends (...args: unknown[]) => Promise<unknown>,
>(name: string, fn: T): T {
  return (async (...args: Parameters<T>) => {
    return PerformanceMonitor.trackApiCall(name, () => fn(...args));
  }) as T;
}

/**
 * Decorator for tracking method performance (for class methods)
 */
export function trackPerformance(name?: string) {
  return function (
    _target: unknown,
    propertyKey: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;
    const metricName = name || propertyKey;

    descriptor.value = async function (...args: unknown[]) {
      return PerformanceMonitor.track(metricName, "custom", () =>
        originalMethod.apply(this, args),
      );
    };

    return descriptor;
  };
}
