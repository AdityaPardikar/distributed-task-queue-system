import { render, screen, waitFor } from "@testing-library/react";
import AlertsPage from "../AlertsPage";

// Mock alertsAPI
jest.mock("../../services/alertsAPI", () => {
  const mockAlerts = [
    {
      alert_id: "alert-1",
      severity: "critical",
      alert_type: "High Error Rate",
      description: "Error rate exceeded 5%",
      source: "api-gateway",
      created_at: new Date(Date.now() - 60_000).toISOString(),
      acknowledged: false,
      acknowledged_at: null,
      metadata: {},
    },
    {
      alert_id: "alert-2",
      severity: "warning",
      alert_type: "High Memory Usage",
      description: "Memory usage above 85%",
      source: "worker-01",
      created_at: new Date(Date.now() - 300_000).toISOString(),
      acknowledged: false,
      acknowledged_at: null,
      metadata: {},
    },
  ];
  return {
    __esModule: true,
    default: {
      getActiveAlerts: jest.fn().mockResolvedValue(mockAlerts),
      getStats: jest.fn().mockResolvedValue({
        total_alerts: 150,
        active_alerts: 12,
        acknowledged_alerts: 38,
        by_severity: { critical: 3, error: 5, warning: 8, info: 4 },
        avg_resolution_time_minutes: 14.5,
      }),
      getHistory: jest.fn().mockResolvedValue([]),
      acknowledge: jest.fn().mockResolvedValue({ success: true }),
    },
  };
});

describe("AlertsPage", () => {
  it("renders the page heading", async () => {
    render(<AlertsPage />);
    await waitFor(() => {
      expect(screen.getByText("Alerts")).toBeInTheDocument();
    });
  });

  it("shows alert items after loading", async () => {
    render(<AlertsPage />);
    await waitFor(() => {
      expect(screen.getByText("High Error Rate")).toBeInTheDocument();
      expect(screen.getByText("High Memory Usage")).toBeInTheDocument();
    });
  });

  it("renders severity badges", async () => {
    render(<AlertsPage />);
    await waitFor(() => {
      expect(screen.getByText("Critical")).toBeInTheDocument();
      expect(screen.getByText("Warning")).toBeInTheDocument();
    });
  });

  it("renders tab navigation", async () => {
    render(<AlertsPage />);
    expect(screen.getByText("Active Alerts")).toBeInTheDocument();
    expect(screen.getByText("History")).toBeInTheDocument();
    expect(screen.getByText("Analytics")).toBeInTheDocument();
  });

  it("shows refresh button", async () => {
    render(<AlertsPage />);
    expect(screen.getByText("Refresh")).toBeInTheDocument();
  });
});
