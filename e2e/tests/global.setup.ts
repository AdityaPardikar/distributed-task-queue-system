/**
 * Global setup — authenticate once and save storage state so all
 * browser projects can reuse the session without logging in again.
 */
import { test as setup, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const AUTH_FILE = path.join(__dirname, ".auth", "user.json");

setup("authenticate", async ({ page }) => {
  // Ensure directory exists
  const dir = path.dirname(AUTH_FILE);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  // Navigate to login page
  await page.goto("/login");
  await expect(page.locator("h1, h2").first()).toBeVisible();

  // Fill credentials (demo defaults shown on the login page)
  await page.locator("#username").fill("admin");
  await page.locator("#password").fill("admin123");

  // Submit
  await page.getByRole("button", { name: /sign in/i }).click();

  // Wait until we're redirected away from /login
  await page.waitForURL("**/dashboard", { timeout: 15_000 });

  // Verify we actually landed on the dashboard
  await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible({
    timeout: 10_000,
  });

  // Persist storage state for other projects
  await page.context().storageState({ path: AUTH_FILE });
});
