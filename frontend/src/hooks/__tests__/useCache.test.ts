import { renderHook, act, waitFor } from "@testing-library/react";
import { useCache, useCacheMultiple } from "../useCache";
import CacheService from "../../services/CacheService";

// Mock CacheService
jest.mock("../../services/CacheService", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    set: jest.fn(),
    remove: jest.fn(),
    has: jest.fn(),
    clearNamespace: jest.fn(),
  },
}));

describe("useCache", () => {
  const mockFetcher = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockFetcher.mockReset();
    (CacheService.get as jest.Mock).mockReturnValue(null);
  });

  describe("Basic Functionality", () => {
    it("should fetch and cache data on mount", async () => {
      mockFetcher.mockResolvedValue({ id: 1, name: "Test" });

      const { result } = renderHook(() =>
        useCache("test-key", mockFetcher)
      );

      // Initially loading
      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual({ id: 1, name: "Test" });
      expect(mockFetcher).toHaveBeenCalledTimes(1);
      expect(CacheService.set).toHaveBeenCalledWith(
        "test-key",
        { id: 1, name: "Test" },
        expect.any(Object)
      );
    });

    it("should use cached data if available", async () => {
      const cachedData = { id: 1, name: "Cached" };
      (CacheService.get as jest.Mock).mockReturnValue(cachedData);
      mockFetcher.mockResolvedValue({ id: 1, name: "Fresh" });

      const { result } = renderHook(() =>
        useCache("cached-key", mockFetcher)
      );

      // Should have cached data immediately
      expect(result.current.data).toEqual(cachedData);
      expect(result.current.isLoading).toBe(false);
    });

    it("should handle fetch errors", async () => {
      mockFetcher.mockRejectedValue(new Error("Fetch failed"));

      const { result } = renderHook(() =>
        useCache("error-key", mockFetcher)
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toBe("Fetch failed");
      expect(result.current.data).toBeNull();
    });

    it("should provide refetch function", async () => {
      mockFetcher
        .mockResolvedValueOnce({ count: 1 })
        .mockResolvedValueOnce({ count: 2 });

      const { result } = renderHook(() =>
        useCache("refetch-key", mockFetcher)
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual({ count: 1 });

      // Trigger refetch
      await act(async () => {
        await result.current.refetch();
      });

      expect(result.current.data).toEqual({ count: 2 });
      expect(mockFetcher).toHaveBeenCalledTimes(2);
    });
  });

  describe("Options", () => {
    it("should not fetch when enabled is false", async () => {
      mockFetcher.mockResolvedValue("data");

      const { result } = renderHook(() =>
        useCache("disabled-key", mockFetcher, { enabled: false })
      );

      // Wait a bit to ensure no fetch happens
      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(mockFetcher).not.toHaveBeenCalled();
      expect(result.current.isLoading).toBe(true); // Still loading since never fetched
    });

    it("should use initialData when provided", async () => {
      mockFetcher.mockResolvedValue("fetched");

      const { result } = renderHook(() =>
        useCache("initial-key", mockFetcher, {
          initialData: "initial",
        })
      );

      expect(result.current.data).toBe("initial");
    });

    it("should call onSuccess callback on successful fetch", async () => {
      const onSuccess = jest.fn();
      mockFetcher.mockResolvedValue("success-data");

      renderHook(() =>
        useCache("success-key", mockFetcher, { onSuccess })
      );

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith("success-data");
      });
    });

    it("should call onError callback on fetch error", async () => {
      const onError = jest.fn();
      mockFetcher.mockRejectedValue(new Error("Error"));

      renderHook(() =>
        useCache("error-callback-key", mockFetcher, { onError })
      );

      await waitFor(() => {
        expect(onError).toHaveBeenCalled();
      });
    });
  });

  describe("Invalidation", () => {
    it("should invalidate cache and refetch", async () => {
      mockFetcher
        .mockResolvedValueOnce("original")
        .mockResolvedValueOnce("updated");

      const { result } = renderHook(() =>
        useCache("invalidate-key", mockFetcher)
      );

      await waitFor(() => {
        expect(result.current.data).toBe("original");
      });

      // Invalidate
      await act(async () => {
        result.current.invalidate();
      });

      await waitFor(() => {
        expect(result.current.data).toBe("updated");
      });

      expect(CacheService.remove).toHaveBeenCalledWith(
        "invalidate-key",
        expect.any(Object)
      );
    });
  });

  describe("setData", () => {
    it("should manually set data and update cache", async () => {
      mockFetcher.mockResolvedValue("fetched");

      const { result } = renderHook(() =>
        useCache("setdata-key", mockFetcher)
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.setData("manual-data");
      });

      expect(result.current.data).toBe("manual-data");
      expect(CacheService.set).toHaveBeenLastCalledWith(
        "setdata-key",
        "manual-data",
        expect.any(Object)
      );
    });
  });

  describe("Fetching States", () => {
    it("should track isFetching state correctly", async () => {
      let resolvePromise: (value: string) => void;
      const promise = new Promise<string>((resolve) => {
        resolvePromise = resolve;
      });
      mockFetcher.mockReturnValue(promise);

      const { result } = renderHook(() =>
        useCache("fetching-key", mockFetcher)
      );

      expect(result.current.isFetching).toBe(true);

      await act(async () => {
        resolvePromise!("data");
        await promise;
      });

      await waitFor(() => {
        expect(result.current.isFetching).toBe(false);
      });
    });
  });
});

describe("useCacheMultiple", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (CacheService.get as jest.Mock).mockReturnValue(null);
  });

  it("should fetch multiple keys", async () => {
    const usersFetcher = jest.fn().mockResolvedValue(["user1", "user2"]);
    const tasksFetcher = jest.fn().mockResolvedValue(["task1"]);

    const { result } = renderHook(() =>
      useCacheMultiple([
        { key: "users", fetcher: usersFetcher },
        { key: "tasks", fetcher: tasksFetcher },
      ])
    );

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data.users).toEqual(["user1", "user2"]);
    expect(result.current.data.tasks).toEqual(["task1"]);
    expect(usersFetcher).toHaveBeenCalledTimes(1);
    expect(tasksFetcher).toHaveBeenCalledTimes(1);
  });

  it("should handle errors in any request", async () => {
    const successFetcher = jest.fn().mockResolvedValue("ok");
    const failureFetcher = jest.fn().mockRejectedValue(new Error("Failed"));

    const { result } = renderHook(() =>
      useCacheMultiple([
        { key: "success", fetcher: successFetcher },
        { key: "failure", fetcher: failureFetcher },
      ])
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // When any request fails, isError should be true
    expect(result.current.isError).toBe(true);
  });
});
