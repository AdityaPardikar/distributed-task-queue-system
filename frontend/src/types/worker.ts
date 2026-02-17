/**
 * Worker type definitions for the Workers Management page.
 */

export type WorkerStatus = "ACTIVE" | "DRAINING" | "OFFLINE" | "PAUSED";

export interface Worker {
  worker_id: string;
  hostname: string;
  status: WorkerStatus;
  capacity: number;
  current_load: number;
  last_heartbeat: string | null;
  created_at: string;
}

export interface WorkerListResponse {
  items: Worker[];
  total: number;
}

export interface WorkerTask {
  task_id: string;
  name: string;
  status: string;
  priority: number;
}

export interface WorkerTasksResponse {
  worker_id: string;
  total_tasks: number;
  tasks: WorkerTask[];
}

export interface WorkerMetrics {
  worker_id: string;
  tasks_completed: number;
  tasks_failed: number;
  avg_execution_time: number;
  uptime_seconds: number;
}

export interface WorkerRegisterParams {
  hostname: string;
  capacity: number;
}

export interface WorkerFilters {
  status: WorkerStatus | "";
  search: string;
  page: number;
  pageSize: number;
}
