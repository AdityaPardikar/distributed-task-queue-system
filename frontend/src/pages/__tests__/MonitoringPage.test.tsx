import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MonitoringPage from "../MonitoringPage";

// Mock recharts
jest.mock("recharts", () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => <div data-testid="line" />,
  AreaChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="area-chart">{children}</div>
  ),
  Area: () => <div data-testid="area" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  Legend: () => <div data-testid="legend" />,
}));

// Mock monitoringAPI — data matches SystemMetrics / WorkerHealthInfo types
jest.mock("../../services/monitoringAPI", () => ({
  monitoringAPI: {
    getMetrics: jest.fn().mockResolvedValue({
      total_tasks: 12500,
      pending_tasks: 42,
      running_tasks: 8,
      completed_tasks: 12300,
      failed_tasks: 150,
      active_workers: 6,
      total_workers: 8,
      queue_size: 15,
      success_rate: 98.8,
      avg_processing_time: 1.2,
      tasks_per_minute: 45,
      error_rate: 1.2,
    }),
    getPerformance: jest.fn().mockResolvedValue([
      {
        timestamp: new Date().toISOString(),
        throughput: 120,
        latency_p50: 45,
        latency_p95: 120,
        latency_p99: 250,
        error_rate: 0.2,
      },
    ]),
    getWorkerHealth: jest.fn().mockResolvedValue([
      {
        worker_id: "w-001",
        hostname: "worker-01",
        status: "ACTIVE",
        capacity: 10,
        current_load: 6,
        cpu_usage: 35,
        memory_usage: 55,
        last_heartbeat: new Date().toISOString(),
        uptime_seconds: 604800,
      },
      {
        worker_id: "w-002",
        hostname: "worker-02",
        status: "DRAINING",
        capacity: 10,
        current_load: 2,
        cpu_usage: 88,
        memory_usage: 72,
        last_heartbeat: new Date().toISOString(),
        uptime_seconds: 345600,
      },
    ]),
    getAlerts: jest.fn().mockResolvedValue([
      {
        id: "sys-alert-1",
        severity: "warning",
        title: "High CPU on worker-02",
        message: "CPU usage has exceeded 80% threshold",
        source: "worker-02",
        timestamp: new Date().toISOString(),
        acknowledged: false,
        resolved: false,
      },
    ]),
    getTrends: jest.fn().mockResolvedValue([
      {
        timestamp: new Date().toISOString(),
        pending: 10,
        running: 5,
        completed: 500,
        failed: 3,
      },
    ]),
  },
}));

describe("MonitoringPage", () => {
  it("renders the page title", async () => {
    render(<MonitoringPage />);
    await waitFor(() => {
      expect(screen.getByText("System Monitoring")).toBeInTheDocument();
    });
  });

  it("renders tab navigation", async () => {
    render(<MonitoringPage />);
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("Performance")).toBeInTheDocument();
    expect(screen.getByText("Workers")).toBeInTheDocument();
    expect(screen.getByText("Alerts")).toBeInTheDocument();
  });

  it("shows system metrics after loading", async () => {
    render(<MonitoringPage />);
    await waitFor(() => {
      expect(screen.getByText("12,500")).toBeInTheDocument(); // Total Tasks
    });
  });

  it("shows time range selector", async () => {
    render(<MonitoringPage />);
    expect(screen.getByText("24h")).toBeInTheDocument();
  });

  it("switches to Workers tab", async () => {
    const user = userEvent.setup();
    render(<MonitoringPage />);

    await user.click(screen.getByText("Workers"));

    await waitFor(() => {
      expect(screen.getByText("worker-01")).toBeInTheDocument();
      expect(screen.getByText("worker-02")).toBeInTheDocument();
    });
  });
});
