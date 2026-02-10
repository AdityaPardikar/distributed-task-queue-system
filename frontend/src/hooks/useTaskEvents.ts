import { useCallback, useEffect, useRef } from "react";
import { useNotification } from "../context/NotificationContext";
// WebSocket URL configuration
const getWebSocketUrl = (): string => {
  const wsUrl = import.meta.env.VITE_WS_URL as string | undefined;
  if (wsUrl) return wsUrl;

  // Construct from current location
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}`;
};
export interface TaskEvent {
  id: string | number;
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  previousStatus?: "pending" | "running" | "completed" | "failed";
  timestamp: number;
  workerId?: string;
  error?: string;
  result?: unknown;
}

export interface UseTaskEventsOptions {
  enabled?: boolean;
  onTaskStatusChange?: (event: TaskEvent) => void;
}

/**
 * Hook to listen for real-time task status updates via WebSocket
 * Automatically sends notifications for task status changes
 * @param options Configuration options for task events
 * @returns Object with methods to handle task events
 */
export const useTaskEvents = (options: UseTaskEventsOptions = {}) => {
  const { enabled = true, onTaskStatusChange } = options;
  const { showNotification } = useNotification();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttemptsRef = useRef(5);
  const reconnectIntervalRef = useRef(1000);

  // Handle incoming task events
  const handleTaskEvent = useCallback(
    (event: TaskEvent) => {
      // Show notification for status changes
      if (event.previousStatus && event.previousStatus !== event.status) {
        const statusMessages: Record<string, string> = {
          pending: `Task "${event.name}" is pending`,
          running: `Task "${event.name}" is running`,
          completed: `Task "${event.name}" completed successfully`,
          failed: `Task "${event.name}" failed: ${event.error || "Unknown error"}`,
        };

        const notificationType =
          event.status === "failed"
            ? "error"
            : event.status === "completed"
              ? "success"
              : "info";

        showNotification(
          statusMessages[event.status] || "Task updated",
          notificationType,
        );
      }

      // Call custom handler if provided
      if (onTaskStatusChange) {
        onTaskStatusChange(event);
      }
    },
    [showNotification, onTaskStatusChange],
  );

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!enabled) return;

    try {
      const wsUrl = getWebSocketUrl();
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        reconnectAttemptsRef.current = 0;
        reconnectIntervalRef.current = 1000;

        // Subscribe to task events
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({ action: "subscribe", channel: "task_events" }),
          );
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === "task_event") {
            handleTaskEvent(data.payload);
          }
        } catch (error) {
          console.error("Failed to parse task event message:", error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("WebSocket task events error:", error);
      };

      wsRef.current.onclose = () => {
        // Attempt to reconnect with exponential backoff
        if (reconnectAttemptsRef.current < maxReconnectAttemptsRef.current) {
          reconnectAttemptsRef.current += 1;
          reconnectIntervalRef.current = Math.min(
            reconnectIntervalRef.current * 2,
            30000,
          );

          window.setTimeout(() => {
            connect();
          }, reconnectIntervalRef.current);
        }
      };
    } catch (error) {
      console.error(
        "Failed to establish WebSocket connection for task events:",
        error,
      );
    }
  }, [enabled, handleTaskEvent]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Publish task event (for testing or manual triggering)
  const publishTaskEvent = useCallback(
    (event: TaskEvent) => {
      handleTaskEvent(event);
    },
    [handleTaskEvent],
  );

  // Connect on mount
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    connect,
    disconnect,
    publishTaskEvent,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
};
