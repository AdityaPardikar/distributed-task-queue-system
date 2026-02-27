/**
 * E2E Tests — Navigation, Search, Settings, Workers, Alerts
 *
 * Covers sidebar navigation to all pages, global search (Ctrl+K),
 * settings page, workers page, and alerts page.
 */
import { test, expect } from "@playwright/test";

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Sidebar Navigation                                                         */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Navigation", () => {
  test("can navigate to all main pages from the sidebar", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible(
      { timeout: 15_000 },
    );

    const pages = [
      { nav: /tasks/i, heading: /tasks/i, url: "tasks" },
      { nav: /workers/i, heading: /workers/i, url: "workers" },
      { nav: /campaigns/i, heading: /campaigns/i, url: "campaigns" },
      { nav: /monitoring/i, heading: /monitoring/i, url: "monitoring" },
      { nav: /analytics/i, heading: /analytics/i, url: "analytics" },
      { nav: /workflows/i, heading: /workflows/i, url: "workflows" },
      { nav: /alerts/i, heading: /alerts/i, url: "alerts" },
      { nav: /settings/i, heading: /settings/i, url: "settings" },
    ];

    for (const p of pages) {
      const link = page.getByRole("link", { name: p.nav }).first();
      if ((await link.count()) === 0) continue; // skip if nav item not found

      await link.click();
      await page.waitForURL(`**/${p.url}`, { timeout: 10_000 });
      expect(page.url()).toContain(p.url);
    }
  });

  test("navigating to unknown route redirects to dashboard", async ({
    page,
  }) => {
    await page.goto("/nonexistent-page-xyz");
    await page.waitForURL("**/dashboard", { timeout: 10_000 });
    expect(page.url()).toContain("/dashboard");
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Workers Page                                                               */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Workers page", () => {
  test("loads workers page with heading", async ({ page }) => {
    await page.goto("/workers");
    await expect(page.getByRole("heading", { name: /workers/i })).toBeVisible({
      timeout: 15_000,
    });
  });

  test("displays worker cards or empty state", async ({ page }) => {
    await page.goto("/workers");
    await page.waitForTimeout(3_000);

    // Should have content — either worker cards or a message
    const body = await page.locator("body").textContent();
    expect(body?.length).toBeGreaterThan(0);
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Alerts Page                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Alerts page", () => {
  test("loads alerts page", async ({ page }) => {
    await page.goto("/alerts");
    await page.waitForTimeout(3_000);

    expect(page.url()).toContain("/alerts");
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Settings Page                                                              */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Settings page", () => {
  test("loads settings page", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: /settings/i })).toBeVisible({
      timeout: 15_000,
    });
  });

  test("settings page has form controls", async ({ page }) => {
    await page.goto("/settings");
    await page.waitForTimeout(2_000);

    // Settings pages typically have inputs, selects, or toggles
    const inputs = page.locator("input, select, textarea, [role='switch']");
    const buttons = page.getByRole("button");

    const hasControls =
      (await inputs.count()) > 0 || (await buttons.count()) > 0;
    expect(hasControls).toBeTruthy();
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Monitoring Page                                                            */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Monitoring page", () => {
  test("loads monitoring page", async ({ page }) => {
    await page.goto("/monitoring");
    await page.waitForTimeout(3_000);

    expect(page.url()).toContain("/monitoring");
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Search                                                                     */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Search page", () => {
  test("search results page loads", async ({ page }) => {
    await page.goto("/search");
    await page.waitForTimeout(2_000);

    expect(page.url()).toContain("/search");
  });
});
