import React, { useState, useEffect, useCallback } from "react";
import {
  RefreshCw,
  Activity,
  Server,
  AlertTriangle,
  BarChart3,
  Clock,
  CheckCircle2,
  XCircle,
  Bell,
  TrendingUp,
  Cpu,
  HardDrive,
  Wifi,
  WifiOff,
} from "lucide-react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { monitoringAPI } from "../services/monitoringAPI";
import type {
  SystemMetrics,
  PerformanceDataPoint,
  WorkerHealthInfo,
  SystemAlert,
  TrendDataPoint,
  MonitoringTab,
  TimeRange,
} from "../types/monitoring";

/* ═══════════════════════════════ Component ═══ */

const MonitoringPage: React.FC = () => {
  const [tab, setTab] = useState<MonitoringTab>("overview");
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [performance, setPerformance] = useState<PerformanceDataPoint[]>([]);
  const [workerHealth, setWorkerHealth] = useState<WorkerHealthInfo[]>([]);
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [trends, setTrends] = useState<TrendDataPoint[]>([]);

  /* ── fetch ────────────────────────────── */
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [m, p, w, a, t] = await Promise.all([
        monitoringAPI.getMetrics(),
        monitoringAPI.getPerformance(timeRange),
        monitoringAPI.getWorkerHealth(),
        monitoringAPI.getAlerts(),
        monitoringAPI.getTrends(timeRange),
      ]);
      setMetrics(m);
      setPerformance(p);
      setWorkerHealth(w);
      setAlerts(a);
      setTrends(t);
    } catch (err) {
      console.error("Monitoring fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(fetchData, 15_000);
    return () => clearInterval(id);
  }, [autoRefresh, fetchData]);

  /* ── tab list ─────────────────────────── */
  const tabs: { key: MonitoringTab; label: string; icon: React.ReactNode }[] = [
    {
      key: "overview",
      label: "Overview",
      icon: <BarChart3 className="w-4 h-4" />,
    },
    { key: "workers", label: "Workers", icon: <Server className="w-4 h-4" /> },
    { key: "alerts", label: "Alerts", icon: <Bell className="w-4 h-4" /> },
    {
      key: "performance",
      label: "Performance",
      icon: <TrendingUp className="w-4 h-4" />,
    },
  ];

  const unresolvedAlerts = alerts.filter((a) => !a.resolved).length;

  /* ═══════════════════════════════ Render ═══ */
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            System Monitoring
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Real-time system health, metrics &amp; alerts
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Time Range */}
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            {(["1h", "6h", "24h", "7d"] as TimeRange[]).map((r) => (
              <button
                key={r}
                onClick={() => setTimeRange(r)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  timeRange === r
                    ? "bg-white text-blue-700 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={() => setAutoRefresh(!autoRefresh)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Auto
          </label>
          <button
            onClick={fetchData}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6 -mb-px">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                tab === t.key
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {t.icon}
              {t.label}
              {t.key === "alerts" && unresolvedAlerts > 0 && (
                <span className="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                  {unresolvedAlerts}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {tab === "overview" && (
        <OverviewTab metrics={metrics} trends={trends} workers={workerHealth} />
      )}
      {tab === "workers" && <WorkersTab workers={workerHealth} />}
      {tab === "alerts" && <AlertsTab alerts={alerts} />}
      {tab === "performance" && <PerformanceTab data={performance} />}
    </div>
  );
};

/* ═══════════════ OVERVIEW TAB ════════════════ */

const OverviewTab: React.FC<{
  metrics: SystemMetrics | null;
  trends: TrendDataPoint[];
  workers: WorkerHealthInfo[];
}> = ({ metrics, trends, workers }) => {
  if (!metrics) return null;

  const healthScore =
    metrics.active_workers > 0 &&
    metrics.error_rate < 5 &&
    metrics.queue_size < 200
      ? "healthy"
      : metrics.error_rate < 10
        ? "degraded"
        : "unhealthy";

  const healthColor = {
    healthy: "text-green-600 bg-green-50 border-green-200",
    degraded: "text-yellow-600 bg-yellow-50 border-yellow-200",
    unhealthy: "text-red-600 bg-red-50 border-red-200",
  }[healthScore];

  return (
    <div className="space-y-6">
      {/* Health Banner */}
      <div
        className={`rounded-lg border p-4 flex items-center gap-4 ${healthColor}`}
      >
        {healthScore === "healthy" ? (
          <CheckCircle2 className="w-8 h-8" />
        ) : healthScore === "degraded" ? (
          <AlertTriangle className="w-8 h-8" />
        ) : (
          <XCircle className="w-8 h-8" />
        )}
        <div>
          <p className="font-semibold text-lg capitalize">
            System {healthScore}
          </p>
          <p className="text-sm opacity-80">
            {metrics.active_workers} active workers &middot;{" "}
            {metrics.tasks_per_minute} tasks/min &middot;{" "}
            {metrics.error_rate.toFixed(1)}% error rate
          </p>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Total Tasks"
          value={metrics.total_tasks.toLocaleString()}
          icon={<Activity className="w-5 h-5 text-blue-600" />}
        />
        <MetricCard
          label="Queue Depth"
          value={metrics.queue_size}
          icon={<BarChart3 className="w-5 h-5 text-indigo-600" />}
        />
        <MetricCard
          label="Success Rate"
          value={`${metrics.success_rate.toFixed(1)}%`}
          icon={<CheckCircle2 className="w-5 h-5 text-green-600" />}
        />
        <MetricCard
          label="Avg Latency"
          value={`${metrics.avg_processing_time.toFixed(1)}s`}
          icon={<Clock className="w-5 h-5 text-amber-600" />}
        />
        <MetricCard
          label="Tasks/Min"
          value={metrics.tasks_per_minute}
          icon={<TrendingUp className="w-5 h-5 text-cyan-600" />}
        />
        <MetricCard
          label="Error Rate"
          value={`${metrics.error_rate.toFixed(1)}%`}
          icon={<XCircle className="w-5 h-5 text-red-500" />}
        />
        <MetricCard
          label="Active Workers"
          value={`${metrics.active_workers} / ${metrics.total_workers}`}
          icon={<Server className="w-5 h-5 text-purple-600" />}
        />
        <MetricCard
          label="Pending Tasks"
          value={metrics.pending_tasks}
          icon={<Clock className="w-5 h-5 text-gray-500" />}
        />
      </div>

      {/* Tasks Trend Chart */}
      {trends.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Task Activity Over Time
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 11 }}
                tickFormatter={(v) =>
                  new Date(v).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                }
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                labelFormatter={(v) => new Date(v as string).toLocaleString()}
                contentStyle={{ fontSize: 12 }}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="completed"
                stroke="#22c55e"
                fill="#22c55e"
                fillOpacity={0.15}
                name="Completed"
              />
              <Area
                type="monotone"
                dataKey="running"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.15}
                name="Running"
              />
              <Area
                type="monotone"
                dataKey="pending"
                stroke="#f59e0b"
                fill="#f59e0b"
                fillOpacity={0.1}
                name="Pending"
              />
              <Area
                type="monotone"
                dataKey="failed"
                stroke="#ef4444"
                fill="#ef4444"
                fillOpacity={0.1}
                name="Failed"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Mini Worker Health */}
      {workers.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Worker Health Snapshot
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {workers.map((w) => (
              <MiniWorkerCard key={w.worker_id} worker={w} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/* ═══════════════ WORKERS TAB ════════════════ */

const WorkersTab: React.FC<{ workers: WorkerHealthInfo[] }> = ({ workers }) => {
  if (workers.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <Server className="w-10 h-10 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-500">No workers connected</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {workers.map((w) => (
        <WorkerCard key={w.worker_id} worker={w} />
      ))}
    </div>
  );
};

/* ═══════════════ ALERTS TAB ════════════════ */

const AlertsTab: React.FC<{ alerts: SystemAlert[] }> = ({ alerts }) => {
  const [filter, setFilter] = useState<"all" | "critical" | "warning" | "info">(
    "all",
  );

  const filtered =
    filter === "all" ? alerts : alerts.filter((a) => a.severity === filter);

  const SEVERITY_STYLE: Record<string, string> = {
    critical: "border-l-red-500 bg-red-50",
    warning: "border-l-yellow-500 bg-yellow-50",
    info: "border-l-blue-500 bg-blue-50",
  };

  const SEVERITY_BADGE: Record<string, string> = {
    critical: "bg-red-100 text-red-800",
    warning: "bg-yellow-100 text-yellow-800",
    info: "bg-blue-100 text-blue-800",
  };

  return (
    <div className="space-y-4">
      {/* Filter */}
      <div className="flex gap-2">
        {(["all", "critical", "warning", "info"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors capitalize ${
              filter === f
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {f}
            {f !== "all" && (
              <span className="ml-1">
                ({alerts.filter((a) => a.severity === f).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Alert List */}
      {filtered.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Bell className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No alerts</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((alert) => (
            <div
              key={alert.id}
              className={`bg-white rounded-lg shadow border-l-4 p-4 ${SEVERITY_STYLE[alert.severity] ?? ""}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`text-xs font-semibold px-2 py-0.5 rounded-full uppercase ${SEVERITY_BADGE[alert.severity] ?? ""}`}
                    >
                      {alert.severity}
                    </span>
                    <span className="text-xs text-gray-400">
                      {alert.source}
                    </span>
                    {alert.resolved && (
                      <span className="text-xs text-green-600 font-semibold">
                        Resolved
                      </span>
                    )}
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm">
                    {alert.title}
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                </div>
                <span className="text-xs text-gray-400 whitespace-nowrap ml-4">
                  {new Date(alert.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

/* ═══════════════ PERFORMANCE TAB ════════════════ */

const PerformanceTab: React.FC<{ data: PerformanceDataPoint[] }> = ({
  data,
}) => {
  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <TrendingUp className="w-10 h-10 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-500">No performance data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Throughput Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">
          Throughput (tasks/min)
        </h3>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="timestamp"
              tick={{ fontSize: 11 }}
              tickFormatter={(v) =>
                new Date(v).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              }
            />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              labelFormatter={(v) => new Date(v as string).toLocaleString()}
              contentStyle={{ fontSize: 12 }}
            />
            <Area
              type="monotone"
              dataKey="throughput"
              stroke="#6366f1"
              fill="#6366f1"
              fillOpacity={0.12}
              name="Throughput"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Latency Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">
          Response Latency (ms)
        </h3>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="timestamp"
              tick={{ fontSize: 11 }}
              tickFormatter={(v) =>
                new Date(v).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              }
            />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              labelFormatter={(v) => new Date(v as string).toLocaleString()}
              contentStyle={{ fontSize: 12 }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="latency_p50"
              stroke="#22c55e"
              strokeWidth={2}
              dot={false}
              name="p50"
            />
            <Line
              type="monotone"
              dataKey="latency_p95"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              name="p95"
            />
            <Line
              type="monotone"
              dataKey="latency_p99"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
              name="p99"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Error Rate Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">
          Error Rate (%)
        </h3>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="timestamp"
              tick={{ fontSize: 11 }}
              tickFormatter={(v) =>
                new Date(v).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              }
            />
            <YAxis tick={{ fontSize: 11 }} domain={[0, "auto"]} />
            <Tooltip
              labelFormatter={(v) => new Date(v as string).toLocaleString()}
              contentStyle={{ fontSize: 12 }}
            />
            <Area
              type="monotone"
              dataKey="error_rate"
              stroke="#ef4444"
              fill="#ef4444"
              fillOpacity={0.12}
              name="Error Rate"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

/* ════════════ shared sub-components ════════════ */

const MetricCard: React.FC<{
  label: string;
  value: string | number;
  icon: React.ReactNode;
}> = ({ label, value, icon }) => (
  <div className="bg-white rounded-lg shadow p-4 flex items-center gap-3">
    <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
    <div>
      <p className="text-xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  </div>
);

const MiniWorkerCard: React.FC<{ worker: WorkerHealthInfo }> = ({ worker }) => {
  const isOnline = worker.status !== "OFFLINE";
  return (
    <div
      className={`rounded-lg border p-3 ${isOnline ? "bg-white" : "bg-gray-50 opacity-60"}`}
    >
      <div className="flex items-center gap-2 mb-2">
        {isOnline ? (
          <Wifi className="w-3.5 h-3.5 text-green-500" />
        ) : (
          <WifiOff className="w-3.5 h-3.5 text-red-400" />
        )}
        <span className="text-xs font-semibold text-gray-800 truncate">
          {worker.hostname.split(".")[0]}
        </span>
      </div>
      <div className="space-y-1.5">
        <MiniGauge label="CPU" value={worker.cpu_usage} />
        <MiniGauge label="MEM" value={worker.memory_usage} />
        <p className="text-[10px] text-gray-400">
          Load: {worker.current_load}/{worker.capacity}
        </p>
      </div>
    </div>
  );
};

const MiniGauge: React.FC<{ label: string; value: number }> = ({
  label,
  value,
}) => (
  <div className="flex items-center gap-1.5">
    <span className="text-[10px] text-gray-500 w-6">{label}</span>
    <div className="flex-1 bg-gray-200 rounded-full h-1.5">
      <div
        className={`h-1.5 rounded-full ${
          value > 80
            ? "bg-red-500"
            : value > 60
              ? "bg-yellow-500"
              : "bg-green-500"
        }`}
        style={{ width: `${Math.min(100, value)}%` }}
      />
    </div>
    <span className="text-[10px] text-gray-500 w-7 text-right">
      {Math.round(value)}%
    </span>
  </div>
);

const WorkerCard: React.FC<{ worker: WorkerHealthInfo }> = ({ worker }) => {
  const isOnline = worker.status !== "OFFLINE";
  const utilPct =
    worker.capacity > 0
      ? Math.round((worker.current_load / worker.capacity) * 100)
      : 0;

  const uptimeStr = (() => {
    const h = Math.floor(worker.uptime_seconds / 3600);
    const d = Math.floor(h / 24);
    return d > 0 ? `${d}d ${h % 24}h` : `${h}h`;
  })();

  const statusColor: Record<string, string> = {
    ACTIVE: "bg-green-100 text-green-800",
    DRAINING: "bg-yellow-100 text-yellow-800",
    OFFLINE: "bg-red-100 text-red-800",
    PAUSED: "bg-gray-200 text-gray-700",
  };

  return (
    <div
      className={`bg-white rounded-lg shadow border p-5 ${
        !isOnline ? "opacity-60" : ""
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-gray-400" />
          <div>
            <p className="font-semibold text-gray-900 text-sm">
              {worker.hostname}
            </p>
            <p className="text-[11px] text-gray-400 font-mono">
              {worker.worker_id.slice(0, 8)}
            </p>
          </div>
        </div>
        <span
          className={`text-xs font-semibold px-2 py-0.5 rounded-full ${statusColor[worker.status] ?? ""}`}
        >
          {worker.status}
        </span>
      </div>

      {/* Gauges */}
      <div className="space-y-3 mb-4">
        <Gauge
          label="CPU Usage"
          value={worker.cpu_usage}
          icon={<Cpu className="w-4 h-4 text-gray-400" />}
        />
        <Gauge
          label="Memory"
          value={worker.memory_usage}
          icon={<HardDrive className="w-4 h-4 text-gray-400" />}
        />
        <Gauge
          label="Load"
          value={utilPct}
          icon={<Activity className="w-4 h-4 text-gray-400" />}
          suffix={`${worker.current_load}/${worker.capacity}`}
        />
      </div>

      {/* Footer */}
      <div className="flex justify-between text-[11px] text-gray-400 pt-3 border-t">
        <span>Uptime: {uptimeStr}</span>
        <span>
          HB:{" "}
          {worker.last_heartbeat
            ? new Date(worker.last_heartbeat).toLocaleTimeString()
            : "—"}
        </span>
      </div>
    </div>
  );
};

const Gauge: React.FC<{
  label: string;
  value: number;
  icon: React.ReactNode;
  suffix?: string;
}> = ({ label, value, icon, suffix }) => (
  <div>
    <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
      <span className="flex items-center gap-1.5">
        {icon} {label}
      </span>
      <span className="font-mono">{suffix ?? `${Math.round(value)}%`}</span>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className={`h-2 rounded-full transition-all ${
          value > 80
            ? "bg-red-500"
            : value > 60
              ? "bg-yellow-500"
              : "bg-green-500"
        }`}
        style={{ width: `${Math.min(100, value)}%` }}
      />
    </div>
  </div>
);

export default MonitoringPage;
