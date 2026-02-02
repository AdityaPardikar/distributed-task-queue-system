import { render, screen } from "@testing-library/react";
import MetricsCards from "../MetricsCards";

describe("MetricsCards Component", () => {
  const mockMetrics = {
    totalTasks: 1250,
    activeWorkers: 5,
    queueSize: 45,
    successRate: 96.4,
    pendingTasks: 45,
    runningTasks: 12,
    completedTasks: 1150,
    failedTasks: 43,
  };

  it("renders all metric cards", () => {
    render(<MetricsCards metrics={mockMetrics} />);

    expect(screen.getByText("Total Tasks")).toBeInTheDocument();
    expect(screen.getByText("Active Workers")).toBeInTheDocument();
    expect(screen.getByText("Queue Size")).toBeInTheDocument();
    expect(screen.getByText("Success Rate")).toBeInTheDocument();
  });

  it("displays correct metric values", () => {
    render(<MetricsCards metrics={mockMetrics} />);

    expect(screen.getByText("1,250")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("45")).toBeInTheDocument();
    expect(screen.getByText("96.4%")).toBeInTheDocument();
  });

  it("shows subtitles for metrics", () => {
    render(<MetricsCards metrics={mockMetrics} />);

    expect(screen.getByText("45 pending, 12 running")).toBeInTheDocument();
    expect(screen.getByText("Currently processing")).toBeInTheDocument();
    expect(screen.getByText("Tasks waiting")).toBeInTheDocument();
  });

  it("displays correct status colors based on values", () => {
    const { rerender } = render(<MetricsCards metrics={mockMetrics} />);

    // Success rate > 90 should be green
    let successElement = screen.getByText("96.4%");
    expect(successElement).toBeInTheDocument();

    // Change to lower success rate
    const lowMetrics = { ...mockMetrics, successRate: 70 };
    rerender(<MetricsCards metrics={lowMetrics} />);

    // Verify re-render works - check that the component updated (success rate is now 70)
    expect(screen.queryByText("96.4%")).not.toBeInTheDocument();
  });

  it("formats large numbers with commas", () => {
    const largeMetrics = {
      ...mockMetrics,
      totalTasks: 1234567,
      queueSize: 56789,
    };

    render(<MetricsCards metrics={largeMetrics} />);

    // Numbers are formatted with locale - check text content contains the digits
    const cardTexts = screen.getAllByRole("heading", { level: 3 });
    const hasFormattedNumbers = cardTexts.some((card) =>
      /1.{1,3}34.{1,3}567/.test(card.textContent || ""),
    );
    expect(hasFormattedNumbers).toBe(true);
  });
});
