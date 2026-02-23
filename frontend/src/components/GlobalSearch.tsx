import React, { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  X,
  FileText,
  Server,
  Megaphone,
  BarChart3,
  Settings,
  Bell,
  GitBranch,
  ArrowRight,
  Command,
} from "lucide-react";

/* ═══════════════════════════════ Types ════ */

interface SearchResult {
  id: string;
  title: string;
  subtitle: string;
  category: "task" | "worker" | "campaign" | "page" | "setting";
  url: string;
  icon: React.ReactNode;
}

/* ═══════════════════════════════ Mock data  */

const ALL_RESULTS: SearchResult[] = [
  /* Pages */
  {
    id: "p-1",
    title: "Dashboard",
    subtitle: "Main overview dashboard",
    category: "page",
    url: "/dashboard",
    icon: <BarChart3 className="w-4 h-4" />,
  },
  {
    id: "p-2",
    title: "Tasks",
    subtitle: "Task management and queue",
    category: "page",
    url: "/tasks",
    icon: <FileText className="w-4 h-4" />,
  },
  {
    id: "p-3",
    title: "Workers",
    subtitle: "Worker management and monitoring",
    category: "page",
    url: "/workers",
    icon: <Server className="w-4 h-4" />,
  },
  {
    id: "p-4",
    title: "Monitoring",
    subtitle: "System metrics and performance",
    category: "page",
    url: "/monitoring",
    icon: <BarChart3 className="w-4 h-4" />,
  },
  {
    id: "p-5",
    title: "Campaigns",
    subtitle: "Campaign management",
    category: "page",
    url: "/campaigns",
    icon: <Megaphone className="w-4 h-4" />,
  },
  {
    id: "p-6",
    title: "Workflows",
    subtitle: "DAG workflow visualization",
    category: "page",
    url: "/workflows",
    icon: <GitBranch className="w-4 h-4" />,
  },
  {
    id: "p-7",
    title: "Alerts",
    subtitle: "Alert management and rules",
    category: "page",
    url: "/alerts",
    icon: <Bell className="w-4 h-4" />,
  },
  {
    id: "p-8",
    title: "Settings",
    subtitle: "Application configuration",
    category: "page",
    url: "/settings",
    icon: <Settings className="w-4 h-4" />,
  },
  {
    id: "p-9",
    title: "Analytics",
    subtitle: "Task analytics dashboard",
    category: "page",
    url: "/analytics",
    icon: <BarChart3 className="w-4 h-4" />,
  },

  /* Mock tasks */
  {
    id: "t-4521",
    title: "Task #4521 — Bulk Import",
    subtitle: "Status: running · Queue: default · Priority: high",
    category: "task",
    url: "/tasks",
    icon: <FileText className="w-4 h-4" />,
  },
  {
    id: "t-4520",
    title: "Task #4520 — Data Export",
    subtitle: "Status: completed · Queue: reports · Duration: 2.3s",
    category: "task",
    url: "/tasks",
    icon: <FileText className="w-4 h-4" />,
  },
  {
    id: "t-4519",
    title: "Task #4519 — Email Send",
    subtitle: "Status: completed · Queue: notifications · Duration: 0.8s",
    category: "task",
    url: "/tasks",
    icon: <FileText className="w-4 h-4" />,
  },

  /* Mock workers */
  {
    id: "w-01",
    title: "worker-node-01",
    subtitle: "Status: active · CPU: 34% · Tasks: 3/10",
    category: "worker",
    url: "/workers",
    icon: <Server className="w-4 h-4" />,
  },
  {
    id: "w-03",
    title: "worker-node-03",
    subtitle: "Status: active · CPU: 67% · Tasks: 7/10",
    category: "worker",
    url: "/workers",
    icon: <Server className="w-4 h-4" />,
  },
  {
    id: "w-07",
    title: "worker-node-07",
    subtitle: "Status: idle · CPU: 12% · Tasks: 0/10",
    category: "worker",
    url: "/workers",
    icon: <Server className="w-4 h-4" />,
  },

  /* Mock campaigns */
  {
    id: "c-12",
    title: "Q4 Email Blast",
    subtitle: "Status: completed · 12,450 tasks · 99.2% success",
    category: "campaign",
    url: "/campaigns",
    icon: <Megaphone className="w-4 h-4" />,
  },
  {
    id: "c-13",
    title: "Monthly Report Generation",
    subtitle: "Status: running · 340/500 tasks · 68% complete",
    category: "campaign",
    url: "/campaigns",
    icon: <Megaphone className="w-4 h-4" />,
  },

  /* Settings */
  {
    id: "s-1",
    title: "General Settings",
    subtitle: "App name, environment, log level, timeouts",
    category: "setting",
    url: "/settings",
    icon: <Settings className="w-4 h-4" />,
  },
  {
    id: "s-2",
    title: "Worker Settings",
    subtitle: "Max workers, heartbeat, auto-scale, memory limits",
    category: "setting",
    url: "/settings",
    icon: <Settings className="w-4 h-4" />,
  },
  {
    id: "s-3",
    title: "Security Settings",
    subtitle: "JWT, rate limiting, CORS, HTTPS",
    category: "setting",
    url: "/settings",
    icon: <Settings className="w-4 h-4" />,
  },
];

const CATEGORY_LABELS: Record<string, string> = {
  page: "Pages",
  task: "Tasks",
  worker: "Workers",
  campaign: "Campaigns",
  setting: "Settings",
};

const CATEGORY_ORDER = ["page", "task", "worker", "campaign", "setting"];

/* ═══════════════════════════════ Component */

interface GlobalSearchProps {
  isOpen: boolean;
  onClose: () => void;
}

const GlobalSearch: React.FC<GlobalSearchProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState("");
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  /* Filter results */
  const results = query.trim()
    ? ALL_RESULTS.filter(
        (r) =>
          r.title.toLowerCase().includes(query.toLowerCase()) ||
          r.subtitle.toLowerCase().includes(query.toLowerCase()),
      )
    : ALL_RESULTS.filter((r) => r.category === "page"); // Show pages by default

  /* Group by category */
  const grouped = CATEGORY_ORDER.reduce<Record<string, SearchResult[]>>(
    (acc, cat) => {
      const items = results.filter((r) => r.category === cat);
      if (items.length > 0) acc[cat] = items;
      return acc;
    },
    {},
  );

  const flatResults = Object.values(grouped).flat();

  /* Reset on open */
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  /* Reset index on query change */
  useEffect(() => {
    setSelectedIdx(0);
  }, [query]);

  /* Scroll selected into view */
  useEffect(() => {
    const el = listRef.current?.querySelector(`[data-idx="${selectedIdx}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [selectedIdx]);

  /* Navigate to result */
  const go = useCallback(
    (r: SearchResult) => {
      navigate(r.url);
      onClose();
    },
    [navigate, onClose],
  );

  /* Keyboard navigation */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIdx((i) => Math.min(i + 1, flatResults.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIdx((i) => Math.max(i - 1, 0));
        break;
      case "Enter":
        e.preventDefault();
        if (flatResults[selectedIdx]) go(flatResults[selectedIdx]);
        break;
      case "Escape":
        onClose();
        break;
    }
  };

  if (!isOpen) return null;

  let flatIdx = 0;

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      {/* Palette */}
      <div
        className="w-full max-w-xl bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200">
          <Search className="w-5 h-5 text-gray-400 flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search tasks, workers, campaigns, pages..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 text-sm text-gray-800 placeholder-gray-400
                       bg-transparent outline-none"
          />
          <kbd className="hidden md:inline-flex items-center gap-1 px-2 py-0.5 text-[10px] text-gray-400 bg-gray-100 rounded border border-gray-200 font-mono">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div ref={listRef} className="max-h-[50vh] overflow-y-auto py-2">
          {flatResults.length === 0 ? (
            <div className="py-8 text-center text-sm text-gray-400">
              No results for "{query}"
            </div>
          ) : (
            Object.entries(grouped).map(([cat, items]) => (
              <div key={cat}>
                <div className="px-4 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                  {CATEGORY_LABELS[cat] ?? cat}
                </div>
                {items.map((r) => {
                  const idx = flatIdx++;
                  return (
                    <button
                      key={r.id}
                      data-idx={idx}
                      onClick={() => go(r)}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                        idx === selectedIdx
                          ? "bg-blue-50 text-blue-700"
                          : "text-gray-700 hover:bg-gray-50"
                      }`}
                    >
                      <span
                        className={`flex-shrink-0 ${
                          idx === selectedIdx
                            ? "text-blue-500"
                            : "text-gray-400"
                        }`}
                      >
                        {r.icon}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {r.title}
                        </p>
                        <p className="text-xs text-gray-400 truncate">
                          {r.subtitle}
                        </p>
                      </div>
                      {idx === selectedIdx && (
                        <ArrowRight className="w-4 h-4 flex-shrink-0 text-blue-400" />
                      )}
                    </button>
                  );
                })}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100 bg-gray-50 text-[10px] text-gray-400">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-white border border-gray-200 rounded font-mono">
                ↑↓
              </kbd>
              navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-white border border-gray-200 rounded font-mono">
                ↵
              </kbd>
              open
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-white border border-gray-200 rounded font-mono">
                esc
              </kbd>
              close
            </span>
          </div>
          <span className="flex items-center gap-1">
            <Command className="w-3 h-3" />K to toggle
          </span>
        </div>
      </div>
    </div>
  );
};

export default GlobalSearch;
