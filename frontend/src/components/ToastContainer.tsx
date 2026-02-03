import React from "react";
import { useNotification } from "../context/NotificationContext";
import Toast from "./Toast";

/**
 * ToastContainer component that renders all active notifications
 * Should be placed at the root of the application (App or main layout)
 */
const ToastContainer: React.FC = () => {
  const { notifications, removeNotification } = useNotification();

  return (
    <div className="toast-container">
      {notifications.map((notification) => (
        <Toast
          key={notification.id}
          id={notification.id}
          message={notification.message}
          type={notification.type}
          duration={notification.duration}
          onClose={removeNotification}
        />
      ))}
    </div>
  );
};

export default ToastContainer;
