import { renderHook, waitFor } from "@testing-library/react";
import { useMetrics } from "../useMetrics";
import * as api from "../../services/api";

// Mock the api module
jest.mock("../../services/api", () => ({
  __esModule: true,
  default: {
    getTasks: jest.fn(),
    dashboardAPI: {
      getStats: jest.fn(),
      getRecentTasks: jest.fn(),
      getWorkers: jest.fn(),
    },
  },
}));

// Mock WebSocket
class MockWebSocket {
  url: string;
  readyState: number = 0; // WebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
  }

  send(_data: string) {
    // Mock implementation
  }

  close() {
    this.readyState = 3; // WebSocket.CLOSED
    this.onclose?.(new CloseEvent("close"));
  }
}

(globalThis as typeof globalThis & { WebSocket: typeof WebSocket }).WebSocket =
  MockWebSocket as unknown as typeof WebSocket;

describe("useMetrics Hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches dashboard metrics on mount", async () => {
    const mockStats = {
      data: {
        total_tasks: 100,
        pending_tasks: 10,
        running_tasks: 5,
        completed_tasks: 80,
        failed_tasks: 5,
        active_workers: 3,
        total_workers: 5,
        queue_size: 10,
        success_rate: 94.1,
        avg_processing_time: 2.5,
      },
    };

    (api.default.dashboardAPI.getStats as jest.Mock).mockResolvedValue(
      mockStats,
    );
    (api.default.dashboardAPI.getRecentTasks as jest.Mock).mockResolvedValue({
      data: [],
    });
    (api.default.dashboardAPI.getWorkers as jest.Mock).mockResolvedValue({
      data: [],
    });

    const { result } = renderHook(() => useMetrics());

    await waitFor(() => {
      expect(result.current.metrics).not.toBeNull();
    });

    expect(result.current.metrics?.totalTasks).toBe(100);
    expect(result.current.metrics?.activeWorkers).toBe(3);
  });

  it("handles API errors gracefully", async () => {
    const mockError = new Error("API Error");

    (api.default.dashboardAPI.getStats as jest.Mock).mockRejectedValue(
      mockError,
    );
    (api.default.dashboardAPI.getRecentTasks as jest.Mock).mockRejectedValue(
      mockError,
    );
    (api.default.dashboardAPI.getWorkers as jest.Mock).mockRejectedValue(
      mockError,
    );

    const { result } = renderHook(() => useMetrics());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).not.toBeNull();
  });

  it("generates chart data with correct format", async () => {
    const mockStats = {
      data: {
        total_tasks: 100,
        pending_tasks: 10,
        running_tasks: 5,
        completed_tasks: 80,
        failed_tasks: 5,
        active_workers: 3,
        total_workers: 5,
        queue_size: 10,
        success_rate: 94.1,
        avg_processing_time: 2.5,
      },
    };

    (api.default.dashboardAPI.getStats as jest.Mock).mockResolvedValue(
      mockStats,
    );
    (api.default.dashboardAPI.getRecentTasks as jest.Mock).mockResolvedValue({
      data: [],
    });
    (api.default.dashboardAPI.getWorkers as jest.Mock).mockResolvedValue({
      data: [],
    });

    const { result } = renderHook(() => useMetrics());

    await waitFor(() => {
      expect(result.current.queueDepthData.length).toBeGreaterThan(0);
    });

    expect(result.current.queueDepthData[0]).toHaveProperty("time");
    expect(result.current.queueDepthData[0]).toHaveProperty("value");
  });

  it("provides refresh function", async () => {
    (api.default.dashboardAPI.getStats as jest.Mock).mockResolvedValue({
      data: {},
    });
    (api.default.dashboardAPI.getRecentTasks as jest.Mock).mockResolvedValue({
      data: [],
    });
    (api.default.dashboardAPI.getWorkers as jest.Mock).mockResolvedValue({
      data: [],
    });

    const { result } = renderHook(() => useMetrics());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const callCount = (api.default.dashboardAPI.getStats as jest.Mock).mock
      .calls.length;

    result.current.refresh();

    await waitFor(() => {
      expect(
        (api.default.dashboardAPI.getStats as jest.Mock).mock.calls.length,
      ).toBeGreaterThan(callCount);
    });
  });
});
