import React, { useState, useEffect, useCallback } from "react";
import {
  Settings,
  Save,
  RefreshCw,
  Shield,
  Database,
  Bell,
  Server,
  Sliders,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  Trash2,
  Download,
  HardDrive,
  Clock,
  Activity,
  Info,
  ChevronRight,
} from "lucide-react";
import { settingsAPI } from "../services/settingsAPI";
import type {
  GeneralSettings,
  WorkerSettings,
  AlertSettings,
  DatabaseSettings,
  SecuritySettings,
  ConfigValidationReport,
  MaintenanceResult,
  BackupInfo,
  TableBloat,
  LongRunningQuery,
} from "../types/settings";

/* ═══════════════════════════════ Types ════ */

type SettingsTab = "general" | "workers" | "alerts" | "database" | "security";

interface TabDef {
  id: SettingsTab;
  label: string;
  icon: React.ReactNode;
}

/* ═══════════════════════════════ Helpers ══ */

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / k ** i).toFixed(1)} ${sizes[i]}`;
};

const formatDate = (iso: string): string =>
  new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });

/* ═══════════════════════════════ Component */

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  /* ── Settings state ── */
  const [general, setGeneral] = useState<GeneralSettings | null>(null);
  const [workers, setWorkers] = useState<WorkerSettings | null>(null);
  const [alerts, setAlerts] = useState<AlertSettings | null>(null);
  const [database, setDatabase] = useState<DatabaseSettings | null>(null);
  const [security, setSecurity] = useState<SecuritySettings | null>(null);

  /* ── Admin state ── */
  const [validation, setValidation] = useState<ConfigValidationReport | null>(
    null,
  );
  const [maintenanceLog, setMaintenanceLog] = useState<MaintenanceResult[]>([]);
  const [maintenanceLoading, setMaintenanceLoading] = useState<string | null>(
    null,
  );
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [backupLoading, setBackupLoading] = useState(false);
  const [tableBloat, setTableBloat] = useState<TableBloat[]>([]);
  const [longQueries, setLongQueries] = useState<LongRunningQuery[]>([]);

  /* ── Tabs ── */
  const TABS: TabDef[] = [
    {
      id: "general",
      label: "General",
      icon: <Sliders className="w-4 h-4" />,
    },
    {
      id: "workers",
      label: "Workers",
      icon: <Server className="w-4 h-4" />,
    },
    { id: "alerts", label: "Alerts", icon: <Bell className="w-4 h-4" /> },
    {
      id: "database",
      label: "Database",
      icon: <Database className="w-4 h-4" />,
    },
    {
      id: "security",
      label: "Security",
      icon: <Shield className="w-4 h-4" />,
    },
  ];

  /* ── Data fetching ── */

  const fetchTabData = useCallback(async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case "general":
          setGeneral(await settingsAPI.getGeneralSettings());
          break;
        case "workers":
          setWorkers(await settingsAPI.getWorkerSettings());
          break;
        case "alerts":
          setAlerts(await settingsAPI.getAlertSettings());
          break;
        case "database": {
          const [db, bloat, queries] = await Promise.all([
            settingsAPI.getDatabaseSettings(),
            settingsAPI.getTableBloat(),
            settingsAPI.getLongRunningQueries(),
          ]);
          setDatabase(db);
          setTableBloat(bloat);
          setLongQueries(queries);
          break;
        }
        case "security":
          setSecurity(await settingsAPI.getSecuritySettings());
          break;
      }
    } catch (err) {
      console.error("Settings fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchTabData();
  }, [fetchTabData]);

  /* ── Save handler ── */

  const handleSave = async () => {
    setSaving(true);
    setSaveMessage(null);
    try {
      // In a real implementation this would POST to the backend.
      // For now we simulate a successful save.
      await new Promise((r) => setTimeout(r, 600));
      setSaveMessage({ type: "success", text: "Settings saved successfully" });
    } catch {
      setSaveMessage({ type: "error", text: "Failed to save settings" });
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMessage(null), 4000);
    }
  };

  /* ── Validate config ── */

  const handleValidate = async () => {
    try {
      const report = await settingsAPI.validateConfig();
      setValidation(report);
    } catch {
      setValidation(null);
    }
  };

  /* ── Maintenance actions ── */

  const runMaintenance = async (
    action: string,
    fn: () => Promise<MaintenanceResult>,
  ) => {
    setMaintenanceLoading(action);
    try {
      const result = await fn();
      setMaintenanceLog((prev) => [result, ...prev]);
    } catch (err) {
      setMaintenanceLog((prev) => [
        {
          operation: action,
          success: false,
          message: String(err),
          duration_ms: 0,
        },
        ...prev,
      ]);
    } finally {
      setMaintenanceLoading(null);
    }
  };

  /* ── Backup actions ── */

  const loadBackups = async () => {
    const res = await settingsAPI.listBackups();
    setBackups(res.backups);
  };

  const handleCreateBackup = async () => {
    setBackupLoading(true);
    try {
      const res = await settingsAPI.createBackup();
      setBackups((prev) => [res.backup, ...prev]);
    } catch (err) {
      console.error("Backup failed:", err);
    } finally {
      setBackupLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "database") loadBackups();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  /* ═══════════════════════════ Rendering ══ */

  /* ── Field helpers ── */

  const InputField: React.FC<{
    label: string;
    value: string | number;
    onChange: (v: string) => void;
    type?: string;
    hint?: string;
    disabled?: boolean;
  }> = ({ label, value, onChange, type = "text", hint, disabled }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                   focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                   disabled:bg-gray-100 disabled:cursor-not-allowed"
      />
      {hint && <p className="mt-1 text-xs text-gray-500">{hint}</p>}
    </div>
  );

  const ToggleField: React.FC<{
    label: string;
    checked: boolean;
    onChange: (v: boolean) => void;
    hint?: string;
  }> = ({ label, checked, onChange, hint }) => (
    <div className="flex items-center justify-between py-2">
      <div>
        <span className="text-sm font-medium text-gray-700">{label}</span>
        {hint && <p className="text-xs text-gray-500 mt-0.5">{hint}</p>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          checked ? "bg-blue-600" : "bg-gray-300"
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            checked ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </button>
    </div>
  );

  const SelectField: React.FC<{
    label: string;
    value: string;
    options: string[];
    onChange: (v: string) => void;
  }> = ({ label, value, options, onChange }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                   focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  );

  /* ── Tab content ── */

  const renderGeneral = () => {
    if (!general) return null;
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <InputField
            label="Application Name"
            value={general.appName}
            onChange={(v) => setGeneral({ ...general, appName: v })}
          />
          <SelectField
            label="Environment"
            value={general.environment}
            options={["development", "staging", "production"]}
            onChange={(v) => setGeneral({ ...general, environment: v })}
          />
          <SelectField
            label="Log Level"
            value={general.logLevel}
            options={["DEBUG", "INFO", "WARNING", "ERROR"]}
            onChange={(v) =>
              setGeneral({
                ...general,
                logLevel: v as GeneralSettings["logLevel"],
              })
            }
          />
          <InputField
            label="Timezone"
            value={general.timezone}
            onChange={(v) => setGeneral({ ...general, timezone: v })}
          />
          <InputField
            label="Max Concurrent Tasks"
            value={general.maxConcurrentTasks}
            type="number"
            onChange={(v) =>
              setGeneral({
                ...general,
                maxConcurrentTasks: parseInt(v) || 0,
              })
            }
            hint="Maximum tasks running at the same time"
          />
          <InputField
            label="Default Task Timeout (s)"
            value={general.defaultTaskTimeout}
            type="number"
            onChange={(v) =>
              setGeneral({
                ...general,
                defaultTaskTimeout: parseInt(v) || 0,
              })
            }
            hint="Seconds before a task is considered timed-out"
          />
          <InputField
            label="Retry Backoff Base"
            value={general.retryBackoffBase}
            type="number"
            onChange={(v) =>
              setGeneral({
                ...general,
                retryBackoffBase: parseFloat(v) || 1,
              })
            }
            hint="Exponential backoff base for retries"
          />
        </div>
        <ToggleField
          label="Debug Mode"
          checked={general.debugMode}
          onChange={(v) => setGeneral({ ...general, debugMode: v })}
          hint="Enable detailed error traces & debug logging"
        />
      </div>
    );
  };

  const renderWorkers = () => {
    if (!workers) return null;
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <InputField
            label="Max Workers"
            value={workers.maxWorkers}
            type="number"
            onChange={(v) =>
              setWorkers({ ...workers, maxWorkers: parseInt(v) || 1 })
            }
          />
          <InputField
            label="Min Workers"
            value={workers.minWorkers}
            type="number"
            onChange={(v) =>
              setWorkers({ ...workers, minWorkers: parseInt(v) || 1 })
            }
          />
          <InputField
            label="Heartbeat Interval (s)"
            value={workers.heartbeatInterval}
            type="number"
            onChange={(v) =>
              setWorkers({
                ...workers,
                heartbeatInterval: parseInt(v) || 10,
              })
            }
            hint="How often workers send heartbeats"
          />
          <InputField
            label="Heartbeat Timeout (s)"
            value={workers.heartbeatTimeout}
            type="number"
            onChange={(v) =>
              setWorkers({
                ...workers,
                heartbeatTimeout: parseInt(v) || 30,
              })
            }
            hint="Mark worker unhealthy after this many seconds"
          />
          <InputField
            label="Drain Timeout (s)"
            value={workers.drainTimeout}
            type="number"
            onChange={(v) =>
              setWorkers({ ...workers, drainTimeout: parseInt(v) || 30 })
            }
            hint="Time allowed for graceful shutdown"
          />
          <InputField
            label="Task Capacity"
            value={workers.taskCapacity}
            type="number"
            onChange={(v) =>
              setWorkers({ ...workers, taskCapacity: parseInt(v) || 1 })
            }
            hint="Max tasks per worker at once"
          />
          <InputField
            label="Max Memory %"
            value={workers.maxMemoryPercent}
            type="number"
            onChange={(v) =>
              setWorkers({
                ...workers,
                maxMemoryPercent: parseInt(v) || 80,
              })
            }
            hint="Restart worker above this memory threshold"
          />
        </div>
        <ToggleField
          label="Auto-Scale Workers"
          checked={workers.autoScale}
          onChange={(v) => setWorkers({ ...workers, autoScale: v })}
          hint="Automatically scale workers based on queue depth"
        />
      </div>
    );
  };

  const renderAlerts = () => {
    if (!alerts) return null;
    return (
      <div className="space-y-6">
        <ToggleField
          label="Alerts Enabled"
          checked={alerts.enabled}
          onChange={(v) => setAlerts({ ...alerts, enabled: v })}
          hint="Master toggle for the alerting pipeline"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <InputField
            label="Evaluation Interval (s)"
            value={alerts.evaluationInterval}
            type="number"
            onChange={(v) =>
              setAlerts({
                ...alerts,
                evaluationInterval: parseInt(v) || 30,
              })
            }
            hint="Seconds between alert evaluations"
          />
          <InputField
            label="Retention Days"
            value={alerts.retentionDays}
            type="number"
            onChange={(v) =>
              setAlerts({ ...alerts, retentionDays: parseInt(v) || 7 })
            }
            hint="Keep resolved alerts for this many days"
          />
        </div>

        {/* Alert Rules table */}
        <div>
          <h3 className="text-sm font-semibold text-gray-800 mb-3">
            Alert Rules
          </h3>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">
                    Severity
                  </th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">
                    Threshold
                  </th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">
                    Cooldown
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-gray-600">
                    Enabled
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {alerts.rules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {rule.name}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{rule.type}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                          rule.severity === "critical"
                            ? "bg-red-100 text-red-800"
                            : rule.severity === "error"
                              ? "bg-orange-100 text-orange-800"
                              : rule.severity === "warning"
                                ? "bg-yellow-100 text-yellow-800"
                                : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {rule.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {rule.threshold}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {rule.cooldownMinutes}m
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        type="button"
                        role="switch"
                        aria-checked={rule.enabled}
                        onClick={() => {
                          setAlerts({
                            ...alerts,
                            rules: alerts.rules.map((r) =>
                              r.id === rule.id
                                ? { ...r, enabled: !r.enabled }
                                : r,
                            ),
                          });
                        }}
                        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                          rule.enabled ? "bg-blue-600" : "bg-gray-300"
                        }`}
                      >
                        <span
                          className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                            rule.enabled ? "translate-x-4" : "translate-x-0.5"
                          }`}
                        />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const renderDatabase = () => {
    if (!database) return null;
    return (
      <div className="space-y-8">
        {/* Connection settings */}
        <div>
          <h3 className="text-sm font-semibold text-gray-800 mb-3">
            Connection Pool
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <InputField
              label="Pool Size"
              value={database.connectionPool}
              type="number"
              onChange={(v) =>
                setDatabase({
                  ...database,
                  connectionPool: parseInt(v) || 5,
                })
              }
            />
            <InputField
              label="Max Overflow"
              value={database.maxOverflow}
              type="number"
              onChange={(v) =>
                setDatabase({ ...database, maxOverflow: parseInt(v) || 0 })
              }
            />
            <InputField
              label="Pool Timeout (s)"
              value={database.poolTimeout}
              type="number"
              onChange={(v) =>
                setDatabase({ ...database, poolTimeout: parseInt(v) || 10 })
              }
            />
          </div>
        </div>

        {/* Maintenance settings */}
        <div>
          <h3 className="text-sm font-semibold text-gray-800 mb-3">
            Maintenance
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InputField
              label="Backup Retention (days)"
              value={database.backupRetention}
              type="number"
              onChange={(v) =>
                setDatabase({
                  ...database,
                  backupRetention: parseInt(v) || 7,
                })
              }
            />
            <InputField
              label="Maintenance Window"
              value={database.maintenanceWindow}
              onChange={(v) =>
                setDatabase({ ...database, maintenanceWindow: v })
              }
              hint="e.g., 02:00-04:00 UTC"
            />
          </div>
          <div className="mt-4">
            <ToggleField
              label="Auto Vacuum"
              checked={database.autoVacuum}
              onChange={(v) => setDatabase({ ...database, autoVacuum: v })}
              hint="Run regular VACUUM ANALYZE automatically"
            />
          </div>
        </div>

        {/* Maintenance Operations */}
        <div>
          <h3 className="text-sm font-semibold text-gray-800 mb-3">
            Maintenance Operations
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {[
              {
                label: "Vacuum",
                key: "vacuum",
                fn: () => settingsAPI.runVacuum(),
              },
              {
                label: "Reindex",
                key: "reindex",
                fn: () => settingsAPI.runReindex(),
              },
              {
                label: "Analyze",
                key: "analyze",
                fn: () => settingsAPI.runAnalyze(),
              },
              {
                label: "Full Maintenance",
                key: "full",
                fn: async () => {
                  const res = await settingsAPI.runFullMaintenance();
                  return {
                    operation: "full-maintenance",
                    success: res.all_successful,
                    message: res.all_successful
                      ? `All ${res.operations.length} operations succeeded`
                      : "Some operations failed",
                    duration_ms: res.operations.reduce(
                      (s, o) => s + o.duration_ms,
                      0,
                    ),
                  };
                },
              },
              {
                label: "Cleanup Tasks",
                key: "cleanup-tasks",
                fn: () => settingsAPI.cleanupTasks(90),
              },
              {
                label: "Cleanup Sessions",
                key: "cleanup-sessions",
                fn: () => settingsAPI.cleanupSessions(24),
              },
            ].map((op) => (
              <button
                key={op.key}
                onClick={() => runMaintenance(op.key, op.fn)}
                disabled={maintenanceLoading !== null}
                className="flex items-center justify-center gap-2 px-4 py-2.5
                           bg-white border border-gray-300 rounded-lg text-sm font-medium
                           text-gray-700 hover:bg-gray-50 disabled:opacity-50
                           disabled:cursor-not-allowed transition-colors"
              >
                {maintenanceLoading === op.key ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {op.label}
              </button>
            ))}
          </div>

          {/* Maintenance log */}
          {maintenanceLog.length > 0 && (
            <div className="mt-4 space-y-2 max-h-48 overflow-y-auto">
              {maintenanceLog.map((entry, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-2 p-3 rounded-lg text-sm ${
                    entry.success
                      ? "bg-green-50 text-green-800"
                      : "bg-red-50 text-red-800"
                  }`}
                >
                  {entry.success ? (
                    <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <span className="font-medium">{entry.operation}</span>
                    <span className="ml-2 text-gray-600">{entry.message}</span>
                  </div>
                  <span className="text-xs text-gray-500 tabular-nums whitespace-nowrap">
                    {entry.duration_ms}ms
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Table Bloat */}
        {tableBloat.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-800 mb-3">
              Table Bloat
            </h3>
            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">
                      Table
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">
                      Live Tuples
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">
                      Dead Tuples
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">
                      Bloat %
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {tableBloat.map((t) => (
                    <tr key={t.table_name} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">
                        {t.table_name}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        {t.live_tuples.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        {t.dead_tuples.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                            t.bloat_ratio > 20
                              ? "bg-red-100 text-red-800"
                              : t.bloat_ratio > 5
                                ? "bg-yellow-100 text-yellow-800"
                                : "bg-green-100 text-green-800"
                          }`}
                        >
                          {t.bloat_ratio.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Long-Running Queries */}
        {longQueries.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-800 mb-3">
              Long-Running Queries
            </h3>
            <div className="space-y-2">
              {longQueries.map((q) => (
                <div
                  key={q.pid}
                  className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-yellow-800">
                      PID {q.pid}
                    </span>
                    <span className="text-xs text-yellow-700 tabular-nums">
                      {q.duration_seconds.toFixed(0)}s &middot; {q.state}
                    </span>
                  </div>
                  <code className="text-xs text-gray-700 break-all">
                    {q.query}
                  </code>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Backups */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-800">Backups</h3>
            <button
              onClick={handleCreateBackup}
              disabled={backupLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium
                         bg-blue-600 text-white rounded-lg hover:bg-blue-700
                         disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {backupLoading ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5" />
              )}
              Create Backup
            </button>
          </div>
          {backups.length === 0 ? (
            <p className="text-sm text-gray-500 py-4 text-center">
              No backups found.
            </p>
          ) : (
            <div className="space-y-2">
              {backups.map((b) => (
                <div
                  key={b.filename}
                  className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <HardDrive className="w-4 h-4 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {b.filename}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatDate(b.created_at)} &middot;{" "}
                        {formatBytes(b.size_bytes)}
                      </p>
                    </div>
                  </div>
                  <Download className="w-4 h-4 text-gray-400 cursor-pointer hover:text-blue-600" />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderSecurity = () => {
    if (!security) return null;
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <InputField
            label="JWT Expire (minutes)"
            value={security.jwtExpireMinutes}
            type="number"
            onChange={(v) =>
              setSecurity({
                ...security,
                jwtExpireMinutes: parseInt(v) || 15,
              })
            }
            hint="Access token expiration"
          />
          <InputField
            label="Refresh Token (days)"
            value={security.refreshTokenDays}
            type="number"
            onChange={(v) =>
              setSecurity({
                ...security,
                refreshTokenDays: parseInt(v) || 1,
              })
            }
          />
          <InputField
            label="Rate Limit (per minute)"
            value={security.rateLimitPerMinute}
            type="number"
            onChange={(v) =>
              setSecurity({
                ...security,
                rateLimitPerMinute: parseInt(v) || 30,
              })
            }
          />
          <InputField
            label="Password Min Length"
            value={security.passwordMinLength}
            type="number"
            onChange={(v) =>
              setSecurity({
                ...security,
                passwordMinLength: parseInt(v) || 6,
              })
            }
          />
          <InputField
            label="Session Timeout (s)"
            value={security.sessionTimeout}
            type="number"
            onChange={(v) =>
              setSecurity({
                ...security,
                sessionTimeout: parseInt(v) || 600,
              })
            }
            hint="Idle session timeout in seconds"
          />
        </div>

        <ToggleField
          label="Require HTTPS"
          checked={security.requireHttps}
          onChange={(v) => setSecurity({ ...security, requireHttps: v })}
          hint="Enforce HTTPS for all API connections"
        />

        {/* CORS Origins */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            CORS Origins
          </label>
          <div className="space-y-2">
            {security.corsOrigins.map((origin, i) => (
              <div key={i} className="flex items-center gap-2">
                <input
                  type="text"
                  value={origin}
                  onChange={(e) => {
                    const updated = [...security.corsOrigins];
                    updated[i] = e.target.value;
                    setSecurity({ ...security, corsOrigins: updated });
                  }}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm
                             focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  type="button"
                  onClick={() =>
                    setSecurity({
                      ...security,
                      corsOrigins: security.corsOrigins.filter(
                        (_, idx) => idx !== i,
                      ),
                    })
                  }
                  className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={() =>
                setSecurity({
                  ...security,
                  corsOrigins: [...security.corsOrigins, ""],
                })
              }
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              + Add Origin
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderTabContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <RefreshCw className="w-6 h-6 animate-spin mr-3" />
          Loading settings...
        </div>
      );
    }
    switch (activeTab) {
      case "general":
        return renderGeneral();
      case "workers":
        return renderWorkers();
      case "alerts":
        return renderAlerts();
      case "database":
        return renderDatabase();
      case "security":
        return renderSecurity();
    }
  };

  /* ═══════════════════════════ Main render ═ */

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Settings className="w-7 h-7 text-gray-700" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
            <p className="text-sm text-gray-500">
              Manage application configuration and admin operations
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleValidate}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium
                       border border-gray-300 rounded-lg text-gray-700
                       hover:bg-gray-50 transition-colors"
          >
            <Activity className="w-4 h-4" />
            Validate Config
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2 text-sm font-medium
                       bg-blue-600 text-white rounded-lg hover:bg-blue-700
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Save Changes
          </button>
        </div>
      </div>

      {/* Save message */}
      {saveMessage && (
        <div
          className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${
            saveMessage.type === "success"
              ? "bg-green-50 text-green-800 border border-green-200"
              : "bg-red-50 text-red-800 border border-red-200"
          }`}
        >
          {saveMessage.type === "success" ? (
            <CheckCircle2 className="w-4 h-4" />
          ) : (
            <XCircle className="w-4 h-4" />
          )}
          {saveMessage.text}
        </div>
      )}

      {/* Validation report */}
      {validation && (
        <div
          className={`p-4 rounded-lg border ${
            validation.valid
              ? "bg-green-50 border-green-200"
              : "bg-red-50 border-red-200"
          }`}
        >
          <div className="flex items-center gap-2 mb-2">
            {validation.valid ? (
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600" />
            )}
            <span className="font-semibold text-sm">
              Configuration {validation.valid ? "Valid" : "Invalid"}
            </span>
            <span className="text-xs text-gray-600 ml-2">
              {validation.passed}/{validation.total_checks} checks passed
              {validation.warnings > 0 &&
                ` · ${validation.warnings} warning(s)`}
            </span>
          </div>
          {validation.errors.length > 0 && (
            <ul className="space-y-1 mt-2">
              {validation.errors.map((e, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  {e.severity === "error" ? (
                    <XCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                  )}
                  <span>
                    <code className="text-xs font-mono bg-white/50 px-1 rounded">
                      {e.field}
                    </code>{" "}
                    {e.message}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Tab bar + content */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {/* Tab strip */}
        <div className="flex border-b border-gray-200">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-2 px-6 py-3.5 text-sm font-medium
                          border-b-2 transition-colors ${
                            activeTab === t.id
                              ? "border-blue-600 text-blue-600"
                              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                          }`}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="p-6">{renderTabContent()}</div>
      </div>

      {/* Quick-info footer */}
      <div className="flex items-center gap-2 text-xs text-gray-400">
        <Info className="w-3.5 h-3.5" />
        Changes are applied after clicking Save. Some settings require a service
        restart to take effect.
      </div>
    </div>
  );
};

export default SettingsPage;
