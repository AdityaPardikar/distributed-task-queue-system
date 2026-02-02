import { render, screen } from "@testing-library/react";
import RecentTasksList from "../RecentTasksList";
import type { RecentTask } from "../../types/dashboard";

describe("RecentTasksList Component", () => {
  const mockTasks: RecentTask[] = [
    {
      id: "task-1",
      name: "Send Email Campaign",
      status: "completed",
      priority: "high",
      createdAt: new Date(Date.now() - 300000).toISOString(),
      duration: 45,
    },
    {
      id: "task-2",
      name: "Process Data",
      status: "running",
      priority: "medium",
      createdAt: new Date(Date.now() - 600000).toISOString(),
      worker: "worker-1",
    },
    {
      id: "task-3",
      name: "Generate Report",
      status: "failed",
      priority: "critical",
      createdAt: new Date(Date.now() - 900000).toISOString(),
      duration: 120,
    },
  ];

  it("renders recent tasks list", () => {
    render(<RecentTasksList tasks={mockTasks} />);

    expect(screen.getByText("Recent Tasks")).toBeInTheDocument();
    expect(screen.getByText("Send Email Campaign")).toBeInTheDocument();
    expect(screen.getByText("Process Data")).toBeInTheDocument();
    expect(screen.getByText("Generate Report")).toBeInTheDocument();
  });

  it("displays correct status badges", () => {
    render(<RecentTasksList tasks={mockTasks} />);

    expect(screen.getByText("COMPLETED")).toBeInTheDocument();
    expect(screen.getByText("RUNNING")).toBeInTheDocument();
    expect(screen.getByText("FAILED")).toBeInTheDocument();
  });

  it("displays correct priority badges", () => {
    render(<RecentTasksList tasks={mockTasks} />);

    expect(screen.getAllByText("HIGH").length).toBeGreaterThan(0);
    expect(screen.getAllByText("MEDIUM").length).toBeGreaterThan(0);
    expect(screen.getAllByText("CRITICAL").length).toBeGreaterThan(0);
  });

  it("shows empty state when no tasks", () => {
    render(<RecentTasksList tasks={[]} />);

    expect(screen.getByText("No recent tasks")).toBeInTheDocument();
  });

  it("calls onTaskClick when task is clicked", () => {
    const mockClick = jest.fn();
    render(<RecentTasksList tasks={mockTasks} onTaskClick={mockClick} />);

    const taskElement = screen.getByText("Send Email Campaign");
    taskElement.click();

    expect(mockClick).toHaveBeenCalledWith("task-1");
  });

  it("displays task IDs (first 8 characters)", () => {
    render(<RecentTasksList tasks={mockTasks} />);

    expect(screen.getByText(/ID: task-1/)).toBeInTheDocument();
  });

  it("displays durations when available", () => {
    render(<RecentTasksList tasks={mockTasks} />);

    expect(screen.getByText(/Duration: 45s/)).toBeInTheDocument();
    expect(screen.getByText(/Duration: 2m 0s/)).toBeInTheDocument();
  });

  it("displays worker assignment when available", () => {
    render(<RecentTasksList tasks={mockTasks} />);

    expect(screen.getByText(/Worker: worker-1/)).toBeInTheDocument();
  });
});
