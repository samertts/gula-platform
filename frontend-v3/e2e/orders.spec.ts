import { test, expect } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("Laboratory Orders", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await page.route("**/api/orders**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            { id: 101, patient_name: "محمد أحمد", test: "CBC", status: "pending", created_at: "2026-07-22" },
            { id: 102, patient_name: "سارة خالد", test: "TSH", status: "completed", created_at: "2026-07-22" },
          ],
          total: 2,
        }),
      });
    });
    await setupAuthenticatedPage(page);
  });

  test("should navigate to orders page", async ({ page }) => {
    await page.goto("/orders");
    await expect(page).toHaveURL(/\/orders/);
  });

  test("should display orders list", async ({ page }) => {
    await page.goto("/orders");
    await expect(page.locator("text=محمد أحمد")).toBeVisible();
  });

  test("should display order status badges", async ({ page }) => {
    await page.goto("/orders");
    await expect(page.locator("text=pending").first()).toBeVisible();
    await expect(page.locator("text=completed").first()).toBeVisible();
  });
});
