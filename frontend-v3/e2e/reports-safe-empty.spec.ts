import { expect, test } from "@playwright/test";

test.use({
  launchOptions: {
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ?? "/usr/bin/chromium",
  },
});

const viewports = [
  { name: "الهاتف 320", width: 320, height: 700 },
  { name: "الهاتف 360", width: 360, height: 780 },
  { name: "الهاتف 375", width: 375, height: 812 },
  { name: "الهاتف 390", width: 390, height: 844 },
  { name: "الهاتف 412", width: 412, height: 915 },
  { name: "اللوحي 768", width: 768, height: 1024 },
  { name: "اللوحي 1024", width: 1024, height: 768 },
  { name: "سطح المكتب 1280", width: 1280, height: 800 },
  { name: "سطح المكتب 1440", width: 1440, height: 900 },
] as const;

test.describe("سطح التقارير الآمن", () => {
  for (const viewport of viewports) {
    test(`يعرض حالة آمنة واتجاه RTL على ${viewport.name}`, async ({ page }) => {
      await page.addInitScript(() => {
        window.sessionStorage.setItem("gula_demo_active", "true");
      });

      await page.route("**/api/session", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            user: { id: 0, email: "demo@gula.test", name: "مستخدم المعاينة", role: "master_admin" },
            demo_mode: true,
          }),
        });
      });

      await page.route("**/api/dashboard", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({}),
        });
      });

      await page.setViewportSize(viewport);
      await page.goto("/reports");

      await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
      await expect(page.getByRole("heading", { name: "التقارير" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "لا توجد تقارير تشغيلية معروضة" })).toBeVisible();
      await expect(page.locator('[data-contract-status="unbound"]')).toHaveAttribute("data-governance-state", "safe-empty");
      await expect(page.locator("body")).not.toContainText("تصدير");

      const hasHorizontalOverflow = await page.evaluate(
        () => document.documentElement.scrollWidth > window.innerWidth,
      );
      expect(hasHorizontalOverflow).toBe(false);

      await page.screenshot({
        path: test.info().outputPath(`reports-${viewport.width}.png`),
        fullPage: true,
      });
    });
  }
});
