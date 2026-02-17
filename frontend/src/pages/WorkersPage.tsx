import React, { useState, useEffect, useCallback } from "react";
import {
  RefreshCw,
  Play,
  Pause,
  Power,
  PowerOff,
  Server,
  Cpu,
  Activity,
  Clock,
  Search,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
} from "lucide-react";
import { workerAPI } from "../services/workerAPI";
import type { Worker, WorkerStatus } from "../types/worker";

/* ────────────────────────────────────────────── helpers ─── */

const STATUS_COLORS: Record<WorkerStatus, string> = {
  ACTIVE: "bg-green-100 text-green-800",
  DRAINING: "bg-yellow-100 text-yellow-800",
  OFFLINE: "bg-red-100 text-red-800",
  PAUSED: "bg-gray-200 text-gray-700",
};

const STATUS_DOT: Record<WorkerStatus, string> = {
  ACTIVE: "bg-green-500",
  DRAINING: "bg-yellow-500",
  OFFLINE: "bg-red-500",
  PAUSED: "bg-gray-400",
};

const formatDate = (d: string | null) =>
  d ? new Date(d).toLocaleString() : "—";

const timeAgo = (d: string | null): string => {
  if (!d) return "never";
  const seconds = Math.floor((Date.now() - new Date(d).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
};

const utilPercent = (w: Worker) =>
  w.capacity > 0 ? Math.round((w.current_load / w.capacity) * 100) : 0;

/* ═══════════════════════════════════════════ Component ═══ */

const WorkersPage: React.FC = () => {
  /* ── state ────────────────────────────────────────────── */
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<WorkerStatus | "">("");
  const [searchQuery, setSearchQuery] = useState("");
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<{
    workerId: string;
    action: string;
  } | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  /* ── data fetching ────────────────────────────────────── */
  const fetchWorkers = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await workerAPI.list(
        page,
        pageSize,
        statusFilter || undefined,
      );
      let items = data.items ?? [];
      // client-side hostname filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        items = items.filter((w) => w.hostname.toLowerCase().includes(q));
      }
      setWorkers(items);
      setTotal(data.total ?? 0);
    } catch (err) {
      console.error("Failed to fetch workers:", err);
      setError("Failed to load workers. The API may be unavailable.");
      // fallback mock data for development
      setWorkers(generateMockWorkers());
      setTotal(6);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, statusFilter, searchQuery]);

  useEffect(() => {
    fetchWorkers();
  }, [fetchWorkers]);

  // Auto-refresh every 10 seconds
  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(fetchWorkers, 10_000);
    return () => clearInterval(id);
  }, [autoRefresh, fetchWorkers]);

  /* ── actions ──────────────────────────────────────────── */
  const handleAction = async (workerId: string, action: string) => {
    try {
      setActionLoading(workerId);
      switch (action) {
        case "pause":
          await workerAPI.pause(workerId);
          break;
        case "resume":
          await workerAPI.resume(workerId);
          break;
        case "drain":
          await workerAPI.drain(workerId);
          break;
        case "remove":
          await workerAPI.remove(workerId);
          break;
        case "activate":
          await workerAPI.updateStatus(workerId, "ACTIVE");
          break;
      }
      setConfirmAction(null);
      await fetchWorkers();
    } catch (err) {
      console.error(`Action ${action} failed:`, err);
      setError(`Failed to ${action} worker.`);
    } finally {
      setActionLoading(null);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  /* ── summary stats ────────────────────────────────────── */
  const stats = {
    active: workers.filter((w) => w.status === "ACTIVE").length,
    draining: workers.filter((w) => w.status === "DRAINING").length,
    offline: workers.filter((w) => w.status === "OFFLINE").length,
    totalCapacity: workers.reduce((s, w) => s + w.capacity, 0),
    totalLoad: workers.reduce((s, w) => s + w.current_load, 0),
  };

  /* ═══════════════════════════════════════════ Render ════ */
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Worker Management
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Monitor and manage task processing workers
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={() => setAutoRefresh(!autoRefresh)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Auto-refresh
          </label>
          <button
            onClick={fetchWorkers}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          icon={<Server className="w-5 h-5 text-blue-600" />}
          label="Total Workers"
          value={workers.length}
          bg="bg-blue-50"
        />
        <StatCard
          icon={<Activity className="w-5 h-5 text-green-600" />}
          label="Active"
          value={stats.active}
          bg="bg-green-50"
        />
        <StatCard
          icon={<Pause className="w-5 h-5 text-yellow-600" />}
          label="Draining"
          value={stats.draining}
          bg="bg-yellow-50"
        />
        <StatCard
          icon={<PowerOff className="w-5 h-5 text-red-600" />}
          label="Offline"
          value={stats.offline}
          bg="bg-red-50"
        />
        <StatCard
          icon={<Cpu className="w-5 h-5 text-indigo-600" />}
          label="Capacity Usage"
          value={`${stats.totalLoad} / ${stats.totalCapacity}`}
          bg="bg-indigo-50"
        />
      </div>

      {/* Capacity Bar */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Overall Capacity Utilization</span>
          <span>
            {stats.totalCapacity > 0
              ? Math.round((stats.totalLoad / stats.totalCapacity) * 100)
              : 0}
            %
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-blue-500 to-indigo-500 h-3 rounded-full transition-all duration-500"
            style={{
              width: `${stats.totalCapacity > 0 ? Math.min(100, Math.round((stats.totalLoad / stats.totalCapacity) * 100)) : 0}%`,
            }}
          />
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 flex flex-wrap gap-4 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by hostname…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value as WorkerStatus | "");
            setPage(1);
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="ACTIVE">Active</option>
          <option value="DRAINING">Draining</option>
          <option value="OFFLINE">Offline</option>
        </select>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <span className="text-sm text-red-700">{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-500 hover:text-red-700 text-sm"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Worker Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <th className="px-6 py-3">Worker</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3 text-center">Load / Capacity</th>
                <th className="px-6 py-3">Utilization</th>
                <th className="px-6 py-3">Last Heartbeat</th>
                <th className="px-6 py-3">Registered</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading && workers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-16 text-center">
                    <RefreshCw className="w-6 h-6 text-gray-400 animate-spin mx-auto mb-2" />
                    <span className="text-gray-500">Loading workers…</span>
                  </td>
                </tr>
              ) : workers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-16 text-center">
                    <Server className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                    <p className="text-gray-500">No workers found</p>
                    <p className="text-xs text-gray-400 mt-1">
                      Workers will appear here once they register
                    </p>
                  </td>
                </tr>
              ) : (
                workers.map((w) => (
                  <tr
                    key={w.worker_id}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    {/* Worker Info */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${STATUS_DOT[w.status] ?? "bg-gray-300"}`}
                        />
                        <div>
                          <p className="font-medium text-gray-900">
                            {w.hostname}
                          </p>
                          <p className="text-xs text-gray-400 font-mono">
                            {w.worker_id.slice(0, 8)}…
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* Status Badge */}
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 text-xs font-semibold rounded-full ${STATUS_COLORS[w.status] ?? "bg-gray-100 text-gray-600"}`}
                      >
                        {w.status}
                      </span>
                    </td>

                    {/* Load */}
                    <td className="px-6 py-4 text-center font-mono">
                      {w.current_load} / {w.capacity}
                    </td>

                    {/* Utilization Bar */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                          <div
                            className={`h-2 rounded-full transition-all ${
                              utilPercent(w) > 80
                                ? "bg-red-500"
                                : utilPercent(w) > 50
                                  ? "bg-yellow-500"
                                  : "bg-green-500"
                            }`}
                            style={{
                              width: `${Math.min(100, utilPercent(w))}%`,
                            }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 w-9 text-right">
                          {utilPercent(w)}%
                        </span>
                      </div>
                    </td>

                    {/* Heartbeat */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-gray-400" />
                        <span className="text-gray-600">
                          {timeAgo(w.last_heartbeat)}
                        </span>
                      </div>
                    </td>

                    {/* Registered */}
                    <td className="px-6 py-4 text-gray-500 text-xs">
                      {formatDate(w.created_at)}
                    </td>

                    {/* Actions */}
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {w.status === "ACTIVE" && (
                          <>
                            <ActionBtn
                              icon={<Pause className="w-4 h-4" />}
                              title="Pause"
                              color="text-yellow-600 hover:bg-yellow-50"
                              loading={actionLoading === w.worker_id}
                              onClick={() =>
                                setConfirmAction({
                                  workerId: w.worker_id,
                                  action: "pause",
                                })
                              }
                            />
                            <ActionBtn
                              icon={<Power className="w-4 h-4" />}
                              title="Drain"
                              color="text-orange-600 hover:bg-orange-50"
                              loading={actionLoading === w.worker_id}
                              onClick={() =>
                                setConfirmAction({
                                  workerId: w.worker_id,
                                  action: "drain",
                                })
                              }
                            />
                          </>
                        )}
                        {(w.status === "PAUSED" || w.status === "DRAINING") && (
                          <ActionBtn
                            icon={<Play className="w-4 h-4" />}
                            title="Resume"
                            color="text-green-600 hover:bg-green-50"
                            loading={actionLoading === w.worker_id}
                            onClick={() =>
                              setConfirmAction({
                                workerId: w.worker_id,
                                action: "resume",
                              })
                            }
                          />
                        )}
                        {w.status === "OFFLINE" && (
                          <ActionBtn
                            icon={<Play className="w-4 h-4" />}
                            title="Activate"
                            color="text-green-600 hover:bg-green-50"
                            loading={actionLoading === w.worker_id}
                            onClick={() =>
                              setConfirmAction({
                                workerId: w.worker_id,
                                action: "activate",
                              })
                            }
                          />
                        )}
                        <ActionBtn
                          icon={<PowerOff className="w-4 h-4" />}
                          title="Remove"
                          color="text-red-600 hover:bg-red-50"
                          loading={actionLoading === w.worker_id}
                          onClick={() =>
                            setConfirmAction({
                              workerId: w.worker_id,
                              action: "remove",
                            })
                          }
                        />
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-3 border-t bg-gray-50">
            <span className="text-sm text-gray-500">
              Showing {(page - 1) * pageSize + 1}–
              {Math.min(page * pageSize, total)} of {total}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm font-medium">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Confirm Dialog */}
      {confirmAction && (
        <ConfirmDialog
          action={confirmAction.action}
          onConfirm={() =>
            handleAction(confirmAction.workerId, confirmAction.action)
          }
          onCancel={() => setConfirmAction(null)}
          loading={actionLoading === confirmAction.workerId}
        />
      )}
    </div>
  );
};

/* ─────────────── sub-components ──────────────────────── */

const StatCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string | number;
  bg: string;
}> = ({ icon, label, value, bg }) => (
  <div className={`${bg} rounded-lg p-4 flex items-center gap-3`}>
    <div className="p-2 bg-white rounded-lg shadow-sm">{icon}</div>
    <div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  </div>
);

const ActionBtn: React.FC<{
  icon: React.ReactNode;
  title: string;
  color: string;
  loading: boolean;
  onClick: () => void;
}> = ({ icon, title, color, loading, onClick }) => (
  <button
    onClick={onClick}
    disabled={loading}
    title={title}
    className={`p-1.5 rounded-lg ${color} transition-colors disabled:opacity-40`}
  >
    {icon}
  </button>
);

const ConfirmDialog: React.FC<{
  action: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading: boolean;
}> = ({ action, onConfirm, onCancel, loading }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center">
    <div
      className="absolute inset-0 bg-black/40"
      onClick={onCancel}
      role="presentation"
    />
    <div className="relative bg-white rounded-xl shadow-xl p-6 max-w-sm w-full mx-4 animate-in fade-in">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Confirm {action.charAt(0).toUpperCase() + action.slice(1)}
      </h3>
      <p className="text-sm text-gray-600 mb-6">
        Are you sure you want to <strong>{action}</strong> this worker? This
        action may affect running tasks.
      </p>
      <div className="flex justify-end gap-3">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          disabled={loading}
          className={`px-4 py-2 text-sm text-white rounded-lg transition-colors disabled:opacity-50 ${
            action === "remove"
              ? "bg-red-600 hover:bg-red-700"
              : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loading ? "Processing…" : `Yes, ${action}`}
        </button>
      </div>
    </div>
  </div>
);

/* ────────────── mock data fallback ──────────────────── */

function generateMockWorkers(): Worker[] {
  const statuses: WorkerStatus[] = [
    "ACTIVE",
    "ACTIVE",
    "ACTIVE",
    "DRAINING",
    "OFFLINE",
    "ACTIVE",
  ];
  return statuses.map((status, i) => ({
    worker_id: `mock-${crypto.randomUUID?.() ?? `0000-${i}`}`,
    hostname: `worker-${i + 1}.taskflow.local`,
    status,
    capacity: 10,
    current_load: status === "OFFLINE" ? 0 : Math.floor(Math.random() * 10),
    last_heartbeat:
      status === "OFFLINE"
        ? new Date(Date.now() - 3600_000).toISOString()
        : new Date(Date.now() - Math.random() * 30_000).toISOString(),
    created_at: new Date(Date.now() - 86400_000 * (i + 1)).toISOString(),
  }));
}

export default WorkersPage;
