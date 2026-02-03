import React, { useEffect } from "react";
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from "lucide-react";
import { NotificationType } from "../context/NotificationContext";
import "../styles/toast.css";

interface ToastProps {
  id: string;
  message: string;
  type: NotificationType;
  onClose: (id: string) => void;
  duration?: number;
}

/**
 * Toast component for displaying notifications
 * Shows at the top-right of the screen with appropriate styling and icon
 */
const Toast: React.FC<ToastProps> = ({
  id,
  message,
  type,
  onClose,
  duration = 5000,
}) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = window.setTimeout(() => {
        onClose(id);
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [id, duration, onClose]);

  const getIcon = () => {
    switch (type) {
      case "success":
        return <CheckCircle size={20} />;
      case "error":
        return <AlertCircle size={20} />;
      case "warning":
        return <AlertTriangle size={20} />;
      case "info":
      default:
        return <Info size={20} />;
    }
  };

  return (
    <div className={`toast toast-${type}`} role="alert" aria-live="polite">
      <div className="toast-content">
        <div className="toast-icon">{getIcon()}</div>
        <p className="toast-message">{message}</p>
      </div>
      <button
        className="toast-close"
        onClick={() => onClose(id)}
        aria-label="Close notification"
      >
        <X size={16} />
      </button>
    </div>
  );
};

export default Toast;
