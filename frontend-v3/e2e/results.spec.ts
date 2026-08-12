import { test, expect } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("Results", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await page.route("**/api/test-results**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            { id: 201, order_id: 101, test_name: "CBC", value: "5.2", unit: "10^3/µL", ref_range: "4.5-11.0", status: "validated" },
            { id: 202, order_id: 102, test_name: "TSH", value: "2.8", unit: "mIU/L", ref_range: "0.4-4.0", status: "pending" },
          ],
          total: 2,
        }),
      });
    });
    await setupAuthenticatedPage(page);
  });

  test("should navigate to results page", async ({ page }) => {
    await page.goto("/results");
    await expect(page).toHaveURL(/\/results/);
  });

  test("should display test results", async ({ page }) => {
    await page.goto("/results");
    await expect(page.locator("text=CBC").first()).toBeVisible();
  });
});
