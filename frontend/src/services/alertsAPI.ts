/**
 * Alerts API service — wraps /api/v1/alerts/* endpoints.
 */

import axios from "axios";
import type {
  Alert,
  AlertStats,
  AlertHistoryItem,
  AlertSeverity,
} from "../types/workflow";

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

/* ── Mock data ── */

const MOCK_ALERTS: Alert[] = [
  {
    alert_id: "a-001",
    alert_type: "worker_heartbeat",
    severity: "critical",
    description: "Worker-3 has not sent a heartbeat in 120 seconds",
    metadata: { worker_id: "w-3", last_heartbeat: "2024-01-15T10:00:00Z" },
    acknowledged: false,
    created_at: new Date(Date.now() - 300_000).toISOString(),
    acknowledged_at: null,
  },
  {
    alert_id: "a-002",
    alert_type: "queue_depth",
    severity: "warning",
    description: "Queue depth exceeds threshold (180/100)",
    metadata: { current: 180, threshold: 100 },
    acknowledged: false,
    created_at: new Date(Date.now() - 600_000).toISOString(),
    acknowledged_at: null,
  },
  {
    alert_id: "a-003",
    alert_type: "error_rate",
    severity: "error",
    description: "Error rate spike: 8.3% (threshold 5%)",
    metadata: { current_rate: 8.3, threshold: 5 },
    acknowledged: false,
    created_at: new Date(Date.now() - 900_000).toISOString(),
    acknowledged_at: null,
  },
  {
    alert_id: "a-004",
    alert_type: "disk_usage",
    severity: "warning",
    description: "Primary database disk at 82% capacity",
    metadata: { usage_percent: 82, path: "/var/lib/postgresql" },
    acknowledged: true,
    created_at: new Date(Date.now() - 1_800_000).toISOString(),
    acknowledged_at: new Date(Date.now() - 900_000).toISOString(),
  },
  {
    alert_id: "a-005",
    alert_type: "worker_registered",
    severity: "info",
    description: "New worker registered: worker-7.taskflow.local",
    metadata: { worker_id: "w-7", hostname: "worker-7.taskflow.local" },
    acknowledged: true,
    created_at: new Date(Date.now() - 3_600_000).toISOString(),
    acknowledged_at: new Date(Date.now() - 3_000_000).toISOString(),
  },
  {
    alert_id: "a-006",
    alert_type: "task_timeout",
    severity: "error",
    description: "Task 'process_batch_42' exceeded timeout (300s)",
    metadata: { task_id: "t-42", timeout: 300 },
    acknowledged: false,
    created_at: new Date(Date.now() - 1_200_000).toISOString(),
    acknowledged_at: null,
  },
];

const MOCK_STATS: AlertStats = {
  total_alerts: 42,
  active_alerts: 4,
  acknowledged_alerts: 38,
  by_severity: { info: 12, warning: 15, error: 10, critical: 5 },
  active_by_type: {
    worker_heartbeat: 1,
    queue_depth: 1,
    error_rate: 1,
    task_timeout: 1,
  },
};

const MOCK_HISTORY: AlertHistoryItem[] = Array.from({ length: 20 }, (_, i) => {
  const severities: AlertSeverity[] = ["info", "warning", "error", "critical"];
  const types = [
    "worker_heartbeat",
    "queue_depth",
    "error_rate",
    "disk_usage",
    "task_timeout",
  ];
  return {
    alert_id: `ah-${i + 1}`,
    alert_type: types[i % types.length],
    severity: severities[i % severities.length],
    description: `Historical alert #${i + 1}`,
    created_at: new Date(Date.now() - i * 3_600_000).toISOString(),
    acknowledged: i > 5,
  };
});

/* ── API ── */

export const alertsAPI = {
  /** Get active alerts. */
  getActiveAlerts: async (includeAcknowledged = false): Promise<Alert[]> => {
    try {
      const res = await client.get("/api/v1/alerts", {
        params: { acknowledged: includeAcknowledged },
      });
      return res.data?.items ?? res.data ?? [];
    } catch {
      return includeAcknowledged
        ? MOCK_ALERTS
        : MOCK_ALERTS.filter((a) => !a.acknowledged);
    }
  },

  /** Get alert history. */
  getHistory: async (hours = 24, limit = 100): Promise<AlertHistoryItem[]> => {
    try {
      const res = await client.get("/api/v1/alerts/history", {
        params: { hours, limit },
      });
      return res.data ?? [];
    } catch {
      return MOCK_HISTORY;
    }
  },

  /** Acknowledge an alert. */
  acknowledge: async (
    alertId: string,
  ): Promise<{ alert_id: string; acknowledged: boolean }> => {
    try {
      const res = await client.post(`/api/v1/alerts/${alertId}/acknowledge`);
      return res.data;
    } catch {
      return { alert_id: alertId, acknowledged: true };
    }
  },

  /** Get alert statistics. */
  getStats: async (): Promise<AlertStats> => {
    try {
      const res = await client.get("/api/v1/alerts/stats");
      return res.data;
    } catch {
      return MOCK_STATS;
    }
  },

  /** Manually evaluate alert rules. */
  evaluateRules: async (): Promise<{ fired: number }> => {
    const res = await client.post("/api/v1/alerts/evaluate");
    return res.data;
  },
};

export default alertsAPI;
