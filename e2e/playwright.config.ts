import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E test configuration for TaskFlow.
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: "./tests",
  outputDir: "./test-results",

  /* ── Parallelism & retries ─────────────────────────────────────────── */
  fullyParallel: true,
  workers: process.env.CI ? 1 : undefined,
  retries: process.env.CI ? 2 : 0,

  /* ── Reporter ──────────────────────────────────────────────────────── */
  reporter: process.env.CI
    ? [
        ["html", { open: "never" }],
        ["junit", { outputFile: "test-results/e2e-junit.xml" }],
      ]
    : [["html", { open: "on-failure" }]],

  /* ── Global settings ───────────────────────────────────────────────── */
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },

  /* ── Projects (browsers) ───────────────────────────────────────────── */
  projects: [
    /* ── Setup: create shared auth state ─────────────────────────────── */
    {
      name: "setup",
      testMatch: /global\.setup\.ts/,
    },

    /* ── Desktop ─────────────────────────────────────────────────────── */
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        storageState: "e2e/.auth/user.json",
      },
      dependencies: ["setup"],
    },
    {
      name: "firefox",
      use: {
        ...devices["Desktop Firefox"],
        storageState: "e2e/.auth/user.json",
      },
      dependencies: ["setup"],
    },
    {
      name: "webkit",
      use: {
        ...devices["Desktop Safari"],
        storageState: "e2e/.auth/user.json",
      },
      dependencies: ["setup"],
    },

    /* ── Mobile viewports ────────────────────────────────────────────── */
    {
      name: "mobile-chrome",
      use: {
        ...devices["Pixel 7"],
        storageState: "e2e/.auth/user.json",
      },
      dependencies: ["setup"],
    },
  ],

  /* ── Dev server ────────────────────────────────────────────────────── */
  webServer: {
    command: "cd ../frontend && npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },

  /* ── Expect defaults ───────────────────────────────────────────────── */
  expect: {
    timeout: 10_000,
    toHaveScreenshot: { maxDiffPixels: 100 },
  },
});
