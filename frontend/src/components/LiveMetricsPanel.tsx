import React, { useMemo } from "react";
import {
  Activity,
  Zap,
  Cpu,
  HardDrive,
  Server,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
} from "lucide-react";
import {
  useMetricsStream,
  MetricsData,
  WorkerHealth,
  AlertData,
} from "../hooks/useMetricsStream";
import "../styles/live-metrics.css";

interface LiveMetricsPanelProps {
  className?: string;
  onMetricsUpdate?: (metrics: MetricsData) => void;
}

const LiveMetricsPanel: React.FC<LiveMetricsPanelProps> = ({
  className = "",
  onMetricsUpdate,
}) => {
  const {
    isConnected,
    metrics,
    workerHealthMap,
    alerts,
    lastUpdate,
    clearAlerts,
  } = useMetricsStream({
    enabled: true,
    onMetricsUpdate,
  });

  // Convert worker health map to array
  const workers = useMemo(
    () => Array.from(workerHealthMap.values()),
    [workerHealthMap]
  );

  // Get status icon
  const getWorkerStatusIcon = (status: WorkerHealth["status"]) => {
    switch (status) {
      case "healthy":
        return <CheckCircle size={14} className="status-icon healthy" />;
      case "degraded":
        return <AlertTriangle size={14} className="status-icon degraded" />;
      case "offline":
        return <XCircle size={14} className="status-icon offline" />;
    }
  };

  // Format timestamp
  const formatTime = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  // Format uptime
  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  // Get alert severity class
  const getAlertClass = (severity: AlertData["severity"]): string => {
    switch (severity) {
      case "critical":
        return "alert-critical";
      case "warning":
        return "alert-warning";
      default:
        return "alert-info";
    }
  };

  return (
    <div className={`live-metrics-panel ${className}`}>
      {/* Connection Status */}
      <div className="connection-status">
        <div className={`status-indicator ${isConnected ? "connected" : "disconnected"}`}>
          <Activity size={14} />
          <span>{isConnected ? "Live" : "Disconnected"}</span>
        </div>
        {lastUpdate && (
          <span className="last-update">
            <Clock size={12} />
            Last update: {formatTime(lastUpdate)}
          </span>
        )}
      </div>

      {/* Real-time Metrics */}
      {metrics && (
        <div className="metrics-grid">
          <div className="metric-card throughput">
            <div className="metric-icon">
              <Zap size={20} />
            </div>
            <div className="metric-content">
              <span className="metric-value">{metrics.throughput}</span>
              <span className="metric-label">Tasks/min</span>
            </div>
          </div>

          <div className="metric-card queue">
            <div className="metric-icon">
              <Server size={20} />
            </div>
            <div className="metric-content">
              <span className="metric-value">{metrics.queueDepth}</span>
              <span className="metric-label">Queue Depth</span>
            </div>
          </div>

          <div className="metric-card running">
            <div className="metric-icon">
              <Activity size={20} />
            </div>
            <div className="metric-content">
              <span className="metric-value">{metrics.runningTasks}</span>
              <span className="metric-label">Running</span>
            </div>
          </div>

          <div className="metric-card error-rate">
            <div className="metric-icon">
              <AlertTriangle size={20} />
            </div>
            <div className="metric-content">
              <span className="metric-value">
                {(metrics.errorRate * 100).toFixed(1)}%
              </span>
              <span className="metric-label">Error Rate</span>
            </div>
          </div>
        </div>
      )}

      {/* Worker Health */}
      {workers.length > 0 && (
        <div className="worker-health-section">
          <h4>Worker Health</h4>
          <div className="workers-grid">
            {workers.map((worker) => (
              <div
                key={worker.workerId}
                className={`worker-card ${worker.status}`}
              >
                <div className="worker-header">
                  {getWorkerStatusIcon(worker.status)}
                  <span className="worker-id">{worker.workerId}</span>
                </div>
                <div className="worker-stats">
                  <div className="worker-stat">
                    <Cpu size={12} />
                    <span>{worker.cpuUsage.toFixed(1)}%</span>
                  </div>
                  <div className="worker-stat">
                    <HardDrive size={12} />
                    <span>{worker.memoryUsage.toFixed(1)}%</span>
                  </div>
                  <div className="worker-stat">
                    <Activity size={12} />
                    <span>{worker.taskCount} tasks</span>
                  </div>
                </div>
                <div className="worker-uptime">
                  Uptime: {formatUptime(worker.uptime)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="alerts-section">
          <div className="alerts-header">
            <h4>Alerts</h4>
            <button onClick={clearAlerts} className="clear-alerts-btn">
              Clear
            </button>
          </div>
          <div className="alerts-list">
            {alerts.slice(-5).reverse().map((alert) => (
              <div
                key={alert.id}
                className={`alert-item ${getAlertClass(alert.severity)}`}
              >
                <span className="alert-time">{formatTime(alert.timestamp)}</span>
                <span className="alert-message">{alert.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fallback when not connected */}
      {!isConnected && !metrics && (
        <div className="no-data">
          <Activity size={32} className="no-data-icon" />
          <p>Connecting to metrics stream...</p>
        </div>
      )}
    </div>
  );
};

export default LiveMetricsPanel;
