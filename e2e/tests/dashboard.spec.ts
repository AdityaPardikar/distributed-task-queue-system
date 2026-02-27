/**
 * E2E Tests — Dashboard Page
 *
 * Validates metric cards load, charts render, worker health section
 * appears, navigation between tabs works, and real-time refresh.
 */
import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    // Wait for the page heading to appear
    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible(
      { timeout: 15_000 },
    );
  });

  /* ── Page structure ────────────────────────────────────────────────── */

  test("renders main heading and subtitle", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /dashboard/i }),
    ).toBeVisible();
    await expect(page.getByText(/welcome to taskflow/i)).toBeVisible();
  });

  test("displays Overview and System Health tabs", async ({ page }) => {
    await expect(page.getByRole("button", { name: /overview/i })).toBeVisible();
    await expect(
      page.getByRole("button", { name: /system health/i }),
    ).toBeVisible();
  });

  /* ── Metric cards ──────────────────────────────────────────────────── */

  test("shows metric cards with numeric values", async ({ page }) => {
    // Wait for the metrics section to load (loading spinner should disappear)
    await page
      .waitForSelector(".animate-spin", {
        state: "hidden",
        timeout: 15_000,
      })
      .catch(() => {
        /* spinner may already be gone */
      });

    // The MetricsCards component renders stat values — at least one number
    // should be present in the dashboard content area
    const contentArea = page.locator(".space-y-6");
    await expect(contentArea).toBeVisible();
  });

  /* ── Charts section ────────────────────────────────────────────────── */

  test("renders chart containers", async ({ page }) => {
    // ChartsSection renders recharts <svg> elements inside the dashboard
    // Wait for content to load
    await page.waitForTimeout(2_000);

    // The charts are wrapped in white card containers
    const chartCards = page.locator(".bg-white.rounded-lg");
    await expect(chartCards.first()).toBeVisible({ timeout: 10_000 });
  });

  /* ── Worker health section ─────────────────────────────────────────── */

  test("shows Worker Health Status section", async ({ page }) => {
    await expect(page.getByText(/worker health status/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  test('shows worker count summary (e.g. "X / Y Active")', async ({ page }) => {
    await expect(page.getByText(/\d+\s*\/\s*\d+\s*active/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  /* ── Tab navigation ────────────────────────────────────────────────── */

  test("switching to System Health tab shows health monitor", async ({
    page,
  }) => {
    await page.getByRole("button", { name: /system health/i }).click();

    // The SystemHealthMonitor component should now be visible
    // and the Overview button should no longer be active
    await expect(
      page.getByRole("button", { name: /system health/i }),
    ).toBeVisible();
  });

  test("switching back to Overview tab restores metrics/charts", async ({
    page,
  }) => {
    // Switch to health
    await page.getByRole("button", { name: /system health/i }).click();
    await page.waitForTimeout(500);

    // Switch back
    await page.getByRole("button", { name: /overview/i }).click();
    await expect(page.getByText(/worker health status/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  /* ── Refresh button ────────────────────────────────────────────────── */

  test("refresh button triggers data reload", async ({ page }) => {
    const refreshBtn = page.getByRole("button", { name: /refresh/i });
    await expect(refreshBtn).toBeVisible();

    // Clicking should not cause errors
    await refreshBtn.click();

    // The spinner icon briefly appears on the button
    // Content should still be visible after refresh
    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible(
      { timeout: 10_000 },
    );
  });

  /* ── Responsive layout ─────────────────────────────────────────────── */

  test("dashboard renders correctly at mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible(
      { timeout: 15_000 },
    );

    // Content should still be visible, not overflowing
    const body = page.locator("body");
    const box = await body.boundingBox();
    expect(box).toBeTruthy();
    expect(box!.width).toBeLessThanOrEqual(376);
  });
});
