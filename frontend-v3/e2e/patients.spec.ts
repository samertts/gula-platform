import { test, expect } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("Patient workspace read safety", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await setupAuthenticatedPage(page);
  });

  test("navigates to the patients surface", async ({ page }) => {
    await page.goto("/patients");
    await expect(page).toHaveURL(/\/patients/);
    await expect(page.locator('[data-contract-id="patients.read"]')).toBeVisible();
  });

  test("blocks direct patient reads until server enforcement is proven", async ({ page }) => {
    await page.goto("/patients");
    await expect(page.getByText("قراءة المرضى غير متاحة لهذه الجلسة")).toBeVisible();
  });
});
