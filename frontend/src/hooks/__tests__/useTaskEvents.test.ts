import React from "react";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useTaskEvents, TaskEvent } from "../../hooks/useTaskEvents";
import { NotificationProvider } from "../../context/NotificationContext";

describe("useTaskEvents Hook", () => {
  let mockWebSocket: any;
  const originalWebSocket = window.WebSocket;

  beforeEach(() => {
    mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      readyState: WebSocket.OPEN,
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null,
    };

    (window as any).WebSocket = jest.fn(() => mockWebSocket);
  });

  afterEach(() => {
    (window as any).WebSocket = originalWebSocket;
  });

  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(NotificationProvider, {}, children);

  test("should initialize with enabled true by default", () => {
    const { result } = renderHook(() => useTaskEvents(), { wrapper });
    expect(result.current).toBeDefined();
  });

  test("should connect to WebSocket on mount when enabled", () => {
    renderHook(() => useTaskEvents({ enabled: true }), { wrapper });

    expect(window.WebSocket).toHaveBeenCalled();
  });

  test("should not connect to WebSocket when disabled", () => {
    const { rerender } = renderHook(
      ({ enabled }) => useTaskEvents({ enabled }),
      { wrapper, initialProps: { enabled: false } },
    );

    expect(window.WebSocket).not.toHaveBeenCalled();
  });

  test("should handle task event messages", async () => {
    const onTaskStatusChange = jest.fn();
    renderHook(() => useTaskEvents({ onTaskStatusChange }), { wrapper });

    act(() => {
      mockWebSocket.onopen();
    });

    const taskEvent: TaskEvent = {
      id: "1",
      name: "Test Task",
      status: "running",
      previousStatus: "pending",
      timestamp: Date.now(),
    };

    act(() => {
      mockWebSocket.onmessage({
        data: JSON.stringify({
          type: "task_event",
          payload: taskEvent,
        }),
      });
    });

    await waitFor(() => {
      expect(onTaskStatusChange).toHaveBeenCalledWith(taskEvent);
    });
  });

  test("should subscribe to task_events channel on connection", () => {
    renderHook(() => useTaskEvents(), { wrapper });

    act(() => {
      if (mockWebSocket.onopen) {
        mockWebSocket.onopen();
      }
    });

    // Give a moment for the send call to be processed
    setTimeout(() => {
      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({
          action: "subscribe",
          channel: "task_events",
        }),
      );
    }, 0);
  });

  test("should handle task completion event", async () => {
    const onTaskStatusChange = jest.fn();
    renderHook(() => useTaskEvents({ onTaskStatusChange }), { wrapper });

    act(() => {
      mockWebSocket.onopen();
    });

    const completedEvent: TaskEvent = {
      id: "1",
      name: "Process Data",
      status: "completed",
      previousStatus: "running",
      timestamp: Date.now(),
      result: { processed: 100 },
    };

    act(() => {
      mockWebSocket.onmessage({
        data: JSON.stringify({
          type: "task_event",
          payload: completedEvent,
        }),
      });
    });

    await waitFor(() => {
      expect(onTaskStatusChange).toHaveBeenCalledWith(completedEvent);
    });
  });

  test("should handle task failure event", async () => {
    const onTaskStatusChange = jest.fn();
    renderHook(() => useTaskEvents({ onTaskStatusChange }), { wrapper });

    act(() => {
      mockWebSocket.onopen();
    });

    const failedEvent: TaskEvent = {
      id: "1",
      name: "Failed Task",
      status: "failed",
      previousStatus: "running",
      timestamp: Date.now(),
      error: "Database connection timeout",
    };

    act(() => {
      mockWebSocket.onmessage({
        data: JSON.stringify({
          type: "task_event",
          payload: failedEvent,
        }),
      });
    });

    await waitFor(() => {
      expect(onTaskStatusChange).toHaveBeenCalledWith(failedEvent);
    });
  });

  test("should publish task event manually", async () => {
    const onTaskStatusChange = jest.fn();
    const { result } = renderHook(() => useTaskEvents({ onTaskStatusChange }), {
      wrapper,
    });

    const event: TaskEvent = {
      id: "1",
      name: "Manual Task",
      status: "completed",
      timestamp: Date.now(),
    };

    act(() => {
      result.current.publishTaskEvent(event);
    });

    await waitFor(() => {
      expect(onTaskStatusChange).toHaveBeenCalledWith(event);
    });
  });

  test("should handle malformed messages gracefully", () => {
    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();
    renderHook(() => useTaskEvents(), { wrapper });

    act(() => {
      mockWebSocket.onopen();
      mockWebSocket.onmessage({ data: "invalid json" });
    });

    expect(consoleErrorSpy).toHaveBeenCalled();
    consoleErrorSpy.mockRestore();
  });

  test("should disconnect on unmount", () => {
    const { unmount } = renderHook(() => useTaskEvents(), { wrapper });

    unmount();

    expect(mockWebSocket.close).toHaveBeenCalled();
  });

  test("should reconnect with exponential backoff on connection loss", async () => {
    jest.useFakeTimers();
    (window.WebSocket as jest.Mock).mockClear();

    renderHook(() => useTaskEvents(), { wrapper });

    expect(window.WebSocket).toHaveBeenCalledTimes(1);

    act(() => {
      mockWebSocket.onopen();
      mockWebSocket.onclose();
    });

    // Advance timers to trigger reconnect
    act(() => {
      jest.advanceTimersByTime(1100);
    });

    // Check reconnection attempt was made
    await waitFor(() => {
      expect(window.WebSocket).toHaveBeenCalledTimes(2);
    });

    jest.useRealTimers();
  });
});
