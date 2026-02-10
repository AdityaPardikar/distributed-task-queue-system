import React, { useState, useEffect } from "react";
import { Trash2, Plus, Download, Calendar } from "lucide-react";
import AnalyticsService from "../services/AnalyticsService";
import type { ReportConfig } from "../services/AnalyticsService";
import "../styles/report-builder.css";

interface SavedReport {
  id: string;
  name: string;
  type: "task" | "worker" | "health" | "custom";
  createdAt: string;
}

const ReportBuilder: React.FC = () => {
  const [reportConfig, setReportConfig] = useState<ReportConfig>({
    name: "",
    type: "task",
    dateRange: {
      startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0],
      endDate: new Date().toISOString().split("T")[0],
    },
    metrics: [],
  });

  const [savedReports, setSavedReports] = useState<SavedReport[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedReports, setExpandedReports] = useState<string[]>([]);

  const metrics = {
    task: [
      "completion_rate",
      "average_duration",
      "failure_rate",
      "queue_depth",
    ],
    worker: ["tasks_completed", "success_rate", "availability", "efficiency"],
    health: ["system_uptime", "error_rate", "latency", "throughput"],
    custom: ["all_metrics"],
  };

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const reports = await AnalyticsService.listReports();
      setSavedReports(reports as SavedReport[]);
    } catch (error) {
      console.error("Failed to load reports:", error);
    }
  };

  const handleMetricToggle = (metric: string) => {
    setReportConfig((prev) => ({
      ...prev,
      metrics: prev.metrics.includes(metric)
        ? prev.metrics.filter((m) => m !== metric)
        : [...prev.metrics, metric],
    }));
  };

  const handleGenerateReport = async () => {
    if (!reportConfig.name.trim()) {
      alert("Please enter a report name");
      return;
    }

    try {
      setLoading(true);
      const reportId = await AnalyticsService.generateReport(reportConfig);
      alert(`Report generated successfully! ID: ${reportId}`);
      loadReports();
      // Reset form
      setReportConfig({
        name: "",
        type: "task",
        dateRange: {
          startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
            .toISOString()
            .split("T")[0],
          endDate: new Date().toISOString().split("T")[0],
        },
        metrics: [],
      });
    } catch (error) {
      alert("Failed to generate report. Please try again.");
      console.error("Report generation error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteReport = async (reportId: string) => {
    if (window.confirm("Are you sure you want to delete this report?")) {
      try {
        setLoading(true);
        await AnalyticsService.deleteReport(reportId);
        loadReports();
      } catch (error) {
        alert("Failed to delete report");
        console.error("Delete error:", error);
      } finally {
        setLoading(false);
      }
    }
  };

  const toggleReportExpanded = (reportId: string) => {
    setExpandedReports((prev) =>
      prev.includes(reportId)
        ? prev.filter((id) => id !== reportId)
        : [...prev, reportId],
    );
  };

  const availableMetrics =
    metrics[reportConfig.type as keyof typeof metrics] || [];

  return (
    <div className="report-builder">
      <div className="builder-container">
        {/* Report Configuration Form */}
        <div className="config-panel">
          <h2>Create New Report</h2>

          <div className="form-group">
            <label htmlFor="report-name">Report Name</label>
            <input
              id="report-name"
              type="text"
              placeholder="e.g., Monthly Performance Report"
              value={reportConfig.name}
              onChange={(e) =>
                setReportConfig((prev) => ({ ...prev, name: e.target.value }))
              }
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="report-type">Report Type</label>
            <select
              id="report-type"
              value={reportConfig.type}
              onChange={(e) =>
                setReportConfig((prev) => ({
                  ...prev,
                  type: e.target.value as
                    | "task"
                    | "worker"
                    | "health"
                    | "custom",
                  metrics: [],
                }))
              }
              disabled={loading}
            >
              <option value="task">Task Performance</option>
              <option value="worker">Worker Efficiency</option>
              <option value="health">System Health</option>
              <option value="custom">Custom Report</option>
            </select>
          </div>

          <div className="date-range-group">
            <div className="form-group">
              <label htmlFor="start-date">Start Date</label>
              <div className="date-input-wrapper">
                <Calendar size={16} />
                <input
                  id="start-date"
                  type="date"
                  value={reportConfig.dateRange.startDate}
                  onChange={(e) =>
                    setReportConfig((prev) => ({
                      ...prev,
                      dateRange: {
                        ...prev.dateRange,
                        startDate: e.target.value,
                      },
                    }))
                  }
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="end-date">End Date</label>
              <div className="date-input-wrapper">
                <Calendar size={16} />
                <input
                  id="end-date"
                  type="date"
                  value={reportConfig.dateRange.endDate}
                  onChange={(e) =>
                    setReportConfig((prev) => ({
                      ...prev,
                      dateRange: { ...prev.dateRange, endDate: e.target.value },
                    }))
                  }
                  disabled={loading}
                />
              </div>
            </div>
          </div>

          <div className="metrics-selection">
            <h4>Select Metrics</h4>
            <div className="metrics-grid">
              {availableMetrics.map((metric) => (
                <label key={metric} className="metric-checkbox">
                  <input
                    type="checkbox"
                    checked={reportConfig.metrics.includes(metric)}
                    onChange={() => handleMetricToggle(metric)}
                    disabled={loading}
                  />
                  <span>{metric.replace(/_/g, " ").toUpperCase()}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerateReport}
            disabled={loading}
            className="btn btn-primary generate-btn"
          >
            <Plus size={16} />
            Generate Report
          </button>
        </div>

        {/* Saved Reports */}
        <div className="reports-panel">
          <h2>Saved Reports ({savedReports.length})</h2>

          {savedReports.length > 0 ? (
            <div className="reports-list">
              {savedReports.map((report) => (
                <div key={report.id} className="report-item">
                  <div
                    className="report-header"
                    onClick={() => toggleReportExpanded(report.id)}
                    role="button"
                    tabIndex={0}
                  >
                    <div className="report-info">
                      <h4>{report.name}</h4>
                      <span className="report-type">{report.type}</span>
                    </div>
                    <div className="report-date">
                      {new Date(report.createdAt).toLocaleDateString()}
                    </div>
                  </div>

                  {expandedReports.includes(report.id) && (
                    <div className="report-actions">
                      <button
                        className="btn btn-sm btn-secondary"
                        disabled={loading}
                        title="Download report"
                      >
                        <Download size={14} />
                        Download
                      </button>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDeleteReport(report.id)}
                        disabled={loading}
                        title="Delete report"
                      >
                        <Trash2 size={14} />
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p>No saved reports yet. Create one to get started!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportBuilder;
