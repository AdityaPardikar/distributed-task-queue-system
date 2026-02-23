/**
 * Workflow & Alert type definitions.
 * Maps to backend schemas in workflows.py, advanced_workflows.py, and alerts.py.
 */

/* ── DAG / Visualization ── */

export interface DAGNode {
  id: string;
  name: string;
  taskName: string;
  status: WorkflowTaskStatus;
  level: number;
  position?: { x: number; y: number };
  priority: number;
  maxRetries: number;
  timeoutSeconds: number;
  condition?: TaskCondition | null;
}

export interface DAGEdge {
  id: string;
  source: string;
  target: string;
  type: DependencyType;
}

export type DependencyType = "wait_for_all" | "wait_for_any" | "sequential";

export type WorkflowTaskStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

/* ── Workflow ── */

export interface Workflow {
  workflow_id: string;
  workflow_name: string;
  total_tasks: number;
  task_ids: string[];
  status: WorkflowStatus;
  created_at: string;
  updated_at?: string;
  progress_percent: number;
  completed: number;
  failed: number;
  running: number;
  pending: number;
}

export type WorkflowStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "partial";

export interface WorkflowVisualization {
  workflow_id: string;
  workflow_name: string | null;
  nodes: DAGNode[];
  edges: DAGEdge[];
  execution_levels: string[][];
}

/* ── Workflow Creation ── */

export interface TaskDefinition {
  name: string;
  task_name: string;
  task_args?: unknown[];
  task_kwargs?: Record<string, unknown>;
  priority?: number;
  max_retries?: number;
  timeout_seconds?: number;
  condition?: TaskCondition | null;
}

export interface TaskCondition {
  field: string;
  operator: "eq" | "neq" | "gt" | "lt" | "contains" | "exists";
  value?: unknown;
  conditions?: TaskCondition[];
}

export interface WorkflowCreate {
  workflow_name: string;
  tasks: TaskDefinition[];
  dependencies?: Record<string, string[]>;
  conditions?: Record<string, TaskCondition>;
}

export interface WorkflowCreateResponse {
  workflow_id: string;
  workflow_name: string;
  total_tasks: number;
  task_ids: string[];
}

/* ── Templates ── */

export interface WorkflowTemplate {
  template_id: string;
  name: string;
  description: string;
  version: string;
  tasks: TaskDefinition[];
  dependencies?: Record<string, string[]>;
  conditions?: Record<string, TaskCondition> | null;
  created_at?: string;
}

export interface WorkflowTemplateCreate {
  name: string;
  description?: string;
  version?: string;
  tasks: TaskDefinition[];
  dependencies?: Record<string, string[]>;
  conditions?: Record<string, TaskCondition>;
}

export interface WorkflowTemplateListResponse {
  templates: WorkflowTemplate[];
  total: number;
}

/* ── Alerts ── */

export interface Alert {
  alert_id: string;
  alert_type: string;
  severity: AlertSeverity;
  description: string;
  metadata: Record<string, unknown>;
  acknowledged: boolean;
  created_at: string;
  acknowledged_at: string | null;
}

export type AlertSeverity = "info" | "warning" | "error" | "critical";

export interface AlertStats {
  total_alerts: number;
  active_alerts: number;
  acknowledged_alerts: number;
  by_severity: Record<string, number>;
  active_by_type: Record<string, number>;
}

export interface AlertHistoryItem {
  alert_id: string;
  alert_type: string;
  severity: string;
  description: string;
  created_at: string;
  acknowledged: boolean;
}
