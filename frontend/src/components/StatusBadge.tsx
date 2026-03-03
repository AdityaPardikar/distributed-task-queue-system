/**
 * StatusBadge – canonical status/priority badge used across all pages.
 * Centralises colour mapping so every table/card renders identically.
 */
import React from "react";

// ────────────────────────────────────────────── task status ──
export type TaskStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "scheduled"
  | "retrying";

const TASK_STATUS_CLASSES: Record<TaskStatus, string> = {
  pending: "bg-yellow-100 text-yellow-800 border border-yellow-200",
  running: "bg-blue-100   text-blue-800   border border-blue-200",
  completed: "bg-green-100  text-green-800  border border-green-200",
  failed: "bg-red-100    text-red-800    border border-red-200",
  cancelled: "bg-gray-100   text-gray-600   border border-gray-200",
  scheduled: "bg-purple-100 text-purple-800 border border-purple-200",
  retrying: "bg-orange-100 text-orange-800 border border-orange-200",
};

// ────────────────────────────────────────── task priority ──
export type TaskPriority = "low" | "medium" | "high" | "critical";

const TASK_PRIORITY_CLASSES: Record<TaskPriority, string> = {
  critical: "bg-red-600    text-white",
  high: "bg-orange-500 text-white",
  medium: "bg-yellow-500 text-white",
  low: "bg-gray-400   text-white",
};

// ────────────────────────────────────────────── worker status ──
export type WorkerStatus = "ACTIVE" | "OFFLINE" | "DRAINING" | "PAUSED";

const WORKER_STATUS_CLASSES: Record<WorkerStatus, string> = {
  ACTIVE: "bg-green-100  text-green-800  border border-green-200",
  DRAINING: "bg-yellow-100 text-yellow-800 border border-yellow-200",
  OFFLINE: "bg-red-100    text-red-800    border border-red-200",
  PAUSED: "bg-gray-200   text-gray-700   border border-gray-200",
};

// ───────────────────────────────────────────────── component ──

interface StatusBadgeProps {
  /** The value to display (will be uppercased) */
  value: string;
  /** Which colour palette to use */
  variant?: "task" | "priority" | "worker";
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  value,
  variant = "task",
  className = "",
}) => {
  const lower = value.toLowerCase();
  let classes = "bg-gray-100 text-gray-600 border border-gray-200"; // fallback

  if (variant === "task") {
    classes = TASK_STATUS_CLASSES[lower as TaskStatus] ?? classes;
  } else if (variant === "priority") {
    classes = TASK_PRIORITY_CLASSES[lower as TaskPriority] ?? classes;
  } else if (variant === "worker") {
    const upper = value.toUpperCase();
    classes = WORKER_STATUS_CLASSES[upper as WorkerStatus] ?? classes;
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${classes} ${className}`}
    >
      {value.toUpperCase()}
    </span>
  );
};

export default StatusBadge;
