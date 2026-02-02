import { render, screen } from "@testing-library/react";
import DashboardPage from "../DashboardPage";

// Mock the useMetrics hook
jest.mock("../../hooks/useMetrics", () => ({
  useMetrics: () => ({
    metrics: {
      totalTasks: 1250,
      activeWorkers: 5,
      queueSize: 45,
      successRate: 96.4,
      pendingTasks: 45,
      runningTasks: 12,
      completedTasks: 1150,
      failedTasks: 43,
    },
    recentTasks: [
      {
        id: "task-1",
        name: "Process Data",
        status: "completed",
        priority: "high",
        duration: "2.5s",
        createdAt: new Date().toISOString(),
        completedAt: new Date().toISOString(),
        assignedWorker: "worker-1",
      },
    ],
    workers: [
      {
        id: "worker-1",
        name: "Worker 1",
        status: "active",
        tasksProcessed: 100,
        cpuUsage: 45,
        memoryUsage: 60,
      },
    ],
    queueDepthData: [
      { date: "2024-01-01", queueDepth: 100 },
      { date: "2024-01-02", queueDepth: 120 },
    ],
    completionRateData: [
      { date: "2024-01-01", rate: 85 },
      { date: "2024-01-02", rate: 88 },
    ],
    isLoading: false,
    error: null,
    refresh: jest.fn(),
  }),
}));

describe("DashboardPage", () => {
  it("renders dashboard title", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Monitor your distributed task queue/i),
    ).toBeInTheDocument();
  });

  it("renders metrics cards", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Total Tasks/i)).toBeInTheDocument();
    expect(screen.getByText(/Active Workers/i)).toBeInTheDocument();
    expect(screen.getByText(/Queue Size/i)).toBeInTheDocument();
    expect(screen.getByText(/Success Rate/i)).toBeInTheDocument();
  });

  it("renders charts section", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Queue Depth/i)).toBeInTheDocument();
  });

  it("renders recent tasks section", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Recent Tasks/i)).toBeInTheDocument();
  });

  it("renders worker health section", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Worker Health/i)).toBeInTheDocument();
  });
});
