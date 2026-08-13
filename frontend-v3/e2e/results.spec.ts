import { test, expect } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("Results safe transitional surface", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await setupAuthenticatedPage(page);
  });

  test("navigates to the results surface", async ({ page }) => {
    await page.goto("/results");
    await expect(page).toHaveURL(/\/results/);
  });

  test("shows a safe bridge instead of ungoverned result data", async ({ page }) => {
    await page.goto("/results");
    await expect(page.locator('[data-unification-state="safe-bridge"]')).toBeVisible();
    await expect(page.getByText("مسار انتقالي موحّد")).toBeVisible();
  });
});
