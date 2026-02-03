import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AdvancedFilters, {
  FilterCriteria,
} from "../../components/AdvancedFilters";

describe("AdvancedFilters Component", () => {
  const mockOnFilterChange = jest.fn();
  const mockOnSavePreset = jest.fn();

  beforeEach(() => {
    mockOnFilterChange.mockClear();
    mockOnSavePreset.mockClear();
  });

  test("should render search input", () => {
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    expect(
      screen.getByPlaceholderText(/Search by task name/i),
    ).toBeInTheDocument();
  });

  test("should render expand button", () => {
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    expect(screen.getByText(/Advanced Filters/i)).toBeInTheDocument();
  });

  test("should expand filter panel on button click", async () => {
    const user = userEvent.setup();
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    const expandButton = screen.getByRole("button", {
      name: /Toggle advanced filters/i,
    });
    await user.click(expandButton);

    const labels = screen.getAllByText("Status");
    expect(labels.length).toBeGreaterThan(0);
    expect(screen.getByText("Priority")).toBeInTheDocument();
  });

  test("should update search query", async () => {
    const user = userEvent.setup();
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    const searchInput = screen.getByPlaceholderText(/Search by task name/i);
    await user.type(searchInput, "test task");

    await waitFor(() => {
      expect(mockOnFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({
          searchQuery: "test task",
        }),
      );
    });
  });

  test("should toggle status filter", async () => {
    const user = userEvent.setup();
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    const expandButton = screen.getByRole("button", {
      name: /Toggle advanced filters/i,
    });
    await user.click(expandButton);

    const pendingCheckbox = screen.getByRole("checkbox", { name: /pending/i });
    await user.click(pendingCheckbox);

    await waitFor(() => {
      expect(mockOnFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({
          statuses: expect.arrayContaining(["pending"]),
        }),
      );
    });
  });

  test("should toggle multiple statuses", async () => {
    const user = userEvent.setup();
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    const expandButton = screen.getByRole("button", {
      name: /Toggle advanced filters/i,
    });
    await user.click(expandButton);

    const pendingCheckbox = screen.getByRole("checkbox", { name: /pending/i });
    const runningCheckbox = screen.getByRole("checkbox", { name: /running/i });

    await user.click(pendingCheckbox);
    await user.click(runningCheckbox);

    await waitFor(() => {
      const lastCall =
        mockOnFilterChange.mock.calls[
          mockOnFilterChange.mock.calls.length - 1
        ][0];
      expect(lastCall.statuses).toContain("pending");
      expect(lastCall.statuses).toContain("running");
    });
  });

  test("should toggle priority filter", async () => {
    const user = userEvent.setup();
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    const expandButton = screen.getByRole("button", {
      name: /Toggle advanced filters/i,
    });
    await user.click(expandButton);

    const highCheckbox = screen.getByRole("checkbox", { name: /high/i });
    await user.click(highCheckbox);

    await waitFor(() => {
      expect(mockOnFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({
          priorities: expect.arrayContaining(["high"]),
        }),
      );
    });
  });

  test("should update date range", async () => {
    const user = userEvent.setup();
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    const expandButton = screen.getByRole("button", {
      name: /Toggle advanced filters/i,
    });
    await user.click(expandButton);

    const startDateInput = screen.getByLabelText("Start date");
    const endDateInput = screen.getByLabelText("End date");

    await user.type(startDateInput, "2024-01-01");
    await user.type(endDateInput, "2024-12-31");

    await waitFor(() => {
      const lastCall =
        mockOnFilterChange.mock.calls[
          mockOnFilterChange.mock.calls.length - 1
        ][0];
      expect(lastCall.startDate).toBe("2024-01-01");
      expect(lastCall.endDate).toBe("2024-12-31");
    });
  });

  test("should update worker ID filter", async () => {
    const user = userEvent.setup();
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    const expandButton = screen.getByRole("button", {
      name: /Toggle advanced filters/i,
    });
    await user.click(expandButton);

    const workerInput = screen.getByLabelText("Worker ID filter");
    await user.type(workerInput, "worker-123");

    await waitFor(() => {
      expect(mockOnFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({
          workerId: "worker-123",
        }),
      );
    });
  });

  test("should change sort field", async () => {
    const user = userEvent.setup();
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    const expandButton = screen.getByRole("button", {
      name: /Toggle advanced filters/i,
    });
    await user.click(expandButton);

    const sortSelect = screen.getByLabelText("Sort field");
    await user.selectOptions(sortSelect, "name");

    await waitFor(() => {
      expect(mockOnFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({
          sortBy: "name",
        }),
      );
    });
  });

  test("should change sort order", async () => {
    const user = userEvent.setup();
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    const expandButton = screen.getByRole("button", {
      name: /Toggle advanced filters/i,
    });
    await user.click(expandButton);

    const sortOrderSelect = screen.getByLabelText("Sort order");
    await user.selectOptions(sortOrderSelect, "asc");

    await waitFor(() => {
      expect(mockOnFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({
          sortOrder: "asc",
        }),
      );
    });
  });

  test("should clear all filters", async () => {
    const user = userEvent.setup();
    render(<AdvancedFilters onFilterChange={mockOnFilterChange} />);

    const expandButton = screen.getByRole("button", {
      name: /Toggle advanced filters/i,
    });
    await user.click(expandButton);

    const searchInput = screen.getByPlaceholderText(/Search by task name/i);
    await user.type(searchInput, "test");

    const clearButton = screen.getByText("Clear All");
    await user.click(clearButton);

    await waitFor(() => {
      const lastCall =
        mockOnFilterChange.mock.calls[
          mockOnFilterChange.mock.calls.length - 1
        ][0];
      expect(lastCall.searchQuery).toBe("");
      expect(lastCall.statuses).toEqual([]);
      expect(lastCall.priorities).toEqual([]);
    });
  });

  test("should disable inputs when loading", () => {
    render(
      <AdvancedFilters onFilterChange={mockOnFilterChange} loading={true} />,
    );

    const searchInput = screen.getByPlaceholderText(/Search by task name/i);
    const expandButton = screen.getByRole("button", {
      name: /Toggle advanced filters/i,
    });

    expect(searchInput).toBeDisabled();
    expect(expandButton).toBeDisabled();
  });
});
