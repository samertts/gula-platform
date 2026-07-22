import { test, expect } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("Samples", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await page.route("**/api/samples/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            { id: 301, barcode: "SMP-001", patient_name: "محمد أحمد", type: "blood", status: "collected" },
            { id: 302, barcode: "SMP-002", patient_name: "سارة خالد", type: "urine", status: "pending" },
          ],
          total: 2,
        }),
      });
    });
    await setupAuthenticatedPage(page);
  });

  test("should navigate to samples page", async ({ page }) => {
    await page.goto("/samples");
    await expect(page).toHaveURL(/\/samples/);
  });

  test("should display sample barcodes", async ({ page }) => {
    await page.goto("/samples");
    await expect(page.locator("text=SMP-001")).toBeVisible();
  });

  test("should display sample types", async ({ page }) => {
    await page.goto("/samples");
    await expect(page.locator("text=blood").first()).toBeVisible();
  });
});
