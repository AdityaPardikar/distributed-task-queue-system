import { useState, useEffect, useCallback } from "react";
import type {
  DashboardMetrics,
  RecentTask,
  WorkerHealth,
  ChartDataPoint,
} from "../types/dashboard";
import { useWebSocket } from "./useWebSocket";
import api from "../services/api";

interface UseMetricsReturn {
  metrics: DashboardMetrics | null;
  recentTasks: RecentTask[];
  workers: WorkerHealth[];
  queueDepthData: ChartDataPoint[];
  completionRateData: ChartDataPoint[];
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

const POLLING_INTERVAL = 10000; // 10 seconds fallback polling
const WEBSOCKET_URL = "ws://localhost:8000/ws/metrics";

export const useMetrics = (): UseMetricsReturn => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentTasks, setRecentTasks] = useState<RecentTask[]>([]);
  const [workers, setWorkers] = useState<WorkerHealth[]>([]);
  const [queueDepthData, setQueueDepthData] = useState<ChartDataPoint[]>([]);
  const [completionRateData, setCompletionRateData] = useState<
    ChartDataPoint[]
  >([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usePolling, setUsePolling] = useState(false);

  // Fetch metrics from API
  const fetchMetrics = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch dashboard metrics
      const metricsResponse = await api.dashboardAPI.getStats();
      const metricsData = metricsResponse.data;

      setMetrics({
        totalTasks: metricsData.total_tasks || 0,
        pendingTasks: metricsData.pending_tasks || 0,
        runningTasks: metricsData.running_tasks || 0,
        completedTasks: metricsData.completed_tasks || 0,
        failedTasks: metricsData.failed_tasks || 0,
        activeWorkers: metricsData.active_workers || 0,
        totalWorkers: metricsData.total_workers || 0,
        queueSize: metricsData.queue_size || 0,
        successRate: metricsData.success_rate || 0,
        avgProcessingTime: metricsData.avg_processing_time || 0,
      });

      // Fetch recent tasks
      const tasksResponse = await api.dashboardAPI.getRecentTasks(20);
      setRecentTasks(
        (tasksResponse.data || []).map((task: Record<string, unknown>) => ({
          id: task.id,
          name: task.name || "Unnamed Task",
          status: task.status,
          priority: task.priority || "medium",
          createdAt: task.created_at,
          startedAt: task.started_at,
          completedAt: task.completed_at,
          duration: task.duration,
          worker: task.worker_id,
        })),
      );

      // Fetch worker status
      const workersResponse = await api.dashboardAPI.getWorkers();
      setWorkers(
        (workersResponse.data || []).map((worker: Record<string, unknown>) => ({
          id: worker.id,
          name: worker.name || `Worker ${worker.id}`,
          status: worker.status,
          taskCount: worker.task_count || 0,
          lastHeartbeat: worker.last_heartbeat,
          cpuUsage: worker.cpu_usage || 0,
          memoryUsage: worker.memory_usage || 0,
        })),
      );

      // Generate mock chart data (replace with real API data)
      const now = Date.now();
      const queueData: ChartDataPoint[] = [];
      const completionData: ChartDataPoint[] = [];

      for (let i = 23; i >= 0; i--) {
        const time = new Date(now - i * 3600000);
        queueData.push({
          time: `${time.getHours()}:00`,
          value: Math.floor(Math.random() * 100) + 20,
        });
        completionData.push({
          time: `${time.getHours()}:00`,
          value: Math.floor(Math.random() * 50) + 10,
        });
      }

      setQueueDepthData(queueData);
      setCompletionRateData(completionData);
    } catch (err) {
      console.error("Failed to fetch metrics:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch metrics");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data: unknown) => {
    if (!data || typeof data !== "object") return;

    const message = data as Record<string, unknown>;

    if (message.type === "metrics_update") {
      setMetrics(message.metrics as DashboardMetrics);
    } else if (message.type === "task_update" && message.task) {
      setRecentTasks((prev) => {
        const updated = [...prev];
        const task = message.task as RecentTask;
        const index = updated.findIndex((t) => t.id === task.id);
        if (index >= 0) {
          updated[index] = task;
        } else {
          updated.unshift(task);
          if (updated.length > 20) updated.pop();
        }
        return updated;
      });
    } else if (message.type === "worker_update") {
      setWorkers(message.workers as WorkerHealth[]);
    }
  }, []);

  // WebSocket connection
  const { isConnected } = useWebSocket({
    url: WEBSOCKET_URL,
    onMessage: handleWebSocketMessage,
    onError: () => {
      console.warn("WebSocket error, falling back to polling");
      setUsePolling(true);
    },
    onDisconnect: () => {
      setUsePolling(true);
    },
  });

  // Initial fetch
  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // Polling fallback when WebSocket is not connected
  useEffect(() => {
    if (!isConnected || usePolling) {
      const interval = setInterval(fetchMetrics, POLLING_INTERVAL);
      return () => clearInterval(interval);
    }
  }, [isConnected, usePolling, fetchMetrics]);

  return {
    metrics,
    recentTasks,
    workers,
    queueDepthData,
    completionRateData,
    isLoading,
    error,
    refresh: fetchMetrics,
  };
};
