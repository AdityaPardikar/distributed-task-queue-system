import React, { useState, useEffect, useCallback } from "react";
import { Download, RefreshCw, AlertCircle, ClipboardList } from "lucide-react";
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
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <div className="flex items-center gap-3">
          <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
          <div>
            <h3 className="font-semibold text-red-900">Failed to load tasks</h3>
            <p className="text-red-700 text-sm mt-1">{error}</p>
            <button
              onClick={fetchTasks}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tasks</h1>
          <p className="text-gray-500 mt-1">View and manage all tasks</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchTasks}
            disabled={loading}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2">
            <Download size={16} />
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
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                  ID
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                  Task Name
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                  Status
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                  Priority
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                  Worker
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                  Created At
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <SkeletonLoader.Table rows={8} cols={7} />
              ) : tasks.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <EmptyState
                      title="No tasks found"
                      description="Try adjusting your filters, or create a new task to get started."
                      icon={<ClipboardList className="w-8 h-8 text-gray-400" />}
                    />
                  </td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <tr key={task.id} className="hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm text-gray-900 font-mono">
                      #{String(task.id).substring(0, 8)}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-900">
                      {task.name}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge value={task.status} variant="task" />
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge value={task.priority} variant="priority" />
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-700">
                      {task.worker_id || "-"}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-500">
                      {formatDate(task.created_at)}
                    </td>
                    <td className="py-3 px-4">
                      <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                        View Details
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
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Page {page} of {totalPages}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  Next
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
