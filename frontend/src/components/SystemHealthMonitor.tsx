import React, { useState, useEffect, useCallback } from "react";
import {
  Activity,
  Server,
  Database,
  HardDrive,
  Cpu,
  MemoryStick,
  Wifi,
  WifiOff,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Clock,
  Zap,
} from "lucide-react";

interface SystemStatus {
  timestamp: string;
  version: string;
  environment: string;
  system: {
    hostname: string;
    os: string;
    os_version: string;
    python_version: string;
    cpu_count: number;
  };
  resources: {
    cpu: { percent: number; count: number };
    memory: { total_gb: number; available_gb: number; percent: number };
    disk: { total_gb: number; free_gb: number; percent: number };
  };
  dependencies: {
    database: { status: string; latency_ms: number; connected: boolean };
    redis: { status: string; latency_ms: number; connected: boolean };
  };
  metrics: {
    tasks: {
      total: number;
      pending: number;
      running: number;
      completed: number;
      failed: number;
      success_rate: number;
      queue_depth: number;
    };
    workers: {
      total: number;
      active: number;
      utilization_percent: number;
    };
    campaigns: {
      total: number;
      active: number;
      completed: number;
    };
  };
  health_score: {
    score: number;
    status: string;
    issues: string[];
  };
}

const API_BASE_URL = "http://127.0.0.1:8000";

const SystemHealthMonitor: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/system/status`);
      if (!response.ok) throw new Error("Failed to fetch system status");
      const data = await response.json();
      setStatus(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    let interval: ReturnType<typeof setInterval>;
    if (autoRefresh) {
      interval = setInterval(fetchStatus, 5000);
    }
    return () => clearInterval(interval);
  }, [fetchStatus, autoRefresh]);

  const getHealthColor = (score: number) => {
    if (score >= 80) return "text-green-500";
    if (score >= 50) return "text-yellow-500";
    return "text-red-500";
  };

  const getHealthBg = (score: number) => {
    if (score >= 80) return "bg-green-500";
    if (score >= 50) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle2 className="text-green-500" size={20} />;
      case "degraded":
        return <AlertTriangle className="text-yellow-500" size={20} />;
      default:
        return <XCircle className="text-red-500" size={20} />;
    }
  };

  const getConnectionIcon = (connected: boolean) => {
    return connected ? (
      <Wifi className="text-green-500" size={16} />
    ) : (
      <WifiOff className="text-red-500" size={16} />
    );
  };

  const ProgressBar: React.FC<{ value: number; color?: string }> = ({
    value,
    color = "bg-blue-500",
  }) => (
    <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-500 ${color}`}
        style={{ width: `${Math.min(100, value)}%` }}
      />
    </div>
  );

  if (loading && !status) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
          <span className="ml-3 text-gray-600">Loading system status...</span>
        </div>
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="bg-red-50 rounded-xl p-6 border border-red-200">
        <div className="flex items-center gap-3">
          <XCircle className="text-red-500" size={24} />
          <div>
            <h3 className="font-semibold text-red-900">Connection Error</h3>
            <p className="text-red-700 text-sm">{error}</p>
            <button
              onClick={fetchStatus}
              className="mt-2 px-4 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!status) return null;

  return (
    <div className="space-y-6">
      {/* Header with Health Score */}
      <div className="bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900 rounded-2xl p-6 text-white shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div
              className={`w-20 h-20 rounded-full flex items-center justify-center ${getHealthBg(status.health_score.score)} bg-opacity-20 border-4 ${getHealthBg(status.health_score.score).replace("bg-", "border-")}`}
            >
              <span
                className={`text-3xl font-bold ${getHealthColor(status.health_score.score)}`}
              >
                {status.health_score.score}
              </span>
            </div>
            <div>
              <h2 className="text-2xl font-bold flex items-center gap-2">
                System Health
                {getStatusIcon(status.health_score.status)}
              </h2>
              <p className="text-blue-200 text-sm mt-1">
                {status.system.hostname} • {status.environment.toUpperCase()}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right text-sm">
              <p className="text-blue-200">Last Updated</p>
              <p className="font-mono">
                {lastUpdated?.toLocaleTimeString() || "-"}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  autoRefresh
                    ? "bg-green-500/20 text-green-300 hover:bg-green-500/30"
                    : "bg-gray-500/20 text-gray-300 hover:bg-gray-500/30"
                }`}
              >
                <RefreshCw
                  size={16}
                  className={autoRefresh ? "animate-spin" : ""}
                />
              </button>
              <button
                onClick={fetchStatus}
                className="px-4 py-2 bg-blue-500/20 text-blue-200 rounded-lg text-sm hover:bg-blue-500/30 transition-colors"
              >
                Refresh Now
              </button>
            </div>
          </div>
        </div>

        {/* Issues Banner */}
        {status.health_score.issues.length > 0 && (
          <div className="mt-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="text-yellow-400 mt-0.5" size={16} />
              <div className="text-sm">
                <span className="font-semibold text-yellow-300">
                  Active Issues:
                </span>
                <span className="text-yellow-100 ml-2">
                  {status.health_score.issues.join(" • ")}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Resource Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* CPU */}
        <div className="bg-white rounded-xl shadow-lg p-5 border border-gray-100 hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-100 rounded-lg">
                <Cpu className="text-blue-600" size={22} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">CPU</h3>
                <p className="text-xs text-gray-500">
                  {status.system.cpu_count} cores
                </p>
              </div>
            </div>
            <span className="text-2xl font-bold text-gray-900">
              {status.resources.cpu.percent.toFixed(1)}%
            </span>
          </div>
          <ProgressBar
            value={status.resources.cpu.percent}
            color={
              status.resources.cpu.percent > 80
                ? "bg-red-500"
                : status.resources.cpu.percent > 60
                  ? "bg-yellow-500"
                  : "bg-blue-500"
            }
          />
        </div>

        {/* Memory */}
        <div className="bg-white rounded-xl shadow-lg p-5 border border-gray-100 hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-purple-100 rounded-lg">
                <MemoryStick className="text-purple-600" size={22} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Memory</h3>
                <p className="text-xs text-gray-500">
                  {status.resources.memory.available_gb.toFixed(1)} GB free
                </p>
              </div>
            </div>
            <span className="text-2xl font-bold text-gray-900">
              {status.resources.memory.percent.toFixed(1)}%
            </span>
          </div>
          <ProgressBar
            value={status.resources.memory.percent}
            color={
              status.resources.memory.percent > 80
                ? "bg-red-500"
                : status.resources.memory.percent > 60
                  ? "bg-yellow-500"
                  : "bg-purple-500"
            }
          />
        </div>

        {/* Disk */}
        <div className="bg-white rounded-xl shadow-lg p-5 border border-gray-100 hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-green-100 rounded-lg">
                <HardDrive className="text-green-600" size={22} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Disk</h3>
                <p className="text-xs text-gray-500">
                  {status.resources.disk.free_gb.toFixed(1)} GB free
                </p>
              </div>
            </div>
            <span className="text-2xl font-bold text-gray-900">
              {status.resources.disk.percent.toFixed(1)}%
            </span>
          </div>
          <ProgressBar
            value={status.resources.disk.percent}
            color={
              status.resources.disk.percent > 80
                ? "bg-red-500"
                : status.resources.disk.percent > 60
                  ? "bg-yellow-500"
                  : "bg-green-500"
            }
          />
        </div>
      </div>

      {/* Dependencies & Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dependencies */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Server size={20} className="text-gray-500" />
            Service Dependencies
          </h3>
          <div className="space-y-4">
            {/* Database */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Database
                  className={
                    status.dependencies.database.connected
                      ? "text-green-600"
                      : "text-red-600"
                  }
                  size={24}
                />
                <div>
                  <p className="font-semibold text-gray-900">Database</p>
                  <p className="text-xs text-gray-500">PostgreSQL</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <p className="text-sm font-mono">
                    {status.dependencies.database.latency_ms?.toFixed(1) ||
                      "--"}{" "}
                    ms
                  </p>
                  <p
                    className={`text-xs ${status.dependencies.database.connected ? "text-green-600" : "text-red-600"}`}
                  >
                    {status.dependencies.database.status}
                  </p>
                </div>
                {getConnectionIcon(status.dependencies.database.connected)}
              </div>
            </div>

            {/* Redis */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Zap
                  className={
                    status.dependencies.redis.connected
                      ? "text-green-600"
                      : "text-red-600"
                  }
                  size={24}
                />
                <div>
                  <p className="font-semibold text-gray-900">Redis</p>
                  <p className="text-xs text-gray-500">Cache & Queue</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <p className="text-sm font-mono">
                    {status.dependencies.redis.latency_ms?.toFixed(1) || "--"}{" "}
                    ms
                  </p>
                  <p
                    className={`text-xs ${status.dependencies.redis.connected ? "text-green-600" : "text-red-600"}`}
                  >
                    {status.dependencies.redis.status}
                  </p>
                </div>
                {getConnectionIcon(status.dependencies.redis.connected)}
              </div>
            </div>
          </div>
        </div>

        {/* Task Metrics */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Activity size={20} className="text-gray-500" />
            Task Metrics
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-3xl font-bold text-blue-600">
                {status.metrics.tasks.total.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Total Tasks</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-3xl font-bold text-green-600">
                {status.metrics.tasks.success_rate}%
              </p>
              <p className="text-sm text-gray-600">Success Rate</p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <p className="text-3xl font-bold text-yellow-600">
                {status.metrics.tasks.queue_depth}
              </p>
              <p className="text-sm text-gray-600">Queue Depth</p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <p className="text-3xl font-bold text-purple-600">
                {status.metrics.workers.active}/{status.metrics.workers.total}
              </p>
              <p className="text-sm text-gray-600">Active Workers</p>
            </div>
          </div>
        </div>
      </div>

      {/* System Info Footer */}
      <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
        <div className="flex flex-wrap items-center justify-between gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-6">
            <span>
              <strong>OS:</strong> {status.system.os} {status.system.os_version}
            </span>
            <span>
              <strong>Python:</strong> {status.system.python_version}
            </span>
            <span>
              <strong>Version:</strong> {status.version}
            </span>
          </div>
          <div className="flex items-center gap-2 text-gray-400">
            <Clock size={14} />
            <span>Updated: {new Date(status.timestamp).toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealthMonitor;
