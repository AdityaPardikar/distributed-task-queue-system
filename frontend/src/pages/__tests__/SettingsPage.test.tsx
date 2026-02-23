import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SettingsPage from "../SettingsPage";

// Mock settingsAPI
jest.mock("../../services/settingsAPI", () => ({
  settingsAPI: {
    getGeneralSettings: jest.fn().mockResolvedValue({
      appName: "TaskFlow",
      environment: "development",
      debugMode: true,
      logLevel: "INFO",
      timezone: "UTC",
      maxConcurrentTasks: 100,
      defaultTaskTimeout: 300,
      retryBackoffBase: 2,
    }),
    getWorkerSettings: jest.fn().mockResolvedValue({
      maxWorkers: 8,
      heartbeatInterval: 30,
      heartbeatTimeout: 90,
      drainTimeout: 60,
      taskCapacity: 10,
      autoScale: true,
      minWorkers: 2,
      maxMemoryPercent: 85,
    }),
    getAlertSettings: jest.fn().mockResolvedValue({
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
      ],
    }),
    getDatabaseSettings: jest.fn().mockResolvedValue({
      connectionPool: 20,
      maxOverflow: 10,
      poolTimeout: 30,
      autoVacuum: true,
      backupRetention: 10,
      maintenanceWindow: "02:00-04:00 UTC",
    }),
    getSecuritySettings: jest.fn().mockResolvedValue({
      jwtExpireMinutes: 30,
      refreshTokenDays: 7,
      rateLimitPerMinute: 60,
      corsOrigins: ["http://localhost:5173"],
      requireHttps: false,
      passwordMinLength: 8,
      sessionTimeout: 1800,
    }),
    validateConfig: jest.fn().mockResolvedValue({
      valid: true,
      total_checks: 12,
      passed: 11,
      failed: 0,
      warnings: 1,
      errors: [],
    }),
    getTableBloat: jest.fn().mockResolvedValue([]),
    getLongRunningQueries: jest.fn().mockResolvedValue([]),
    listBackups: jest.fn().mockResolvedValue({ count: 0, backups: [] }),
    runVacuum: jest.fn().mockResolvedValue({
      operation: "vacuum",
      success: true,
      message: "Done",
      duration_ms: 100,
    }),
    runReindex: jest.fn().mockResolvedValue({
      operation: "reindex",
      success: true,
      message: "Done",
      duration_ms: 200,
    }),
    runAnalyze: jest.fn().mockResolvedValue({
      operation: "analyze",
      success: true,
      message: "Done",
      duration_ms: 50,
    }),
    runFullMaintenance: jest.fn().mockResolvedValue({
      operations: [],
      all_successful: true,
    }),
    cleanupTasks: jest.fn().mockResolvedValue({
      operation: "cleanup-tasks",
      success: true,
      message: "Done",
      duration_ms: 30,
    }),
    cleanupSessions: jest.fn().mockResolvedValue({
      operation: "cleanup-sessions",
      success: true,
      message: "Done",
      duration_ms: 20,
    }),
    createBackup: jest.fn().mockResolvedValue({
      status: "success",
      backup: {
        filename: "backup_test.sql",
        filepath: "/backups/backup_test.sql",
        size_bytes: 1000,
        created_at: new Date().toISOString(),
      },
    }),
  },
}));

describe("SettingsPage", () => {
  it("renders the page title", async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText("Settings")).toBeInTheDocument();
    });
  });

  it("renders all setting tabs", async () => {
    render(<SettingsPage />);
    expect(screen.getByText("General")).toBeInTheDocument();
    expect(screen.getByText("Workers")).toBeInTheDocument();
    expect(screen.getByText("Alerts")).toBeInTheDocument();
    expect(screen.getByText("Database")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
  });

  it("renders General tab content by default", async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText("Application Name")).toBeInTheDocument();
    });
  });

  it("shows save and validate buttons", () => {
    render(<SettingsPage />);
    expect(screen.getByText("Save Changes")).toBeInTheDocument();
    expect(screen.getByText("Validate Config")).toBeInTheDocument();
  });

  it("switches to Workers tab on click", async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);

    const workersTab = screen.getByText("Workers");
    await user.click(workersTab);

    await waitFor(() => {
      expect(screen.getByText("Max Workers")).toBeInTheDocument();
    });
  });

  it("switches to Alerts tab and shows rules", async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);

    await user.click(screen.getByText("Alerts"));

    await waitFor(() => {
      expect(screen.getByText("Alert Rules")).toBeInTheDocument();
      expect(screen.getByText("High Error Rate")).toBeInTheDocument();
    });
  });

  it("switches to Database tab and shows maintenance section", async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);

    await user.click(screen.getByText("Database"));

    await waitFor(() => {
      expect(screen.getByText("Connection Pool")).toBeInTheDocument();
      expect(screen.getByText("Maintenance Operations")).toBeInTheDocument();
    });
  });

  it("switches to Security tab", async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);

    await user.click(screen.getByText("Security"));

    await waitFor(() => {
      expect(screen.getByText("JWT Expire (minutes)")).toBeInTheDocument();
      expect(screen.getByText("CORS Origins")).toBeInTheDocument();
    });
  });

  it("shows save success message when saving", async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);

    await user.click(screen.getByText("Save Changes"));

    await waitFor(() => {
      expect(
        screen.getByText("Settings saved successfully"),
      ).toBeInTheDocument();
    });
  });
});
