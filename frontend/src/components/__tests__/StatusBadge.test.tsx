import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import StatusBadge from "../../components/StatusBadge";

describe("StatusBadge", () => {
  // ── task variant (default) ─────────────────────────────
  describe("task variant", () => {
    const cases: Array<[string, string]> = [
      ["pending", "PENDING"],
      ["running", "RUNNING"],
      ["completed", "COMPLETED"],
      ["failed", "FAILED"],
      ["cancelled", "CANCELLED"],
      ["scheduled", "SCHEDULED"],
      ["retrying", "RETRYING"],
    ];

    test.each(cases)('renders "%s" uppercased', (value, expected) => {
      render(<StatusBadge value={value} />);
      expect(screen.getByText(expected)).toBeInTheDocument();
    });

    test("pending badge has yellow styling", () => {
      const { container } = render(<StatusBadge value="pending" />);
      expect(container.firstChild).toHaveClass("bg-yellow-100");
    });

    test("running badge has blue styling", () => {
      const { container } = render(<StatusBadge value="running" />);
      expect(container.firstChild).toHaveClass("bg-blue-100");
    });

    test("completed badge has green styling", () => {
      const { container } = render(<StatusBadge value="completed" />);
      expect(container.firstChild).toHaveClass("bg-green-100");
    });

    test("failed badge has red styling", () => {
      const { container } = render(<StatusBadge value="failed" />);
      expect(container.firstChild).toHaveClass("bg-red-100");
    });

    test("unknown value falls back to gray", () => {
      const { container } = render(<StatusBadge value="unknown-status" />);
      expect(container.firstChild).toHaveClass("bg-gray-100");
    });
  });

  // ── priority variant ───────────────────────────────────
  describe("priority variant", () => {
    test("critical has red background", () => {
      const { container } = render(
        <StatusBadge value="critical" variant="priority" />,
      );
      expect(container.firstChild).toHaveClass("bg-red-600");
    });

    test("high has orange background", () => {
      const { container } = render(
        <StatusBadge value="high" variant="priority" />,
      );
      expect(container.firstChild).toHaveClass("bg-orange-500");
    });

    test("medium has yellow background", () => {
      const { container } = render(
        <StatusBadge value="medium" variant="priority" />,
      );
      expect(container.firstChild).toHaveClass("bg-yellow-500");
    });

    test("low has gray background", () => {
      const { container } = render(
        <StatusBadge value="low" variant="priority" />,
      );
      expect(container.firstChild).toHaveClass("bg-gray-400");
    });
  });

  // ── worker variant ─────────────────────────────────────
  describe("worker variant", () => {
    test("ACTIVE has green background", () => {
      const { container } = render(
        <StatusBadge value="ACTIVE" variant="worker" />,
      );
      expect(container.firstChild).toHaveClass("bg-green-100");
    });

    test("OFFLINE has red background", () => {
      const { container } = render(
        <StatusBadge value="OFFLINE" variant="worker" />,
      );
      expect(container.firstChild).toHaveClass("bg-red-100");
    });

    test("PAUSED has gray background", () => {
      const { container } = render(
        <StatusBadge value="PAUSED" variant="worker" />,
      );
      expect(container.firstChild).toHaveClass("bg-gray-200");
    });
  });

  // ── className passthrough ──────────────────────────────
  test("passes extra className to root element", () => {
    const { container } = render(
      <StatusBadge value="pending" className="my-extra-class" />,
    );
    expect(container.firstChild).toHaveClass("my-extra-class");
  });
});
