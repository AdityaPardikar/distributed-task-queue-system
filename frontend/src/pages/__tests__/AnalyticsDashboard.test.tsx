import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AnalyticsDashboard from "../../pages/AnalyticsDashboard";
import AnalyticsService from "../../services/AnalyticsService";

jest.mock("../../services/api", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
  },
}));

jest.mock("../../services/AnalyticsService", () => ({
  __esModule: true,
  default: {
    getAnalytics: jest.fn(),
    getTaskTrends: jest.fn(),
    getWorkerStats: jest.fn(),
    exportToCSV: jest.fn(),
    exportToJSON: jest.fn(),
    listReports: jest.fn(),
    generateReport: jest.fn(),
    deleteReport: jest.fn(),
    getReport: jest.fn(),
  },
}));

const mockAnalyticsData = {
  totalTasks: 1000,
  completedTasks: 850,
  failedTasks: 150,
  averageCompletionTime: 45.5,
  workerStats: [
    {
      workerId: "worker-1",
      tasksCompleted: 500,
      averageCompletionTime: 40,
      successRate: 0.95,
      lastActive: new Date().toISOString(),
    },
  ],
  taskTrends: [
    {
      timestamp: new Date().toISOString(),
      completedCount: 100,
      failedCount: 20,
      pendingCount: 10,
    },
  ],
  errorRates: [],
  queueDepthHistory: [],
};

const mockTrends = [
  {
    timestamp: new Date().toISOString(),
    completedCount: 100,
    failedCount: 20,
    pendingCount: 10,
  },
];

const mockWorkers = [
  {
    workerId: "worker-1",
    tasksCompleted: 500,
    averageCompletionTime: 40,
    successRate: 0.95,
    lastActive: new Date().toISOString(),
  },
];

describe("AnalyticsDashboard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (AnalyticsService.getAnalytics as jest.Mock).mockResolvedValue(
      mockAnalyticsData,
    );
    (AnalyticsService.getTaskTrends as jest.Mock).mockResolvedValue(mockTrends);
    (AnalyticsService.getWorkerStats as jest.Mock).mockResolvedValue(
      mockWorkers,
    );
  });

  test("should render dashboard header", async () => {
    render(<AnalyticsDashboard />);

    expect(screen.getByText("Analytics & Reporting")).toBeInTheDocument();
    expect(
      screen.getByText("View system performance and generate custom reports"),
    ).toBeInTheDocument();
  });

  test("should display refresh, CSV, and JSON buttons", async () => {
    render(<AnalyticsDashboard />);

    expect(
      screen.getByRole("button", { name: /Refresh/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /CSV/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /JSON/i })).toBeInTheDocument();
  });

  test("should display loading state initially", () => {
    render(<AnalyticsDashboard />);

    expect(screen.getByText("Loading analytics...")).toBeInTheDocument();
  });

  test("should fetch and display analytics data", async () => {
    render(<AnalyticsDashboard />);

    expect(await screen.findByText("Total Tasks")).toBeInTheDocument();
    expect(screen.getByText("1,000")).toBeInTheDocument();
    expect(screen.getByText("Completion Rate")).toBeInTheDocument();
  });

  test("should calculate and display completion rate correctly", async () => {
    render(<AnalyticsDashboard />);

    const rate = ((850 / (850 + 150)) * 100).toFixed(2);
    expect(await screen.findByText(`${rate}%`)).toBeInTheDocument();
  });

  test("should display worker performance table", async () => {
    render(<AnalyticsDashboard />);

    expect(await screen.findByText("Worker Performance")).toBeInTheDocument();
    expect(screen.getByText("worker-1")).toBeInTheDocument();
    expect(screen.getByText("500")).toBeInTheDocument();
  });

  test("should display task trends", async () => {
    render(<AnalyticsDashboard />);

    expect(
      await screen.findByText("Task Trends (Last 30 Days)"),
    ).toBeInTheDocument();
  });

  test("should allow changing date range", async () => {
    render(<AnalyticsDashboard />);

    const startDateInput = screen.getByLabelText(
      "Start Date",
    ) as HTMLInputElement;
    fireEvent.change(startDateInput, { target: { value: "2024-01-01" } });

    expect(startDateInput).toHaveValue("2024-01-01");
  });

  test("should handle export to CSV", async () => {
    const user = userEvent.setup();
    const exportToCSVMock = jest.spyOn(AnalyticsService, "exportToCSV");

    render(<AnalyticsDashboard />);

    expect(await screen.findByText("Total Tasks")).toBeInTheDocument();

    const csvButton = screen.getByRole("button", { name: /CSV/i });
    await user.click(csvButton);

    expect(exportToCSVMock).toHaveBeenCalled();
    exportToCSVMock.mockRestore();
  });

  test("should handle export to JSON", async () => {
    const user = userEvent.setup();
    const exportToJSONMock = jest.spyOn(AnalyticsService, "exportToJSON");

    render(<AnalyticsDashboard />);

    expect(await screen.findByText("Total Tasks")).toBeInTheDocument();

    const jsonButton = screen.getByRole("button", { name: /JSON/i });
    await user.click(jsonButton);

    expect(exportToJSONMock).toHaveBeenCalled();
    exportToJSONMock.mockRestore();
  });

  test("should handle refresh button click", async () => {
    const user = userEvent.setup();
    render(<AnalyticsDashboard />);

    expect(await screen.findByText("Total Tasks")).toBeInTheDocument();

    const refreshButton = screen.getByRole("button", { name: /Refresh/i });
    await user.click(refreshButton);

    expect(AnalyticsService.getAnalytics).toHaveBeenCalledTimes(2);
  });

  test("should display error message on fetch failure", async () => {
    const errorMessage = "Failed to fetch analytics";
    (AnalyticsService.getAnalytics as jest.Mock).mockRejectedValueOnce(
      new Error(errorMessage),
    );

    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  test("should display all metric cards", async () => {
    render(<AnalyticsDashboard />);

    expect(await screen.findByText("Total Tasks")).toBeInTheDocument();
    expect(screen.getByText("Completion Rate")).toBeInTheDocument();
    expect(screen.getByText("Completed Tasks")).toBeInTheDocument();
    expect(screen.getByText("Failed Tasks")).toBeInTheDocument();
    // "Avg Completion Time" appears both in metric cards and table header
    expect(
      screen.getAllByText("Avg Completion Time").length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Active Workers")).toBeInTheDocument();
  });

  test("should display worker success rate", async () => {
    render(<AnalyticsDashboard />);

    expect(await screen.findByText("Worker Performance")).toBeInTheDocument();

    expect(screen.getByText("95.00%")).toBeInTheDocument();
  });

  test("should format large numbers with commas", async () => {
    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("1,000")).toBeInTheDocument();
    });
  });
});
