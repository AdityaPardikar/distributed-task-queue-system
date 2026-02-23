/**
 * Settings & Admin type definitions.
 * Maps to backend operations.py, config_validator, and maintenance endpoints.
 */

/* ── General settings ── */

export interface GeneralSettings {
  appName: string;
  environment: string;
  debugMode: boolean;
  logLevel: "DEBUG" | "INFO" | "WARNING" | "ERROR";
  timezone: string;
  maxConcurrentTasks: number;
  defaultTaskTimeout: number;
  retryBackoffBase: number;
}

/* ── Worker settings ── */

export interface WorkerSettings {
  maxWorkers: number;
  heartbeatInterval: number;
  heartbeatTimeout: number;
  drainTimeout: number;
  taskCapacity: number;
  autoScale: boolean;
  minWorkers: number;
  maxMemoryPercent: number;
}

/* ── Alert settings ── */

export interface AlertSettings {
  enabled: boolean;
  evaluationInterval: number;
  retentionDays: number;
  rules: AlertRule[];
}

export interface AlertRule {
  id: string;
  name: string;
  type: string;
  severity: "info" | "warning" | "error" | "critical";
  threshold: number;
  enabled: boolean;
  cooldownMinutes: number;
}

/* ── Database settings ── */

export interface DatabaseSettings {
  connectionPool: number;
  maxOverflow: number;
  poolTimeout: number;
  autoVacuum: boolean;
  backupRetention: number;
  maintenanceWindow: string;
}

/* ── Security settings ── */

export interface SecuritySettings {
  jwtExpireMinutes: number;
  refreshTokenDays: number;
  rateLimitPerMinute: number;
  corsOrigins: string[];
  requireHttps: boolean;
  passwordMinLength: number;
  sessionTimeout: number;
}

/* ── Config validation ── */

export interface ConfigValidationReport {
  valid: boolean;
  total_checks: number;
  passed: number;
  failed: number;
  warnings: number;
  errors: ConfigValidationError[];
}

export interface ConfigValidationError {
  field: string;
  message: string;
  severity: "warning" | "error";
}

export interface CurrentConfig {
  config: Record<string, string | number | boolean>;
}

/* ── Maintenance ── */

export interface MaintenanceResult {
  operation: string;
  success: boolean;
  message: string;
  duration_ms: number;
  details?: Record<string, unknown>;
}

export interface FullMaintenanceResult {
  operations: MaintenanceResult[];
  all_successful: boolean;
}

/* ── Backup ── */

export interface BackupInfo {
  filename: string;
  filepath: string;
  size_bytes: number;
  checksum?: string;
  created_at: string;
  type?: string;
}

export interface BackupListResponse {
  count: number;
  backups: BackupInfo[];
}

/* ── System health ── */

export interface TableBloat {
  table_name: string;
  dead_tuples: number;
  live_tuples: number;
  bloat_ratio: number;
}

export interface LongRunningQuery {
  pid: number;
  query: string;
  duration_seconds: number;
  state: string;
}

/* ── User management ── */

export interface UserInfo {
  id: string;
  username: string;
  email: string;
  role: "admin" | "operator" | "viewer";
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}
