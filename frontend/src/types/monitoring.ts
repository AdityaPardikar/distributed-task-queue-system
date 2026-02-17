/**
 * Monitoring type definitions for system health, metrics, and alerts.
 */

export interface SystemHealth {
  status: "healthy" | "degraded" | "unhealthy";
  uptime_seconds: number;
  version: string;
  checks: HealthCheck[];
}

export interface HealthCheck {
  name: string;
  status: "pass" | "fail" | "warn";
  message?: string;
  duration_ms?: number;
}

export interface SystemMetrics {
  total_tasks: number;
  pending_tasks: number;
  running_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  active_workers: number;
  total_workers: number;
  queue_size: number;
  success_rate: number;
  avg_processing_time: number;
  tasks_per_minute: number;
  error_rate: number;
}

export interface PerformanceDataPoint {
  timestamp: string;
  throughput: number;
  latency_p50: number;
  latency_p95: number;
  latency_p99: number;
  error_rate: number;
}

export interface WorkerHealthInfo {
  worker_id: string;
  hostname: string;
  status: "ACTIVE" | "DRAINING" | "OFFLINE" | "PAUSED";
  capacity: number;
  current_load: number;
  cpu_usage: number;
  memory_usage: number;
  last_heartbeat: string | null;
  uptime_seconds: number;
}

export interface SystemAlert {
  id: string;
  severity: "info" | "warning" | "critical";
  title: string;
  message: string;
  source: string;
  timestamp: string;
  acknowledged: boolean;
  resolved: boolean;
}

export interface AlertsResponse {
  items: SystemAlert[];
  total: number;
}

export interface TrendDataPoint {
  timestamp: string;
  pending: number;
  running: number;
  completed: number;
  failed: number;
}

export type TimeRange = "1h" | "6h" | "24h" | "7d";
export type MonitoringTab = "overview" | "workers" | "alerts" | "performance";
