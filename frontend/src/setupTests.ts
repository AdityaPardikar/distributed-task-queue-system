import "@testing-library/jest-dom";
import { TextEncoder, TextDecoder } from "util";

// Polyfill TextEncoder/TextDecoder for jsdom (required by react-router-dom)
if (typeof globalThis.TextEncoder === "undefined") {
  (globalThis as unknown as { TextEncoder: typeof TextEncoder }).TextEncoder =
    TextEncoder;
}
if (typeof globalThis.TextDecoder === "undefined") {
  (globalThis as unknown as { TextDecoder: typeof TextDecoder }).TextDecoder =
    TextDecoder as typeof globalThis.TextDecoder;
}

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock scrollIntoView (not implemented in jsdom)
Element.prototype.scrollIntoView = jest.fn();

// Mock IntersectionObserver
(
  globalThis as typeof globalThis & {
    IntersectionObserver: typeof IntersectionObserver;
  }
).IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
} as unknown as typeof IntersectionObserver;

// Suppress console errors in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    if (
      typeof args[0] === "string" &&
      args[0].includes("Warning: ReactDOM.render")
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
