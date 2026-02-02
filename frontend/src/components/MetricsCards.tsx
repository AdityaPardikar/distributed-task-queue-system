import React from "react";
import { CheckCircle2, Clock, AlertCircle, Users, Layers } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: "blue" | "green" | "yellow" | "red" | "purple" | "indigo";
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  color,
  trend,
}) => {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    yellow: "bg-yellow-50 text-yellow-600",
    red: "bg-red-50 text-red-600",
    purple: "bg-purple-50 text-purple-600",
    indigo: "bg-indigo-50 text-indigo-600",
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        {trend && (
          <div
            className={`text-sm font-semibold ${trend.isPositive ? "text-green-600" : "text-red-600"}`}
          >
            {trend.isPositive ? "+" : ""}
            {trend.value}%
          </div>
        )}
      </div>
      <div>
        <p className="text-sm text-gray-500 font-medium mb-1">{title}</p>
        <h3 className="text-3xl font-bold text-gray-900">{value}</h3>
        {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
};

interface MetricsCardsProps {
  metrics: {
    totalTasks: number;
    activeWorkers: number;
    queueSize: number;
    successRate: number;
    pendingTasks: number;
    runningTasks: number;
    completedTasks: number;
    failedTasks: number;
  };
}

const MetricsCards: React.FC<MetricsCardsProps> = ({ metrics }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="Total Tasks"
        value={metrics.totalTasks.toLocaleString()}
        subtitle={`${metrics.pendingTasks} pending, ${metrics.runningTasks} running`}
        icon={<Layers size={24} />}
        color="blue"
      />

      <MetricCard
        title="Active Workers"
        value={metrics.activeWorkers}
        subtitle="Currently processing"
        icon={<Users size={24} />}
        color="green"
      />

      <MetricCard
        title="Queue Size"
        value={metrics.queueSize.toLocaleString()}
        subtitle="Tasks waiting"
        icon={<Clock size={24} />}
        color={metrics.queueSize > 100 ? "yellow" : "indigo"}
      />

      <MetricCard
        title="Success Rate"
        value={`${metrics.successRate.toFixed(1)}%`}
        subtitle={`${metrics.completedTasks} completed, ${metrics.failedTasks} failed`}
        icon={
          metrics.successRate >= 90 ? (
            <CheckCircle2 size={24} />
          ) : (
            <AlertCircle size={24} />
          )
        }
        color={
          metrics.successRate >= 90
            ? "green"
            : metrics.successRate >= 75
              ? "yellow"
              : "red"
        }
        trend={{
          value: 2.5,
          isPositive: true,
        }}
      />
    </div>
  );
};

export default MetricsCards;
