import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bell,
  X,
  Check,
  CheckCheck,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Info,
  XCircle,
  Server,
  Activity,
  Shield,
  Megaphone,
} from "lucide-react";
import { useNotification } from "../context/NotificationContext";
import type { PersistentNotification } from "../context/NotificationContext";

/* ═══════════════════════════════ Helpers ══ */

const timeAgo = (ts: number): string => {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
};

const typeIcon = (type: PersistentNotification["type"]) => {
  switch (type) {
    case "success":
      return <CheckCircle2 className="w-4 h-4 text-green-500" />;
    case "error":
      return <XCircle className="w-4 h-4 text-red-500" />;
    case "warning":
      return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    default:
      return <Info className="w-4 h-4 text-blue-500" />;
  }
};

const categoryIcon = (cat: PersistentNotification["category"]) => {
  switch (cat) {
    case "worker":
      return <Server className="w-3.5 h-3.5" />;
    case "alert":
      return <AlertTriangle className="w-3.5 h-3.5" />;
    case "system":
      return <Shield className="w-3.5 h-3.5" />;
    case "campaign":
      return <Megaphone className="w-3.5 h-3.5" />;
    default:
      return <Activity className="w-3.5 h-3.5" />;
  }
};

type FilterCategory = "all" | PersistentNotification["category"];

/* ═══════════════════════════════ Component */

const NotificationCenter: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState<FilterCategory>("all");
  const panelRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const {
    persistent,
    unreadCount,
    markRead,
    markAllRead,
    removePersistent,
    clearPersistent,
  } = useNotification();

  /* Close on outside click */
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  /* Close on Escape */
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    if (open) document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  const filtered =
    filter === "all"
      ? persistent
      : persistent.filter((n) => n.category === filter);

  const CATEGORIES: { id: FilterCategory; label: string }[] = [
    { id: "all", label: "All" },
    { id: "task", label: "Tasks" },
    { id: "worker", label: "Workers" },
    { id: "alert", label: "Alerts" },
    { id: "system", label: "System" },
    { id: "campaign", label: "Campaigns" },
  ];

  const handleClick = (n: PersistentNotification) => {
    markRead(n.id);
    if (n.actionUrl) {
      navigate(n.actionUrl);
      setOpen(false);
    }
  };

  return (
    <div className="relative" ref={panelRef}>
      {/* Bell trigger */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        aria-label="Notifications"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 flex items-center justify-center
                       min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-white
                       bg-red-500 rounded-full"
          >
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Slide-out panel */}
      {open && (
        <div
          className="absolute right-0 top-12 w-[400px] max-h-[calc(100vh-80px)]
                     bg-white rounded-xl shadow-2xl border border-gray-200
                     flex flex-col z-50 animate-in fade-in slide-in-from-top-2"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">Notifications</h3>
            <div className="flex items-center gap-1">
              {unreadCount > 0 && (
                <button
                  onClick={markAllRead}
                  className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="Mark all read"
                >
                  <CheckCheck className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={clearPersistent}
                className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                title="Clear all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => setOpen(false)}
                className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Category filter */}
          <div className="flex gap-1 px-4 py-2 border-b border-gray-100 overflow-x-auto">
            {CATEGORIES.map((c) => (
              <button
                key={c.id}
                onClick={() => setFilter(c.id)}
                className={`px-2.5 py-1 text-xs font-medium rounded-full whitespace-nowrap transition-colors ${
                  filter === c.id
                    ? "bg-blue-100 text-blue-700"
                    : "text-gray-500 hover:bg-gray-100"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>

          {/* Notification list */}
          <div className="flex-1 overflow-y-auto">
            {filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                <Bell className="w-8 h-8 mb-2 opacity-40" />
                <p className="text-sm">No notifications</p>
              </div>
            ) : (
              <ul>
                {filtered.map((n) => (
                  <li
                    key={n.id}
                    className={`flex items-start gap-3 px-4 py-3 border-b border-gray-50
                                cursor-pointer hover:bg-gray-50 transition-colors ${
                                  !n.read ? "bg-blue-50/40" : ""
                                }`}
                    onClick={() => handleClick(n)}
                  >
                    {/* Icon */}
                    <div className="flex-shrink-0 mt-0.5">
                      {typeIcon(n.type)}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-sm font-medium ${
                            n.read ? "text-gray-700" : "text-gray-900"
                          }`}
                        >
                          {n.title}
                        </span>
                        {!n.read && (
                          <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                        {n.message}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="flex items-center gap-1 text-[10px] text-gray-400 uppercase tracking-wide">
                          {categoryIcon(n.category)}
                          {n.category}
                        </span>
                        <span className="text-[10px] text-gray-400">
                          {timeAgo(n.timestamp)}
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-1 flex-shrink-0">
                      {!n.read && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            markRead(n.id);
                          }}
                          className="p-1 text-gray-400 hover:text-blue-600 rounded transition-colors"
                          title="Mark read"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removePersistent(n.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-500 rounded transition-colors"
                        title="Remove"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;
