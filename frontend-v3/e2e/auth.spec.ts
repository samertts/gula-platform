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
        user: {
          id: 1,
          email: TEST_CREDENTIALS.email,
          name: "Admin User",
          role: "admin",
        },
      }),
    });
  });
}

async function mockAuthenticatedRoutes(page: Page) {
  const workspace = {
    id: "workspace-e2e",
    uuid: "workspace-e2e-uuid",
    workspace_type: "facility",
    name: "E2E Finance Workspace",
    name_ar: "مساحة اختبار مالية",
    status: "active",
    organization_id: "org-e2e",
    facility_id: "facility-e2e",
    department_id: null,
    professional_type: null,
    is_personal: false,
  };
  await page.route("**/api/niam/memberships/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        memberships: [
          {
            id: "membership-e2e",
            uuid: "membership-e2e-uuid",
            account_id: "account-e2e",
            identity_id: "identity-e2e",
            organization_id: "org-e2e",
            facility_id: "facility-e2e",
            workspace_id: "workspace-e2e",
            relationship_type: "staff",
            scope_type: "facility",
            status: "active",
            source: "e2e",
            expires_at: null,
            version: 1,
            is_active: true,
          },
        ],
      }),
    });
  });
  await page.route("**/api/niam/workspaces", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ workspaces: [workspace] }),
    });
  });
  await page.route(
    "**/api/niam/workspaces/workspace-e2e/switch",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          context: {
            account_id: "account-e2e",
            identity_id: "identity-e2e",
            workspace_id: workspace.id,
            version: 1,
          },
          workspace,
        }),
      });
    },
  );
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
  test("should display login page with correct Arabic text", async ({
    page,
  }) => {
    await page.goto("/login");
    await expect(page.locator("h2")).toContainText(
      "اختر مسار الوصول المناسب لك",
    );
    await expect(page.locator('label[for="email"]')).toContainText(
      "البريد الإلكتروني",
    );
    await expect(page.locator('label[for="password"]')).toContainText(
      "كلمة المرور",
    );
    await expect(page.locator('button[type="submit"]')).toContainText(
      "الدخول إلى مساحة المواطن",
    );
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
    await expect(
      page.locator("text=تعذر تسجيل الدخول بالبيانات المقدمة."),
    ).toBeVisible();
  });

  test("should login successfully and redirect to dashboard", async ({
    page,
  }) => {
    await mockLogin(page);
    await mockAuthenticatedRoutes(page);

    await page.goto("/login");
    await page.locator("#email").fill(TEST_CREDENTIALS.email);
    await page.locator("#password").fill(TEST_CREDENTIALS.password);
    await page.locator('button[type="submit"]').click();

    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("should redirect to login when accessing protected routes without token", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  test("should show enumeration-resistant recovery request result", async ({ page }) => {
    await page.route("**/auth/forgot-password", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ message: "If the account exists, recovery instructions will be sent." }),
      });
    });

    await page.goto("/recover");
    await page.locator("#recovery-identifier").fill("unknown@example.test");
    await page.getByRole("button", { name: "إرسال طلب الاسترداد" }).click();
    await expect(page.getByRole("status")).toContainText("لم يتم تغيير الحساب بعد");
  });

  test("should sanitize recovery URL and complete server verify/reset flow", async ({ page }) => {
    await page.route("**/auth/recovery/verify", async (route) => {
      const body = route.request().postDataJSON();
      expect(body.token).toBe("test-recovery-token");
      expect(body.request_id).toBe("12345678-1234-1234-1234-123456789012");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "approved", message: "verified" }),
      });
    });
    await page.route("**/auth/reset-password", async (route) => {
      const body = route.request().postDataJSON();
      expect(body.new_password).toBe("NewRecoveryPassword123!");
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: "ok" }) });
    });

    await page.goto("/recover?token=test-recovery-token&request_id=12345678-1234-1234-1234-123456789012");
    await expect(page).toHaveURL(/\/recover$/);
    await page.getByRole("button", { name: "تحقق من الرمز" }).click();
    await page.locator("#new-recovery-password").fill("NewRecoveryPassword123!");
    await page.getByRole("button", { name: "تغيير كلمة المرور" }).click();
    await expect(page.getByRole("status")).toContainText("تم تغيير كلمة المرور");
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
