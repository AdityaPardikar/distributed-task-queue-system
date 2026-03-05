import React, { useState, useEffect, useCallback } from "react";
import {
  Download,
  RefreshCw,
  AlertCircle,
  ClipboardList,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import api from "../services/api";
import AdvancedFilters from "../components/AdvancedFilters";
import type { FilterCriteria } from "../components/AdvancedFilters";
import { useFilterPresets } from "../services/FilterService";
import StatusBadge from "../components/StatusBadge";
import SkeletonLoader from "../components/SkeletonLoader";
import EmptyState from "../components/EmptyState";

interface Task {
  id: number | string;
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  priority: "low" | "medium" | "high" | "critical";
  created_at: string;
  started_at?: string;
  completed_at?: string;
  worker_id?: string;
}

const TasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState<FilterCriteria>({
    searchQuery: "",
    statuses: [],
    priorities: [],
    startDate: "",
    endDate: "",
    workerId: "",
    sortBy: "date",
    sortOrder: "desc",
  });
  const { presets, savePreset } = useFilterPresets();

  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params: Record<string, unknown> = {
        page,
        per_page: 20,
      };

      if (filters.searchQuery) params.search = filters.searchQuery;
      if (filters.statuses.length > 0) params.status = filters.statuses;
      if (filters.priorities.length > 0) params.priority = filters.priorities;
      if (filters.startDate) params.start_date = filters.startDate;
      if (filters.endDate) params.end_date = filters.endDate;
      if (filters.workerId) params.worker_id = filters.workerId;
      params.sort_by = filters.sortBy;
      params.sort_order = filters.sortOrder;

      const response = await api.getTasks(params);
      setTasks(response.data || []);
      setTotalPages(Math.ceil((response.total || 0) / 20));
    } catch (err) {
      console.error("Failed to fetch tasks:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch tasks");
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (error && tasks.length === 0) {
    return (
      <div className="bg-white border border-red-200 rounded-2xl p-8 shadow-sm animate-fade-in">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <AlertCircle className="text-red-600" size={24} />
          </div>
          <div>
            <h3 className="font-bold text-red-900 text-lg">
              Failed to load tasks
            </h3>
            <p className="text-red-600 text-sm mt-1">{error}</p>
            <button
              onClick={fetchTasks}
              className="mt-4 px-5 py-2.5 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors text-sm font-semibold"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Tasks
          </h1>
          <p className="text-slate-500 text-sm mt-0.5">
            View and manage all tasks across your queue
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchTasks}
            disabled={loading}
            className="px-4 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-all
                       disabled:opacity-50 flex items-center gap-2 text-sm font-semibold shadow-sm shadow-primary-600/20"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
          <button className="px-4 py-2.5 bg-white text-slate-700 border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors flex items-center gap-2 text-sm font-semibold">
            <Download size={15} />
            Export
          </button>
        </div>
      </div>

      {/* Filters */}
      <AdvancedFilters
        onFilterChange={(newFilters) => {
          setFilters(newFilters);
          setPage(1);
        }}
        onSavePreset={(name, filters) => {
          savePreset(name, filters);
        }}
        savedPresets={presets}
        loading={loading}
      />

      {/* Tasks Table */}
      <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="text-left py-3.5 px-5 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  ID
                </th>
                <th className="text-left py-3.5 px-5 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Task Name
                </th>
                <th className="text-left py-3.5 px-5 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="text-left py-3.5 px-5 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Priority
                </th>
                <th className="text-left py-3.5 px-5 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Worker
                </th>
                <th className="text-left py-3.5 px-5 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Created
                </th>
                <th className="text-left py-3.5 px-5 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <SkeletonLoader.Table rows={8} cols={7} />
              ) : tasks.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <EmptyState
                      title="No tasks found"
                      description="Try adjusting your filters, or create a new task to get started."
                      icon={
                        <ClipboardList className="w-8 h-8 text-slate-300" />
                      }
                    />
                  </td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <tr
                    key={task.id}
                    className="hover:bg-slate-50/50 transition-colors"
                  >
                    <td className="py-3.5 px-5 text-sm text-slate-500 font-mono">
                      #{String(task.id).substring(0, 8)}
                    </td>
                    <td className="py-3.5 px-5 text-sm font-semibold text-slate-900">
                      {task.name}
                    </td>
                    <td className="py-3.5 px-5">
                      <StatusBadge value={task.status} variant="task" />
                    </td>
                    <td className="py-3.5 px-5">
                      <StatusBadge value={task.priority} variant="priority" />
                    </td>
                    <td className="py-3.5 px-5 text-sm text-slate-500 font-mono">
                      {task.worker_id || (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                    <td className="py-3.5 px-5 text-sm text-slate-500">
                      {formatDate(task.created_at)}
                    </td>
                    <td className="py-3.5 px-5">
                      <button className="text-primary-600 hover:text-primary-700 text-sm font-semibold transition-colors">
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-slate-100">
            <div className="flex items-center justify-between">
              <div className="text-sm text-slate-500">
                Page{" "}
                <span className="font-semibold text-slate-700">{page}</span> of{" "}
                <span className="font-semibold text-slate-700">
                  {totalPages}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-3.5 py-2 bg-white border border-slate-200 rounded-xl hover:bg-slate-50
                             disabled:opacity-40 disabled:cursor-not-allowed text-sm font-semibold text-slate-600
                             transition-colors flex items-center gap-1.5"
                >
                  <ChevronLeft size={15} />
                  Previous
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="px-3.5 py-2 bg-white border border-slate-200 rounded-xl hover:bg-slate-50
                             disabled:opacity-40 disabled:cursor-not-allowed text-sm font-semibold text-slate-600
                             transition-colors flex items-center gap-1.5"
                >
                  Next
                  <ChevronRight size={15} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TasksPage;
