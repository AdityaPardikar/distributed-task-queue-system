import React, { useCallback, useState } from "react";
import { ChevronDown } from "lucide-react";
import "../styles/advanced-filters.css";

export interface FilterCriteria {
  statuses: string[];
  priorities: string[];
  startDate?: string;
  endDate?: string;
  workerId?: string;
  searchQuery: string;
  sortBy: "name" | "date" | "duration" | "status";
  sortOrder: "asc" | "desc";
}

export interface AdvancedFiltersProps {
  onFilterChange: (filters: FilterCriteria) => void;
  onSavePreset?: (name: string, filters: FilterCriteria) => void;
  savedPresets?: Array<{ name: string; filters: FilterCriteria }>;
  loading?: boolean;
}

const STATUS_OPTIONS = ["pending", "running", "completed", "failed"];
const PRIORITY_OPTIONS = ["low", "medium", "high", "critical"];
const SORT_OPTIONS = ["name", "date", "duration", "status"] as const;

/**
 * Advanced Filters component for multi-criteria filtering and search
 * Supports status, priority, date range, worker filters, and sorting
 */
const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  onFilterChange,
  onSavePreset,
  savedPresets = [],
  loading = false,
}) => {
  const [filters, setFilters] = useState<FilterCriteria>({
    statuses: [],
    priorities: [],
    searchQuery: "",
    sortBy: "date",
    sortOrder: "desc",
  });

  const [isExpanded, setIsExpanded] = useState(false);
  const [presetName, setPresetName] = useState("");
  const [showPresetInput, setShowPresetInput] = useState(false);

  const handleStatusChange = useCallback(
    (status: string) => {
      setFilters((prev) => {
        const newStatuses = prev.statuses.includes(status)
          ? prev.statuses.filter((s) => s !== status)
          : [...prev.statuses, status];

        const updated = { ...prev, statuses: newStatuses };
        onFilterChange(updated);
        return updated;
      });
    },
    [onFilterChange],
  );

  const handlePriorityChange = useCallback(
    (priority: string) => {
      setFilters((prev) => {
        const newPriorities = prev.priorities.includes(priority)
          ? prev.priorities.filter((p) => p !== priority)
          : [...prev.priorities, priority];

        const updated = { ...prev, priorities: newPriorities };
        onFilterChange(updated);
        return updated;
      });
    },
    [onFilterChange],
  );

  const handleSearchChange = useCallback(
    (query: string) => {
      setFilters((prev) => {
        const updated = { ...prev, searchQuery: query };
        onFilterChange(updated);
        return updated;
      });
    },
    [onFilterChange],
  );

  const handleDateChange = useCallback(
    (type: "startDate" | "endDate", value: string) => {
      setFilters((prev) => {
        const updated = { ...prev, [type]: value };
        onFilterChange(updated);
        return updated;
      });
    },
    [onFilterChange],
  );

  const handleWorkerIdChange = useCallback(
    (workerId: string) => {
      setFilters((prev) => {
        const updated = { ...prev, workerId: workerId || undefined };
        onFilterChange(updated);
        return updated;
      });
    },
    [onFilterChange],
  );

  const handleSortChange = useCallback(
    (sortBy: FilterCriteria["sortBy"]) => {
      setFilters((prev) => {
        const updated = { ...prev, sortBy };
        onFilterChange(updated);
        return updated;
      });
    },
    [onFilterChange],
  );

  const handleSortOrderChange = useCallback(
    (sortOrder: "asc" | "desc") => {
      setFilters((prev) => {
        const updated = { ...prev, sortOrder };
        onFilterChange(updated);
        return updated;
      });
    },
    [onFilterChange],
  );

  const handleSavePreset = useCallback(() => {
    if (presetName.trim() && onSavePreset) {
      onSavePreset(presetName, filters);
      setPresetName("");
      setShowPresetInput(false);
    }
  }, [presetName, filters, onSavePreset]);

  const handleLoadPreset = useCallback(
    (preset: { name: string; filters: FilterCriteria }) => {
      setFilters(preset.filters);
      onFilterChange(preset.filters);
    },
    [onFilterChange],
  );

  const handleClearFilters = useCallback(() => {
    const cleared: FilterCriteria = {
      statuses: [],
      priorities: [],
      searchQuery: "",
      sortBy: "date",
      sortOrder: "desc",
    };
    setFilters(cleared);
    onFilterChange(cleared);
  }, [onFilterChange]);

  const activeFilterCount =
    filters.statuses.length +
    filters.priorities.length +
    (filters.startDate ? 1 : 0) +
    (filters.endDate ? 1 : 0) +
    (filters.workerId ? 1 : 0) +
    (filters.searchQuery ? 1 : 0);

  return (
    <div className="advanced-filters">
      <div className="filters-header">
        <div className="search-container">
          <input
            type="text"
            placeholder="Search by task name, ID, or description..."
            value={filters.searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            disabled={loading}
            className="search-input"
            aria-label="Search tasks"
          />
        </div>

        <button
          className={`expand-button ${isExpanded ? "expanded" : ""}`}
          onClick={() => setIsExpanded(!isExpanded)}
          disabled={loading}
          aria-label="Toggle advanced filters"
        >
          <ChevronDown size={20} />
          Advanced Filters{" "}
          {activeFilterCount > 0 && (
            <span className="badge">{activeFilterCount}</span>
          )}
        </button>
      </div>

      {isExpanded && (
        <div className="filters-panel">
          <div className="filter-group">
            <label className="group-label">Status</label>
            <div className="checkbox-group">
              {STATUS_OPTIONS.map((status) => (
                <label key={status} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={filters.statuses.includes(status)}
                    onChange={() => handleStatusChange(status)}
                    disabled={loading}
                    className="checkbox-input"
                  />
                  <span className="checkbox-text">{status}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="filter-group">
            <label className="group-label">Priority</label>
            <div className="checkbox-group">
              {PRIORITY_OPTIONS.map((priority) => (
                <label key={priority} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={filters.priorities.includes(priority)}
                    onChange={() => handlePriorityChange(priority)}
                    disabled={loading}
                    className="checkbox-input"
                  />
                  <span className="checkbox-text">{priority}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="filter-group">
            <label className="group-label">Date Range</label>
            <div className="date-inputs">
              <input
                type="date"
                value={filters.startDate || ""}
                onChange={(e) => handleDateChange("startDate", e.target.value)}
                disabled={loading}
                className="date-input"
                aria-label="Start date"
              />
              <span className="date-separator">to</span>
              <input
                type="date"
                value={filters.endDate || ""}
                onChange={(e) => handleDateChange("endDate", e.target.value)}
                disabled={loading}
                className="date-input"
                aria-label="End date"
              />
            </div>
          </div>

          <div className="filter-group">
            <label className="group-label">Worker ID</label>
            <input
              type="text"
              placeholder="Filter by worker ID..."
              value={filters.workerId || ""}
              onChange={(e) => handleWorkerIdChange(e.target.value)}
              disabled={loading}
              className="text-input"
              aria-label="Worker ID filter"
            />
          </div>

          <div className="filter-group">
            <label className="group-label">Sort By</label>
            <div className="sort-controls">
              <select
                value={filters.sortBy}
                onChange={(e) =>
                  handleSortChange(e.target.value as FilterCriteria["sortBy"])
                }
                disabled={loading}
                className="sort-select"
                aria-label="Sort field"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option.charAt(0).toUpperCase() + option.slice(1)}
                  </option>
                ))}
              </select>

              <select
                value={filters.sortOrder}
                onChange={(e) =>
                  handleSortOrderChange(e.target.value as "asc" | "desc")
                }
                disabled={loading}
                className="sort-select"
                aria-label="Sort order"
              >
                <option value="asc">Ascending</option>
                <option value="desc">Descending</option>
              </select>
            </div>
          </div>

          {savedPresets.length > 0 && (
            <div className="filter-group">
              <label className="group-label">Load Preset</label>
              <div className="preset-buttons">
                {savedPresets.map((preset) => (
                  <button
                    key={preset.name}
                    className="preset-button"
                    onClick={() => handleLoadPreset(preset)}
                    disabled={loading}
                    title={`Load preset: ${preset.name}`}
                  >
                    {preset.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="filter-actions">
            <button
              className="save-preset-button"
              onClick={() => setShowPresetInput(!showPresetInput)}
              disabled={loading}
            >
              Save as Preset
            </button>

            <button
              className="clear-button"
              onClick={handleClearFilters}
              disabled={loading}
            >
              Clear All
            </button>
          </div>

          {showPresetInput && (
            <div className="preset-input-group">
              <input
                type="text"
                placeholder="Preset name..."
                value={presetName}
                onChange={(e) => setPresetName(e.target.value)}
                disabled={loading}
                className="preset-input"
                aria-label="Preset name"
              />
              <button
                onClick={handleSavePreset}
                disabled={loading}
                className="preset-save"
              >
                Save
              </button>
              <button
                onClick={() => {
                  setShowPresetInput(false);
                  setPresetName("");
                }}
                disabled={loading}
                className="preset-cancel"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdvancedFilters;
