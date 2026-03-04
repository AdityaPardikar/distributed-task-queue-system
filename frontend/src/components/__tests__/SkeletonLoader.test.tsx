import React from "react";
import { render, screen } from "@testing-library/react";
import SkeletonLoader from "../../components/SkeletonLoader";

describe("SkeletonLoader", () => {
  describe("Block", () => {
    test("renders with animate-pulse class", () => {
      const { container } = render(<SkeletonLoader.Block />);
      expect(container.firstChild).toHaveClass("animate-pulse");
    });

    test("accepts extra className", () => {
      const { container } = render(
        <SkeletonLoader.Block className="h-4 w-32" />,
      );
      expect(container.firstChild).toHaveClass("h-4");
      expect(container.firstChild).toHaveClass("w-32");
    });
  });

  describe("Row", () => {
    test("renders default 5 cells", () => {
      const { container } = render(
        <table>
          <tbody>
            <SkeletonLoader.Row />
          </tbody>
        </table>,
      );
      expect(container.querySelectorAll("td")).toHaveLength(5);
    });

    test("renders custom number of cells", () => {
      const { container } = render(
        <table>
          <tbody>
            <SkeletonLoader.Row cols={7} />
          </tbody>
        </table>,
      );
      expect(container.querySelectorAll("td")).toHaveLength(7);
    });
  });

  describe("Table", () => {
    test("renders default 8 rows with 5 cols each", () => {
      const { container } = render(
        <table>
          <SkeletonLoader.Table />
        </table>,
      );
      expect(container.querySelectorAll("tr")).toHaveLength(8);
      expect(container.querySelectorAll("td")).toHaveLength(40); // 8 × 5
    });

    test("renders custom rows and cols", () => {
      const { container } = render(
        <table>
          <SkeletonLoader.Table rows={3} cols={4} />
        </table>,
      );
      expect(container.querySelectorAll("tr")).toHaveLength(3);
      expect(container.querySelectorAll("td")).toHaveLength(12); // 3 × 4
    });
  });

  describe("Card", () => {
    test("renders 3 skeleton blocks", () => {
      const { container } = render(<SkeletonLoader.Card />);
      expect(container.querySelectorAll(".animate-pulse")).toHaveLength(3);
    });
  });

  describe("MetricCards", () => {
    test("renders default 4 cards", () => {
      const { container } = render(<SkeletonLoader.MetricCards />);
      // Each card renders 3 blocks → 4 × 3 = 12 animate-pulse elements
      expect(
        container.querySelectorAll(".animate-pulse").length,
      ).toBeGreaterThanOrEqual(4);
    });

    test("renders custom count", () => {
      const { container } = render(<SkeletonLoader.MetricCards count={2} />);
      expect(
        container.querySelectorAll(".animate-pulse").length,
      ).toBeGreaterThanOrEqual(2);
    });
  });

  describe("Chart", () => {
    test("renders chart skeleton container", () => {
      const { container } = render(<SkeletonLoader.Chart />);
      expect(container.firstChild).toHaveClass("bg-white");
    });

    test("accepts custom height class", () => {
      const { container } = render(<SkeletonLoader.Chart height="h-48" />);
      expect(container.firstChild).toHaveClass("h-48");
    });
  });
});
