import { useState, useEffect, useCallback, useRef } from "react";
import CacheService from "../services/CacheService";
import type { CacheOptions } from "../services/CacheService";

export interface UseCacheOptions<T> extends CacheOptions {
  /** Enable/disable caching */
  enabled?: boolean;
  /** Initial data before fetch */
  initialData?: T;
  /** Refetch on window focus */
  refetchOnFocus?: boolean;
  /** Refetch on network reconnect */
  refetchOnReconnect?: boolean;
  /** Stale time in ms before background refetch */
  staleTime?: number;
  /** Callback on successful fetch */
  onSuccess?: (data: T) => void;
  /** Callback on fetch error */
  onError?: (error: Error) => void;
}

export interface UseCacheReturn<T> {
  data: T | null;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isFetching: boolean;
  isStale: boolean;
  refetch: () => Promise<void>;
  invalidate: () => void;
  setData: (data: T) => void;
}

/**
 * Custom hook for cached data fetching
 * Provides automatic caching, refetching, and invalidation
 */
export function useCache<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: UseCacheOptions<T> = {},
): UseCacheReturn<T> {
  const {
    enabled = true,
    initialData,
    refetchOnFocus = false,
    refetchOnReconnect = true,
    staleTime = 30000, // 30 seconds
    ttl = 5 * 60 * 1000, // 5 minutes
    storage = "memory",
    namespace,
    onSuccess,
    onError,
  } = options;

  const [data, setDataState] = useState<T | null>(() => {
    // Try to get cached data on initial render
    const cached = CacheService.get<T>(key, { storage, namespace });
    return cached ?? initialData ?? null;
  });
  const [isLoading, setIsLoading] = useState(!data);
  const [isFetching, setIsFetching] = useState(false);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isStale, setIsStale] = useState(false);

  const lastFetchTimeRef = useRef<number>(0);
  const isMountedRef = useRef(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  // Cache options
  const cacheOptions: CacheOptions = { ttl, storage, namespace };

  // Fetch data and update cache
  const fetchData = useCallback(
    async (background = false) => {
      if (!enabled) return;

      if (!background) {
        setIsLoading(true);
      }
      setIsFetching(true);
      setIsError(false);
      setError(null);

      try {
        const result = await fetcherRef.current();

        if (isMountedRef.current) {
          setDataState(result);
          CacheService.set(key, result, cacheOptions);
          lastFetchTimeRef.current = Date.now();
          setIsStale(false);
          onSuccess?.(result);
        }
      } catch (err) {
        if (isMountedRef.current) {
          const error =
            err instanceof Error ? err : new Error("Failed to fetch data");
          setIsError(true);
          setError(error);
          onError?.(error);
        }
      } finally {
        if (isMountedRef.current) {
          setIsLoading(false);
          setIsFetching(false);
        }
      }
    },
    [enabled, key, cacheOptions, onSuccess, onError],
  );

  // Refetch function exposed to consumers
  const refetch = useCallback(async () => {
    await fetchData(false);
  }, [fetchData]);

  // Invalidate cache and refetch
  const invalidate = useCallback(() => {
    CacheService.remove(key, cacheOptions);
    fetchData(false);
  }, [key, cacheOptions, fetchData]);

  // Manually set data
  const setData = useCallback(
    (newData: T) => {
      setDataState(newData);
      CacheService.set(key, newData, cacheOptions);
      lastFetchTimeRef.current = Date.now();
      setIsStale(false);
    },
    [key, cacheOptions],
  );

  // Initial fetch on mount
  useEffect(() => {
    isMountedRef.current = true;

    if (enabled) {
      const cached = CacheService.get<T>(key, cacheOptions);
      if (cached) {
        setDataState(cached);
        setIsLoading(false);
        // Check if stale
        // Note: We don't have access to timestamp here, so we'll trigger a background fetch
        fetchData(true);
      } else {
        fetchData(false);
      }
    }

    return () => {
      isMountedRef.current = false;
    };
  }, [enabled, key]);

  // Check for stale data
  useEffect(() => {
    if (!enabled || !data || staleTime <= 0) return;

    const checkStale = () => {
      const isDataStale = Date.now() - lastFetchTimeRef.current > staleTime;
      setIsStale(isDataStale);

      if (isDataStale && !isFetching) {
        fetchData(true);
      }
    };

    const interval = setInterval(checkStale, staleTime / 2);
    return () => clearInterval(interval);
  }, [enabled, data, staleTime, isFetching, fetchData]);

  // Refetch on window focus
  useEffect(() => {
    if (!refetchOnFocus || !enabled) return;

    const handleFocus = () => {
      const isDataStale = Date.now() - lastFetchTimeRef.current > staleTime;
      if (isDataStale) {
        fetchData(true);
      }
    };

    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, [refetchOnFocus, enabled, staleTime, fetchData]);

  // Refetch on network reconnect
  useEffect(() => {
    if (!refetchOnReconnect || !enabled) return;

    const handleOnline = () => {
      fetchData(true);
    };

    window.addEventListener("online", handleOnline);
    return () => window.removeEventListener("online", handleOnline);
  }, [refetchOnReconnect, enabled, fetchData]);

  return {
    data,
    isLoading,
    isError,
    error,
    isFetching,
    isStale,
    refetch,
    invalidate,
    setData,
  };
}

/**
 * Hook for multiple cached queries
 */
export function useCacheMultiple<T extends Record<string, unknown>>(
  queries: {
    key: string;
    fetcher: () => Promise<unknown>;
    options?: UseCacheOptions<unknown>;
  }[],
): {
  data: Partial<T>;
  isLoading: boolean;
  isError: boolean;
  refetchAll: () => Promise<void>;
} {
  const [data, setData] = useState<Partial<T>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  const fetchAll = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);

    try {
      const results = await Promise.all(
        queries.map(async ({ key, fetcher, options }) => {
          const cached = CacheService.get(key, options);
          if (cached !== null) {
            return { key, data: cached };
          }

          const result = await fetcher();
          CacheService.set(key, result, options);
          return { key, data: result };
        }),
      );

      const dataMap = results.reduce(
        (acc, { key, data }) => {
          acc[key] = data;
          return acc;
        },
        {} as Record<string, unknown>,
      );

      setData(dataMap as Partial<T>);
    } catch (error) {
      console.error("useCacheMultiple error:", error);
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  }, [queries]);

  useEffect(() => {
    fetchAll();
  }, []);

  return {
    data,
    isLoading,
    isError,
    refetchAll: fetchAll,
  };
}

export default useCache;
