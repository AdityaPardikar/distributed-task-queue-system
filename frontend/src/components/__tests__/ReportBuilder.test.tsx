import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ReportBuilder from "../../components/ReportBuilder";
import AnalyticsService from "../../services/AnalyticsService";

jest.mock("../../services/api", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
  },
}));

jest.mock("../../services/AnalyticsService", () => ({
  __esModule: true,
  default: {
    listReports: jest.fn(),
    generateReport: jest.fn(),
    deleteReport: jest.fn(),
    exportToCSV: jest.fn(),
    exportToJSON: jest.fn(),
    getAnalytics: jest.fn(),
    getTaskTrends: jest.fn(),
    getWorkerStats: jest.fn(),
    getReport: jest.fn(),
  },
}));

const mockReports = [
  {
    id: "report-1",
    name: "Monthly Performance",
    type: "task" as const,
    createdAt: new Date().toISOString(),
  },
  {
    id: "report-2",
    name: "Worker Efficiency",
    type: "worker" as const,
    createdAt: new Date().toISOString(),
  },
];

describe("ReportBuilder", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (AnalyticsService.listReports as jest.Mock).mockResolvedValue(mockReports);
    (AnalyticsService.generateReport as jest.Mock).mockResolvedValue(
      "report-3",
    );
    (AnalyticsService.deleteReport as jest.Mock).mockResolvedValue(undefined);
  });

  test("should render report builder form", () => {
    render(<ReportBuilder />);

    expect(screen.getByText("Create New Report")).toBeInTheDocument();
    expect(screen.getByLabelText("Report Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Report Type")).toBeInTheDocument();
  });

  test("should display report type options", () => {
    render(<ReportBuilder />);

    const typeSelect = screen.getByLabelText(
      "Report Type",
    ) as HTMLSelectElement;
    expect(typeSelect.value).toBe("task");

    expect(
      screen.getByRole("option", { name: /Task Performance/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Worker Efficiency/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /System Health/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Custom Report/i }),
    ).toBeInTheDocument();
  });

  test("should display date range inputs", () => {
    render(<ReportBuilder />);

    expect(screen.getByLabelText("Start Date")).toBeInTheDocument();
    expect(screen.getByLabelText("End Date")).toBeInTheDocument();
  });

  test("should display metrics selection for task type", async () => {
    render(<ReportBuilder />);

    await waitFor(() => {
      expect(screen.getByText("Select Metrics")).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/COMPLETION RATE/i)).toBeInTheDocument();
  });

  test("should change metrics when report type changes", async () => {
    const user = userEvent.setup();
    render(<ReportBuilder />);

    const typeSelect = screen.getByLabelText("Report Type");
    await user.selectOptions(typeSelect, "worker");

    await waitFor(() => {
      expect(screen.getByLabelText(/TASKS COMPLETED/i)).toBeInTheDocument();
    });
  });

  test("should load and display saved reports", async () => {
    render(<ReportBuilder />);

    await waitFor(() => {
      expect(screen.getByText("Saved Reports (2)")).toBeInTheDocument();
    });

    const reports = screen.getAllByText("Monthly Performance");
    expect(reports.length).toBeGreaterThan(0);

    const workerReports = screen.getAllByText("Worker Efficiency");
    expect(workerReports.length).toBeGreaterThan(0);
  });

  test("should display empty state when no reports exist", async () => {
    (AnalyticsService.listReports as jest.Mock).mockResolvedValueOnce([]);

    render(<ReportBuilder />);

    await waitFor(() => {
      expect(
        screen.getByText("No saved reports yet. Create one to get started!"),
      ).toBeInTheDocument();
    });
  });

  test("should generate report with valid input", async () => {
    const user = userEvent.setup();
    window.alert = jest.fn();

    render(<ReportBuilder />);

    const nameInput = screen.getByLabelText("Report Name");
    await user.type(nameInput, "Test Report");

    const generateButton = screen.getByRole("button", {
      name: /Generate Report/i,
    });
    await user.click(generateButton);

    await waitFor(() => {
      expect(AnalyticsService.generateReport).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "Test Report",
          type: "task",
        }),
      );
    });
  });

  test("should show alert if report name is empty", async () => {
    const user = userEvent.setup();
    window.alert = jest.fn();

    render(<ReportBuilder />);

    const generateButton = screen.getByRole("button", {
      name: /Generate Report/i,
    });
    await user.click(generateButton);

    expect(window.alert).toHaveBeenCalledWith("Please enter a report name");
  });

  test("should toggle metric checkbox", async () => {
    const user = userEvent.setup();
    render(<ReportBuilder />);

    const checkbox = screen.getByLabelText(/COMPLETION RATE/i);
    expect(checkbox).not.toBeChecked();

    await user.click(checkbox);
    expect(checkbox).toBeChecked();

    await user.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });

  test("should expand report details on click", async () => {
    const user = userEvent.setup();
    render(<ReportBuilder />);

    await waitFor(() => {
      expect(screen.getByText("Monthly Performance")).toBeInTheDocument();
    });

    const reportHeader = screen
      .getByText("Monthly Performance")
      .closest(".report-header");
    if (reportHeader) {
      await user.click(reportHeader);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /Delete/i }),
        ).toBeInTheDocument();
      });
    }
  });

  test("should delete report when confirmed", async () => {
    const user = userEvent.setup();
    window.confirm = jest.fn(() => true);
    window.alert = jest.fn();

    render(<ReportBuilder />);

    await waitFor(() => {
      expect(screen.getByText("Monthly Performance")).toBeInTheDocument();
    });

    const reportHeader = screen
      .getByText("Monthly Performance")
      .closest(".report-header");
    if (reportHeader) {
      await user.click(reportHeader);

      const deleteButton = screen.getByRole("button", { name: /Delete/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(AnalyticsService.deleteReport).toHaveBeenCalledWith("report-1");
      });
    }
  });

  test("should not delete report when not confirmed", async () => {
    const user = userEvent.setup();
    window.confirm = jest.fn(() => false);

    render(<ReportBuilder />);

    await waitFor(() => {
      expect(screen.getByText("Monthly Performance")).toBeInTheDocument();
    });

    const reportHeader = screen
      .getByText("Monthly Performance")
      .closest(".report-header");
    if (reportHeader) {
      await user.click(reportHeader);

      const deleteButton = screen.getByRole("button", { name: /Delete/i });
      await user.click(deleteButton);

      expect(AnalyticsService.deleteReport).not.toHaveBeenCalled();
    }
  });

  test("should update report name input", async () => {
    const user = userEvent.setup();
    render(<ReportBuilder />);

    const nameInput = screen.getByLabelText("Report Name") as HTMLInputElement;
    await user.type(nameInput, "New Report");

    expect(nameInput.value).toBe("New Report");
  });

  test("should update date range inputs", async () => {
    const user = userEvent.setup();
    render(<ReportBuilder />);

    const startDateInput = screen.getByLabelText(
      "Start Date",
    ) as HTMLInputElement;
    const endDateInput = screen.getByLabelText("End Date") as HTMLInputElement;

    await user.clear(startDateInput);
    await user.type(startDateInput, "2024-01-01");

    await user.clear(endDateInput);
    await user.type(endDateInput, "2024-12-31");

    expect(startDateInput.value).toBe("2024-01-01");
    expect(endDateInput.value).toBe("2024-12-31");
  });

  test("should display report type badge", async () => {
    render(<ReportBuilder />);

    await waitFor(() => {
      expect(screen.getByText("task")).toBeInTheDocument();
      expect(screen.getByText("worker")).toBeInTheDocument();
    });
  });

  test("should disable form during generation", async () => {
    const user = userEvent.setup();
    (AnalyticsService.generateReport as jest.Mock).mockImplementationOnce(
      () =>
        new Promise((resolve) => setTimeout(() => resolve("report-id"), 100)),
    );

    render(<ReportBuilder />);

    const nameInput = screen.getByLabelText("Report Name");
    const typeSelect = screen.getByLabelText("Report Type");
    const generateButton = screen.getByRole("button", {
      name: /Generate Report/i,
    });

    await user.type(nameInput, "Test Report");
    await user.click(generateButton);

    expect(nameInput).toBeDisabled();
    expect(typeSelect).toBeDisabled();
    expect(generateButton).toBeDisabled();
  });
});
