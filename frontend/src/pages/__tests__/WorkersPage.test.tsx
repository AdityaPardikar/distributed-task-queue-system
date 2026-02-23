import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import WorkersPage from "../WorkersPage";

// Mock workerAPI - the module exports both named and default
jest.mock("../../services/workerAPI", () => {
  const api = {
    list: jest.fn().mockResolvedValue({
      items: [
        {
          worker_id: "w-100001",
          hostname: "worker-node-01",
          status: "ACTIVE",
          capacity: 10,
          current_load: 3,
          last_heartbeat: new Date().toISOString(),
          created_at: new Date().toISOString(),
        },
        {
          worker_id: "w-200002",
          hostname: "worker-node-02",
          status: "PAUSED",
          capacity: 10,
          current_load: 0,
          last_heartbeat: new Date().toISOString(),
          created_at: new Date().toISOString(),
        },
      ],
      total: 2,
    }),
    get: jest.fn(),
    register: jest.fn(),
    heartbeat: jest.fn(),
    updateStatus: jest.fn().mockResolvedValue({}),
    getTasks: jest.fn(),
    pause: jest.fn().mockResolvedValue({}),
    resume: jest.fn().mockResolvedValue({}),
    drain: jest.fn().mockResolvedValue({}),
    remove: jest.fn().mockResolvedValue(undefined),
  };
  return { __esModule: true, workerAPI: api, default: api };
});

// Mock recharts to avoid rendering issues in tests
jest.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  AreaChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="area-chart">{children}</div>
  ),
  Area: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
}));

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

describe("WorkersPage", () => {
  it("renders the page title", async () => {
    renderWithRouter(<WorkersPage />);
    await waitFor(() => {
      expect(screen.getByText("Worker Management")).toBeInTheDocument();
    });
  });

  it("shows worker cards after loading", async () => {
    renderWithRouter(<WorkersPage />);
    await waitFor(() => {
      expect(screen.getByText("worker-node-01")).toBeInTheDocument();
      expect(screen.getByText("worker-node-02")).toBeInTheDocument();
    });
  });

  it("displays worker status badges", async () => {
    renderWithRouter(<WorkersPage />);
    await waitFor(() => {
      expect(screen.getByText("ACTIVE")).toBeInTheDocument();
      expect(screen.getByText("PAUSED")).toBeInTheDocument();
    });
  });

  it("shows refresh button", async () => {
    renderWithRouter(<WorkersPage />);
    const refreshBtn = screen.getByRole("button", { name: /refresh/i });
    expect(refreshBtn).toBeInTheDocument();
  });
});
