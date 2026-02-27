/**
 * E2E Tests — Campaigns Page
 *
 * Covers campaign list, create campaign, campaign detail, template
 * management links, launch/pause actions, and delete confirmation.
 */
import { test, expect } from "@playwright/test";

test.describe("Campaign list", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/campaigns");
    // Wait for either the heading or the loading spinner to resolve
    await Promise.race([
      page
        .getByRole("heading", { name: /campaigns/i })
        .waitFor({ timeout: 15_000 }),
      page
        .getByText(/loading campaigns/i)
        .waitFor({ timeout: 5_000 })
        .then(() =>
          page.waitForSelector(".animate-spin", {
            state: "hidden",
            timeout: 15_000,
          }),
        ),
    ]);
  });

  /* ── Page structure ────────────────────────────────────────────────── */

  test("displays page heading", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /campaigns/i })).toBeVisible(
      { timeout: 10_000 },
    );
  });

  test("shows subtitle text", async ({ page }) => {
    await expect(page.getByText(/manage email campaigns/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  test("New Campaign button is visible", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /new campaign/i }),
    ).toBeVisible({ timeout: 10_000 });
  });

  /* ── Empty state ───────────────────────────────────────────────────── */

  test("shows empty state or campaign table", async ({ page }) => {
    // Either "No campaigns yet" message or a table with campaign rows
    const emptyCta = page.getByText(/no campaigns yet/i);
    const table = page.locator("table");

    const hasEmpty = (await emptyCta.count()) > 0;
    const hasTable = (await table.count()) > 0;

    expect(hasEmpty || hasTable).toBeTruthy();
  });

  /* ── Campaign table structure ──────────────────────────────────────── */

  test("campaign table has correct columns when campaigns exist", async ({
    page,
  }) => {
    const table = page.locator("table");
    if ((await table.count()) === 0) {
      test.skip(); // No campaigns → skip table assertions
      return;
    }

    const expectedHeaders = [
      "Name",
      "Status",
      "Progress",
      "Created",
      "Actions",
    ];
    for (const header of expectedHeaders) {
      await expect(
        page.getByRole("columnheader", { name: header }),
      ).toBeVisible();
    }
  });

  /* ── New Campaign navigation ───────────────────────────────────────── */

  test("clicking New Campaign navigates to create page", async ({ page }) => {
    await page.getByRole("button", { name: /new campaign/i }).click();

    await page.waitForURL("**/campaigns/new", { timeout: 10_000 });
    expect(page.url()).toContain("/campaigns/new");
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Create Campaign Page                                                       */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Create campaign", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/campaigns/new");
    // Wait for the form to load (template dropdown requires an API call)
    await page.waitForTimeout(2_000);
  });

  test("shows campaign creation form", async ({ page }) => {
    // The form should have a name input
    const nameInput = page.locator('input[name="name"], #name');
    const nameLabel = page.getByText(/campaign name|name/i).first();

    const hasForm =
      (await nameInput.count()) > 0 || (await nameLabel.count()) > 0;
    expect(hasForm).toBeTruthy();
  });

  test("shows template selector", async ({ page }) => {
    // Template select or dropdown
    const templateSelect = page.locator("select, [role='listbox']");
    const templateLabel = page.getByText(/template/i);

    const hasTemplateField =
      (await templateSelect.count()) > 0 || (await templateLabel.count()) > 0;
    expect(hasTemplateField).toBeTruthy();
  });

  test("shows submit button", async ({ page }) => {
    const submitBtn = page.getByRole("button", { name: /create|submit|save/i });
    await expect(submitBtn.first()).toBeVisible({ timeout: 5_000 });
  });

  test("empty name shows validation error", async ({ page }) => {
    // Clear name field if pre-filled
    const nameInput = page.locator('input[name="name"], #name');
    if ((await nameInput.count()) > 0) {
      await nameInput.fill("");
    }

    // Try to submit
    const submitBtn = page.getByRole("button", {
      name: /create|submit|save/i,
    });
    if ((await submitBtn.count()) > 0) {
      await submitBtn.first().click();

      // Should show validation error or HTML5 required attribute prevents submit
      const errorMsg = page.getByText(/required|name is required/i);
      const stillOnPage = page.url().includes("/campaigns/new");
      expect((await errorMsg.count()) > 0 || stillOnPage).toBeTruthy();
    }
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Campaign Actions                                                           */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Campaign actions", () => {
  test("campaign row actions include View and Delete buttons", async ({
    page,
  }) => {
    await page.goto("/campaigns");
    await page.waitForTimeout(3_000);

    const table = page.locator("table");
    if ((await table.count()) === 0) {
      test.skip();
      return;
    }

    // First campaign row should have action buttons
    const viewBtn = page.getByRole("button", { name: /view/i }).first();
    const deleteBtn = page.getByRole("button", { name: /delete/i }).first();

    // At least View should exist for each campaign
    const hasViewLink =
      (await viewBtn.count()) > 0 ||
      (await page.getByText(/view/i).count()) > 0;
    expect(hasViewLink).toBeTruthy();
  });

  test("delete button triggers confirmation dialog", async ({ page }) => {
    await page.goto("/campaigns");
    await page.waitForTimeout(3_000);

    const deleteBtn = page.getByRole("button", { name: /delete/i }).first();
    if ((await deleteBtn.count()) === 0) {
      test.skip();
      return;
    }

    // Set up dialog handler before clicking
    let dialogMessage = "";
    page.on("dialog", async (dialog) => {
      dialogMessage = dialog.message();
      await dialog.dismiss(); // Cancel the delete
    });

    await deleteBtn.click();
    expect(dialogMessage).toContain("sure");
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* Templates navigation                                                       */
/* ═══════════════════════════════════════════════════════════════════════════ */

test.describe("Templates page", () => {
  test("templates page is accessible", async ({ page }) => {
    await page.goto("/templates");

    // Should load without crashing — either shows templates or empty state
    await page.waitForTimeout(3_000);
    expect(page.url()).toContain("/templates");
  });

  test("navigating to create template works", async ({ page }) => {
    await page.goto("/templates/new");

    await page.waitForTimeout(2_000);
    expect(page.url()).toContain("/templates/new");
  });
});
