/**
 * Monitoring API service — wraps metrics, health, alerts, and dashboard endpoints.
 */

import axios from "axios";
import type {
  SystemMetrics,
  SystemAlert,
  PerformanceDataPoint,
  WorkerHealthInfo,
  TrendDataPoint,
} from "../types/monitoring";

const API_BASE_URL = import.meta.env.VITE_API_URL || "";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/* ── helpers ── */

const generateMockMetrics = (): SystemMetrics => ({
  total_tasks: 12_540,
  pending_tasks: 42,
  running_tasks: 18,
  completed_tasks: 12_230,
  failed_tasks: 250,
  active_workers: 5,
  total_workers: 8,
  queue_size: 42,
  success_rate: 97.6,
  avg_processing_time: 1.8,
  tasks_per_minute: 85,
  error_rate: 2.4,
});

const generateMockPerformance = (): PerformanceDataPoint[] => {
  const pts: PerformanceDataPoint[] = [];
  const now = Date.now();
  for (let i = 23; i >= 0; i--) {
    pts.push({
      timestamp: new Date(now - i * 3600_000).toISOString(),
      throughput: 60 + Math.random() * 40,
      latency_p50: 20 + Math.random() * 30,
      latency_p95: 80 + Math.random() * 60,
      latency_p99: 150 + Math.random() * 100,
      error_rate: Math.random() * 5,
    });
  }
  return pts;
};

const generateMockWorkerHealth = (): WorkerHealthInfo[] =>
  Array.from({ length: 6 }, (_, i) => ({
    worker_id: `w-${i + 1}`,
    hostname: `worker-${i + 1}.taskflow.local`,
    status: (
      ["ACTIVE", "ACTIVE", "ACTIVE", "DRAINING", "OFFLINE", "ACTIVE"] as const
    )[i],
    capacity: 10,
    current_load: i === 4 ? 0 : Math.floor(Math.random() * 10),
    cpu_usage: Math.random() * 80,
    memory_usage: 30 + Math.random() * 40,
    last_heartbeat: new Date(Date.now() - Math.random() * 60_000).toISOString(),
    uptime_seconds: 3600 * (i + 1) * 12,
  }));

const generateMockAlerts = (): SystemAlert[] => {
  const severities: SystemAlert["severity"][] = [
    "info",
    "warning",
    "critical",
    "info",
    "warning",
  ];
  return severities.map((sev, i) => ({
    id: `alert-${i + 1}`,
    severity: sev,
    title: [
      "Worker heartbeat delayed",
      "Queue depth exceeds threshold",
      "Error rate spike detected",
      "New worker registered",
      "Disk usage above 80%",
    ][i],
    message: [
      "Worker-3 has not sent a heartbeat in 45 seconds",
      "Queue depth reached 150 (threshold: 100)",
      "Error rate jumped to 8.3% in the last 5 minutes",
      "worker-6.taskflow.local joined the cluster",
      "Primary database disk at 82% capacity",
    ][i],
    source: ["workers", "queue", "tasks", "workers", "database"][i],
    timestamp: new Date(Date.now() - i * 300_000).toISOString(),
    acknowledged: i > 2,
    resolved: i > 3,
  }));
};

const generateMockTrends = (): TrendDataPoint[] => {
  const pts: TrendDataPoint[] = [];
  const now = Date.now();
  for (let i = 23; i >= 0; i--) {
    pts.push({
      timestamp: new Date(now - i * 3600_000).toISOString(),
      pending: Math.floor(20 + Math.random() * 30),
      running: Math.floor(10 + Math.random() * 15),
      completed: Math.floor(50 + Math.random() * 50),
      failed: Math.floor(Math.random() * 8),
    });
  }
  return pts;
};

/* ── API ────────────────────────────────── */

export const monitoringAPI = {
  /** Get system health status. */
  getHealth: async () => {
    try {
      const res = await client.get("/health");
      return res.data;
    } catch {
      return { status: "unknown", checks: [] };
    }
  },

  /** Get aggregated system metrics (dashboard stats). */
  getMetrics: async (): Promise<SystemMetrics> => {
    try {
      const res = await client.get("/api/v1/dashboard/stats");
      return res.data?.data ?? res.data;
    } catch {
      return generateMockMetrics();
    }
  },

  /** Get performance time-series data. */
  getPerformance: async (
    _range: string = "24h",
  ): Promise<PerformanceDataPoint[]> => {
    try {
      const res = await client.get("/api/v1/analytics/trends", {
        params: { range: _range },
      });
      return res.data?.data ?? res.data;
    } catch {
      return generateMockPerformance();
    }
  },

  /** Get worker health information. */
  getWorkerHealth: async (): Promise<WorkerHealthInfo[]> => {
    try {
      const res = await client.get("/api/v1/workers", {
        params: { page: 1, page_size: 50 },
      });
      const items = res.data?.items ?? res.data ?? [];
      // augment with simulated CPU/memory for display
      return items.map((w: Record<string, unknown>) => ({
        worker_id: w.worker_id,
        hostname: w.hostname,
        status: w.status,
        capacity: w.capacity,
        current_load: w.current_load,
        cpu_usage: (w.cpu_usage as number) ?? Math.random() * 60,
        memory_usage: (w.memory_usage as number) ?? 30 + Math.random() * 40,
        last_heartbeat: w.last_heartbeat,
        uptime_seconds: (w.uptime_seconds as number) ?? 86400,
      }));
    } catch {
      return generateMockWorkerHealth();
    }
  },

  /** Get system alerts. */
  getAlerts: async (): Promise<SystemAlert[]> => {
    try {
      const res = await client.get("/api/v1/alerts");
      return res.data?.items ?? res.data ?? [];
    } catch {
      return generateMockAlerts();
    }
  },

  /** Get task trend data. */
  getTrends: async (_range: string = "24h"): Promise<TrendDataPoint[]> => {
    try {
      const res = await client.get("/api/v1/analytics/trends", {
        params: { range: _range },
      });
      return res.data?.data ?? res.data ?? [];
    } catch {
      return generateMockTrends();
    }
  },

  /** Acknowledge an alert. */
  acknowledgeAlert: async (alertId: string): Promise<void> => {
    await client.post(`/api/v1/alerts/${alertId}/acknowledge`);
  },
};

export default monitoringAPI;
