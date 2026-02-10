import React, { useState, useEffect, useCallback } from "react";
import {
  Download,
  RefreshCw,
  TrendingUp,
  AlertCircle,
  Users,
  Zap,
} from "lucide-react";
import AnalyticsService from "../services/AnalyticsService";
import type {
  AnalyticsData,
  TrendDataPoint,
  WorkerStat,
} from "../services/AnalyticsService";
import "../styles/analytics-dashboard.css";

const AnalyticsDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [trends, setTrends] = useState<TrendDataPoint[]>([]);
  const [workers, setWorkers] = useState<WorkerStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split("T")[0],
    endDate: new Date().toISOString().split("T")[0],
  });

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [analyticsData, trendsData, workersData] = await Promise.all([
        AnalyticsService.getAnalytics(dateRange),
        AnalyticsService.getTaskTrends(30),
        AnalyticsService.getWorkerStats(),
      ]);
      setAnalytics(analyticsData);
      setTrends(trendsData);
      setWorkers(workersData);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to fetch analytics";
      setError(message);
      console.error("Analytics fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [dateRange]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const handleExport = (format: "csv" | "json"): void => {
    if (!analytics) return;

    const timestamp = new Date().toISOString().split("T")[0];
    const filename = `analytics-${timestamp}.${format === "csv" ? "csv" : "json"}`;

    if (format === "csv") {
      AnalyticsService.exportToCSV(workers, filename);
    } else {
      AnalyticsService.exportToJSON(analytics, filename);
    }
  };

  const completionRate = analytics
    ? (
        (analytics.completedTasks /
          (analytics.completedTasks + analytics.failedTasks)) *
        100
      ).toFixed(2)
    : 0;

  return (
    <div className="analytics-dashboard">
      {/* Header */}
      <div className="analytics-header">
        <div>
          <h1>Analytics & Reporting</h1>
          <p>View system performance and generate custom reports</p>
        </div>
        <div className="header-actions">
          <button
            onClick={() => fetchAnalytics()}
            disabled={loading}
            className="btn btn-primary"
            title="Refresh analytics"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
          <button
            onClick={() => handleExport("csv")}
            disabled={loading || !analytics}
            className="btn btn-secondary"
            title="Export as CSV"
          >
            <Download size={16} />
            CSV
          </button>
          <button
            onClick={() => handleExport("json")}
            disabled={loading || !analytics}
            className="btn btn-secondary"
            title="Export as JSON"
          >
            <Download size={16} />
            JSON
          </button>
        </div>
      </div>

      {/* Date Range Filter */}
      <div className="analytics-filters">
        <div className="filter-group">
          <label htmlFor="start-date">Start Date</label>
          <input
            id="start-date"
            type="date"
            value={dateRange.startDate}
            onChange={(e) =>
              setDateRange((prev) => ({ ...prev, startDate: e.target.value }))
            }
            disabled={loading}
          />
        </div>
        <div className="filter-group">
          <label htmlFor="end-date">End Date</label>
          <input
            id="end-date"
            type="date"
            value={dateRange.endDate}
            onChange={(e) =>
              setDateRange((prev) => ({ ...prev, endDate: e.target.value }))
            }
            disabled={loading}
          />
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <RefreshCw size={32} className="animate-spin" />
          <p>Loading analytics...</p>
        </div>
      ) : analytics ? (
        <>
          {/* Key Metrics */}
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-header">
                <h3>Total Tasks</h3>
                <Zap size={20} className="metric-icon" />
              </div>
              <p className="metric-value">
                {analytics.totalTasks.toLocaleString()}
              </p>
              <p className="metric-label">All tasks processed</p>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <h3>Completion Rate</h3>
                <TrendingUp size={20} className="metric-icon" />
              </div>
              <p className="metric-value">{completionRate}%</p>
              <p className="metric-label">Successfully completed</p>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <h3>Completed Tasks</h3>
                <Zap size={20} className="metric-icon success" />
              </div>
              <p className="metric-value">
                {analytics.completedTasks.toLocaleString()}
              </p>
              <p className="metric-label">Finished successfully</p>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <h3>Failed Tasks</h3>
                <AlertCircle size={20} className="metric-icon danger" />
              </div>
              <p className="metric-value">
                {analytics.failedTasks.toLocaleString()}
              </p>
              <p className="metric-label">Completed with errors</p>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <h3>Avg Completion Time</h3>
                <TrendingUp size={20} className="metric-icon" />
              </div>
              <p className="metric-value">
                {Math.round(analytics.averageCompletionTime)}s
              </p>
              <p className="metric-label">Average task duration</p>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <h3>Active Workers</h3>
                <Users size={20} className="metric-icon" />
              </div>
              <p className="metric-value">{workers.length}</p>
              <p className="metric-label">Workers in system</p>
            </div>
          </div>

          {/* Worker Performance Table */}
          <div className="analytics-section">
            <h2>Worker Performance</h2>
            <div className="table-container">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Worker ID</th>
                    <th>Tasks Completed</th>
                    <th>Success Rate</th>
                    <th>Avg Completion Time</th>
                    <th>Last Active</th>
                  </tr>
                </thead>
                <tbody>
                  {workers.length > 0 ? (
                    workers.map((worker) => (
                      <tr key={worker.workerId}>
                        <td className="worker-id">{worker.workerId}</td>
                        <td>{worker.tasksCompleted}</td>
                        <td>
                          <span
                            className={`success-rate ${worker.successRate >= 95 ? "excellent" : "good"}`}
                          >
                            {(worker.successRate * 100).toFixed(2)}%
                          </span>
                        </td>
                        <td>{Math.round(worker.averageCompletionTime)}s</td>
                        <td>{new Date(worker.lastActive).toLocaleString()}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="empty-state">
                        No worker data available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Task Trends */}
          <div className="analytics-section">
            <h2>Task Trends (Last 30 Days)</h2>
            <div className="trends-container">
              {trends.length > 0 ? (
                <div className="trends-list">
                  {trends.slice(-7).map((point, idx) => (
                    <div key={idx} className="trend-item">
                      <div className="trend-date">
                        {new Date(point.timestamp).toLocaleDateString()}
                      </div>
                      <div className="trend-stats">
                        <span className="trend-stat completed">
                          ✓ {point.completedCount}
                        </span>
                        <span className="trend-stat failed">
                          ✕ {point.failedCount}
                        </span>
                        <span className="trend-stat pending">
                          ⏳ {point.pendingCount}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">No trend data available</div>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="empty-state">No analytics data available</div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
