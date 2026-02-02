import React from "react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { ChartDataPoint } from "../types/dashboard";

interface ChartsSectionProps {
  queueDepthData: ChartDataPoint[];
  completionRateData: ChartDataPoint[];
}

const ChartsSection: React.FC<ChartsSectionProps> = ({
  queueDepthData,
  completionRateData,
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Queue Depth Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">Task Queue Depth</h3>
          <span className="text-sm text-gray-500">Last 24 hours</span>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={queueDepthData}>
            <defs>
              <linearGradient id="colorQueue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="time"
              stroke="#6B7280"
              style={{ fontSize: "12px" }}
            />
            <YAxis stroke="#6B7280" style={{ fontSize: "12px" }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#FFF",
                border: "1px solid #E5E7EB",
                borderRadius: "8px",
                padding: "8px 12px",
              }}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#3B82F6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorQueue)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Completion Rate Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">
            Task Completion Rate
          </h3>
          <span className="text-sm text-gray-500">Hourly</span>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={completionRateData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="time"
              stroke="#6B7280"
              style={{ fontSize: "12px" }}
            />
            <YAxis stroke="#6B7280" style={{ fontSize: "12px" }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#FFF",
                border: "1px solid #E5E7EB",
                borderRadius: "8px",
                padding: "8px 12px",
              }}
            />
            <Bar
              dataKey="value"
              fill="#10B981"
              radius={[8, 8, 0, 0]}
              maxBarSize={60}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Task Status Over Time */}
      <div className="bg-white rounded-lg shadow-md p-6 lg:col-span-2">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">
            Task Status Timeline
          </h3>
          <div className="flex gap-2">
            <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors">
              1H
            </button>
            <button className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
              24H
            </button>
            <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors">
              7D
            </button>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={queueDepthData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="time"
              stroke="#6B7280"
              style={{ fontSize: "12px" }}
            />
            <YAxis stroke="#6B7280" style={{ fontSize: "12px" }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#FFF",
                border: "1px solid #E5E7EB",
                borderRadius: "8px",
                padding: "8px 12px",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "14px", paddingTop: "20px" }} />
            <Line
              type="monotone"
              dataKey="value"
              name="Pending"
              stroke="#F59E0B"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="value"
              name="Running"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="value"
              name="Completed"
              stroke="#10B981"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="value"
              name="Failed"
              stroke="#EF4444"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ChartsSection;
