/**
 * ChaosEngineeringPanel - Visualize and manage chaos experiments
 * Day 3: Resilience & Fault Tolerance Patterns
 */

import React, { useState, useEffect, useCallback } from "react";

// Types
interface ChaosExperiment {
  experiment_id: string;
  chaos_type: string;
  target_pattern: string;
  probability: number;
  injections_count: number;
  is_active?: boolean;
}

interface DLQItem {
  task_id: string;
  error_message: string;
  failed_at: string;
  retry_count: number;
}

interface RetryDelay {
  attempt: number;
  delay_seconds: number;
}

const CHAOS_TYPES = [
  { value: "latency", label: "Latency Injection", icon: "⏱️", color: "yellow" },
  { value: "error", label: "Error Injection", icon: "❌", color: "red" },
  { value: "timeout", label: "Timeout Injection", icon: "⏰", color: "orange" },
  {
    value: "resource_exhaustion",
    label: "Resource Exhaustion",
    icon: "💾",
    color: "purple",
  },
  {
    value: "network_partition",
    label: "Network Partition",
    icon: "🔌",
    color: "blue",
  },
];

// Status badge component
const StatusBadge: React.FC<{ active: boolean }> = ({ active }) => (
  <span
    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
      active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"
    }`}
  >
    <span
      className={`w-2 h-2 mr-1 rounded-full ${
        active ? "bg-green-500 animate-pulse" : "bg-gray-400"
      }`}
    />
    {active ? "Active" : "Inactive"}
  </span>
);

// Chaos type icon component
const ChaosTypeIcon: React.FC<{ type: string }> = ({ type }) => {
  const chaos = CHAOS_TYPES.find((c) => c.value === type);
  return <span className="text-xl">{chaos?.icon || "🔧"}</span>;
};

// Create experiment form
const CreateExperimentForm: React.FC<{
  onSubmit: (
    experiment: Partial<ChaosExperiment> & { duration_seconds: number },
  ) => void;
  onCancel: () => void;
}> = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    experiment_id: `chaos-${Date.now()}`,
    chaos_type: "latency",
    target_pattern: ".*",
    probability: 0.1,
    duration_seconds: 60,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Experiment ID
        </label>
        <input
          type="text"
          value={formData.experiment_id}
          onChange={(e) =>
            setFormData({ ...formData, experiment_id: e.target.value })
          }
          className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Chaos Type
        </label>
        <select
          value={formData.chaos_type}
          onChange={(e) =>
            setFormData({ ...formData, chaos_type: e.target.value })
          }
          className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500"
        >
          {CHAOS_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.icon} {type.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Target Pattern (Regex)
        </label>
        <input
          type="text"
          value={formData.target_pattern}
          onChange={(e) =>
            setFormData({ ...formData, target_pattern: e.target.value })
          }
          className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 font-mono"
          placeholder="api.*, task_*, etc."
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Probability ({Math.round(formData.probability * 100)}%)
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={formData.probability}
            onChange={(e) =>
              setFormData({
                ...formData,
                probability: parseFloat(e.target.value),
              })
            }
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Duration (seconds)
          </label>
          <input
            type="number"
            min="1"
            max="3600"
            value={formData.duration_seconds}
            onChange={(e) =>
              setFormData({
                ...formData,
                duration_seconds: parseInt(e.target.value),
              })
            }
            className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      <div className="flex gap-2 pt-2">
        <button
          type="submit"
          className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          🚀 Start Experiment
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border rounded-md hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};

// Main ChaosEngineeringPanel component
export const ChaosEngineeringPanel: React.FC = () => {
  const [experiments, setExperiments] = useState<ChaosExperiment[]>([]);
  const [dlqItems, setDlqItems] = useState<DLQItem[]>([]);
  const [retryDelays, setRetryDelays] = useState<RetryDelay[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [activeTab, setActiveTab] = useState<"experiments" | "dlq" | "retry">(
    "experiments",
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch experiments
  const fetchExperiments = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/chaos/experiments");
      if (response.ok) {
        const data = await response.json();
        setExperiments(data.active_experiments || []);
      }
    } catch (err) {
      console.error("Failed to fetch experiments:", err);
    }
  }, []);

  // Fetch DLQ items
  const fetchDLQ = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/chaos/dlq");
      if (response.ok) {
        const data = await response.json();
        setDlqItems(data.items || []);
      }
    } catch (err) {
      console.error("Failed to fetch DLQ:", err);
    }
  }, []);

  // Fetch retry configuration
  const fetchRetryConfig = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/chaos/retry/test");
      if (response.ok) {
        const data = await response.json();
        setRetryDelays(data.delays || []);
      }
    } catch (err) {
      console.error("Failed to fetch retry config:", err);
    }
  }, []);

  // Create experiment
  const createExperiment = async (
    experiment: Partial<ChaosExperiment> & { duration_seconds: number },
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/v1/chaos/experiments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(experiment),
      });

      if (response.ok) {
        setShowCreateForm(false);
        fetchExperiments();
      } else {
        const data = await response.json();
        setError(data.detail || "Failed to create experiment");
      }
    } catch (err) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  // Stop experiment
  const stopExperiment = async (experimentId: string) => {
    try {
      const response = await fetch(
        `/api/v1/chaos/experiments/${experimentId}`,
        {
          method: "DELETE",
        },
      );

      if (response.ok) {
        fetchExperiments();
      }
    } catch (err) {
      console.error("Failed to stop experiment:", err);
    }
  };

  // Requeue DLQ item
  const requeueItem = async (taskId: string) => {
    try {
      const response = await fetch(`/api/v1/chaos/dlq/${taskId}/requeue`, {
        method: "POST",
      });

      if (response.ok) {
        fetchDLQ();
      }
    } catch (err) {
      console.error("Failed to requeue item:", err);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchExperiments();
    fetchDLQ();
    fetchRetryConfig();

    // Poll for updates
    const interval = setInterval(() => {
      if (activeTab === "experiments") fetchExperiments();
      if (activeTab === "dlq") fetchDLQ();
    }, 5000);

    return () => clearInterval(interval);
  }, [activeTab, fetchExperiments, fetchDLQ, fetchRetryConfig]);

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold flex items-center gap-2">
              🔬 Chaos Engineering
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Test system resilience with controlled fault injection
            </p>
          </div>
          {!showCreateForm && (
            <button
              onClick={() => setShowCreateForm(true)}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors flex items-center gap-2"
            >
              <span>🧪</span> New Experiment
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex -mb-px">
          {[
            { id: "experiments", label: "Experiments", icon: "🧪" },
            { id: "dlq", label: "Dead Letter Queue", icon: "📪" },
            { id: "retry", label: "Retry Policy", icon: "🔄" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Error message */}
      {error && (
        <div className="px-6 py-3 bg-red-50 border-b border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Content */}
      <div className="p-6">
        {/* Loading indicator */}
        {loading && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-2">
            <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" />
            <span className="text-blue-700 text-sm">Processing...</span>
          </div>
        )}

        {/* Create form */}
        {showCreateForm && (
          <div className="mb-6 p-4 border rounded-lg bg-gray-50">
            <h3 className="font-semibold mb-4">Create New Experiment</h3>
            <CreateExperimentForm
              onSubmit={createExperiment}
              onCancel={() => setShowCreateForm(false)}
            />
          </div>
        )}

        {/* Experiments tab */}
        {activeTab === "experiments" && (
          <div className="space-y-4">
            {experiments.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-2">🧪</div>
                <p>No active experiments</p>
                <p className="text-sm">
                  Create an experiment to test system resilience
                </p>
              </div>
            ) : (
              <div className="grid gap-4">
                {experiments.map((exp) => (
                  <div
                    key={exp.experiment_id}
                    className="border rounded-lg p-4 hover:border-indigo-200 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <ChaosTypeIcon type={exp.chaos_type} />
                        <div>
                          <div className="font-medium">{exp.experiment_id}</div>
                          <div className="text-sm text-gray-500">
                            {
                              CHAOS_TYPES.find(
                                (c) => c.value === exp.chaos_type,
                              )?.label
                            }
                          </div>
                        </div>
                      </div>
                      <StatusBadge active={true} />
                    </div>

                    <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Target: </span>
                        <code className="bg-gray-100 px-1 rounded">
                          {exp.target_pattern}
                        </code>
                      </div>
                      <div>
                        <span className="text-gray-500">Probability: </span>
                        <span className="font-medium">
                          {Math.round(exp.probability * 100)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Injections: </span>
                        <span className="font-medium">
                          {exp.injections_count}
                        </span>
                      </div>
                    </div>

                    <div className="mt-3 flex gap-2">
                      <button
                        onClick={() => stopExperiment(exp.experiment_id)}
                        className="px-3 py-1 text-sm border border-red-300 text-red-600 rounded hover:bg-red-50 transition-colors"
                      >
                        Stop Experiment
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Dead Letter Queue tab */}
        {activeTab === "dlq" && (
          <div className="space-y-4">
            {dlqItems.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-2">📪</div>
                <p>Dead letter queue is empty</p>
                <p className="text-sm">Failed tasks will appear here</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Task ID
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Error
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Retries
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Failed At
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {dlqItems.map((item) => (
                      <tr key={item.task_id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-mono">
                          {item.task_id}
                        </td>
                        <td className="px-4 py-3 text-sm text-red-600 max-w-xs truncate">
                          {item.error_message}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {item.retry_count}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {new Date(item.failed_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => requeueItem(item.task_id)}
                            className="text-indigo-600 hover:text-indigo-800 text-sm"
                          >
                            Requeue
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Retry Policy tab */}
        {activeTab === "retry" && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold mb-3">Retry Configuration</h3>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Max Retries</dt>
                    <dd className="font-medium">5</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Base Delay</dt>
                    <dd className="font-medium">1.0s</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Max Delay</dt>
                    <dd className="font-medium">60.0s</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Exponential Base</dt>
                    <dd className="font-medium">2.0</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Jitter</dt>
                    <dd className="font-medium">Enabled</dd>
                  </div>
                </dl>
              </div>

              <div className="border rounded-lg p-4">
                <h3 className="font-semibold mb-3">
                  Retry Delays (Exponential Backoff)
                </h3>
                <div className="space-y-2">
                  {retryDelays.map((delay) => (
                    <div
                      key={delay.attempt}
                      className="flex items-center gap-2"
                    >
                      <span className="text-sm text-gray-500 w-20">
                        Attempt {delay.attempt}
                      </span>
                      <div className="flex-1">
                        <div
                          className="h-4 bg-indigo-500 rounded"
                          style={{
                            width: `${Math.min(100, (delay.delay_seconds / 60) * 100)}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm font-mono w-16 text-right">
                        {delay.delay_seconds.toFixed(1)}s
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="border rounded-lg p-4 bg-yellow-50">
              <h4 className="font-medium text-yellow-800 mb-2">
                ⚠️ About Exponential Backoff
              </h4>
              <p className="text-sm text-yellow-700">
                Retry delays increase exponentially with jitter to prevent
                thundering herd. Each retry waits longer than the previous,
                giving the system time to recover. After max retries, tasks are
                moved to the Dead Letter Queue for manual review.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChaosEngineeringPanel;
