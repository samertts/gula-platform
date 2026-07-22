import { test, expect } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("Navigation & Routing", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await page.route("**/api/**", async (route) => {
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
