import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import EmptyState from "../../components/EmptyState";

describe("EmptyState", () => {
  test("renders default title when none provided", () => {
    render(<EmptyState />);
    expect(screen.getByText("Nothing here yet")).toBeInTheDocument();
  });

  test("renders custom title", () => {
    render(<EmptyState title="No tasks found" />);
    expect(screen.getByText("No tasks found")).toBeInTheDocument();
  });

  test("renders custom description", () => {
    render(<EmptyState description="Create your first task to get started." />);
    expect(
      screen.getByText("Create your first task to get started."),
    ).toBeInTheDocument();
  });

  test("renders custom icon", () => {
    render(<EmptyState icon={<span data-testid="custom-icon">📭</span>} />);
    expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
  });

  test("does not render CTA button when action not provided", () => {
    render(<EmptyState />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  test("renders CTA button with correct label", () => {
    render(
      <EmptyState action={{ label: "Create Task", onClick: jest.fn() }} />,
    );
    expect(
      screen.getByRole("button", { name: "Create Task" }),
    ).toBeInTheDocument();
  });

  test("calls onClick when CTA button is clicked", () => {
    const handleClick = jest.fn();
    render(
      <EmptyState action={{ label: "Create Task", onClick: handleClick }} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Create Task" }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test("applies extra className to root element", () => {
    const { container } = render(<EmptyState className="py-32" />);
    expect(container.firstChild).toHaveClass("py-32");
  });

  test("renders InboxIcon by default", () => {
    const { container } = render(<EmptyState />);
    // lucide icons render as SVG
    expect(container.querySelector("svg")).toBeInTheDocument();
  });
});
