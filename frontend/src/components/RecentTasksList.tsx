import React from "react";
import {
  Clock,
  CheckCircle2,
  XCircle,
  RefreshCw,
  PlayCircle,
  AlertTriangle,
} from "lucide-react";
import type { RecentTask } from "../types/dashboard";

interface RecentTasksListProps {
  tasks: RecentTask[];
  onTaskClick?: (taskId: string) => void;
}

const RecentTasksList: React.FC<RecentTasksListProps> = ({
  tasks,
  onTaskClick,
}) => {
  const getStatusIcon = (status: RecentTask["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 size={16} className="text-green-600" />;
      case "failed":
        return <XCircle size={16} className="text-red-600" />;
      case "running":
        return <PlayCircle size={16} className="text-blue-600" />;
      case "retry":
        return <RefreshCw size={16} className="text-yellow-600" />;
      case "pending":
        return <Clock size={16} className="text-gray-400" />;
      default:
        return <AlertTriangle size={16} className="text-gray-400" />;
    }
  };

  const getStatusBadge = (status: RecentTask["status"]) => {
    const classes = {
      completed: "bg-green-100 text-green-800",
      failed: "bg-red-100 text-red-800",
      running: "bg-blue-100 text-blue-800",
      retry: "bg-yellow-100 text-yellow-800",
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

  const getPriorityBadge = (priority: RecentTask["priority"]) => {
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

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const formatDuration = (duration?: number) => {
    if (!duration) return "-";
    if (duration < 60) return `${duration}s`;
    const mins = Math.floor(duration / 60);
    const secs = duration % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-900">Recent Tasks</h3>
          <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View All →
          </button>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {tasks.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-500">
            No recent tasks
          </div>
        ) : (
          tasks.map((task) => (
            <div
              key={task.id}
              onClick={() => onTaskClick?.(task.id)}
              className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  <div className="mt-1">{getStatusIcon(task.status)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-gray-900 truncate">
                        {task.name}
                      </h4>
                      {getPriorityBadge(task.priority)}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>ID: {task.id.substring(0, 8)}</span>
                      {task.worker && (
                        <span className="flex items-center gap-1">
                          Worker: {task.worker}
                        </span>
                      )}
                      <span>{formatTimestamp(task.createdAt)}</span>
                      {task.duration && (
                        <span>Duration: {formatDuration(task.duration)}</span>
                      )}
                    </div>
                  </div>
                </div>
                <div>{getStatusBadge(task.status)}</div>
              </div>
            </div>
          ))
        )}
      </div>

      {tasks.length > 0 && (
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-center">
          <button className="text-sm text-gray-600 hover:text-gray-900 font-medium">
            Load More Tasks
          </button>
        </div>
      )}
    </div>
  );
};

export default RecentTasksList;
