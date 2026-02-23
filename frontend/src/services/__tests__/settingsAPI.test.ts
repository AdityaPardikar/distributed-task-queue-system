import { settingsAPI } from "../settingsAPI";

// Mock axios at module level — calls fail so settingsAPI falls back to mock data
jest.mock("axios", () => {
  const mockClient = {
    get: jest.fn().mockRejectedValue(new Error("mock")),
    post: jest.fn().mockRejectedValue(new Error("mock")),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  };
  return {
    __esModule: true,
    default: { create: jest.fn(() => mockClient) },
    create: jest.fn(() => mockClient),
  };
});

describe("settingsAPI", () => {
  describe("getGeneralSettings", () => {
    it("should return GeneralSettings with correct shape", async () => {
      const settings = await settingsAPI.getGeneralSettings();
      expect(settings).toHaveProperty("appName");
      expect(settings).toHaveProperty("environment");
      expect(settings).toHaveProperty("debugMode");
      expect(settings).toHaveProperty("logLevel");
      expect(settings).toHaveProperty("timezone");
      expect(settings).toHaveProperty("maxConcurrentTasks");
      expect(settings).toHaveProperty("defaultTaskTimeout");
      expect(settings).toHaveProperty("retryBackoffBase");
      expect(typeof settings.debugMode).toBe("boolean");
      expect(typeof settings.maxConcurrentTasks).toBe("number");
    });
  });

  describe("getWorkerSettings", () => {
    it("should return WorkerSettings with correct shape", async () => {
      const settings = await settingsAPI.getWorkerSettings();
      expect(settings).toHaveProperty("maxWorkers");
      expect(settings).toHaveProperty("heartbeatInterval");
      expect(settings).toHaveProperty("heartbeatTimeout");
      expect(settings).toHaveProperty("drainTimeout");
      expect(settings).toHaveProperty("taskCapacity");
      expect(settings).toHaveProperty("autoScale");
      expect(settings).toHaveProperty("minWorkers");
      expect(settings).toHaveProperty("maxMemoryPercent");
      expect(typeof settings.autoScale).toBe("boolean");
    });
  });

  describe("getAlertSettings", () => {
    it("should return AlertSettings with rules array", async () => {
      const settings = await settingsAPI.getAlertSettings();
      expect(settings).toHaveProperty("enabled");
      expect(settings).toHaveProperty("evaluationInterval");
      expect(settings).toHaveProperty("retentionDays");
      expect(Array.isArray(settings.rules)).toBe(true);
      expect(settings.rules.length).toBeGreaterThan(0);
      expect(settings.rules[0]).toHaveProperty("id");
      expect(settings.rules[0]).toHaveProperty("name");
      expect(settings.rules[0]).toHaveProperty("severity");
      expect(settings.rules[0]).toHaveProperty("threshold");
    });
  });

  describe("getDatabaseSettings", () => {
    it("should return DatabaseSettings", async () => {
      const settings = await settingsAPI.getDatabaseSettings();
      expect(settings).toHaveProperty("connectionPool");
      expect(settings).toHaveProperty("maxOverflow");
      expect(settings).toHaveProperty("poolTimeout");
      expect(settings).toHaveProperty("autoVacuum");
      expect(settings).toHaveProperty("backupRetention");
      expect(settings).toHaveProperty("maintenanceWindow");
    });
  });

  describe("getSecuritySettings", () => {
    it("should return SecuritySettings", async () => {
      const settings = await settingsAPI.getSecuritySettings();
      expect(settings).toHaveProperty("jwtExpireMinutes");
      expect(settings).toHaveProperty("refreshTokenDays");
      expect(settings).toHaveProperty("rateLimitPerMinute");
      expect(settings).toHaveProperty("corsOrigins");
      expect(Array.isArray(settings.corsOrigins)).toBe(true);
      expect(settings).toHaveProperty("requireHttps");
      expect(settings).toHaveProperty("passwordMinLength");
    });
  });

  describe("validateConfig", () => {
    it("should return a validation report", async () => {
      const report = await settingsAPI.validateConfig();
      expect(report).toHaveProperty("valid");
      expect(report).toHaveProperty("total_checks");
      expect(report).toHaveProperty("passed");
      expect(report).toHaveProperty("failed");
      expect(report).toHaveProperty("warnings");
      expect(report).toHaveProperty("errors");
      expect(typeof report.valid).toBe("boolean");
      expect(Array.isArray(report.errors)).toBe(true);
    });
  });

  describe("maintenance operations", () => {
    it("runVacuum should return a MaintenanceResult", async () => {
      const result = await settingsAPI.runVacuum();
      expect(result).toHaveProperty("operation");
      expect(result).toHaveProperty("success");
      expect(result).toHaveProperty("message");
      expect(result).toHaveProperty("duration_ms");
      expect(result.operation).toBe("vacuum");
    });

    it("runReindex should return a MaintenanceResult", async () => {
      const result = await settingsAPI.runReindex();
      expect(result.operation).toBe("reindex");
      expect(result.success).toBe(true);
    });

    it("runAnalyze should return a MaintenanceResult", async () => {
      const result = await settingsAPI.runAnalyze();
      expect(result.operation).toBe("analyze");
      expect(result.success).toBe(true);
    });

    it("runFullMaintenance should return all operations", async () => {
      const result = await settingsAPI.runFullMaintenance();
      expect(result).toHaveProperty("operations");
      expect(result).toHaveProperty("all_successful");
      expect(Array.isArray(result.operations)).toBe(true);
      expect(result.operations.length).toBeGreaterThan(0);
    });

    it("cleanupTasks should accept days parameter", async () => {
      const result = await settingsAPI.cleanupTasks(30);
      expect(result.operation).toBe("cleanup-tasks");
      expect(result.success).toBe(true);
    });

    it("cleanupSessions should accept maxAgeHours parameter", async () => {
      const result = await settingsAPI.cleanupSessions(12);
      expect(result.operation).toBe("cleanup-sessions");
      expect(result.success).toBe(true);
    });
  });

  describe("backup operations", () => {
    it("listBackups should return backups array", async () => {
      const result = await settingsAPI.listBackups();
      expect(result).toHaveProperty("count");
      expect(result).toHaveProperty("backups");
      expect(Array.isArray(result.backups)).toBe(true);
    });

    it("createBackup should return status and backup info", async () => {
      const result = await settingsAPI.createBackup();
      expect(result).toHaveProperty("status");
      expect(result).toHaveProperty("backup");
      expect(result.backup).toHaveProperty("filename");
      expect(result.backup).toHaveProperty("size_bytes");
    });
  });

  describe("health operations", () => {
    it("getSystemHealth should return health data", async () => {
      const health = await settingsAPI.getSystemHealth();
      expect(health).toHaveProperty("status");
    });

    it("getTableBloat should return array of table bloat", async () => {
      const bloat = await settingsAPI.getTableBloat();
      expect(Array.isArray(bloat)).toBe(true);
    });

    it("getLongRunningQueries should return array", async () => {
      const queries = await settingsAPI.getLongRunningQueries();
      expect(Array.isArray(queries)).toBe(true);
    });
  });
});
