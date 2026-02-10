import api from "./api";

export interface AnalyticsData {
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  averageCompletionTime: number;
  workerStats: WorkerStat[];
  taskTrends: TrendDataPoint[];
  errorRates: ErrorRateData[];
  queueDepthHistory: QueueDepthPoint[];
}

export interface WorkerStat {
  workerId: string;
  tasksCompleted: number;
  averageCompletionTime: number;
  successRate: number;
  lastActive: string;
}

export interface TrendDataPoint {
  timestamp: string;
  completedCount: number;
  failedCount: number;
  pendingCount: number;
}

export interface ErrorRateData {
  timestamp: string;
  errorRate: number;
  errorCount: number;
  totalTasks: number;
}

export interface QueueDepthPoint {
  timestamp: string;
  depth: number;
}

export interface ReportConfig {
  name: string;
  type: "task" | "worker" | "health" | "custom";
  dateRange: {
    startDate: string;
    endDate: string;
  };
  metrics: string[];
  filters?: Record<string, unknown>;
}

export interface ExportOptions {
  format: "csv" | "json" | "pdf";
  data: unknown;
  filename: string;
}

class AnalyticsServiceClass {
  async getAnalytics(dateRange?: {
    startDate: string;
    endDate: string;
  }): Promise<AnalyticsData> {
    try {
      const params: Record<string, unknown> = {};
      if (dateRange) {
        params.start_date = dateRange.startDate;
        params.end_date = dateRange.endDate;
      }
      const response = await api.get("/analytics", { params });
      return response.data as AnalyticsData;
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
      throw error;
    }
  }

  async getTaskTrends(days: number = 30): Promise<TrendDataPoint[]> {
    try {
      const response = await api.get("/analytics/trends", { params: { days } });
      return response.data as TrendDataPoint[];
    } catch (error) {
      console.error("Failed to fetch task trends:", error);
      throw error;
    }
  }

  async getWorkerStats(): Promise<WorkerStat[]> {
    try {
      const response = await api.get("/analytics/workers");
      return response.data as WorkerStat[];
    } catch (error) {
      console.error("Failed to fetch worker stats:", error);
      throw error;
    }
  }

  async getErrorRates(days: number = 30): Promise<ErrorRateData[]> {
    try {
      const response = await api.get("/analytics/errors", { params: { days } });
      return response.data as ErrorRateData[];
    } catch (error) {
      console.error("Failed to fetch error rates:", error);
      throw error;
    }
  }

  async getQueueDepthHistory(hours: number = 24): Promise<QueueDepthPoint[]> {
    try {
      const response = await api.get("/analytics/queue-depth", {
        params: { hours },
      });
      return response.data as QueueDepthPoint[];
    } catch (error) {
      console.error("Failed to fetch queue depth history:", error);
      throw error;
    }
  }

  async generateReport(config: ReportConfig): Promise<string> {
    try {
      const response = await api.post("/reports/generate", config);
      return (response.data as { reportId: string }).reportId;
    } catch (error) {
      console.error("Failed to generate report:", error);
      throw error;
    }
  }

  async getReport(reportId: string): Promise<unknown> {
    try {
      const response = await api.get(`/reports/${reportId}`);
      return response.data;
    } catch (error) {
      console.error("Failed to fetch report:", error);
      throw error;
    }
  }

  async listReports(): Promise<
    Array<{ id: string; name: string; type: string; createdAt: string }>
  > {
    try {
      const response = await api.get("/reports");
      return response.data as Array<{
        id: string;
        name: string;
        type: string;
        createdAt: string;
      }>;
    } catch (error) {
      console.error("Failed to list reports:", error);
      throw error;
    }
  }

  async deleteReport(reportId: string): Promise<void> {
    try {
      await api.delete(`/reports/${reportId}`);
    } catch (error) {
      console.error("Failed to delete report:", error);
      throw error;
    }
  }

  exportToCSV(data: unknown[], filename: string): void {
    try {
      const rows = Array.isArray(data) ? data : [data];
      if (rows.length === 0) return;

      const headers = Object.keys(rows[0] as Record<string, unknown>);
      const csvContent = [
        headers.join(","),
        ...rows.map((row) => {
          const r = row as Record<string, unknown>;
          return headers
            .map((header) => {
              const value = r[header];
              const stringValue =
                typeof value === "string" ? value : JSON.stringify(value);
              return `"${stringValue.replace(/"/g, '""')}"`;
            })
            .join(",");
        }),
      ].join("\n");

      this.downloadFile(csvContent, filename, "text/csv");
    } catch (error) {
      console.error("Failed to export CSV:", error);
      throw error;
    }
  }

  exportToJSON(data: unknown, filename: string): void {
    try {
      const jsonContent = JSON.stringify(data, null, 2);
      this.downloadFile(jsonContent, filename, "application/json");
    } catch (error) {
      console.error("Failed to export JSON:", error);
      throw error;
    }
  }

  private downloadFile(
    content: string,
    filename: string,
    mimeType: string,
  ): void {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}

export const AnalyticsService = new AnalyticsServiceClass();
export default AnalyticsService;
