import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import GlobalSearch from "../GlobalSearch";

// Mock react-router-dom navigate
const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

const renderSearch = (isOpen = true) => {
  const onClose = jest.fn();
  const result = render(
    <BrowserRouter>
      <GlobalSearch isOpen={isOpen} onClose={onClose} />
    </BrowserRouter>,
  );
  return { ...result, onClose };
};

describe("GlobalSearch", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it("renders nothing when closed", () => {
    const { container } = renderSearch(false);
    // The component returns null when isOpen is false
    expect(container.firstChild).toBeNull();
  });

  it("renders search overlay when open", () => {
    renderSearch(true);
    const input = screen.getByPlaceholderText(/search/i);
    expect(input).toBeInTheDocument();
  });

  it("shows default results before typing", () => {
    renderSearch(true);
    // Should show page results by default (e.g., "Dashboard")
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("filters results based on search query", async () => {
    const user = userEvent.setup();
    renderSearch(true);

    const input = screen.getByPlaceholderText(/search/i);
    await user.type(input, "worker");

    await waitFor(() => {
      const matches = screen.getAllByText(/worker/i);
      expect(matches.length).toBeGreaterThan(0);
    });
  });

  it("calls onClose when Escape is pressed", async () => {
    const user = userEvent.setup();
    const { onClose } = renderSearch(true);

    // Focus the input first, then press Escape (component handles Escape in onKeyDown)
    const input = screen.getByPlaceholderText(/search/i);
    await user.click(input);
    await user.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalled();
  });

  it("calls onClose when backdrop is clicked", async () => {
    const user = userEvent.setup();
    const { onClose } = renderSearch(true);

    // Click the backdrop overlay (the outer fixed div)
    const backdrop = document.querySelector(".fixed.inset-0");
    if (backdrop) {
      await user.click(backdrop);
      expect(onClose).toHaveBeenCalled();
    }
  });

  it("shows keyboard shortcuts footer", () => {
    renderSearch(true);
    expect(screen.getByText(/navigate/i)).toBeInTheDocument();
  });
});
