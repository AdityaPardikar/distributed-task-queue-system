export interface DashboardMetrics {
  totalTasks: number;
  pendingTasks: number;
  runningTasks: number;
  completedTasks: number;
  failedTasks: number;
  activeWorkers: number;
  totalWorkers: number;
  queueSize: number;
  successRate: number;
  avgProcessingTime: number;
}

export interface TaskStats {
  timestamp: string;
  pending: number;
  running: number;
  completed: number;
  failed: number;
}

export interface WorkerHealth {
  id: string;
  name: string;
  status: "active" | "idle" | "offline";
  taskCount: number;
  lastHeartbeat: string;
  cpuUsage: number;
  memoryUsage: number;
}

export interface RecentTask {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed" | "retry";
  priority: "low" | "medium" | "high" | "critical";
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  duration?: number;
  worker?: string;
}

export interface SystemAlert {
  id: string;
  severity: "info" | "warning" | "error" | "critical";
  message: string;
  timestamp: string;
  resolved: boolean;
}

export interface ChartDataPoint {
  time: string;
  value: number;
  label?: string;
}
