/**
 * Workflow API service — wraps workflow CRUD, visualization, template,
 * and chain endpoints under /api/v1/workflows/*.
 */

import axios from "axios";
import type {
  Workflow,
  WorkflowCreate,
  WorkflowCreateResponse,
  WorkflowVisualization,
  WorkflowTemplate,
  WorkflowTemplateCreate,
  WorkflowTemplateListResponse,
  DAGNode,
  DAGEdge,
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

/* ── Mock data for development ── */

const MOCK_WORKFLOWS: Workflow[] = [
  {
    workflow_id: "wf-001",
    workflow_name: "Data Ingestion Pipeline",
    total_tasks: 5,
    task_ids: ["t1", "t2", "t3", "t4", "t5"],
    status: "completed",
    created_at: new Date(Date.now() - 86_400_000 * 2).toISOString(),
    progress_percent: 100,
    completed: 5,
    failed: 0,
    running: 0,
    pending: 0,
  },
  {
    workflow_id: "wf-002",
    workflow_name: "Email Campaign Dispatch",
    total_tasks: 8,
    task_ids: ["t6", "t7", "t8", "t9", "t10", "t11", "t12", "t13"],
    status: "running",
    created_at: new Date(Date.now() - 3_600_000).toISOString(),
    progress_percent: 62.5,
    completed: 5,
    failed: 0,
    running: 2,
    pending: 1,
  },
  {
    workflow_id: "wf-003",
    workflow_name: "Report Generation",
    total_tasks: 4,
    task_ids: ["t14", "t15", "t16", "t17"],
    status: "failed",
    created_at: new Date(Date.now() - 7_200_000).toISOString(),
    progress_percent: 50,
    completed: 2,
    failed: 1,
    running: 0,
    pending: 1,
  },
  {
    workflow_id: "wf-004",
    workflow_name: "Nightly Cleanup",
    total_tasks: 3,
    task_ids: ["t18", "t19", "t20"],
    status: "pending",
    created_at: new Date(Date.now() - 600_000).toISOString(),
    progress_percent: 0,
    completed: 0,
    failed: 0,
    running: 0,
    pending: 3,
  },
  {
    workflow_id: "wf-005",
    workflow_name: "User Onboarding Flow",
    total_tasks: 6,
    task_ids: ["t21", "t22", "t23", "t24", "t25", "t26"],
    status: "completed",
    created_at: new Date(Date.now() - 172_800_000).toISOString(),
    progress_percent: 100,
    completed: 6,
    failed: 0,
    running: 0,
    pending: 0,
  },
];

const generateMockVisualization = (
  workflowId: string,
): WorkflowVisualization => {
  const nodes: DAGNode[] = [
    {
      id: "fetch",
      name: "Fetch Data",
      taskName: "fetch_data",
      status: "completed",
      level: 0,
      priority: 8,
      maxRetries: 3,
      timeoutSeconds: 120,
    },
    {
      id: "validate",
      name: "Validate",
      taskName: "validate_data",
      status: "completed",
      level: 1,
      priority: 7,
      maxRetries: 2,
      timeoutSeconds: 60,
    },
    {
      id: "transform_a",
      name: "Transform A",
      taskName: "transform_chunk",
      status: "completed",
      level: 2,
      priority: 5,
      maxRetries: 3,
      timeoutSeconds: 300,
    },
    {
      id: "transform_b",
      name: "Transform B",
      taskName: "transform_chunk",
      status: "running",
      level: 2,
      priority: 5,
      maxRetries: 3,
      timeoutSeconds: 300,
    },
    {
      id: "aggregate",
      name: "Aggregate",
      taskName: "aggregate_results",
      status: "pending",
      level: 3,
      priority: 7,
      maxRetries: 2,
      timeoutSeconds: 180,
    },
    {
      id: "notify",
      name: "Send Report",
      taskName: "send_notification",
      status: "pending",
      level: 4,
      priority: 6,
      maxRetries: 5,
      timeoutSeconds: 60,
    },
  ];

  const edges: DAGEdge[] = [
    { id: "e1", source: "fetch", target: "validate", type: "sequential" },
    { id: "e2", source: "validate", target: "transform_a", type: "sequential" },
    { id: "e3", source: "validate", target: "transform_b", type: "sequential" },
    { id: "e4", source: "transform_a", target: "aggregate", type: "wait_for_all" },
    { id: "e5", source: "transform_b", target: "aggregate", type: "wait_for_all" },
    { id: "e6", source: "aggregate", target: "notify", type: "sequential" },
  ];

  return {
    workflow_id: workflowId,
    workflow_name:
      MOCK_WORKFLOWS.find((w) => w.workflow_id === workflowId)
        ?.workflow_name ?? "Workflow",
    nodes,
    edges,
    execution_levels: [
      ["fetch"],
      ["validate"],
      ["transform_a", "transform_b"],
      ["aggregate"],
      ["notify"],
    ],
  };
};

const MOCK_TEMPLATES: WorkflowTemplate[] = [
  {
    template_id: "tpl-001",
    name: "Data Pipeline",
    description: "Standard ETL pipeline with parallel transforms",
    version: "1.0.0",
    tasks: [
      { name: "extract", task_name: "extract_data" },
      { name: "transform", task_name: "transform_data" },
      { name: "load", task_name: "load_data" },
    ],
    dependencies: { transform: ["extract"], load: ["transform"] },
  },
  {
    template_id: "tpl-002",
    name: "Notification Chain",
    description: "Sequential notification dispatch with retry",
    version: "1.1.0",
    tasks: [
      { name: "render", task_name: "render_template" },
      { name: "send", task_name: "send_email" },
      { name: "log", task_name: "log_delivery" },
    ],
    dependencies: { send: ["render"], log: ["send"] },
  },
];

/* ── API object ── */

export const workflowAPI = {
  /* ── Workflows ── */

  /** List all workflows. */
  listWorkflows: async (): Promise<Workflow[]> => {
    try {
      const res = await client.get("/api/v1/workflows");
      return res.data?.items ?? res.data ?? [];
    } catch {
      return MOCK_WORKFLOWS;
    }
  },

  /** Create a new workflow. */
  createWorkflow: async (
    data: WorkflowCreate,
  ): Promise<WorkflowCreateResponse> => {
    const res = await client.post("/api/v1/workflows", data);
    return res.data;
  },

  /** Get workflow status. */
  getWorkflowStatus: async (workflowId: string): Promise<Workflow> => {
    try {
      const res = await client.get(`/api/v1/workflows/${workflowId}`);
      return res.data;
    } catch {
      return (
        MOCK_WORKFLOWS.find((w) => w.workflow_id === workflowId) ??
        MOCK_WORKFLOWS[0]
      );
    }
  },

  /** Get DAG visualization data. */
  getVisualization: async (
    workflowId: string,
  ): Promise<WorkflowVisualization> => {
    try {
      const res = await client.get(
        `/api/v1/workflows/advanced/${workflowId}/visualization`,
      );
      return res.data;
    } catch {
      return generateMockVisualization(workflowId);
    }
  },

  /* ── Advanced Workflow ── */

  createAdvancedWorkflow: async (
    data: WorkflowCreate,
  ): Promise<WorkflowCreateResponse> => {
    const res = await client.post("/api/v1/workflows/advanced", data);
    return res.data;
  },

  /* ── Templates ── */

  listTemplates: async (): Promise<WorkflowTemplateListResponse> => {
    try {
      const res = await client.get("/api/v1/workflows/advanced/templates");
      return res.data;
    } catch {
      return { templates: MOCK_TEMPLATES, total: MOCK_TEMPLATES.length };
    }
  },

  getTemplate: async (templateId: string): Promise<WorkflowTemplate> => {
    try {
      const res = await client.get(
        `/api/v1/workflows/advanced/templates/${templateId}`,
      );
      return res.data;
    } catch {
      return (
        MOCK_TEMPLATES.find((t) => t.template_id === templateId) ??
        MOCK_TEMPLATES[0]
      );
    }
  },

  createTemplate: async (
    data: WorkflowTemplateCreate,
  ): Promise<WorkflowTemplate> => {
    const res = await client.post(
      "/api/v1/workflows/advanced/templates",
      data,
    );
    return res.data;
  },

  deleteTemplate: async (templateId: string): Promise<void> => {
    await client.delete(
      `/api/v1/workflows/advanced/templates/${templateId}`,
    );
  },

  /** Create a workflow from a template. */
  createFromTemplate: async (
    templateId: string,
    workflowName: string,
    parameters?: Record<string, unknown>,
  ): Promise<WorkflowCreateResponse> => {
    const res = await client.post(
      "/api/v1/workflows/advanced/from-template",
      { template_id: templateId, workflow_name: workflowName, parameters },
    );
    return res.data;
  },
};

export default workflowAPI;
