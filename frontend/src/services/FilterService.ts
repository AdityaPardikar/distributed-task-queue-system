import React, { useCallback } from "react";
import { AdvancedFiltersProps, FilterCriteria } from "../AdvancedFilters";

/**
 * Filter service for managing filter presets
 * Provides methods to save, load, and manage saved filter presets
 */
export class FilterService {
  private static readonly STORAGE_KEY = "task_filter_presets";

  /**
   * Save a filter preset to local storage
   */
  static savePreset(name: string, filters: FilterCriteria): boolean {
    try {
      const presets = this.getAllPresets();
      const exists = presets.some((p) => p.name === name);

      if (exists) {
        const index = presets.findIndex((p) => p.name === name);
        presets[index] = { name, filters };
      } else {
        presets.push({ name, filters });
      }

      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(presets));
      return true;
    } catch (error) {
      console.error("Failed to save preset:", error);
      return false;
    }
  }

  /**
   * Get all saved presets
   */
  static getAllPresets(): Array<{ name: string; filters: FilterCriteria }> {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error("Failed to load presets:", error);
      return [];
    }
  }

  /**
   * Get a preset by name
   */
  static getPreset(name: string): FilterCriteria | null {
    try {
      const presets = this.getAllPresets();
      const preset = presets.find((p) => p.name === name);
      return preset ? preset.filters : null;
    } catch (error) {
      console.error("Failed to get preset:", error);
      return null;
    }
  }

  /**
   * Delete a preset
   */
  static deletePreset(name: string): boolean {
    try {
      const presets = this.getAllPresets();
      const filtered = presets.filter((p) => p.name !== name);
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(filtered));
      return true;
    } catch (error) {
      console.error("Failed to delete preset:", error);
      return false;
    }
  }

  /**
   * Clear all presets
   */
  static clearAllPresets(): boolean {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
      return true;
    } catch (error) {
      console.error("Failed to clear presets:", error);
      return false;
    }
  }
}

/**
 * Hook to manage filter presets
 */
export const useFilterPresets = () => {
  const [presets, setPresets] = React.useState(FilterService.getAllPresets());

  const savePreset = useCallback((name: string, filters: FilterCriteria) => {
    if (FilterService.savePreset(name, filters)) {
      setPresets(FilterService.getAllPresets());
      return true;
    }
    return false;
  }, []);

  const deletePreset = useCallback((name: string) => {
    if (FilterService.deletePreset(name)) {
      setPresets(FilterService.getAllPresets());
      return true;
    }
    return false;
  }, []);

  const loadPreset = useCallback((name: string): FilterCriteria | null => {
    return FilterService.getPreset(name);
  }, []);

  const clearAllPresets = useCallback(() => {
    if (FilterService.clearAllPresets()) {
      setPresets([]);
      return true;
    }
    return false;
  }, []);

  return {
    presets,
    savePreset,
    deletePreset,
    loadPreset,
    clearAllPresets,
  };
};
