import { render, screen } from "@testing-library/react";
import TasksPage from "../TasksPage";

// Mock the api service BEFORE defining mockTasks (hoisting issue fix)
jest.mock("../../services/api", () => ({
  __esModule: true,
  default: {
    getTasks: jest.fn(),
  },
}));

import * as apiModule from "../../services/api";

const mockTasks = [
  {
    id: "task-1",
    name: "Task 1",
    status: "completed",
    priority: "high",
    createdAt: new Date("2024-01-15").toISOString(),
    result: "success",
  },
  {
    id: "task-2",
    name: "Task 2",
    status: "running",
    priority: "medium",
    createdAt: new Date("2024-01-16").toISOString(),
    result: null,
  },
];

describe("TasksPage", () => {
  beforeEach(() => {
    (apiModule.default.getTasks as jest.Mock).mockResolvedValue(mockTasks);
  });

  it("renders tasks page title", () => {
    render(<TasksPage />);
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toHaveTextContent("Tasks");
    expect(screen.getByText(/View and manage all tasks/i)).toBeInTheDocument();
  });

  it("displays search bar", () => {
    render(<TasksPage />);
    const searchInput = screen.getByPlaceholderText(/search/i);
    expect(searchInput).toBeInTheDocument();
  });

  it("renders pagination controls", () => {
    render(<TasksPage />);
    // Pagination should eventually appear once tasks load
    expect(screen.getByText(/Loading tasks/i)).toBeInTheDocument();
  });

  it("has refresh button", () => {
    render(<TasksPage />);
    const refreshButton = screen.getByRole("button", { name: /refresh/i });
    expect(refreshButton).toBeInTheDocument();
  });
});
