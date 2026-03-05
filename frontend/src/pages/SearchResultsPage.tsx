import React, { useState, useMemo } from "react";
import {
  Search,
  Filter,
  FileText,
  Server,
  Megaphone,
  Settings,
  ChevronRight,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

/* ═══════════════════════════════ Types ════ */

interface SearchResultItem {
  id: string;
  title: string;
  description: string;
  category: "task" | "worker" | "campaign" | "setting";
  status?: string;
  url: string;
  matchedField: string;
  updatedAt: string;
}

type CategoryFilter = "all" | SearchResultItem["category"];
type SortBy = "relevance" | "date" | "name";

/* ═══════════════════════════════ Mock data  */

const MOCK_RESULTS: SearchResultItem[] = [
  {
    id: "t-4521",
    title: "Bulk Import Job",
    description:
      "Task #4521 — Importing 12,000 records from CSV upload. Assigned to default queue with high priority.",
    category: "task",
    status: "running",
    url: "/tasks",
    matchedField: "title",
    updatedAt: new Date(Date.now() - 120_000).toISOString(),
  },
  {
    id: "t-4520",
    title: "Data Export — Monthly Report",
    description:
      "Task #4520 — Generate and export monthly analytics report. Completed in 2.3 seconds.",
    category: "task",
    status: "completed",
    url: "/tasks",
    matchedField: "title",
    updatedAt: new Date(Date.now() - 600_000).toISOString(),
  },
  {
    id: "t-4518",
    title: "Email Notification Batch",
    description:
      "Task #4518 — Sending 500 notification emails for Q4 campaign. Retry count: 0.",
    category: "task",
    status: "completed",
    url: "/tasks",
    matchedField: "description",
    updatedAt: new Date(Date.now() - 3_600_000).toISOString(),
  },
  {
    id: "w-01",
    title: "worker-node-01",
    description:
      "Active worker processing tasks from default queue. CPU 34%, Memory 62%, 3/10 tasks.",
    category: "worker",
    status: "active",
    url: "/workers",
    matchedField: "title",
    updatedAt: new Date(Date.now() - 30_000).toISOString(),
  },
  {
    id: "w-03",
    title: "worker-node-03",
    description:
      "Active worker processing tasks from reports queue. CPU 67%, Memory 78%, 7/10 tasks.",
    category: "worker",
    status: "active",
    url: "/workers",
    matchedField: "description",
    updatedAt: new Date(Date.now() - 45_000).toISOString(),
  },
  {
    id: "w-07",
    title: "worker-node-07",
    description:
      "Newly joined worker in idle state. CPU 12%, Memory 45%, 0/10 tasks.",
    category: "worker",
    status: "idle",
    url: "/workers",
    matchedField: "title",
    updatedAt: new Date(Date.now() - 900_000).toISOString(),
  },
  {
    id: "c-12",
    title: "Q4 Email Blast",
    description:
      "Completed campaign with 12,450 tasks. Success rate 99.2%. Duration: 45 min.",
    category: "campaign",
    status: "completed",
    url: "/campaigns",
    matchedField: "title",
    updatedAt: new Date(Date.now() - 7_200_000).toISOString(),
  },
  {
    id: "c-13",
    title: "Monthly Report Generation",
    description:
      "Running campaign — 340/500 tasks completed (68%). Estimated completion: 12 min.",
    category: "campaign",
    status: "running",
    url: "/campaigns",
    matchedField: "title",
    updatedAt: new Date(Date.now() - 1_800_000).toISOString(),
  },
  {
    id: "s-jwt",
    title: "JWT Configuration",
    description:
      "Security settings: JWT token expiration, refresh token duration, signing algorithm.",
    category: "setting",
    url: "/settings",
    matchedField: "title",
    updatedAt: new Date(Date.now() - 86_400_000).toISOString(),
  },
  {
    id: "s-pool",
    title: "Connection Pool Settings",
    description:
      "Database connection pool size, max overflow, pool timeout configuration.",
    category: "setting",
    url: "/settings",
    matchedField: "description",
    updatedAt: new Date(Date.now() - 172_800_000).toISOString(),
  },
];

/* ═══════════════════════════════ Helpers ══ */

const categoryMeta: Record<
  SearchResultItem["category"],
  { label: string; icon: React.ReactNode; color: string }
> = {
  task: {
    label: "Tasks",
    icon: <FileText className="w-4 h-4" />,
    color: "bg-primary-100 text-primary-700",
  },
  worker: {
    label: "Workers",
    icon: <Server className="w-4 h-4" />,
    color: "bg-violet-100 text-violet-700",
  },
  campaign: {
    label: "Campaigns",
    icon: <Megaphone className="w-4 h-4" />,
    color: "bg-amber-100 text-amber-700",
  },
  setting: {
    label: "Settings",
    icon: <Settings className="w-4 h-4" />,
    color: "bg-slate-100 text-slate-700",
  },
};

const statusBadge = (status?: string) => {
  if (!status) return null;
  const colors: Record<string, string> = {
    running: "bg-emerald-50 text-emerald-700",
    completed: "bg-primary-50 text-primary-700",
    failed: "bg-red-50 text-red-700",
    active: "bg-emerald-50 text-emerald-700",
    idle: "bg-slate-100 text-slate-600",
  };
  return (
    <span
      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
        colors[status] ?? "bg-slate-100 text-slate-600"
      }`}
    >
      {status}
    </span>
  );
};

const formatDate = (iso: string) =>
  new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });

/* ═══════════════════════════════ Component */

const SearchResultsPage: React.FC = () => {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [sortBy, setSortBy] = useState<SortBy>("relevance");
  const [showFilters, setShowFilters] = useState(true);
  const navigate = useNavigate();

  /* Filter & sort */
  const results = useMemo(() => {
    let items = MOCK_RESULTS;

    if (query.trim()) {
      const q = query.toLowerCase();
      items = items.filter(
        (r) =>
          r.title.toLowerCase().includes(q) ||
          r.description.toLowerCase().includes(q),
      );
    }

    if (category !== "all") {
      items = items.filter((r) => r.category === category);
    }

    switch (sortBy) {
      case "date":
        items = [...items].sort(
          (a, b) =>
            new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
        );
        break;
      case "name":
        items = [...items].sort((a, b) => a.title.localeCompare(b.title));
        break;
    }

    return items;
  }, [query, category, sortBy]);

  /* Facet counts */
  const facetCounts = useMemo(() => {
    const base = query.trim()
      ? MOCK_RESULTS.filter(
          (r) =>
            r.title.toLowerCase().includes(query.toLowerCase()) ||
            r.description.toLowerCase().includes(query.toLowerCase()),
        )
      : MOCK_RESULTS;

    const counts: Record<string, number> = { all: base.length };
    for (const r of base) {
      counts[r.category] = (counts[r.category] || 0) + 1;
    }
    return counts;
  }, [query]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <Search className="w-7 h-7 text-slate-700" />
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Search
          </h1>
        </div>
        <p className="text-sm text-slate-500">
          Find tasks, workers, campaigns, and settings across the system
        </p>
      </div>

      {/* Search bar */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search everything..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-3 border border-slate-200 rounded-xl text-sm
                       focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 outline-none transition-all"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        <button
          onClick={() => setShowFilters((v) => !v)}
          className={`flex items-center gap-2 px-4 py-3 border rounded-xl text-sm font-semibold transition-all ${
            showFilters
              ? "bg-primary-50 border-primary-200 text-primary-700"
              : "border-slate-200 text-slate-600 hover:bg-slate-50"
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filters
        </button>
      </div>

      <div className="flex gap-6">
        {/* Facet sidebar */}
        {showFilters && (
          <div className="w-56 flex-shrink-0 space-y-6">
            {/* Category filter */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Category
              </h3>
              <ul className="space-y-1">
                {(
                  [
                    "all",
                    "task",
                    "worker",
                    "campaign",
                    "setting",
                  ] as CategoryFilter[]
                ).map((cat) => (
                  <li key={cat}>
                    <button
                      onClick={() => setCategory(cat)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-sm transition-colors ${
                        category === cat
                          ? "bg-primary-50 text-primary-700 font-semibold"
                          : "text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        {cat === "all" ? (
                          <Filter className="w-3.5 h-3.5" />
                        ) : (
                          categoryMeta[cat].icon
                        )}
                        {cat === "all" ? "All" : categoryMeta[cat].label}
                      </span>
                      <span className="text-xs text-slate-400">
                        {facetCounts[cat] ?? 0}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            {/* Sort */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Sort By
              </h3>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortBy)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm
                           focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 outline-none transition-all"
              >
                <option value="relevance">Relevance</option>
                <option value="date">Most Recent</option>
                <option value="name">Name A–Z</option>
              </select>
            </div>
          </div>
        )}

        {/* Results */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-slate-600">
              <span className="font-semibold">{results.length}</span> result
              {results.length !== 1 ? "s" : ""}
              {query.trim() && (
                <span>
                  {" "}
                  for "<span className="font-medium">{query}</span>"
                </span>
              )}
            </p>
          </div>

          {results.length === 0 ? (
            <div className="text-center py-16 text-slate-400">
              <Search className="w-10 h-10 mx-auto mb-3 opacity-40" />
              <p className="text-sm">No results found</p>
              <p className="text-xs mt-1">
                Try a different search term or filter
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {results.map((r) => {
                const meta = categoryMeta[r.category];
                return (
                  <div
                    key={r.id}
                    onClick={() => navigate(r.url)}
                    className="flex items-start gap-4 p-4 bg-white border border-slate-200/60
                               rounded-xl hover:shadow-md hover:border-primary-200
                               cursor-pointer transition-all group"
                  >
                    {/* Icon */}
                    <div
                      className={`flex items-center justify-center w-10 h-10 rounded-xl ${meta.color}`}
                    >
                      {meta.icon}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-slate-900 group-hover:text-primary-600 transition-colors">
                          {r.title}
                        </h3>
                        {statusBadge(r.status)}
                      </div>
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                        {r.description}
                      </p>
                      <div className="flex items-center gap-3 mt-2 text-[10px] text-slate-400">
                        <span
                          className={`px-1.5 py-0.5 rounded font-medium ${meta.color}`}
                        >
                          {meta.label}
                        </span>
                        <span>
                          Matched:{" "}
                          <span className="font-medium">{r.matchedField}</span>
                        </span>
                        <span>{formatDate(r.updatedAt)}</span>
                      </div>
                    </div>

                    {/* Arrow */}
                    <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-primary-400 flex-shrink-0 mt-2 transition-colors" />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchResultsPage;
