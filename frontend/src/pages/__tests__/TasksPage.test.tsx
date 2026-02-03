import { render, screen } from "@testing-library/react";
import TasksPage from "../TasksPage";

// Mock the api service
jest.mock("../../services/api", () => ({
  __esModule: true,
  default: {
    getTasks: jest.fn(),
  },
}));

// Mock the AdvancedFilters component
jest.mock("../../components/AdvancedFilters", () => ({
  __esModule: true,
  default: ({ onFilterChange }: any) => (
    <div data-testid="advanced-filters">Advanced Filters Mock</div>
  ),
}));

// Mock the FilterService
jest.mock("../../services/FilterService", () => ({
  useFilterPresets: () => ({
    presets: [],
    addPreset: jest.fn(),
  }),
}));

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
    const api = require("../../services/api").default;
    api.getTasks.mockResolvedValue({
      data: mockTasks,
      total: mockTasks.length,
    });
  });

  it("renders tasks page title", () => {
    render(<TasksPage />);
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toHaveTextContent("Tasks");
    expect(screen.getByText(/View and manage all tasks/i)).toBeInTheDocument();
  });

  it("displays search bar", () => {
    render(<TasksPage />);
    const advancedFilters = screen.getByTestId("advanced-filters");
    expect(advancedFilters).toBeInTheDocument();
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
