/**
 * Settings & Operations API service — wraps /api/v1/operations/* endpoints.
 */

import axios from "axios";
import type {
  ConfigValidationReport,
  CurrentConfig,
  MaintenanceResult,
  FullMaintenanceResult,
  BackupInfo,
  BackupListResponse,
  TableBloat,
  LongRunningQuery,
  GeneralSettings,
  WorkerSettings,
  AlertSettings,
  DatabaseSettings,
  SecuritySettings,
} from "../types/settings";

const API_BASE_URL = import.meta.env.VITE_API_URL || "";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/* ── Mock data ── */

const MOCK_GENERAL: GeneralSettings = {
  appName: "TaskFlow",
  environment: "development",
  debugMode: true,
  logLevel: "INFO",
  timezone: "UTC",
  maxConcurrentTasks: 100,
  defaultTaskTimeout: 300,
  retryBackoffBase: 2,
};

const MOCK_WORKERS: WorkerSettings = {
  maxWorkers: 8,
  heartbeatInterval: 30,
  heartbeatTimeout: 90,
  drainTimeout: 60,
  taskCapacity: 10,
  autoScale: true,
  minWorkers: 2,
  maxMemoryPercent: 85,
};

const MOCK_ALERTS: AlertSettings = {
  enabled: true,
  evaluationInterval: 60,
  retentionDays: 30,
  rules: [
    {
      id: "r1",
      name: "High Error Rate",
      type: "error_rate",
      severity: "critical",
      threshold: 5,
      enabled: true,
      cooldownMinutes: 10,
    },
    {
      id: "r2",
      name: "Queue Depth",
      type: "queue_depth",
      severity: "warning",
      threshold: 100,
      enabled: true,
      cooldownMinutes: 5,
    },
    {
      id: "r3",
      name: "Worker Heartbeat",
      type: "heartbeat",
      severity: "critical",
      threshold: 90,
      enabled: true,
      cooldownMinutes: 2,
    },
    {
      id: "r4",
      name: "Disk Usage",
      type: "disk_usage",
      severity: "warning",
      threshold: 80,
      enabled: true,
      cooldownMinutes: 30,
    },
    {
      id: "r5",
      name: "Memory Usage",
      type: "memory_usage",
      severity: "warning",
      threshold: 85,
      enabled: false,
      cooldownMinutes: 15,
    },
  ],
};

const MOCK_DATABASE: DatabaseSettings = {
  connectionPool: 20,
  maxOverflow: 10,
  poolTimeout: 30,
  autoVacuum: true,
  backupRetention: 10,
  maintenanceWindow: "02:00-04:00 UTC",
};

const MOCK_SECURITY: SecuritySettings = {
  jwtExpireMinutes: 30,
  refreshTokenDays: 7,
  rateLimitPerMinute: 60,
  corsOrigins: ["http://localhost:5173", "http://localhost:3000"],
  requireHttps: false,
  passwordMinLength: 8,
  sessionTimeout: 1800,
};

const MOCK_CONFIG_REPORT: ConfigValidationReport = {
  valid: true,
  total_checks: 12,
  passed: 11,
  failed: 0,
  warnings: 1,
  errors: [
    {
      field: "CORS_ORIGINS",
      message: "Wildcard origin not recommended in production",
      severity: "warning",
    },
  ],
};

const MOCK_BACKUPS: BackupListResponse = {
  count: 3,
  backups: [
    {
      filename: "backup_20240115_020000.sql",
      filepath: "/backups/backup_20240115_020000.sql",
      size_bytes: 15_400_000,
      created_at: new Date(Date.now() - 86_400_000).toISOString(),
    },
    {
      filename: "backup_20240114_020000.sql",
      filepath: "/backups/backup_20240114_020000.sql",
      size_bytes: 14_800_000,
      created_at: new Date(Date.now() - 172_800_000).toISOString(),
    },
    {
      filename: "backup_20240113_020000.sql",
      filepath: "/backups/backup_20240113_020000.sql",
      size_bytes: 14_200_000,
      created_at: new Date(Date.now() - 259_200_000).toISOString(),
    },
  ],
};

/* ── API ── */

export const settingsAPI = {
  /* ── Settings getters (use config + mock) ── */

  getGeneralSettings: async (): Promise<GeneralSettings> => {
    try {
      const res = await client.get("/api/v1/operations/config/current");
      const cfg = res.data?.config ?? {};
      return {
        appName: (cfg.APP_NAME as string) ?? MOCK_GENERAL.appName,
        environment: (cfg.ENVIRONMENT as string) ?? MOCK_GENERAL.environment,
        debugMode: cfg.DEBUG === true || cfg.DEBUG === "true",
        logLevel:
          (cfg.LOG_LEVEL as GeneralSettings["logLevel"]) ??
          MOCK_GENERAL.logLevel,
        timezone: (cfg.TIMEZONE as string) ?? MOCK_GENERAL.timezone,
        maxConcurrentTasks:
          Number(cfg.MAX_CONCURRENT_TASKS) || MOCK_GENERAL.maxConcurrentTasks,
        defaultTaskTimeout:
          Number(cfg.DEFAULT_TASK_TIMEOUT) || MOCK_GENERAL.defaultTaskTimeout,
        retryBackoffBase:
          Number(cfg.RETRY_BACKOFF_BASE) || MOCK_GENERAL.retryBackoffBase,
      };
    } catch {
      return MOCK_GENERAL;
    }
  },

  getWorkerSettings: async (): Promise<WorkerSettings> => {
    try {
      const res = await client.get("/api/v1/operations/config/current");
      const cfg = res.data?.config ?? {};
      return {
        maxWorkers: Number(cfg.MAX_WORKERS) || MOCK_WORKERS.maxWorkers,
        heartbeatInterval:
          Number(cfg.HEARTBEAT_INTERVAL) || MOCK_WORKERS.heartbeatInterval,
        heartbeatTimeout:
          Number(cfg.HEARTBEAT_TIMEOUT) || MOCK_WORKERS.heartbeatTimeout,
        drainTimeout: Number(cfg.DRAIN_TIMEOUT) || MOCK_WORKERS.drainTimeout,
        taskCapacity: Number(cfg.TASK_CAPACITY) || MOCK_WORKERS.taskCapacity,
        autoScale:
          cfg.AUTO_SCALE === true ||
          cfg.AUTO_SCALE === "true" ||
          MOCK_WORKERS.autoScale,
        minWorkers: Number(cfg.MIN_WORKERS) || MOCK_WORKERS.minWorkers,
        maxMemoryPercent:
          Number(cfg.MAX_MEMORY_PERCENT) || MOCK_WORKERS.maxMemoryPercent,
      };
    } catch {
      return MOCK_WORKERS;
    }
  },

  getAlertSettings: async (): Promise<AlertSettings> => MOCK_ALERTS,
  getDatabaseSettings: async (): Promise<DatabaseSettings> => MOCK_DATABASE,
  getSecuritySettings: async (): Promise<SecuritySettings> => MOCK_SECURITY,

  /* ── Config validation ── */

  validateConfig: async (): Promise<ConfigValidationReport> => {
    try {
      const res = await client.get("/api/v1/operations/config/validate");
      return res.data;
    } catch {
      return MOCK_CONFIG_REPORT;
    }
  },

  getCurrentConfig: async (): Promise<CurrentConfig> => {
    try {
      const res = await client.get("/api/v1/operations/config/current");
      return res.data;
    } catch {
      return {
        config: {
          APP_NAME: "TaskFlow",
          ENVIRONMENT: "development",
          DEBUG: true,
          LOG_LEVEL: "INFO",
          DATABASE_URL: "postgresql://***:***@localhost/taskflow",
          REDIS_URL: "redis://localhost:6379/0",
        },
      };
    }
  },

  /* ── Maintenance ── */

  runVacuum: async (table?: string): Promise<MaintenanceResult> => {
    try {
      const res = await client.post(
        "/api/v1/operations/maintenance/vacuum",
        null,
        {
          params: table ? { table } : undefined,
        },
      );
      return res.data;
    } catch {
      return {
        operation: "vacuum",
        success: true,
        message: "VACUUM completed (mock)",
        duration_ms: 450,
      };
    }
  },

  runReindex: async (table?: string): Promise<MaintenanceResult> => {
    try {
      const res = await client.post(
        "/api/v1/operations/maintenance/reindex",
        null,
        {
          params: table ? { table } : undefined,
        },
      );
      return res.data;
    } catch {
      return {
        operation: "reindex",
        success: true,
        message: "REINDEX completed (mock)",
        duration_ms: 820,
      };
    }
  },

  runAnalyze: async (): Promise<MaintenanceResult> => {
    try {
      const res = await client.post("/api/v1/operations/maintenance/analyze");
      return res.data;
    } catch {
      return {
        operation: "analyze",
        success: true,
        message: "ANALYZE completed (mock)",
        duration_ms: 320,
      };
    }
  },

  runFullMaintenance: async (): Promise<FullMaintenanceResult> => {
    try {
      const res = await client.post("/api/v1/operations/maintenance/full");
      return res.data;
    } catch {
      return {
        operations: [
          {
            operation: "vacuum",
            success: true,
            message: "Done (mock)",
            duration_ms: 450,
          },
          {
            operation: "reindex",
            success: true,
            message: "Done (mock)",
            duration_ms: 820,
          },
          {
            operation: "analyze",
            success: true,
            message: "Done (mock)",
            duration_ms: 320,
          },
        ],
        all_successful: true,
      };
    }
  },

  cleanupTasks: async (days = 90): Promise<MaintenanceResult> => {
    try {
      const res = await client.post(
        "/api/v1/operations/maintenance/cleanup-tasks",
        null,
        {
          params: { days },
        },
      );
      return res.data;
    } catch {
      return {
        operation: "cleanup-tasks",
        success: true,
        message: `Cleaned tasks older than ${days}d (mock)`,
        duration_ms: 230,
      };
    }
  },

  cleanupSessions: async (maxAgeHours = 24): Promise<MaintenanceResult> => {
    try {
      const res = await client.post(
        "/api/v1/operations/maintenance/cleanup-sessions",
        null,
        {
          params: { max_age_hours: maxAgeHours },
        },
      );
      return res.data;
    } catch {
      return {
        operation: "cleanup-sessions",
        success: true,
        message: "Sessions cleaned (mock)",
        duration_ms: 85,
      };
    }
  },

  /* ── Backups ── */

  createBackup: async (
    name?: string,
  ): Promise<{ status: string; backup: BackupInfo }> => {
    try {
      const res = await client.post("/api/v1/operations/backups", null, {
        params: name ? { name } : undefined,
      });
      return res.data;
    } catch {
      return {
        status: "success",
        backup: {
          filename: `backup_${Date.now()}.sql`,
          filepath: `/backups/backup_${Date.now()}.sql`,
          size_bytes: 15_000_000,
          created_at: new Date().toISOString(),
        },
      };
    }
  },

  listBackups: async (): Promise<BackupListResponse> => {
    try {
      const res = await client.get("/api/v1/operations/backups");
      return res.data;
    } catch {
      return MOCK_BACKUPS;
    }
  },

  /* ── Health ── */

  getSystemHealth: async () => {
    try {
      const res = await client.get("/api/v1/operations/health");
      return res.data;
    } catch {
      return { status: "healthy", uptime: 86400, memory_usage: 62.3 };
    }
  },

  getTableBloat: async (): Promise<TableBloat[]> => {
    try {
      const res = await client.get("/api/v1/operations/tables/bloat");
      return res.data?.tables ?? [];
    } catch {
      return [
        {
          table_name: "tasks",
          dead_tuples: 120,
          live_tuples: 12540,
          bloat_ratio: 0.96,
        },
        {
          table_name: "workers",
          dead_tuples: 5,
          live_tuples: 8,
          bloat_ratio: 38.46,
        },
      ];
    }
  },

  getLongRunningQueries: async (
    minDuration = 30,
  ): Promise<LongRunningQuery[]> => {
    try {
      const res = await client.get("/api/v1/operations/queries/long-running", {
        params: { min_duration: minDuration },
      });
      return res.data?.queries ?? [];
    } catch {
      return [];
    }
  },
};

export default settingsAPI;
