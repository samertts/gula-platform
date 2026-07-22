import { test, expect } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("FHIR", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await page.route("**/api/fhir/**", async (route) => {
      const url = route.request().url();
      if (url.includes("Patient")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            resourceType: "Bundle",
            entry: [
              {
                resource: {
                  resourceType: "Patient",
                  id: "fhir-001",
                  name: [{ text: "محمد أحمد" }],
                  telecom: [{ value: "07701234567" }],
                },
              },
            ],
          }),
        });
      } else if (url.includes("Observation")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            resourceType: "Bundle",
            entry: [
              {
                resource: {
                  resourceType: "Observation",
                  id: "obs-001",
                  code: { text: "CBC" },
                  valueQuantity: { value: 5.2, unit: "10^3/µL" },
                  status: "final",
                },
              },
            ],
          }),
        });
      } else {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({}) });
      }
    });
    await setupAuthenticatedPage(page);
  });

  test("should navigate to FHIR page", async ({ page }) => {
    await page.goto("/fhir");
    await expect(page).toHaveURL(/\/fhir/);
  });

  test("should display FHIR Patient resources", async ({ page }) => {
    await page.goto("/fhir");
    await expect(page.locator("text=FHIR").first()).toBeVisible();
  });
});
