import AnalyticsService, {
  AnalyticsData,
  ReportConfig,
  WorkerStat,
  TrendDataPoint,
  ErrorRateData,
  QueueDepthPoint,
} from "../../services/AnalyticsService";
import api from "../../services/api";

jest.mock("../../services/api", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
  },
}));

// Mock URL methods
global.URL.createObjectURL = jest.fn(() => "blob:mock-url");
global.URL.revokeObjectURL = jest.fn();

const mockAnalyticsData: AnalyticsData = {
  totalTasks: 1000,
  completedTasks: 850,
  failedTasks: 150,
  averageCompletionTime: 45.5,
  workerStats: [],
  taskTrends: [],
  errorRates: [],
  queueDepthHistory: [],
};

describe("AnalyticsService", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("getAnalytics", () => {
    test("should fetch analytics without date range", async () => {
      (api.get as jest.Mock).mockResolvedValueOnce({ data: mockAnalyticsData });

      const result = await AnalyticsService.getAnalytics();

      expect(api.get).toHaveBeenCalledWith("/analytics", { params: {} });
      expect(result).toEqual(mockAnalyticsData);
    });

    test("should fetch analytics with date range", async () => {
      (api.get as jest.Mock).mockResolvedValueOnce({ data: mockAnalyticsData });

      const dateRange = { startDate: "2024-01-01", endDate: "2024-01-31" };
      const result = await AnalyticsService.getAnalytics(dateRange);

      expect(api.get).toHaveBeenCalledWith("/analytics", {
        params: {
          start_date: "2024-01-01",
          end_date: "2024-01-31",
        },
      });
      expect(result).toEqual(mockAnalyticsData);
    });

    test("should handle analytics fetch error", async () => {
      const error = new Error("API Error");
      (api.get as jest.Mock).mockRejectedValueOnce(error);

      await expect(AnalyticsService.getAnalytics()).rejects.toThrow(
        "API Error",
      );
    });
  });

  describe("getTaskTrends", () => {
    test("should fetch task trends with default days", async () => {
      (api.get as jest.Mock).mockResolvedValueOnce({ data: [] });

      await AnalyticsService.getTaskTrends();

      expect(api.get).toHaveBeenCalledWith("/analytics/trends", {
        params: { days: 30 },
      });
    });

    test("should fetch task trends with custom days", async () => {
      (api.get as jest.Mock).mockResolvedValueOnce({ data: [] });

      await AnalyticsService.getTaskTrends(60);

      expect(api.get).toHaveBeenCalledWith("/analytics/trends", {
        params: { days: 60 },
      });
    });
  });

  describe("getWorkerStats", () => {
    test("should fetch worker statistics", async () => {
      const mockWorkers = [
        {
          workerId: "worker-1",
          tasksCompleted: 100,
          averageCompletionTime: 45,
          successRate: 0.95,
          lastActive: new Date().toISOString(),
        },
      ];
      (api.get as jest.Mock).mockResolvedValueOnce({ data: mockWorkers });

      const result = await AnalyticsService.getWorkerStats();

      expect(api.get).toHaveBeenCalledWith("/analytics/workers");
      expect(result).toEqual(mockWorkers);
    });
  });

  describe("getErrorRates", () => {
    test("should fetch error rates with default days", async () => {
      (api.get as jest.Mock).mockResolvedValueOnce({ data: [] });

      await AnalyticsService.getErrorRates();

      expect(api.get).toHaveBeenCalledWith("/analytics/errors", {
        params: { days: 30 },
      });
    });

    test("should fetch error rates with custom days", async () => {
      (api.get as jest.Mock).mockResolvedValueOnce({ data: [] });

      await AnalyticsService.getErrorRates(7);

      expect(api.get).toHaveBeenCalledWith("/analytics/errors", {
        params: { days: 7 },
      });
    });
  });

  describe("getQueueDepthHistory", () => {
    test("should fetch queue depth with default hours", async () => {
      (api.get as jest.Mock).mockResolvedValueOnce({ data: [] });

      await AnalyticsService.getQueueDepthHistory();

      expect(api.get).toHaveBeenCalledWith("/analytics/queue-depth", {
        params: { hours: 24 },
      });
    });

    test("should fetch queue depth with custom hours", async () => {
      (api.get as jest.Mock).mockResolvedValueOnce({ data: [] });

      await AnalyticsService.getQueueDepthHistory(48);

      expect(api.get).toHaveBeenCalledWith("/analytics/queue-depth", {
        params: { hours: 48 },
      });
    });
  });

  describe("generateReport", () => {
    test("should generate report with config", async () => {
      (api.post as jest.Mock).mockResolvedValueOnce({
        data: { reportId: "report-123" },
      });

      const config: ReportConfig = {
        name: "Test Report",
        type: "task",
        dateRange: { startDate: "2024-01-01", endDate: "2024-01-31" },
        metrics: ["completion_rate"],
      };

      const result = await AnalyticsService.generateReport(config);

      expect(api.post).toHaveBeenCalledWith("/reports/generate", config);
      expect(result).toBe("report-123");
    });

    test("should handle report generation error", async () => {
      const error = new Error("Generation failed");
      (api.post as jest.Mock).mockRejectedValueOnce(error);

      const config: ReportConfig = {
        name: "Test Report",
        type: "task",
        dateRange: { startDate: "2024-01-01", endDate: "2024-01-31" },
        metrics: [],
      };

      await expect(AnalyticsService.generateReport(config)).rejects.toThrow(
        "Generation failed",
      );
    });
  });

  describe("getReport", () => {
    test("should fetch specific report", async () => {
      const mockReport = { id: "report-1", name: "Test Report" };
      (api.get as jest.Mock).mockResolvedValueOnce({ data: mockReport });

      const result = await AnalyticsService.getReport("report-1");

      expect(api.get).toHaveBeenCalledWith("/reports/report-1");
      expect(result).toEqual(mockReport);
    });
  });

  describe("listReports", () => {
    test("should list all reports", async () => {
      const mockReports = [
        {
          id: "report-1",
          name: "Report 1",
          type: "task",
          createdAt: new Date().toISOString(),
        },
        {
          id: "report-2",
          name: "Report 2",
          type: "worker",
          createdAt: new Date().toISOString(),
        },
      ];
      (api.get as jest.Mock).mockResolvedValueOnce({ data: mockReports });

      const result = await AnalyticsService.listReports();

      expect(api.get).toHaveBeenCalledWith("/reports");
      expect(result).toEqual(mockReports);
    });
  });

  describe("deleteReport", () => {
    test("should delete report", async () => {
      (api.delete as jest.Mock).mockResolvedValueOnce({});

      await AnalyticsService.deleteReport("report-1");

      expect(api.delete).toHaveBeenCalledWith("/reports/report-1");
    });

    test("should handle delete error", async () => {
      const error = new Error("Delete failed");
      (api.delete as jest.Mock).mockRejectedValueOnce(error);

      await expect(AnalyticsService.deleteReport("report-1")).rejects.toThrow(
        "Delete failed",
      );
    });
  });

  describe("exportToCSV", () => {
    test("should export data to CSV", () => {
      const data = [
        { name: "Task 1", status: "completed", duration: 45 },
        { name: "Task 2", status: "failed", duration: 60 },
      ];

      const createElementSpy = jest.spyOn(document, "createElement");
      const appendChildSpy = jest.spyOn(document.body, "appendChild");
      const removeChildSpy = jest.spyOn(document.body, "removeChild");

      AnalyticsService.exportToCSV(data, "test.csv");

      expect(createElementSpy).toHaveBeenCalledWith("a");
      expect(appendChildSpy).toHaveBeenCalled();
      expect(removeChildSpy).toHaveBeenCalled();

      createElementSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
    });

    test("should handle CSV export error", () => {
      const invalidData = null;

      expect(() => {
        AnalyticsService.exportToCSV(
          invalidData as unknown as unknown[],
          "test.csv",
        );
      }).toThrow();
    });
  });

  describe("exportToJSON", () => {
    test("should export data to JSON", () => {
      const data = { totalTasks: 100, completedTasks: 85 };

      const createElementSpy = jest.spyOn(document, "createElement");
      const appendChildSpy = jest.spyOn(document.body, "appendChild");
      const removeChildSpy = jest.spyOn(document.body, "removeChild");

      AnalyticsService.exportToJSON(data, "test.json");

      expect(createElementSpy).toHaveBeenCalledWith("a");
      expect(appendChildSpy).toHaveBeenCalled();
      expect(removeChildSpy).toHaveBeenCalled();

      createElementSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
    });
  });
});
