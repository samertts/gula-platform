import { expect, test, type Page } from "@playwright/test";

const viewports = [
  { name: "320px", width: 320, height: 568 },
  { name: "390px", width: 390, height: 844 },
  { name: "desktop", width: 1440, height: 900 },
] as const;

async function expectNoHorizontalOverflow(page: Page) {
  const hasOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(hasOverflow).toBe(false);
}

test.describe("Session authorization bootstrap", () => {
  for (const viewport of viewports) {
    test(`demo mode remains RTL and responsive without authz reads at ${viewport.name}`, async ({
      page,
    }) => {
      const authzRequests: string[] = [];
      page.on("request", (request) => {
        if (request.url().includes("/authz/")) authzRequests.push(request.url());
      });

      // No backend is required for the safe demo path. Return an explicit
      // unauthenticated bootstrap so the login shell renders deterministically
      // instead of waiting on the Vite proxy to an absent API.
      await page.route("**/session", (route) =>
        route.fulfill({ status: 401, contentType: "application/json", body: "{}" }),
      );
      await page.route("**/authz/**", (route) => {
        authzRequests.push(route.request().url());
        return route.fulfill({ status: 401, contentType: "application/json", body: "{}" });
      });
      await page.route("**/auth/refresh", (route) =>
        route.fulfill({ status: 401, contentType: "application/json", body: "{}" }),
      );

      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto("/login");
      await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
      await expectNoHorizontalOverflow(page);

      await page.getByRole("button", { name: "فتح العرض التجريبي الآمن" }).click();
      await expect(page).toHaveURL(/\/dashboard/);
      await expect(page.locator("#main-content")).toBeVisible();
      await expectNoHorizontalOverflow(page);

      expect(authzRequests).toEqual([]);
    });
  }
});
