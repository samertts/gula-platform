import { test, expect } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("Samples safe transitional surface", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await setupAuthenticatedPage(page);
  });

  test("navigates to the samples surface", async ({ page }) => {
    await page.goto("/samples");
    await expect(page).toHaveURL(/\/samples/);
  });

  test("shows a safe bridge instead of ungoverned sample data", async ({ page }) => {
    await page.goto("/samples");
    await expect(page.locator('[data-unification-state="safe-bridge"]')).toBeVisible();
    await expect(page.getByText("مسار انتقالي موحّد")).toBeVisible();
  });
});
