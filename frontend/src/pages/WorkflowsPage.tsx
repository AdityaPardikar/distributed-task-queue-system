/**
 * WorkflowsPage — List workflows with DAG visualization + template management.
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  GitBranch,
  Play,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  AlertTriangle,
  Layers,
  Filter,
} from "lucide-react";
import DAGVisualization from "../components/DAGVisualization";
import workflowAPI from "../services/workflowAPI";
import type {
  Workflow,
  WorkflowStatus,
  WorkflowVisualization,
  WorkflowTemplate,
  DAGNode,
} from "../types/workflow";

/* ── Status helpers ── */

const STATUS_CONFIG: Record<
  WorkflowStatus,
  { label: string; color: string; icon: React.ReactNode }
> = {
  pending: {
    label: "Pending",
    color: "bg-slate-100 text-slate-700",
    icon: <Clock className="w-3.5 h-3.5" />,
  },
  running: {
    label: "Running",
    color: "bg-primary-100 text-primary-700",
    icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
  },
  completed: {
    label: "Completed",
    color: "bg-emerald-50 text-emerald-700",
    icon: <CheckCircle2 className="w-3.5 h-3.5" />,
  },
  failed: {
    label: "Failed",
    color: "bg-red-50 text-red-700",
    icon: <XCircle className="w-3.5 h-3.5" />,
  },
  partial: {
    label: "Partial",
    color: "bg-amber-100 text-amber-700",
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
  },
};

/* ── Component ── */

const WorkflowsPage: React.FC = () => {
  /* state */
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<WorkflowStatus | "all">(
    "all",
  );
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [visualisation, setVisualisation] =
    useState<WorkflowVisualization | null>(null);
  const [vizLoading, setVizLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"workflows" | "templates">(
    "workflows",
  );

  /* fetchers */
  const fetchWorkflows = useCallback(async () => {
    setLoading(true);
    try {
      const data = await workflowAPI.listWorkflows();
      setWorkflows(data);
    } catch {
      /* handled by API mock fallback */
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTemplates = useCallback(async () => {
    try {
      const { templates: tpls } = await workflowAPI.listTemplates();
      setTemplates(tpls);
    } catch {
      /* handled by API mock fallback */
    }
  }, []);

  useEffect(() => {
    fetchWorkflows();
    fetchTemplates();
  }, [fetchWorkflows, fetchTemplates]);

  /* auto-refresh every 30 s */
  useEffect(() => {
    const id = setInterval(fetchWorkflows, 30_000);
    return () => clearInterval(id);
  }, [fetchWorkflows]);

  /* expand / collapse a workflow to view its DAG */
  const toggleExpand = useCallback(
    async (workflowId: string) => {
      if (expandedId === workflowId) {
        setExpandedId(null);
        setVisualisation(null);
        setSelectedNode(null);
        return;
      }
      setExpandedId(workflowId);
      setVizLoading(true);
      try {
        const viz = await workflowAPI.getVisualization(workflowId);
        setVisualisation(viz);
      } catch {
        setVisualisation(null);
      } finally {
        setVizLoading(false);
      }
    },
    [expandedId],
  );

  /* filtering */
  const filtered =
    statusFilter === "all"
      ? workflows
      : workflows.filter((w) => w.status === statusFilter);

  /* summary stats */
  const stats = {
    total: workflows.length,
    running: workflows.filter((w) => w.status === "running").length,
    completed: workflows.filter((w) => w.status === "completed").length,
    failed: workflows.filter((w) => w.status === "failed").length,
  };

  /* selected node detail panel */
  const selectedNodeData: DAGNode | null =
    visualisation?.nodes.find((n) => n.id === selectedNode) ?? null;

  /* ── Render ── */

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <GitBranch className="w-7 h-7 text-primary-600" />
            Workflows
          </h1>
          <p className="mt-0.5 text-sm text-slate-500">
            Manage task workflows and DAG pipelines
          </p>
        </div>
        <button
          onClick={fetchWorkflows}
          className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 hover:bg-slate-50 transition-all"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {(
          [
            {
              label: "Total Workflows",
              value: stats.total,
              color: "bg-primary-50 text-primary-700",
              icon: <Layers className="w-5 h-5" />,
            },
            {
              label: "Running",
              value: stats.running,
              color: "bg-primary-50 text-primary-700",
              icon: <Play className="w-5 h-5" />,
            },
            {
              label: "Completed",
              value: stats.completed,
              color: "bg-emerald-50 text-emerald-700",
              icon: <CheckCircle2 className="w-5 h-5" />,
            },
            {
              label: "Failed",
              value: stats.failed,
              color: "bg-red-50 text-red-700",
              icon: <XCircle className="w-5 h-5" />,
            },
          ] as const
        ).map((card) => (
          <div
            key={card.label}
            className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-4 flex items-center gap-4"
          >
            <div className={`rounded-xl p-2.5 ${card.color}`}>{card.icon}</div>
            <div>
              <p className="text-sm text-slate-500">{card.label}</p>
              <p className="text-2xl font-bold text-slate-900">{card.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-6">
          {(["workflows", "templates"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 text-sm font-semibold border-b-2 transition-colors capitalize ${
                activeTab === tab
                  ? "border-primary-600 text-primary-600"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              {tab === "workflows" ? (
                <span className="flex items-center gap-1.5">
                  <GitBranch className="w-4 h-4" /> Workflows
                </span>
              ) : (
                <span className="flex items-center gap-1.5">
                  <FileText className="w-4 h-4" /> Templates ({templates.length}
                  )
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* ── Workflows Tab ── */}
      {activeTab === "workflows" && (
        <>
          {/* Filter bar */}
          <div className="flex items-center gap-3">
            <Filter className="w-4 h-4 text-slate-400" />
            {(
              ["all", "pending", "running", "completed", "failed"] as const
            ).map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-3 py-1.5 text-xs rounded-full font-semibold transition-colors ${
                  statusFilter === s
                    ? "bg-primary-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {s === "all" ? "All" : STATUS_CONFIG[s].label}
              </button>
            ))}
          </div>

          {/* Workflow list */}
          {loading && workflows.length === 0 ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16 text-slate-400">
              <GitBranch className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p>No workflows found</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filtered.map((wf) => {
                const cfg = STATUS_CONFIG[wf.status];
                const isExpanded = expandedId === wf.workflow_id;
                return (
                  <div
                    key={wf.workflow_id}
                    className="bg-white rounded-2xl border border-slate-200/60 overflow-hidden"
                  >
                    {/* Row */}
                    <button
                      onClick={() => toggleExpand(wf.workflow_id)}
                      className="w-full flex items-center justify-between px-5 py-4 hover:bg-slate-50/50 transition-colors text-left"
                    >
                      <div className="flex items-center gap-4 min-w-0">
                        <span
                          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.color}`}
                        >
                          {cfg.icon} {cfg.label}
                        </span>
                        <div className="min-w-0">
                          <p className="font-semibold text-slate-900 truncate">
                            {wf.workflow_name}
                          </p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {wf.total_tasks} tasks · Created{" "}
                            {new Date(wf.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-6">
                        {/* Progress */}
                        <div className="hidden sm:flex items-center gap-3 w-48">
                          <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                wf.status === "failed"
                                  ? "bg-red-400"
                                  : wf.status === "running"
                                    ? "bg-primary-500"
                                    : "bg-emerald-500"
                              }`}
                              style={{ width: `${wf.progress_percent}%` }}
                            />
                          </div>
                          <span className="text-xs text-slate-500 w-10 text-right">
                            {wf.progress_percent.toFixed(0)}%
                          </span>
                        </div>

                        {/* Task counts */}
                        <div className="hidden md:flex items-center gap-2 text-xs text-slate-500">
                          <span className="text-emerald-600" title="Completed">
                            ✓{wf.completed}
                          </span>
                          <span className="text-primary-600" title="Running">
                            ▶{wf.running}
                          </span>
                          <span className="text-red-600" title="Failed">
                            ✕{wf.failed}
                          </span>
                          <span className="text-slate-400" title="Pending">
                            ◌{wf.pending}
                          </span>
                        </div>

                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-slate-400" />
                        )}
                      </div>
                    </button>

                    {/* Expanded DAG Panel */}
                    {isExpanded && (
                      <div className="border-t border-slate-100 px-5 py-4 bg-slate-50/50">
                        {vizLoading ? (
                          <div className="flex items-center justify-center h-48">
                            <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
                            <span className="ml-2 text-sm text-slate-500">
                              Loading DAG…
                            </span>
                          </div>
                        ) : visualisation ? (
                          <div className="flex flex-col lg:flex-row gap-4">
                            <div className="flex-1">
                              <h3 className="text-sm font-semibold text-slate-700 mb-2">
                                Dependency Graph
                              </h3>
                              <DAGVisualization
                                nodes={visualisation.nodes}
                                edges={visualisation.edges}
                                executionLevels={visualisation.execution_levels}
                                selectedNodeId={selectedNode}
                                onNodeClick={setSelectedNode}
                              />
                            </div>

                            {/* Node detail sidebar */}
                            {selectedNodeData && (
                              <div className="w-full lg:w-72 bg-white rounded-xl border border-slate-200/60 p-4 space-y-3 self-start">
                                <h4 className="font-semibold text-slate-900">
                                  {selectedNodeData.name}
                                </h4>
                                <dl className="space-y-2 text-sm">
                                  <div className="flex justify-between">
                                    <dt className="text-slate-500">Handler</dt>
                                    <dd className="font-mono text-slate-700 text-xs">
                                      {selectedNodeData.taskName}
                                    </dd>
                                  </div>
                                  <div className="flex justify-between">
                                    <dt className="text-slate-500">Status</dt>
                                    <dd>
                                      <span
                                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                                          STATUS_CONFIG[
                                            selectedNodeData.status as WorkflowStatus
                                          ]?.color ??
                                          "bg-slate-100 text-slate-600"
                                        }`}
                                      >
                                        {selectedNodeData.status}
                                      </span>
                                    </dd>
                                  </div>
                                  <div className="flex justify-between">
                                    <dt className="text-slate-500">Priority</dt>
                                    <dd className="text-slate-700">
                                      {selectedNodeData.priority}
                                    </dd>
                                  </div>
                                  <div className="flex justify-between">
                                    <dt className="text-slate-500">
                                      Max Retries
                                    </dt>
                                    <dd className="text-slate-700">
                                      {selectedNodeData.maxRetries}
                                    </dd>
                                  </div>
                                  <div className="flex justify-between">
                                    <dt className="text-slate-500">Timeout</dt>
                                    <dd className="text-slate-700">
                                      {selectedNodeData.timeoutSeconds}s
                                    </dd>
                                  </div>
                                  <div className="flex justify-between">
                                    <dt className="text-slate-500">Level</dt>
                                    <dd className="text-slate-700">
                                      {selectedNodeData.level}
                                    </dd>
                                  </div>
                                </dl>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-slate-400 text-center py-8">
                            Visualization unavailable
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* ── Templates Tab ── */}
      {activeTab === "templates" && (
        <div className="space-y-3">
          {templates.length === 0 ? (
            <div className="text-center py-16 text-slate-400">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p>No workflow templates yet</p>
            </div>
          ) : (
            templates.map((tpl) => (
              <div
                key={tpl.template_id}
                className="bg-white rounded-2xl border border-slate-200/60 p-5 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-slate-900">{tpl.name}</h3>
                    <p className="text-sm text-slate-500 mt-1">
                      {tpl.description || "No description"}
                    </p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                      <span>v{tpl.version}</span>
                      <span>·</span>
                      <span>{tpl.tasks.length} tasks</span>
                      {tpl.dependencies && (
                        <>
                          <span>·</span>
                          <span>
                            {Object.keys(tpl.dependencies).length} dependencies
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                  <button
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-primary-600 bg-primary-50 rounded-xl hover:bg-primary-100 transition-colors"
                    onClick={() => {
                      /* future: open create-from-template modal */
                    }}
                  >
                    <Play className="w-3.5 h-3.5" />
                    Use Template
                  </button>
                </div>

                {/* Task list preview */}
                <div className="mt-3 flex flex-wrap gap-2">
                  {tpl.tasks.map((t) => (
                    <span
                      key={t.name}
                      className="px-2 py-1 bg-slate-50 rounded-lg text-xs text-slate-600 border border-slate-100"
                    >
                      {t.name}
                    </span>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default WorkflowsPage;
