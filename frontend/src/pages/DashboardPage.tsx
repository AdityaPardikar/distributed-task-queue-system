import React from "react";
import { RefreshCw, Activity, Server, AlertCircle } from "lucide-react";
import MetricsCards from "../components/MetricsCards";
import ChartsSection from "../components/ChartsSection";
import RecentTasksList from "../components/RecentTasksList";
import { useMetrics } from "../hooks/useMetrics";

const DashboardPage: React.FC = () => {
  const {
    metrics,
    recentTasks,
    workers,
    queueDepthData,
    completionRateData,
    isLoading,
    error,
    refresh,
  } = useMetrics();

  if (isLoading && !metrics) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <AlertCircle className="text-red-600" size={24} />
          <div>
            <h3 className="font-semibold text-red-900">
              Error loading dashboard
            </h3>
            <p className="text-red-700 text-sm mt-1">{error}</p>
            <button
              onClick={refresh}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
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
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">
            Welcome to TaskFlow - Monitor your distributed task queue
          </p>
        </div>
        <button
          onClick={refresh}
          disabled={isLoading}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <RefreshCw size={16} className={isLoading ? "animate-spin" : ""} />
          Refresh Data
        </button>
      </div>

      {/* Metrics Cards */}
      {metrics && (
        <MetricsCards
          metrics={{
            totalTasks: metrics.totalTasks,
            activeWorkers: metrics.activeWorkers,
            queueSize: metrics.queueSize,
            successRate: metrics.successRate,
            pendingTasks: metrics.pendingTasks,
            runningTasks: metrics.runningTasks,
            completedTasks: metrics.completedTasks,
            failedTasks: metrics.failedTasks,
          }}
        />
      )}

      {/* Worker Health Status */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Server size={20} />
            Worker Health Status
          </h3>
          <span className="text-sm text-gray-500">
            {workers.filter((w) => w.status === "active").length} /{" "}
            {workers.length} Active
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {workers.slice(0, 8).map((worker) => (
            <div
              key={worker.id}
              className={`p-4 rounded-lg border-2 ${
                worker.status === "active"
                  ? "border-green-200 bg-green-50"
                  : worker.status === "idle"
                    ? "border-yellow-200 bg-yellow-50"
                    : "border-gray-200 bg-gray-50"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900 truncate">
                  {worker.name}
                </span>
                <Activity
                  size={16}
                  className={
                    worker.status === "active"
                      ? "text-green-600"
                      : worker.status === "idle"
                        ? "text-yellow-600"
                        : "text-gray-400"
                  }
                />
              </div>
              <div className="text-xs text-gray-600 space-y-1">
                <div>Tasks: {worker.taskCount}</div>
                <div>CPU: {worker.cpuUsage.toFixed(1)}%</div>
                <div>Memory: {worker.memoryUsage.toFixed(1)}%</div>
              </div>
            </div>
          ))}
        </div>
        {workers.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No workers registered
          </div>
        )}
      </div>

      {/* Charts */}
      <ChartsSection
        queueDepthData={queueDepthData}
        completionRateData={completionRateData}
      />

      {/* Recent Tasks */}
      <RecentTasksList
        tasks={recentTasks}
        onTaskClick={(id) => console.log("Task clicked:", id)}
      />
    </div>
  );
};

export default DashboardPage;
