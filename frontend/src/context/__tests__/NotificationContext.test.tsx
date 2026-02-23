import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
    readyState: 3,
  }));

// Test component that uses the notification context
const TestNotificationComponent = () => {
  const {
    showNotification,
    notifications,
    removeNotification,
    clearNotifications,
  } = useNotification();

  return (
    <div>
      <button onClick={() => showNotification("Success message", "success")}>
        Show Success
      </button>
      <button onClick={() => showNotification("Error message", "error")}>
        Show Error
      </button>
      <button onClick={() => showNotification("Warning message", "warning")}>
        Show Warning
      </button>
      <button onClick={() => showNotification("Info message", "info")}>
        Show Info
      </button>
      <button onClick={() => clearNotifications()}>Clear All</button>

      <div data-testid="notification-count">{notifications.length}</div>
      {notifications.map((n) => (
        <div key={n.id} data-testid={`notification-${n.type}`}>
          {n.message}
          <button onClick={() => removeNotification(n.id)}>Close</button>
        </div>
      ))}
    </div>
  );
};

// Test component for persistent notification features
const TestPersistentComponent = () => {
  const {
    persistent,
    unreadCount,
    addPersistent,
    markRead,
    markAllRead,
    removePersistent,
    clearPersistent,
    activities,
    addActivity,
    clearActivities,
    wsConnected,
  } = useNotification();

  return (
    <div>
      <div data-testid="unread-count">{unreadCount}</div>
      <div data-testid="persistent-count">{persistent.length}</div>
      <div data-testid="activity-count">{activities.length}</div>
      <div data-testid="ws-connected">{wsConnected ? "yes" : "no"}</div>

      <button
        onClick={() =>
          addPersistent({
            title: "Test Persistent",
            message: "Test persistent notification",
            type: "info",
            category: "system",
          })
        }
      >
        Add Persistent
      </button>
      <button onClick={markAllRead}>Mark All Read</button>
      <button onClick={clearPersistent}>Clear Persistent</button>

      <button
        onClick={() =>
          addActivity({
            action: "created",
            entity: "task",
            actor: "test-user",
            details: "Test activity event",
          })
        }
      >
        Add Activity
      </button>
      <button onClick={clearActivities}>Clear Activities</button>

      {persistent.map((p) => (
        <div key={p.id} data-testid={`persistent-${p.id}`}>
          {p.title} ({p.read ? "read" : "unread"})
          <button onClick={() => markRead(p.id)}>Mark Read</button>
          <button onClick={() => removePersistent(p.id)}>Remove</button>
        </div>
      ))}

      {activities.map((a) => (
        <div key={a.id} data-testid={`activity-${a.id}`}>
          {a.action} {a.entity}
        </div>
      ))}
    </div>
  );
};

describe("NotificationContext", () => {
  test("should provide notification context to children", () => {
    render(
      <NotificationProvider>
        <TestNotificationComponent />
      </NotificationProvider>,
    );

    expect(screen.getByText("Show Success")).toBeInTheDocument();
  });

  test("should show success notification", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestNotificationComponent />
      </NotificationProvider>,
    );

    const showButton = screen.getByText("Show Success");
    await user.click(showButton);

    await waitFor(() => {
      expect(screen.getByText("Success message")).toBeInTheDocument();
    });
  });

  test("should show error notification", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestNotificationComponent />
      </NotificationProvider>,
    );

    const showButton = screen.getByText("Show Error");
    await user.click(showButton);

    await waitFor(() => {
      expect(screen.getByText("Error message")).toBeInTheDocument();
    });
  });

  test("should show warning notification", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestNotificationComponent />
      </NotificationProvider>,
    );

    const showButton = screen.getByText("Show Warning");
    await user.click(showButton);

    await waitFor(() => {
      expect(screen.getByText("Warning message")).toBeInTheDocument();
    });
  });

  test("should show info notification", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestNotificationComponent />
      </NotificationProvider>,
    );

    const showButton = screen.getByText("Show Info");
    await user.click(showButton);

    await waitFor(() => {
      expect(screen.getByText("Info message")).toBeInTheDocument();
    });
  });

  test("should display multiple notifications", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestNotificationComponent />
      </NotificationProvider>,
    );

    await user.click(screen.getByText("Show Success"));
    await user.click(screen.getByText("Show Error"));

    await waitFor(() => {
      expect(screen.getByText("Success message")).toBeInTheDocument();
      expect(screen.getByText("Error message")).toBeInTheDocument();
    });

    expect(screen.getByTestId("notification-count")).toHaveTextContent("2");
  });

  test("should remove individual notification", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestNotificationComponent />
      </NotificationProvider>,
    );

    await user.click(screen.getByText("Show Success"));

    await waitFor(() => {
      expect(screen.getByText("Success message")).toBeInTheDocument();
    });

    const closeButtons = screen.getAllByText("Close");
    await user.click(closeButtons[0]);

    await waitFor(() => {
      expect(screen.getByTestId("notification-count")).toHaveTextContent("0");
    });
  });

  test("should clear all notifications", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestNotificationComponent />
      </NotificationProvider>,
    );

    await user.click(screen.getByText("Show Success"));
    await user.click(screen.getByText("Show Error"));

    await waitFor(() => {
      expect(screen.getByTestId("notification-count")).toHaveTextContent("2");
    });

    await user.click(screen.getByText("Clear All"));

    await waitFor(() => {
      expect(screen.getByTestId("notification-count")).toHaveTextContent("0");
    });
  });

  test("should throw error when used outside provider", () => {
    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    expect(() => {
      render(<TestNotificationComponent />);
    }).toThrow("useNotification must be used within NotificationProvider");

    consoleErrorSpy.mockRestore();
  });

  test("should auto-remove notification after duration", async () => {
    jest.useFakeTimers();

    render(
      <NotificationProvider>
        <TestNotificationComponent />
      </NotificationProvider>,
    );

    const user = userEvent.setup({ delay: null });
    await user.click(screen.getByText("Show Success"));

    expect(screen.getByTestId("notification-count")).toHaveTextContent("1");

    // Fast-forward time by 5 seconds (default duration)
    jest.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(screen.getByTestId("notification-count")).toHaveTextContent("0");
    });

    jest.useRealTimers();
  });
});

/* ═══════════════════ Persistent & Activity Tests ═══════════════════ */

describe("NotificationContext — Persistent Notifications", () => {
  it("initializes with mock persistent notifications", () => {
    render(
      <NotificationProvider>
        <TestPersistentComponent />
      </NotificationProvider>,
    );
    // Provider seeds 5 initial persistent notifications
    const count = parseInt(
      screen.getByTestId("persistent-count").textContent || "0",
    );
    expect(count).toBeGreaterThan(0);
  });

  it("tracks unread count", () => {
    render(
      <NotificationProvider>
        <TestPersistentComponent />
      </NotificationProvider>,
    );
    const unread = parseInt(
      screen.getByTestId("unread-count").textContent || "0",
    );
    expect(unread).toBeGreaterThan(0);
  });

  it("adds a new persistent notification", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestPersistentComponent />
      </NotificationProvider>,
    );

    const initialCount = parseInt(
      screen.getByTestId("persistent-count").textContent || "0",
    );

    await user.click(screen.getByText("Add Persistent"));

    await waitFor(() => {
      expect(screen.getByText(/Test Persistent/)).toBeInTheDocument();
      const newCount = parseInt(
        screen.getByTestId("persistent-count").textContent || "0",
      );
      expect(newCount).toBe(initialCount + 1);
    });
  });

  it("marks all as read", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestPersistentComponent />
      </NotificationProvider>,
    );

    await user.click(screen.getByText("Mark All Read"));

    await waitFor(() => {
      expect(screen.getByTestId("unread-count")).toHaveTextContent("0");
    });
  });

  it("clears all persistent notifications", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestPersistentComponent />
      </NotificationProvider>,
    );

    await user.click(screen.getByText("Clear Persistent"));

    await waitFor(() => {
      expect(screen.getByTestId("persistent-count")).toHaveTextContent("0");
    });
  });
});

describe("NotificationContext — Activity Feed", () => {
  it("initializes with mock activities", () => {
    render(
      <NotificationProvider>
        <TestPersistentComponent />
      </NotificationProvider>,
    );
    const count = parseInt(
      screen.getByTestId("activity-count").textContent || "0",
    );
    expect(count).toBeGreaterThan(0);
  });

  it("adds a new activity event", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestPersistentComponent />
      </NotificationProvider>,
    );

    const initialCount = parseInt(
      screen.getByTestId("activity-count").textContent || "0",
    );

    await user.click(screen.getByText("Add Activity"));

    await waitFor(() => {
      const newCount = parseInt(
        screen.getByTestId("activity-count").textContent || "0",
      );
      expect(newCount).toBe(initialCount + 1);
    });
  });

  it("clears all activities", async () => {
    const user = userEvent.setup();
    render(
      <NotificationProvider>
        <TestPersistentComponent />
      </NotificationProvider>,
    );

    await user.click(screen.getByText("Clear Activities"));

    await waitFor(() => {
      expect(screen.getByTestId("activity-count")).toHaveTextContent("0");
    });
  });

  it("exposes wsConnected state", () => {
    render(
      <NotificationProvider>
        <TestPersistentComponent />
      </NotificationProvider>,
    );
    // WebSocket mock is CLOSED (readyState 3), so wsConnected should be false
    expect(screen.getByTestId("ws-connected")).toHaveTextContent("no");
  });
});
