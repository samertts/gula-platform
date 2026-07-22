import { test, expect, type Page } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("Patient Search", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await page.route("**/api/patients/**", async (route) => {
      const url = route.request().url();
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(
          url.includes("search")
            ? {
                items: [
                  { id: 3, full_name: "محمود علي", phone: "07701111111", lab_id: 1 },
                ],
                total: 1,
              }
            : {
                items: [
                  { id: 1, full_name: "محمد أحمد", phone: "07701234567", lab_id: 1 },
                  { id: 2, full_name: "سارة خالد", phone: "07707654321", lab_id: 1 },
                  { id: 3, full_name: "محمود علي", phone: "07701111111", lab_id: 1 },
                ],
                total: 3,
              },
        ),
      });
    });
    await setupAuthenticatedPage(page);
  });

  test("should navigate to patients page", async ({ page }) => {
    await page.goto("/patients");
    await expect(page).toHaveURL(/\/patients/);
  });

  test("should display patients list after login", async ({ page }) => {
    await page.goto("/patients");
    await expect(page.locator("text=محمد أحمد")).toBeVisible();
  });
});
