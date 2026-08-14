import { expect, test, type Page } from "@playwright/test";

const viewports = [
  { name: "320px", width: 320, height: 568 },
  { name: "390px", width: 390, height: 844 },
  { name: "desktop", width: 1440, height: 900 },
] as const;

async function expectNoHorizontalOverflow(page: Page) {
  const hasOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(hasOverflow).toBe(false);
}

test.describe("Mobile app-like shell", () => {
  for (const viewport of viewports) {
    test(`keeps login and demo dashboard usable at ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto("/login");
      await expect(page.getByRole("heading", { name: "اختر مسار الوصول المناسب لك" })).toBeVisible();
      await expectNoHorizontalOverflow(page);

      await page.getByRole("button", { name: "فتح العرض التجريبي الآمن" }).click();
      await expect(page).toHaveURL(/\/dashboard/);
      await expectNoHorizontalOverflow(page);
      await expect(page.locator("#main-content")).toBeVisible();

      if (viewport.width < 768) {
        await expect(page.getByRole("navigation", { name: "التنقل السريع" })).toBeVisible();
        await expect(page.getByRole("button", { name: "فتح جميع الأقسام" })).toBeVisible();
        await page.getByRole("button", { name: "فتح جميع الأقسام" }).click();
        await expect(page.locator('aside[aria-label="التنقل الرئيسي"]')).toBeVisible();
        await page.getByRole("button", { name: "إغلاق القائمة" }).click({ position: { x: 4, y: 4 } });
      } else {
        await expect(page.getByRole("navigation", { name: "التنقل السريع" })).toBeHidden();
      }
    });
  }
});
