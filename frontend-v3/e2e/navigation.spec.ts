import { test, expect } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("Navigation & Routing", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await page.route("**/*", async (route) => {
      const pathname = new URL(route.request().url()).pathname;
      if (!pathname.startsWith("/api/")) {
        await route.fallback();
        return;
      }
      if (pathname === "/api/session" || pathname === "/api/login" || pathname === "/api/auth/refresh" || pathname.startsWith("/api/niam/")) {
        await route.fallback();
        return;
      }
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({}) });
    });
    await setupAuthenticatedPage(page);
  });

  const protectedRoutes = [
    { path: "/dashboard", name: "Dashboard" },
    { path: "/patients", name: "Patients" },
    { path: "/orders", name: "Orders" },
    { path: "/results", name: "Results" },
    { path: "/samples", name: "Samples" },
    { path: "/labs", name: "Labs" },
    { path: "/alerts", name: "Critical Alerts" },
    { path: "/notifications", name: "Notifications" },
    { path: "/ai", name: "AI" },
    { path: "/stats", name: "Stats" },
    { path: "/qc", name: "QC" },
    { path: "/patient-card", name: "Patient Card" },
    { path: "/identity", name: "Identity" },
    { path: "/compliance", name: "Compliance" },
    { path: "/settings", name: "Settings" },
    { path: "/profile", name: "Profile" },
    { path: "/security", name: "Security" },
    { path: "/fhir", name: "FHIR" },
    { path: "/ehr", name: "EHR" },
    { path: "/hospital", name: "Hospital" },
    { path: "/edge", name: "Edge" },
    { path: "/national-data", name: "National Data" },
  ];

  for (const route of protectedRoutes) {
    test(`should navigate to ${route.name} page`, async ({ page }) => {
      await page.goto(route.path);
      await expect(page).toHaveURL(new RegExp(route.path.replace("/", "\\/")));
    });
  }
});
