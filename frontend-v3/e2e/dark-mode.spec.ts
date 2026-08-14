import { expect, test } from "@playwright/test";

test.use({
  launchOptions: {
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ?? "/usr/bin/chromium",
  },
});

test("يطبق dark mode palette آمنة ومتسقة على سطح التقارير", async ({ page }) => {
  await page.addInitScript(() => {
    window.sessionStorage.setItem("gula_demo_active", "true");
    window.localStorage.setItem("theme", "dark");
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
    await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/reports");
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");

  const colors = await page.evaluate(() => {
    const body = getComputedStyle(document.body);
    return {
      background: body.backgroundColor,
      color: body.color,
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    };
  });

  expect(colors.background).toBe("rgb(16, 32, 43)");
  expect(colors.color).toBe("rgb(230, 240, 244)");
  expect(colors.scrollWidth).toBe(colors.viewportWidth);
});
