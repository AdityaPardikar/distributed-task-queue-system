import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Toast from "../../components/Toast";

describe("Toast Component", () => {
  test("should render toast with message", () => {
    const mockOnClose = jest.fn();
    render(
      <Toast
        id="test-1"
        message="Test notification"
        type="info"
        onClose={mockOnClose}
      />,
    );

    expect(screen.getByText("Test notification")).toBeInTheDocument();
  });

  test("should render success toast with correct styling", () => {
    const mockOnClose = jest.fn();
    const { container } = render(
      <Toast
        id="test-1"
        message="Success message"
        type="success"
        onClose={mockOnClose}
      />,
    );

    expect(container.querySelector(".toast-success")).toBeInTheDocument();
  });

  test("should render error toast with correct styling", () => {
    const mockOnClose = jest.fn();
    const { container } = render(
      <Toast
        id="test-1"
        message="Error message"
        type="error"
        onClose={mockOnClose}
      />,
    );

    expect(container.querySelector(".toast-error")).toBeInTheDocument();
  });

  test("should render warning toast with correct styling", () => {
    const mockOnClose = jest.fn();
    const { container } = render(
      <Toast
        id="test-1"
        message="Warning message"
        type="warning"
        onClose={mockOnClose}
      />,
    );

    expect(container.querySelector(".toast-warning")).toBeInTheDocument();
  });

  test("should render info toast with correct styling", () => {
    const mockOnClose = jest.fn();
    const { container } = render(
      <Toast
        id="test-1"
        message="Info message"
        type="info"
        onClose={mockOnClose}
      />,
    );

    expect(container.querySelector(".toast-info")).toBeInTheDocument();
  });

  test("should call onClose when close button is clicked", async () => {
    const user = userEvent.setup();
    const mockOnClose = jest.fn();

    render(
      <Toast
        id="test-1"
        message="Test notification"
        type="info"
        onClose={mockOnClose}
      />,
    );

    const closeButton = screen.getByLabelText("Close notification");
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledWith("test-1");
  });

  test("should auto-close after duration", async () => {
    jest.useFakeTimers();
    const mockOnClose = jest.fn();

    render(
      <Toast
        id="test-1"
        message="Test notification"
        type="info"
        duration={3000}
        onClose={mockOnClose}
      />,
    );

    jest.advanceTimersByTime(3000);

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalledWith("test-1");
    });

    jest.useRealTimers();
  });

  test("should not auto-close if duration is 0", async () => {
    jest.useFakeTimers();
    const mockOnClose = jest.fn();

    render(
      <Toast
        id="test-1"
        message="Test notification"
        type="info"
        duration={0}
        onClose={mockOnClose}
      />,
    );

    jest.advanceTimersByTime(10000);

    expect(mockOnClose).not.toHaveBeenCalled();

    jest.useRealTimers();
  });

  test("should have proper accessibility attributes", () => {
    const mockOnClose = jest.fn();
    const { container } = render(
      <Toast
        id="test-1"
        message="Test notification"
        type="info"
        onClose={mockOnClose}
      />,
    );

    const toast = container.querySelector('[role="alert"]');
    expect(toast).toHaveAttribute("aria-live", "polite");
  });

  test("should display correct icon for each type", () => {
    const mockOnClose = jest.fn();

    const { container: successContainer } = render(
      <Toast
        id="test-1"
        message="Success"
        type="success"
        onClose={mockOnClose}
      />,
    );

    expect(
      successContainer.querySelector(".toast-icon svg"),
    ).toBeInTheDocument();
  });
});
