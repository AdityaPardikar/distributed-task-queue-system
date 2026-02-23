import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import SearchResultsPage from "../SearchResultsPage";

const renderPage = () =>
  render(
    <BrowserRouter>
      <SearchResultsPage />
    </BrowserRouter>,
  );

describe("SearchResultsPage", () => {
  it("renders the search heading", () => {
    renderPage();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Search",
    );
  });

  it("shows a search input with placeholder", () => {
    renderPage();
    expect(
      screen.getByPlaceholderText("Search everything..."),
    ).toBeInTheDocument();
  });

  it("displays category filters", () => {
    renderPage();
    // Category labels appear in both sidebar and result items
    expect(screen.getAllByText("All").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Tasks").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Workers").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Campaigns").length).toBeGreaterThan(0);
  });

  it("shows sort options", () => {
    renderPage();
    expect(screen.getByText(/Relevance/)).toBeInTheDocument();
  });

  it("displays mock result items", () => {
    renderPage();
    expect(screen.getByText("Bulk Import Job")).toBeInTheDocument();
    expect(
      screen.getByText("Data Export — Monthly Report"),
    ).toBeInTheDocument();
  });
});
