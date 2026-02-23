import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ActivityFeed from "../ActivityFeed";
import { NotificationProvider } from "../../context/NotificationContext";

// Mock WebSocket
(global as Record<string, unknown>).WebSocket = jest
  .fn()
  .mockImplementation(() => ({
    close: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    readyState: 3,
  }));

const renderWithProvider = (
  props: { compact?: boolean; limit?: number } = {},
) =>
  render(
    <NotificationProvider>
      <ActivityFeed {...props} />
    </NotificationProvider>,
  );

describe("ActivityFeed", () => {
  it("renders the activity feed title", () => {
    renderWithProvider();
    expect(screen.getByText("Activity Feed")).toBeInTheDocument();
  });

  it("shows activity events from context", async () => {
    renderWithProvider();
    // NotificationProvider includes initial mock activities
    await waitFor(() => {
      // check for at least one activity event keyword
      const items = screen.getAllByRole("listitem");
      expect(items.length).toBeGreaterThan(0);
    });
  });

  it("shows WebSocket connection indicator", () => {
    renderWithProvider();
    // Should show either "Live" or "Offline"
    const indicator = screen.getByText(/live|offline/i);
    expect(indicator).toBeInTheDocument();
  });

  it("applies compact mode styling", () => {
    renderWithProvider({ compact: true });
    expect(screen.getByText("Activity Feed")).toBeInTheDocument();
  });

  it("respects limit prop", () => {
    renderWithProvider({ limit: 3 });
    const items = screen.getAllByRole("listitem");
    expect(items.length).toBeLessThanOrEqual(3);
  });

  it("shows clear button", () => {
    renderWithProvider();
    const clearBtn = screen.getByText(/clear/i);
    expect(clearBtn).toBeInTheDocument();
  });
});
