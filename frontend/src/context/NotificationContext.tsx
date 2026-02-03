import React, {
  createContext,
  useContext,
  useCallback,
  useState,
  ReactNode,
} from "react";

export type NotificationType = "success" | "error" | "warning" | "info";

export interface Notification {
  id: string;
  message: string;
  type: NotificationType;
  duration?: number;
  timestamp: number;
}

interface NotificationContextType {
  notifications: Notification[];
  showNotification: (
    message: string,
    type: NotificationType,
    duration?: number,
  ) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(
  undefined,
);

/**
 * NotificationProvider component that manages global notifications
 * Provides notification queue system for toast messages
 */
export const NotificationProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

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

      // Auto-remove notification after duration
      if (duration > 0) {
        window.setTimeout(() => {
          removeNotification(id);
        }, duration);
      }

      return id;
    },
    [],
  );

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const value: NotificationContextType = {
    notifications,
    showNotification,
    removeNotification,
    clearNotifications,
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
