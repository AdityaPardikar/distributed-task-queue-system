/**
 * AlertsPage — Alert management with filtering, acknowledgment, and statistics.
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  Info,
  ShieldAlert,
  CheckCircle2,
  RefreshCw,
  Filter,
  BarChart3,
  Clock,
  History,
  Loader2,
  Check,
} from "lucide-react";
import alertsAPI from "../services/alertsAPI";
import type {
  Alert,
  AlertSeverity,
  AlertStats,
  AlertHistoryItem,
} from "../types/workflow";

/* ── Severity config ── */

const SEVERITY_CONFIG: Record<
  AlertSeverity,
  { label: string; color: string; bg: string; icon: React.ReactNode }
> = {
  critical: {
    label: "Critical",
    color: "text-red-700",
    bg: "bg-red-50 border-red-200",
    icon: <ShieldAlert className="w-4 h-4 text-red-600" />,
  },
  error: {
    label: "Error",
    color: "text-orange-700",
    bg: "bg-orange-50 border-orange-200",
    icon: <AlertCircle className="w-4 h-4 text-orange-600" />,
  },
  warning: {
    label: "Warning",
    color: "text-amber-700",
    bg: "bg-amber-50 border-amber-200",
    icon: <AlertTriangle className="w-4 h-4 text-amber-600" />,
  },
  info: {
    label: "Info",
    color: "text-primary-700",
    bg: "bg-primary-50 border-primary-200",
    icon: <Info className="w-4 h-4 text-primary-600" />,
  },
};

const SEVERITY_ORDER: AlertSeverity[] = [
  "critical",
  "error",
  "warning",
  "info",
];

/* ── Helpers ── */

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

/* ── Component ── */

const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [history, setHistory] = useState<AlertHistoryItem[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | "all">(
    "all",
  );
  const [showAcknowledged, setShowAcknowledged] = useState(false);
  const [acknowledging, setAcknowledging] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"active" | "history" | "stats">(
    "active",
  );

  /* fetchers */
  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const [alertData, statsData] = await Promise.all([
        alertsAPI.getActiveAlerts(showAcknowledged),
        alertsAPI.getStats(),
      ]);
      setAlerts(alertData);
      setStats(statsData);
    } catch {
      /* API services provide mock fallback */
    } finally {
      setLoading(false);
    }
  }, [showAcknowledged]);

  const fetchHistory = useCallback(async () => {
    try {
      const data = await alertsAPI.getHistory(24, 100);
      setHistory(data);
    } catch {
      /* handled */
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    fetchHistory();
  }, [fetchAlerts, fetchHistory]);

  /* auto-refresh every 15s */
  useEffect(() => {
    const id = setInterval(fetchAlerts, 15_000);
    return () => clearInterval(id);
  }, [fetchAlerts]);

  /* acknowledge handler */
  const handleAcknowledge = useCallback(async (alertId: string) => {
    setAcknowledging(alertId);
    try {
      await alertsAPI.acknowledge(alertId);
      setAlerts((prev) =>
        prev.map((a) =>
          a.alert_id === alertId
            ? {
                ...a,
                acknowledged: true,
                acknowledged_at: new Date().toISOString(),
              }
            : a,
        ),
      );
    } catch {
      /* silent */
    } finally {
      setAcknowledging(null);
    }
  }, []);

  /* filter */
  const filtered =
    severityFilter === "all"
      ? alerts
      : alerts.filter((a) => a.severity === severityFilter);

  /* sort by severity then time */
  const sorted = [...filtered].sort((a, b) => {
    const sa = SEVERITY_ORDER.indexOf(a.severity as AlertSeverity);
    const sb = SEVERITY_ORDER.indexOf(b.severity as AlertSeverity);
    if (sa !== sb) return sa - sb;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  const activeCount = alerts.filter((a) => !a.acknowledged).length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Bell className="w-7 h-7 text-amber-600" />
            Alerts
            {activeCount > 0 && (
              <span className="ml-2 px-2.5 py-0.5 bg-red-50 text-red-700 text-sm font-bold rounded-full border border-red-200">
                {activeCount}
              </span>
            )}
          </h1>
          <p className="mt-0.5 text-sm text-slate-500">
            Monitor and manage system alerts
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-500 cursor-pointer">
            <input
              type="checkbox"
              checked={showAcknowledged}
              onChange={(e) => setShowAcknowledged(e.target.checked)}
              className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
            />
            Show acknowledged
          </label>
          <button
            onClick={fetchAlerts}
            className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 hover:bg-slate-50 transition-all"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-4 flex items-center gap-4">
            <div className="rounded-xl p-2.5 bg-red-50 text-red-700">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Active Alerts</p>
              <p className="text-2xl font-bold text-slate-900">
                {stats.active_alerts}
              </p>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-4 flex items-center gap-4">
            <div className="rounded-xl p-2.5 bg-emerald-50 text-emerald-700">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Acknowledged</p>
              <p className="text-2xl font-bold text-slate-900">
                {stats.acknowledged_alerts}
              </p>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-4 flex items-center gap-4">
            <div className="rounded-xl p-2.5 bg-amber-50 text-amber-700">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Total (All Time)</p>
              <p className="text-2xl font-bold text-slate-900">
                {stats.total_alerts}
              </p>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-4">
            <p className="text-sm text-slate-500 mb-2">By Severity</p>
            <div className="flex items-center gap-3">
              {SEVERITY_ORDER.map((sev) => (
                <span
                  key={sev}
                  className={`flex items-center gap-1 text-xs font-medium ${SEVERITY_CONFIG[sev].color}`}
                >
                  {SEVERITY_CONFIG[sev].icon}
                  {stats.by_severity[sev] ?? 0}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-6">
          {(
            [
              {
                key: "active",
                label: "Active Alerts",
                icon: <Bell className="w-4 h-4" />,
              },
              {
                key: "history",
                label: "History",
                icon: <History className="w-4 h-4" />,
              },
              {
                key: "stats",
                label: "Analytics",
                icon: <BarChart3 className="w-4 h-4" />,
              },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              onClick={() => {
                setActiveTab(tab.key);
                if (tab.key === "history") fetchHistory();
              }}
              className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-primary-600 text-primary-600"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              <span className="flex items-center gap-1.5">
                {tab.icon} {tab.label}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {/* ── Active Alerts Tab ── */}
      {activeTab === "active" && (
        <>
          {/* Severity filter */}
          <div className="flex items-center gap-3">
            <Filter className="w-4 h-4 text-slate-400" />
            {(["all", ...SEVERITY_ORDER] as const).map((s) => (
              <button
                key={s}
                onClick={() => setSeverityFilter(s)}
                className={`px-3 py-1.5 text-xs rounded-full font-semibold transition-colors ${
                  severityFilter === s
                    ? "bg-primary-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {s === "all" ? "All" : SEVERITY_CONFIG[s].label}
              </button>
            ))}
          </div>

          {loading && alerts.length === 0 ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
            </div>
          ) : sorted.length === 0 ? (
            <div className="text-center py-16 text-slate-400">
              <CheckCircle2 className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p className="font-semibold">No alerts</p>
              <p className="text-sm mt-1">All clear — the system is healthy.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {sorted.map((alert) => {
                const cfg =
                  SEVERITY_CONFIG[alert.severity as AlertSeverity] ??
                  SEVERITY_CONFIG.info;
                return (
                  <div
                    key={alert.alert_id}
                    className={`rounded-xl border p-4 transition-colors ${cfg.bg} ${
                      alert.acknowledged ? "opacity-60" : ""
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 min-w-0">
                        <div className="mt-0.5">{cfg.icon}</div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span
                              className={`text-xs font-semibold uppercase ${cfg.color}`}
                            >
                              {cfg.label}
                            </span>
                            <span className="text-xs text-slate-400 font-mono">
                              {alert.alert_type}
                            </span>
                            {alert.acknowledged && (
                              <span className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                                <Check className="w-3 h-3" /> Acknowledged
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-slate-700 mt-1">
                            {alert.description}
                          </p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {timeAgo(alert.created_at)}
                            </span>
                            {alert.acknowledged_at && (
                              <span>
                                Ack'd {timeAgo(alert.acknowledged_at)}
                              </span>
                            )}
                          </div>

                          {/* Metadata */}
                          {Object.keys(alert.metadata).length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-2">
                              {Object.entries(alert.metadata).map(([k, v]) => (
                                <span
                                  key={k}
                                  className="px-2 py-0.5 text-xs font-mono bg-white/60 rounded-lg border border-slate-200 text-slate-600"
                                >
                                  {k}: {String(v)}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Acknowledge button */}
                      {!alert.acknowledged && (
                        <button
                          onClick={() => handleAcknowledge(alert.alert_id)}
                          disabled={acknowledging === alert.alert_id}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 rounded-xl border border-emerald-200 hover:bg-emerald-100 disabled:opacity-50 transition-colors whitespace-nowrap"
                        >
                          {acknowledging === alert.alert_id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Check className="w-3.5 h-3.5" />
                          )}
                          Acknowledge
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* ── History Tab ── */}
      {activeTab === "history" && (
        <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-100">
              <tr>
                <th className="px-4 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Severity
                </th>
                <th className="px-4 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-4 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-4 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Time
                </th>
                <th className="px-4 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {history.map((h) => {
                const cfg =
                  SEVERITY_CONFIG[h.severity as AlertSeverity] ??
                  SEVERITY_CONFIG.info;
                return (
                  <tr key={h.alert_id} className="hover:bg-slate-50/50">
                    <td className="px-4 py-3">
                      <span
                        className={`flex items-center gap-1.5 text-xs font-medium ${cfg.color}`}
                      >
                        {cfg.icon} {cfg.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-600">
                      {h.alert_type}
                    </td>
                    <td className="px-4 py-3 text-slate-700 max-w-md truncate">
                      {h.description}
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap">
                      {timeAgo(h.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      {h.acknowledged ? (
                        <span className="text-green-600 text-xs flex items-center gap-1">
                          <Check className="w-3 h-3" /> Ack'd
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs">Active</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Stats Tab ── */}
      {activeTab === "stats" && stats && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* By severity */}
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5">
            <h3 className="font-semibold text-slate-900 mb-4">
              Alerts by Severity
            </h3>
            <div className="space-y-3">
              {SEVERITY_ORDER.map((sev) => {
                const count = stats.by_severity[sev] ?? 0;
                const pct =
                  stats.total_alerts > 0
                    ? (count / stats.total_alerts) * 100
                    : 0;
                const cfg = SEVERITY_CONFIG[sev];
                return (
                  <div key={sev}>
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className={`flex items-center gap-1.5 text-sm font-medium ${cfg.color}`}
                      >
                        {cfg.icon} {cfg.label}
                      </span>
                      <span className="text-sm text-slate-600">{count}</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          sev === "critical"
                            ? "bg-red-500"
                            : sev === "error"
                              ? "bg-orange-500"
                              : sev === "warning"
                                ? "bg-amber-400"
                                : "bg-primary-400"
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* By type */}
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5">
            <h3 className="font-semibold text-slate-900 mb-4">
              Active Alerts by Type
            </h3>
            {Object.keys(stats.active_by_type).length === 0 ? (
              <p className="text-sm text-slate-400">No active alerts</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(stats.active_by_type)
                  .sort((a, b) => b[1] - a[1])
                  .map(([type, count]) => (
                    <div
                      key={type}
                      className="flex items-center justify-between px-3 py-2 bg-slate-50 rounded-xl"
                    >
                      <span className="text-sm font-mono text-slate-700">
                        {type}
                      </span>
                      <span className="text-sm font-semibold text-slate-900">
                        {count}
                      </span>
                    </div>
                  ))}
              </div>
            )}
          </div>

          {/* Summary */}
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5 lg:col-span-2">
            <h3 className="font-semibold text-slate-900 mb-4">Summary</h3>
            <div className="grid grid-cols-3 gap-6 text-center">
              <div>
                <p className="text-3xl font-bold text-red-600">
                  {stats.active_alerts}
                </p>
                <p className="text-sm text-slate-500 mt-1">Active</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-green-600">
                  {stats.acknowledged_alerts}
                </p>
                <p className="text-sm text-slate-500 mt-1">Acknowledged</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-slate-700">
                  {stats.total_alerts}
                </p>
                <p className="text-sm text-slate-500 mt-1">Total</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertsPage;
