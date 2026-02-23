import React, {
  createContext,
  useContext,
  useCallback,
  useState,
  useEffect,
  useRef,
} from "react";
import type { ReactNode } from "react";

/* ═══════════════════════════════ Types ════ */

export type NotificationType = "success" | "error" | "warning" | "info";

/** Toast notifications — short-lived, auto-dismiss */
export interface Notification {
  id: string;
  message: string;
  type: NotificationType;
  duration?: number;
  timestamp: number;
}

/** Persistent notification for the notification center */
export interface PersistentNotification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  category: "task" | "worker" | "system" | "alert" | "campaign";
  read: boolean;
  timestamp: number;
  actionUrl?: string;
  metadata?: Record<string, unknown>;
}

/** Activity feed event */
export interface ActivityEvent {
  id: string;
  action: string;
  entity: string;
  entityId?: string;
  actor: string;
  timestamp: number;
  details?: string;
}

interface NotificationContextType {
  /* Toast notifications */
  notifications: Notification[];
  showNotification: (
    message: string,
    type: NotificationType,
    duration?: number,
  ) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  /* Persistent notifications (notification center) */
  persistent: PersistentNotification[];
  unreadCount: number;
  addPersistent: (
    n: Omit<PersistentNotification, "id" | "read" | "timestamp">,
  ) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  removePersistent: (id: string) => void;
  clearPersistent: () => void;

  /* Activity feed */
  activities: ActivityEvent[];
  addActivity: (a: Omit<ActivityEvent, "id" | "timestamp">) => void;
  clearActivities: () => void;

  /* WebSocket status */
  wsConnected: boolean;
}

const NotificationContext = createContext<NotificationContextType | undefined>(
  undefined,
);

/* ═══════════════════════════════ Mock data  */

const INITIAL_PERSISTENT: PersistentNotification[] = [
  {
    id: "pn-1",
    title: "Worker Scaling Event",
    message:
      "Auto-scaler increased worker count from 4 to 6 due to queue depth",
    type: "info",
    category: "worker",
    read: false,
    timestamp: Date.now() - 120_000,
    actionUrl: "/workers",
  },
  {
    id: "pn-2",
    title: "High Error Rate Alert",
    message: "Task error rate exceeded 5% threshold in the last 10 minutes",
    type: "error",
    category: "alert",
    read: false,
    timestamp: Date.now() - 300_000,
    actionUrl: "/alerts",
  },
  {
    id: "pn-3",
    title: "Backup Completed",
    message: "Scheduled database backup completed successfully (14.8 MB)",
    type: "success",
    category: "system",
    read: true,
    timestamp: Date.now() - 3_600_000,
    actionUrl: "/settings",
  },
  {
    id: "pn-4",
    title: "Campaign Finished",
    message: 'Campaign "Q4 Email Blast" completed: 12,450 tasks processed',
    type: "success",
    category: "campaign",
    read: true,
    timestamp: Date.now() - 7_200_000,
    actionUrl: "/campaigns",
  },
  {
    id: "pn-5",
    title: "New Worker Registered",
    message: "worker-node-07 joined the cluster and is accepting tasks",
    type: "info",
    category: "worker",
    read: true,
    timestamp: Date.now() - 14_400_000,
  },
];

const INITIAL_ACTIVITIES: ActivityEvent[] = [
  {
    id: "act-1",
    action: "created",
    entity: "task",
    entityId: "task-4521",
    actor: "admin",
    timestamp: Date.now() - 60_000,
    details: "Bulk import task queued",
  },
  {
    id: "act-2",
    action: "completed",
    entity: "task",
    entityId: "task-4520",
    actor: "worker-03",
    timestamp: Date.now() - 180_000,
    details: "Processed in 2.3 s",
  },
  {
    id: "act-3",
    action: "joined",
    entity: "worker",
    entityId: "worker-07",
    actor: "system",
    timestamp: Date.now() - 900_000,
  },
  {
    id: "act-4",
    action: "launched",
    entity: "campaign",
    entityId: "cmp-12",
    actor: "admin",
    timestamp: Date.now() - 1_800_000,
    details: "Q4 Email Blast — 12,450 tasks",
  },
  {
    id: "act-5",
    action: "triggered",
    entity: "alert",
    entityId: "alert-89",
    actor: "system",
    timestamp: Date.now() - 3_600_000,
    details: "High error rate threshold breached",
  },
  {
    id: "act-6",
    action: "completed",
    entity: "maintenance",
    actor: "system",
    timestamp: Date.now() - 7_200_000,
    details: "Scheduled VACUUM ANALYZE",
  },
];

/* ═══════════════════════════════ Provider ══ */

/**
 * NotificationProvider — manages toast notifications, persistent
 * notification center entries, activity feed, and WebSocket status.
 */
export const NotificationProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  /* ── Toast state ── */
  const [notifications, setNotifications] = useState<Notification[]>([]);

  /* ── Persistent state ── */
  const [persistent, setPersistent] =
    useState<PersistentNotification[]>(INITIAL_PERSISTENT);

  /* ── Activity feed ── */
  const [activities, setActivities] =
    useState<ActivityEvent[]>(INITIAL_ACTIVITIES);

  /* ── WebSocket ── */
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  /* ── Derived ── */
  const unreadCount = persistent.filter((n) => !n.read).length;

  /* ── Toast helpers ── */

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const showNotification = useCallback(
    (
      message: string,
      type: NotificationType = "info",
      duration: number = 5000,
    ) => {
      const id = `notification-${Date.now()}-${Math.random()}`;
      const notification: Notification = {
        id,
        message,
        type,
        duration,
        timestamp: Date.now(),
      };

      setNotifications((prev) => [...prev, notification]);

      if (duration > 0) {
        window.setTimeout(() => {
          removeNotification(id);
        }, duration);
      }

      return id;
    },
    [removeNotification],
  );

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  /* ── Persistent helpers ── */

  const addPersistent = useCallback(
    (n: Omit<PersistentNotification, "id" | "read" | "timestamp">) => {
      const entry: PersistentNotification = {
        ...n,
        id: `pn-${Date.now()}-${Math.random()}`,
        read: false,
        timestamp: Date.now(),
      };
      setPersistent((prev) => [entry, ...prev]);
    },
    [],
  );

  const markRead = useCallback((id: string) => {
    setPersistent((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
    );
  }, []);

  const markAllRead = useCallback(() => {
    setPersistent((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const removePersistent = useCallback((id: string) => {
    setPersistent((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearPersistent = useCallback(() => {
    setPersistent([]);
  }, []);

  /* ── Activity helpers ── */

  const addActivity = useCallback(
    (a: Omit<ActivityEvent, "id" | "timestamp">) => {
      const event: ActivityEvent = {
        ...a,
        id: `act-${Date.now()}-${Math.random()}`,
        timestamp: Date.now(),
      };
      setActivities((prev) => [event, ...prev].slice(0, 100));
    },
    [],
  );

  const clearActivities = useCallback(() => {
    setActivities([]);
  }, []);

  /* ── WebSocket connection ── */

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl =
      import.meta.env.VITE_WS_URL ||
      `${protocol}//${window.location.hostname}:8000/ws/tasks`;

    let ws: WebSocket;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => setWsConnected(true);
        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimer = setTimeout(connect, 5000);
        };
        ws.onerror = () => ws.close();

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "notification") {
              addPersistent({
                title: data.title ?? "System Notification",
                message: data.message ?? "",
                type: data.severity ?? "info",
                category: data.category ?? "system",
              });
            }
            if (data.type === "activity") {
              addActivity({
                action: data.action ?? "event",
                entity: data.entity ?? "system",
                entityId: data.entity_id,
                actor: data.actor ?? "system",
                details: data.details,
              });
            }
          } catch {
            /* ignore non-JSON messages */
          }
        };
      } catch {
        reconnectTimer = setTimeout(connect, 5000);
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [addPersistent, addActivity]);

  /* ── Context value ── */

  const value: NotificationContextType = {
    notifications,
    showNotification,
    removeNotification,
    clearNotifications,
    persistent,
    unreadCount,
    addPersistent,
    markRead,
    markAllRead,
    removePersistent,
    clearPersistent,
    activities,
    addActivity,
    clearActivities,
    wsConnected,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

/**
 * Hook to use notification context
 * @returns NotificationContextType with notification methods
 * @throws Error if used outside NotificationProvider
 */
export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotification must be used within NotificationProvider");
  }
  return context;
};
