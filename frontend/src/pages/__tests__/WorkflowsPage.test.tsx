import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import WorkflowsPage from "../WorkflowsPage";

// Mock DAGVisualization component
jest.mock("../../components/DAGVisualization", () => {
  const MockDAG = () => <div data-testid="dag-visualization">DAG</div>;
  MockDAG.displayName = "DAGVisualization";
  return { __esModule: true, default: MockDAG };
});

// Mock workflowAPI
jest.mock("../../services/workflowAPI", () => ({
  __esModule: true,
  default: {
    listWorkflows: jest.fn().mockResolvedValue([
      {
        workflow_id: "wf-1",
        workflow_name: "Data Pipeline",
        status: "running",
        total_tasks: 5,
        task_ids: ["t1", "t2", "t3", "t4", "t5"],
        completed: 3,
        running: 1,
        failed: 0,
        pending: 1,
        progress_percent: 60,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        workflow_id: "wf-2",
        workflow_name: "Batch Processing",
        status: "completed",
        total_tasks: 10,
        task_ids: ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9", "t10"],
        completed: 10,
        running: 0,
        failed: 0,
        pending: 0,
        progress_percent: 100,
        created_at: new Date(Date.now() - 3600_000).toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        workflow_id: "wf-3",
        workflow_name: "Report Generation",
        status: "failed",
        total_tasks: 3,
        task_ids: ["t1", "t2", "t3"],
        completed: 2,
        running: 0,
        failed: 1,
        pending: 0,
        progress_percent: 66.7,
        created_at: new Date(Date.now() - 7200_000).toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]),
    listTemplates: jest.fn().mockResolvedValue({
      templates: [
        {
          template_id: "tmpl-1",
          name: "ETL Pipeline",
          description: "Extract-Transform-Load workflow",
          version: "1.0",
          tasks: [
            { name: "Extract", task_name: "extract_handler" },
            { name: "Transform", task_name: "transform_handler" },
            { name: "Load", task_name: "load_handler" },
          ],
          created_at: new Date().toISOString(),
        },
      ],
    }),
    getVisualization: jest.fn().mockResolvedValue({
      workflow_id: "wf-1",
      workflow_name: "Data Pipeline",
      nodes: [],
      edges: [],
      execution_levels: [],
    }),
    triggerWorkflow: jest.fn().mockResolvedValue({ success: true }),
  },
}));

describe("WorkflowsPage", () => {
  it("renders the page title", async () => {
    render(<WorkflowsPage />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
        "Workflows",
      );
    });
  });

  it("shows workflow list after loading", async () => {
    render(<WorkflowsPage />);
    await waitFor(() => {
      expect(screen.getByText("Data Pipeline")).toBeInTheDocument();
      expect(screen.getByText("Batch Processing")).toBeInTheDocument();
      expect(screen.getByText("Report Generation")).toBeInTheDocument();
    });
  });

  it("displays stat cards", async () => {
    render(<WorkflowsPage />);
    await waitFor(() => {
      expect(screen.getByText("Total Workflows")).toBeInTheDocument();
      expect(screen.getByText("Data Pipeline")).toBeInTheDocument();
    });
  });

  it("renders tab navigation for workflows and templates", async () => {
    render(<WorkflowsPage />);
    await waitFor(() => {
      expect(screen.getByText(/Templates \(/)).toBeInTheDocument();
    });
  });

  it("shows refresh button", async () => {
    render(<WorkflowsPage />);
    expect(screen.getByText("Refresh")).toBeInTheDocument();
  });

  it("switches to Templates tab", async () => {
    const user = userEvent.setup();
    render(<WorkflowsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Templates \(/)).toBeInTheDocument();
    });

    await user.click(screen.getByText(/Templates \(/));

    await waitFor(() => {
      expect(screen.getByText("ETL Pipeline")).toBeInTheDocument();
    });
  });
});
