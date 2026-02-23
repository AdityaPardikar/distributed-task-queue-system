import React from "react";
import {
  Activity,
  Play,
  CheckCircle2,
  XCircle,
  UserPlus,
  Zap,
  Wrench,
  AlertTriangle,
  Rocket,
  Clock,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useNotification } from "../context/NotificationContext";
import type { ActivityEvent } from "../context/NotificationContext";

/* ═══════════════════════════════ Helpers ══ */

const timeAgo = (ts: number): string => {
  const diff = Date.now() - ts;
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
};

const eventIcon = (e: ActivityEvent) => {
  const map: Record<string, React.ReactNode> = {
    created: <Play className="w-3.5 h-3.5 text-blue-500" />,
    completed: <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />,
    failed: <XCircle className="w-3.5 h-3.5 text-red-500" />,
    joined: <UserPlus className="w-3.5 h-3.5 text-indigo-500" />,
    launched: <Rocket className="w-3.5 h-3.5 text-purple-500" />,
    triggered: <AlertTriangle className="w-3.5 h-3.5 text-yellow-500" />,
    maintenance: <Wrench className="w-3.5 h-3.5 text-gray-500" />,
    scaled: <Zap className="w-3.5 h-3.5 text-orange-500" />,
    timeout: <Clock className="w-3.5 h-3.5 text-amber-500" />,
  };
  return map[e.action] ?? <Activity className="w-3.5 h-3.5 text-gray-400" />;
};

const entityColor = (entity: string): string => {
  const map: Record<string, string> = {
    task: "bg-blue-100 text-blue-800",
    worker: "bg-indigo-100 text-indigo-800",
    campaign: "bg-purple-100 text-purple-800",
    alert: "bg-yellow-100 text-yellow-800",
    maintenance: "bg-gray-100 text-gray-800",
    system: "bg-teal-100 text-teal-800",
  };
  return map[entity] ?? "bg-gray-100 text-gray-700";
};

/* ═══════════════════════════════ Component */

interface ActivityFeedProps {
  /** Max events to display */
  limit?: number;
  /** Compact mode (no details, smaller) */
  compact?: boolean;
}

const ActivityFeed: React.FC<ActivityFeedProps> = ({
  limit = 20,
  compact = false,
}) => {
  const { activities, clearActivities, wsConnected } = useNotification();

  const visible = activities.slice(0, limit);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-gray-600" />
          <h3 className="text-sm font-semibold text-gray-800">Activity Feed</h3>
          <span className="text-xs text-gray-400">
            ({activities.length} events)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${
              wsConnected
                ? "bg-green-100 text-green-700"
                : "bg-gray-100 text-gray-500"
            }`}
          >
            {wsConnected ? (
              <Wifi className="w-3 h-3" />
            ) : (
              <WifiOff className="w-3 h-3" />
            )}
            {wsConnected ? "Live" : "Offline"}
          </span>
          {activities.length > 0 && (
            <button
              onClick={clearActivities}
              className="text-xs text-gray-400 hover:text-red-500 transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Event list */}
      {visible.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 text-gray-400">
          <Activity className="w-6 h-6 mb-2 opacity-40" />
          <p className="text-sm">No recent activity</p>
        </div>
      ) : (
        <ul className={compact ? "" : "divide-y divide-gray-50"}>
          {visible.map((event) => (
            <li
              key={event.id}
              className={`flex items-start gap-3 px-4 hover:bg-gray-50 transition-colors ${
                compact ? "py-2" : "py-3"
              }`}
            >
              {/* Timeline dot */}
              <div className="flex-shrink-0 mt-1">{eventIcon(event)}</div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p
                  className={`text-gray-800 ${compact ? "text-xs" : "text-sm"}`}
                >
                  <span className="font-medium">{event.actor}</span>
                  <span className="text-gray-500"> {event.action} </span>
                  <span
                    className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${entityColor(
                      event.entity,
                    )}`}
                  >
                    {event.entity}
                  </span>
                  {event.entityId && (
                    <span className="text-gray-400 text-xs ml-1">
                      {event.entityId}
                    </span>
                  )}
                </p>
                {!compact && event.details && (
                  <p className="text-xs text-gray-500 mt-0.5">
                    {event.details}
                  </p>
                )}
              </div>

              {/* Timestamp */}
              <span
                className={`flex-shrink-0 text-gray-400 tabular-nums ${
                  compact ? "text-[10px]" : "text-xs"
                }`}
              >
                {timeAgo(event.timestamp)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ActivityFeed;
