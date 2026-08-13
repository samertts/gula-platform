import { test, expect } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("Order workspace read safety", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await setupAuthenticatedPage(page);
  });

  test("navigates to the orders surface", async ({ page }) => {
    await page.goto("/orders");
    await expect(page).toHaveURL(/\/orders/);
    await expect(page.locator('[data-contract-id="orders.read"]')).toBeVisible();
  });

  test("blocks direct order reads until server enforcement is proven", async ({ page }) => {
    await page.goto("/orders");
    await expect(page.getByText("قراءة الطلبات غير متاحة لهذه الجلسة")).toBeVisible();
  });
});
