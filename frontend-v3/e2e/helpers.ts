import { type Page } from "@playwright/test";

export const TEST_CREDENTIALS = {
  email: "admin@test.com",
  password: "testpassword123",
};

export async function mockLogin(page: Page) {
  await page.route("**/api/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "test-token-12345",
        token_type: "bearer",
        user: {
          id: 1,
          email: TEST_CREDENTIALS.email,
          name: "Admin User",
          role: "admin",
        },
      }),
    });
  });

  await page.route("**/api/dashboard/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        total_patients: 150,
        total_orders: 320,
        pending_results: 12,
        critical_alerts: 3,
        recent_activity: [],
      }),
    });
  });

  await page.route("**/api/notifications/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });
}

export async function setupAuthenticatedPage(page: Page) {
  await page.goto("/login");
  await page.locator("#email").fill(TEST_CREDENTIALS.email);
  await page.locator("#password").fill(TEST_CREDENTIALS.password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(/\/dashboard/);
}
