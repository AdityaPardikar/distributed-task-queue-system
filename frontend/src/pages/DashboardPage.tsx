import React, { useState } from "react";
import {
  RefreshCw,
  Activity,
  Server,
  AlertCircle,
  LayoutDashboard,
  HeartPulse,
  Cpu,
  TrendingUp,
} from "lucide-react";
import MetricsCards from "../components/MetricsCards";
import ChartsSection from "../components/ChartsSection";
import RecentTasksList from "../components/RecentTasksList";
import SystemHealthMonitor from "../components/SystemHealthMonitor";
import SkeletonLoader from "../components/SkeletonLoader";
import EmptyState from "../components/EmptyState";
import { useMetrics } from "../hooks/useMetrics";

type ViewTab = "dashboard" | "health";

const DashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ViewTab>("dashboard");
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
      <div className="space-y-6 animate-fade-in">
        <SkeletonLoader.MetricCards count={4} />
        <SkeletonLoader.Chart height="h-72" />
        <SkeletonLoader.Chart height="h-72" />
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="bg-white border border-red-200 rounded-2xl p-8 shadow-sm animate-fade-in">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <AlertCircle className="text-red-600" size={24} />
          </div>
          <div>
            <h3 className="font-bold text-red-900 text-lg">
              Error loading dashboard
            </h3>
            <p className="text-red-600 text-sm mt-1">{error}</p>
            <button
              onClick={refresh}
              className="mt-4 px-5 py-2.5 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors text-sm font-semibold shadow-sm"
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
            Dashboard
          </h1>
          <p className="text-slate-500 text-sm mt-0.5">
            Monitor your distributed task queue in real time
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Tab Navigation */}
          <div className="bg-slate-100 rounded-xl p-1 flex">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all ${
                activeTab === "dashboard"
                  ? "bg-white text-primary-700 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <LayoutDashboard size={15} />
              Overview
            </button>
            <button
              onClick={() => setActiveTab("health")}
              className={`px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all ${
                activeTab === "health"
                  ? "bg-white text-primary-700 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <HeartPulse size={15} />
              Health
            </button>
          </div>
          {activeTab === "dashboard" && (
            <button
              onClick={refresh}
              disabled={isLoading}
              className="px-4 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-all
                         disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm font-semibold
                         shadow-sm shadow-primary-600/20"
            >
              <RefreshCw
                size={15}
                className={isLoading ? "animate-spin" : ""}
              />
              Refresh
            </button>
          )}
        </div>
      </div>

      {/* Content based on active tab */}
      {activeTab === "health" ? (
        <SystemHealthMonitor />
      ) : (
        <>
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
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Server size={18} className="text-slate-500" />
                Worker Health
              </h3>
              <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-lg">
                {workers.filter((w) => w.status === "active").length} /{" "}
                {workers.length} Active
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {workers.slice(0, 8).map((worker) => (
                <div
                  key={worker.id}
                  className={`p-4 rounded-xl border transition-all hover:shadow-sm ${
                    worker.status === "active"
                      ? "border-emerald-200 bg-emerald-50/50"
                      : worker.status === "idle"
                        ? "border-amber-200 bg-amber-50/50"
                        : "border-slate-200 bg-slate-50/50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2.5">
                    <span className="font-semibold text-sm text-slate-900 truncate">
                      {worker.name}
                    </span>
                    <Activity
                      size={14}
                      className={
                        worker.status === "active"
                          ? "text-emerald-500"
                          : worker.status === "idle"
                            ? "text-amber-500"
                            : "text-slate-400"
                      }
                    />
                  </div>
                  <div className="text-xs text-slate-500 space-y-1">
                    <div className="flex justify-between">
                      <span>Tasks</span>
                      <span className="font-semibold text-slate-700">
                        {worker.taskCount}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>CPU</span>
                      <span className="font-semibold text-slate-700">
                        {worker.cpuUsage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Memory</span>
                      <span className="font-semibold text-slate-700">
                        {worker.memoryUsage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {workers.length === 0 && (
              <EmptyState
                title="No workers registered"
                description="Start a worker process to begin consuming tasks."
                icon={<Cpu className="w-8 h-8 text-slate-300" />}
              />
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
        </>
      )}
    </div>
  );
};

export default DashboardPage;
