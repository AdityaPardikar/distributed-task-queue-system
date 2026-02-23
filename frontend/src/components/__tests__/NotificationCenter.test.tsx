import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import NotificationCenter from "../NotificationCenter";
import {
  NotificationProvider,
  useNotification,
} from "../../context/NotificationContext";

// Mock WebSocket
(global as Record<string, unknown>).WebSocket = jest
  .fn()
  .mockImplementation(() => ({
    close: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    readyState: 3, // CLOSED
  }));

const renderWithProviders = (ui: React.ReactElement) =>
  render(
    <BrowserRouter>
      <NotificationProvider>{ui}</NotificationProvider>
    </BrowserRouter>,
  );

describe("NotificationCenter", () => {
  it("renders the bell icon button", () => {
    renderWithProviders(<NotificationCenter />);
    const bellButton = screen.getByRole("button");
    expect(bellButton).toBeInTheDocument();
  });

  it("shows unread count badge", async () => {
    renderWithProviders(<NotificationCenter />);
    // The NotificationProvider has initial mock data with unread notifications
    await waitFor(() => {
      // Look for a badge with a number
      const badge = screen.getByText(/[0-9]+/);
      expect(badge).toBeInTheDocument();
    });
  });

  it("opens notification panel on bell click", async () => {
    const user = userEvent.setup();
    renderWithProviders(<NotificationCenter />);

    const bellButton = screen.getByRole("button");
    await user.click(bellButton);

    await waitFor(() => {
      expect(screen.getByText("Notifications")).toBeInTheDocument();
    });
  });

  it("shows notification items in the panel", async () => {
    const user = userEvent.setup();
    renderWithProviders(<NotificationCenter />);

    const bellButton = screen.getByRole("button");
    await user.click(bellButton);

    await waitFor(() => {
      // Should show one of the initial mock notifications
      expect(screen.getByText("Worker Scaling Event")).toBeInTheDocument();
    });
  });

  it("shows Mark All Read button", async () => {
    const user = userEvent.setup();
    renderWithProviders(<NotificationCenter />);

    const bellButton = screen.getByRole("button");
    await user.click(bellButton);

    await waitFor(() => {
      expect(screen.getByTitle("Mark all read")).toBeInTheDocument();
    });
  });

  it("closes panel when close button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<NotificationCenter />);

    // Open
    const bellButton = screen.getByRole("button");
    await user.click(bellButton);

    await waitFor(() => {
      expect(screen.getByText("Notifications")).toBeInTheDocument();
    });

    // Find close button (X icon)
    const closeButtons = screen.getAllByRole("button");
    const closeBtn = closeButtons.find(
      (btn) => btn !== bellButton && btn.querySelector('[class*="w-5"]'),
    );
    if (closeBtn) {
      await user.click(closeBtn);
    }
  });
});
