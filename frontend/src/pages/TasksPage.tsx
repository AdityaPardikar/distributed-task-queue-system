import React, { useState, useEffect, useCallback } from "react";
import { Download, RefreshCw } from "lucide-react";
import api from "../services/api";
import AdvancedFilters from "../components/AdvancedFilters";
import type { FilterCriteria } from "../components/AdvancedFilters";
import { useFilterPresets } from "../services/FilterService";

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
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const getStatusBadge = (status: Task["status"]) => {
    const classes = {
      completed: "bg-green-100 text-green-800",
      failed: "bg-red-100 text-red-800",
      running: "bg-blue-100 text-blue-800",
      pending: "bg-gray-100 text-gray-800",
    };
    return (
      <span
        className={`px-2 py-1 text-xs font-semibold rounded ${classes[status]}`}
      >
        {status.toUpperCase()}
      </span>
    );
  };

  const getPriorityBadge = (priority: Task["priority"]) => {
    const classes = {
      critical: "bg-red-600 text-white",
      high: "bg-orange-500 text-white",
      medium: "bg-yellow-500 text-white",
      low: "bg-gray-400 text-white",
    };
    return (
      <span
        className={`px-2 py-1 text-xs font-semibold rounded ${classes[priority]}`}
      >
        {priority.toUpperCase()}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

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
                <tr>
                  <td colSpan={7} className="text-center py-12">
                    <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-2" />
                    <p className="text-gray-600">Loading tasks...</p>
                  </td>
                </tr>
              ) : tasks.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-gray-500">
                    No tasks found
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
                    <td className="py-3 px-4">{getStatusBadge(task.status)}</td>
                    <td className="py-3 px-4">
                      {getPriorityBadge(task.priority)}
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
