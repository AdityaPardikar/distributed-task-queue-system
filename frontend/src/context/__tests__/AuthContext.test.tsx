/**
 * Tests for AuthContext
 */

import { renderHook, act, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "../AuthContext";

// Mock fetch
(globalThis as { fetch?: typeof fetch }).fetch = jest.fn();

const mockFetch = globalThis.fetch as jest.MockedFunction<typeof fetch>;

describe("AuthContext", () => {
  beforeEach(() => {
    // Clear localStorage
    localStorage.clear();
    // Reset fetch mock
    mockFetch.mockReset();
  });

  it("should initialize with unauthenticated state", () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it("should login successfully", async () => {
    const mockUser = {
      user_id: "123",
      username: "testuser",
      email: "test@example.com",
      role: "viewer" as const,
      is_active: true,
      is_superuser: false,
      created_at: new Date().toISOString(),
    };

    // Mock login response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: "mock-access-token",
        refresh_token: "mock-refresh-token",
        token_type: "bearer",
      }),
    } as Response);

    // Mock /me response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    } as Response);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await act(async () => {
      await result.current.login("testuser", "password123");
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(localStorage.getItem("access_token")).toBe("mock-access-token");
      expect(localStorage.getItem("refresh_token")).toBe("mock-refresh-token");
    });
  });

  it("should handle login failure", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Invalid credentials" }),
    } as Response);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await expect(
      result.current.login("testuser", "wrongpassword"),
    ).rejects.toThrow("Invalid credentials");

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it("should register successfully", async () => {
    const mockUser = {
      user_id: "123",
      username: "newuser",
      email: "new@example.com",
      role: "viewer" as const,
      is_active: true,
      is_superuser: false,
      created_at: new Date().toISOString(),
    };

    // Mock register response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => mockUser,
    } as Response);

    // Mock login response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: "mock-access-token",
        refresh_token: "mock-refresh-token",
        token_type: "bearer",
      }),
    } as Response);

    // Mock /me response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    } as Response);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await act(async () => {
      await result.current.register(
        "newuser",
        "new@example.com",
        "password123",
      );
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user?.username).toBe("newuser");
    });
  });

  it("should handle register failure", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Username already exists" }),
    } as Response);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await expect(
      result.current.register(
        "existinguser",
        "existing@example.com",
        "password123",
      ),
    ).rejects.toThrow("Username already exists");

    expect(result.current.isAuthenticated).toBe(false);
  });

  it("should logout successfully", async () => {
    const mockUser = {
      user_id: "123",
      username: "testuser",
      email: "test@example.com",
      role: "viewer" as const,
      is_active: true,
      is_superuser: false,
      created_at: new Date().toISOString(),
    };

    // Setup authenticated state via session restore
    localStorage.setItem("access_token", "mock-access-token");
    localStorage.setItem("refresh_token", "mock-refresh-token");

    // Mock /me response for session restore
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    } as Response);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    // Wait for session to be restored
    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("access_token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
  });

  it("should refresh token successfully", async () => {
    localStorage.setItem("refresh_token", "mock-refresh-token");

    // Mock refresh response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: "new-access-token",
        refresh_token: "new-refresh-token",
        token_type: "bearer",
      }),
    } as Response);

    // Mock /me response after refresh
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        user_id: "123",
        username: "testuser",
        email: "test@example.com",
        role: "viewer",
        is_active: true,
        is_superuser: false,
        created_at: new Date().toISOString(),
      }),
    } as Response);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await act(async () => {
      await result.current.refreshToken();
    });

    expect(localStorage.getItem("access_token")).toBe("new-access-token");
  });

  it("should handle refresh token failure", async () => {
    localStorage.setItem("refresh_token", "invalid-token");

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Invalid refresh token" }),
    } as Response);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await expect(result.current.refreshToken()).rejects.toThrow(
      "Token refresh failed",
    );
  });

  it("should check role permissions correctly", async () => {
    // Test admin role
    localStorage.setItem("access_token", "mock-token");
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        user_id: "1",
        username: "admin",
        email: "admin@example.com",
        role: "admin",
        is_active: true,
        is_superuser: true,
        created_at: new Date().toISOString(),
      }),
    } as Response);

    const { result: adminResult } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(adminResult.current.user).not.toBeNull();
    });

    expect(adminResult.current.hasRole("admin")).toBe(true);
    expect(adminResult.current.hasRole("operator")).toBe(true);
    expect(adminResult.current.hasRole("viewer")).toBe(true);

    // Test operator role
    localStorage.clear();
    localStorage.setItem("access_token", "mock-token");
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        user_id: "2",
        username: "operator",
        email: "op@example.com",
        role: "operator",
        is_active: true,
        is_superuser: false,
        created_at: new Date().toISOString(),
      }),
    } as Response);

    const { result: opResult } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(opResult.current.user).not.toBeNull();
    });

    expect(opResult.current.hasRole("admin")).toBe(false);
    expect(opResult.current.hasRole("operator")).toBe(true);
    expect(opResult.current.hasRole("viewer")).toBe(true);

    // Test viewer role
    localStorage.clear();
    localStorage.setItem("access_token", "mock-token");
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        user_id: "3",
        username: "viewer",
        email: "viewer@example.com",
        role: "viewer",
        is_active: true,
        is_superuser: false,
        created_at: new Date().toISOString(),
      }),
    } as Response);

    const { result: viewerResult } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(viewerResult.current.user).not.toBeNull();
    });

    expect(viewerResult.current.hasRole("admin")).toBe(false);
    expect(viewerResult.current.hasRole("operator")).toBe(false);
    expect(viewerResult.current.hasRole("viewer")).toBe(true);
  });

  it("should restore session from localStorage on mount", async () => {
    const mockUser = {
      user_id: "123",
      username: "testuser",
      email: "test@example.com",
      role: "viewer" as const,
      is_active: true,
      is_superuser: false,
      created_at: new Date().toISOString(),
    };

    localStorage.setItem("access_token", "existing-token");
    localStorage.setItem("refresh_token", "existing-refresh-token");

    // Mock /me response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    } as Response);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });
  });

  it("should handle invalid stored token on mount", async () => {
    localStorage.setItem("access_token", "invalid-token");

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Invalid token" }),
    } as Response);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(localStorage.getItem("access_token")).toBeNull();
    });
  });
});
