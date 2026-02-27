/**
 * E2E Tests — Authentication Flows
 *
 * Covers login, registration, protected route redirect, session
 * persistence, logout, and error handling.
 */
import { test, expect, type Page } from "@playwright/test";

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Helpers                                                                    */
/* ═══════════════════════════════════════════════════════════════════════════ */

/** Clear auth state so we start as an unauthenticated user. */
async function clearAuth(page: Page) {
  await page.context().clearCookies();
  await page.evaluate(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  });
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Login Tests                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Login", () => {
  test.use({ storageState: { cookies: [], origins: [] } }); // start fresh

  test("shows login form with required fields", async ({ page }) => {
    await page.goto("/login");

    await expect(page.locator("#username")).toBeVisible();
    await expect(page.locator("#password")).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  });

  test("displays demo credentials hint", async ({ page }) => {
    await page.goto("/login");

    await expect(page.getByText("Demo Credentials")).toBeVisible();
    await expect(
      page.getByText("admin", { exact: true }).first(),
    ).toBeVisible();
  });

  test("successful login redirects to dashboard", async ({ page }) => {
    await page.goto("/login");

    await page.locator("#username").fill("admin");
    await page.locator("#password").fill("admin123");
    await page.getByRole("button", { name: /sign in/i }).click();

    await page.waitForURL("**/dashboard", { timeout: 15_000 });
    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible(
      { timeout: 10_000 },
    );
  });

  test("failed login shows error message", async ({ page }) => {
    await page.goto("/login");

    await page.locator("#username").fill("wronguser");
    await page.locator("#password").fill("wrongpassword");
    await page.getByRole("button", { name: /sign in/i }).click();

    // Should show an error banner
    await expect(
      page.getByText(/failed|invalid|incorrect|unauthorized/i),
    ).toBeVisible({ timeout: 10_000 });

    // Should stay on login page
    expect(page.url()).toContain("/login");
  });

  test("login button shows loading state", async ({ page }) => {
    await page.goto("/login");

    await page.locator("#username").fill("admin");
    await page.locator("#password").fill("admin123");
    await page.getByRole("button", { name: /sign in/i }).click();

    // Button text changes to "Signing in..."
    await expect(page.getByText(/signing in/i)).toBeVisible();
  });

  test("empty form does not submit (HTML5 validation)", async ({ page }) => {
    await page.goto("/login");

    const submitBtn = page.getByRole("button", { name: /sign in/i });
    await submitBtn.click();

    // Should still be on login
    expect(page.url()).toContain("/login");
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Registration Tests                                                         */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Registration", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("shows registration form with all fields", async ({ page }) => {
    await page.goto("/register");

    await expect(
      page.getByRole("heading", { name: /create your account/i }),
    ).toBeVisible();
    await expect(page.locator("#username")).toBeVisible();
    await expect(page.locator("#email")).toBeVisible();
    await expect(page.locator("#password")).toBeVisible();
    await expect(page.locator("#confirmPassword")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /create account/i }),
    ).toBeVisible();
  });

  test("shows link to login page", async ({ page }) => {
    await page.goto("/register");

    const loginLink = page.getByRole("link", { name: /sign in/i });
    await expect(loginLink).toBeVisible();
    await loginLink.click();

    await page.waitForURL("**/login");
  });

  test("password mismatch shows error", async ({ page }) => {
    await page.goto("/register");

    await page.locator("#username").fill("testuser_e2e");
    await page.locator("#email").fill("testuser@example.com");
    await page.locator("#password").fill("Secret123!");
    await page.locator("#confirmPassword").fill("Mismatch!");
    await page.getByRole("button", { name: /create account/i }).click();

    await expect(page.getByText(/passwords do not match/i)).toBeVisible({
      timeout: 5_000,
    });
  });

  test("short password shows error", async ({ page }) => {
    await page.goto("/register");

    await page.locator("#username").fill("testuser_e2e");
    await page.locator("#email").fill("testuser@example.com");
    await page.locator("#password").fill("abc");
    await page.locator("#confirmPassword").fill("abc");
    await page.getByRole("button", { name: /create account/i }).click();

    await expect(page.getByText(/at least 6 characters/i)).toBeVisible({
      timeout: 5_000,
    });
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Protected Route Redirect                                                   */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Protected routes", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("unauthenticated user is redirected to /login", async ({ page }) => {
    await clearAuth(page);
    await page.goto("/dashboard");

    await page.waitForURL("**/login", { timeout: 10_000 });
    expect(page.url()).toContain("/login");
  });

  test("unauthenticated user accessing /tasks is redirected", async ({
    page,
  }) => {
    await clearAuth(page);
    await page.goto("/tasks");

    await page.waitForURL("**/login", { timeout: 10_000 });
    expect(page.url()).toContain("/login");
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Session Persistence                                                        */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Session persistence", () => {
  // Uses the shared storageState (authenticated)

  test("authenticated user can navigate directly to dashboard", async ({
    page,
  }) => {
    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible(
      { timeout: 10_000 },
    );
  });

  test("token is stored in localStorage after login", async ({ page }) => {
    await page.goto("/dashboard");

    const token = await page.evaluate(() =>
      localStorage.getItem("access_token"),
    );
    expect(token).toBeTruthy();
  });

  test("page reload preserves authentication", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible(
      { timeout: 10_000 },
    );

    // Hard reload
    await page.reload();
    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible(
      { timeout: 10_000 },
    );

    // Still on dashboard, not redirected to login
    expect(page.url()).toContain("/dashboard");
  });
});
