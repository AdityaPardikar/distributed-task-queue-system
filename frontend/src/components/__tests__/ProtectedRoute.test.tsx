/**
 * Tests for ProtectedRoute component
 */

import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import ProtectedRoute from "../ProtectedRoute";
import { AuthProvider, useAuth } from "../../context/AuthContext";

// Mock AuthContext
jest.mock("../../context/AuthContext", () => ({
  ...jest.requireActual("../../context/AuthContext"),
  useAuth: jest.fn(),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe("ProtectedRoute", () => {
  it("should show loading spinner when loading", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      loading: true,
      user: null,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      refreshToken: jest.fn(),
      hasRole: jest.fn(),
    });

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </BrowserRouter>,
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("should redirect to login when not authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      loading: false,
      user: null,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      refreshToken: jest.fn(),
      hasRole: jest.fn(),
    });

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </BrowserRouter>,
    );

    // Should redirect (not render protected content)
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it("should render children when authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      loading: false,
      user: {
        user_id: "123",
        username: "testuser",
        email: "test@example.com",
        role: "viewer",
        is_active: true,
        is_superuser: false,
        created_at: new Date().toISOString(),
      },
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      refreshToken: jest.fn(),
      hasRole: jest.fn().mockReturnValue(true),
    });

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </BrowserRouter>,
    );

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });

  it("should show access denied when user lacks required role", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      loading: false,
      user: {
        user_id: "123",
        username: "testuser",
        email: "test@example.com",
        role: "viewer",
        is_active: true,
        is_superuser: false,
        created_at: new Date().toISOString(),
      },
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      refreshToken: jest.fn(),
      hasRole: jest.fn().mockReturnValue(false),
    });

    render(
      <BrowserRouter>
        <ProtectedRoute requiredRole="admin">
          <div>Admin Only Content</div>
        </ProtectedRoute>
      </BrowserRouter>,
    );

    expect(screen.getByText("Access Denied")).toBeInTheDocument();
    expect(screen.queryByText("Admin Only Content")).not.toBeInTheDocument();
  });

  it("should render children when user has required role", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      loading: false,
      user: {
        user_id: "123",
        username: "admin",
        email: "admin@example.com",
        role: "admin",
        is_active: true,
        is_superuser: true,
        created_at: new Date().toISOString(),
      },
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      refreshToken: jest.fn(),
      hasRole: jest.fn().mockReturnValue(true),
    });

    render(
      <BrowserRouter>
        <ProtectedRoute requiredRole="admin">
          <div>Admin Only Content</div>
        </ProtectedRoute>
      </BrowserRouter>,
    );

    expect(screen.getByText("Admin Only Content")).toBeInTheDocument();
  });
});
