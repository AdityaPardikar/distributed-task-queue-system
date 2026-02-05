import { useState, useEffect, useCallback, useRef } from "react";

// WebSocket URL configuration
const getMetricsWebSocketUrl = (): string => {
  const wsUrl = process.env.REACT_APP_WS_URL || process.env.VITE_WS_URL;
  if (wsUrl) return `${wsUrl}/metrics`;

  // Construct from current location
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/metrics`;
};

export interface MetricsData {
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  pendingTasks: number;
  runningTasks: number;
  avgCompletionTime: number;
  activeWorkers: number;
  queueDepth: number;
  throughput: number;
  errorRate: number;
  timestamp: number;
}

export interface WorkerHealth {
  workerId: string;
  status: "healthy" | "degraded" | "offline";
  cpuUsage: number;
  memoryUsage: number;
  taskCount: number;
  lastHeartbeat: number;
  uptime: number;
}

export interface MetricsStreamEvent {
  type: "metrics_update" | "worker_health" | "alert";
  payload: MetricsData | WorkerHealth | AlertData;
}

export interface AlertData {
  id: string;
  severity: "info" | "warning" | "critical";
  message: string;
  timestamp: number;
}

export interface UseMetricsStreamOptions {
  enabled?: boolean;
  onMetricsUpdate?: (metrics: MetricsData) => void;
  onWorkerHealthUpdate?: (health: WorkerHealth) => void;
  onAlert?: (alert: AlertData) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface UseMetricsStreamReturn {
  isConnected: boolean;
  metrics: MetricsData | null;
  workerHealthMap: Map<string, WorkerHealth>;
  alerts: AlertData[];
  lastUpdate: number | null;
  connect: () => void;
  disconnect: () => void;
  clearAlerts: () => void;
}

/**
 * Hook to stream real-time metrics from the server via WebSocket
 * Provides live metrics updates, worker health status, and system alerts
 */
export const useMetricsStream = (
  options: UseMetricsStreamOptions = {}
): UseMetricsStreamReturn => {
  const {
    enabled = true,
    onMetricsUpdate,
    onWorkerHealthUpdate,
    onAlert,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [workerHealthMap, setWorkerHealthMap] = useState<
    Map<string, WorkerHealth>
  >(new Map());
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | undefined>(undefined);

  // Handle incoming metrics update
  const handleMetricsUpdate = useCallback(
    (data: MetricsData) => {
      setMetrics(data);
      setLastUpdate(Date.now());
      onMetricsUpdate?.(data);
    },
    [onMetricsUpdate]
  );

  // Handle incoming worker health update
  const handleWorkerHealthUpdate = useCallback(
    (health: WorkerHealth) => {
      setWorkerHealthMap((prev) => {
        const newMap = new Map(prev);
        newMap.set(health.workerId, health);
        return newMap;
      });
      onWorkerHealthUpdate?.(health);
    },
    [onWorkerHealthUpdate]
  );

  // Handle incoming alert
  const handleAlert = useCallback(
    (alert: AlertData) => {
      setAlerts((prev) => [...prev.slice(-99), alert]); // Keep last 100 alerts
      onAlert?.(alert);
    },
    [onAlert]
  );

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!enabled) return;

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const wsUrl = getMetricsWebSocketUrl();
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("Metrics WebSocket connected");
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;

        // Subscribe to metrics stream
        ws.send(
          JSON.stringify({
            action: "subscribe",
            channels: ["metrics", "worker_health", "alerts"],
          })
        );
      };

      ws.onmessage = (event) => {
        try {
          const data: MetricsStreamEvent = JSON.parse(event.data);

          switch (data.type) {
            case "metrics_update":
              handleMetricsUpdate(data.payload as MetricsData);
              break;
            case "worker_health":
              handleWorkerHealthUpdate(data.payload as WorkerHealth);
              break;
            case "alert":
              handleAlert(data.payload as AlertData);
              break;
            default:
              console.warn("Unknown metrics event type:", data.type);
          }
        } catch (error) {
          console.error("Failed to parse metrics message:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("Metrics WebSocket error:", error);
      };

      ws.onclose = () => {
        console.log("Metrics WebSocket disconnected");
        setIsConnected(false);

        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(
            `Reconnecting metrics stream... Attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`
          );
          reconnectTimeoutRef.current = window.setTimeout(
            connect,
            reconnectInterval
          );
        } else {
          console.error("Max reconnection attempts reached for metrics stream");
        }
      };
    } catch (error) {
      console.error("Failed to connect to metrics stream:", error);
    }
  }, [
    enabled,
    handleMetricsUpdate,
    handleWorkerHealthUpdate,
    handleAlert,
    reconnectInterval,
    maxReconnectAttempts,
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Clear alerts
  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  // Connect on mount
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    isConnected,
    metrics,
    workerHealthMap,
    alerts,
    lastUpdate,
    connect,
    disconnect,
    clearAlerts,
  };
};

export default useMetricsStream;
