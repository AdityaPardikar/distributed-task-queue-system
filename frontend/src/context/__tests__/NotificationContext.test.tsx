import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  NotificationProvider,
  useNotification,
} from "../../context/NotificationContext";

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
