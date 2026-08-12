import { test, expect, Page } from "@playwright/test";

const TEST_CREDENTIALS = {
  email: "admin@test.com",
  password: "testpassword123",
};

async function mockLogin(page: Page) {
  await page.route("**/api/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "test-token-12345",
        token_type: "bearer",
        user: { id: 1, email: TEST_CREDENTIALS.email, name: "Admin User", role: "admin" },
      }),
    });
  });
}

async function mockAuthenticatedRoutes(page: Page) {
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

  await page.route("**/api/patients/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          { id: 1, full_name: "محمد أحمد", phone: "07701234567", lab_id: 1 },
          { id: 2, full_name: "سارة خالد", phone: "07707654321", lab_id: 1 },
        ],
        total: 2,
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

test.describe("Authentication", () => {
  test("should display login page with correct Arabic text", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h2")).toContainText("مرحباً بعودتك");
    await expect(page.locator('label[for="email"]')).toContainText("البريد الإلكتروني");
    await expect(page.locator('label[for="password"]')).toContainText("كلمة المرور");
    await expect(page.locator('button[type="submit"]')).toContainText("تسجيل الدخول");
  });

  test("should show validation error for empty fields", async ({ page }) => {
    await page.goto("/login");
    await page.locator('button[type="submit"]').click();
    await expect(page.locator("input#email")).toBeVisible();
    await expect(page.locator("input#password")).toBeVisible();
  });

  test("should show error message on failed login", async ({ page }) => {
    await page.route("**/api/login", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "بيانات الاعتماد غير صحيحة" }),
      });
    });

    await page.goto("/login");
    await page.locator("#email").fill(TEST_CREDENTIALS.email);
    await page.locator("#password").fill("wrongpassword");
    await page.locator('button[type="submit"]').click();
    await expect(page.locator("text=بيانات الاعتماد غير صحيحة")).toBeVisible();
  });

  test("should login successfully and redirect to dashboard", async ({ page }) => {
    await mockLogin(page);
    await mockAuthenticatedRoutes(page);

    await page.goto("/login");
    await page.locator("#email").fill(TEST_CREDENTIALS.email);
    await page.locator("#password").fill(TEST_CREDENTIALS.password);
    await page.locator('button[type="submit"]').click();

    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("should redirect to login when accessing protected routes without token", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  test("should logout successfully", async ({ page }) => {
    await mockLogin(page);
    await mockAuthenticatedRoutes(page);

    await page.goto("/login");
    await page.locator("#email").fill(TEST_CREDENTIALS.email);
    await page.locator("#password").fill(TEST_CREDENTIALS.password);
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/\/dashboard/);

    await page.evaluate(() => localStorage.removeItem("access_token"));
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });
});
