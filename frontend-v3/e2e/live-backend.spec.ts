/**
 * The login journey against a REAL backend. No route mocking anywhere.
 *
 * Every other spec in this directory mocks the API with page.route -- auth.spec
 * intercepts **\/api/login outright -- so the whole suite passed while the dev
 * proxy could not reach a backend at all (NR-131). Mocks prove the UI and say
 * nothing about the integration. This spec closes that gap: it drives the real
 * login form, through the real dev proxy, against a real backend, and asserts
 * on what the backend actually returns.
 *
 * It needs infrastructure CI does not have, so it declares that requirement
 * instead of failing without it:
 *
 *     # backend on :8000 with its database, then
 *     GULA_LIVE_BACKEND=1 GULA_ADMIN_EMAIL=... GULA_ADMIN_PASSWORD=... \
 *       npx playwright test e2e/live-backend.spec.ts
 *
 * Skipping is not the same as passing: without the flag these tests report as
 * skipped, never as green.
 */
import { expect, test, type APIRequestContext } from "@playwright/test";

const LIVE = process.env.GULA_LIVE_BACKEND === "1";
const ADMIN_EMAIL = process.env.GULA_ADMIN_EMAIL ?? "";
const ADMIN_PASSWORD = process.env.GULA_ADMIN_PASSWORD ?? "";

/** Tag every identity this run creates, so reruns cannot collide (see NR-133). */
const RUN_TAG = String(Date.now()).slice(-7);
const TENANT_EMAIL = `e2e-live-${RUN_TAG}@gula.test`;
const TENANT_PASSWORD = "Tenant#Passw0rd!1";
const LAB_NAME = `E2E Live Lab ${RUN_TAG}`;

/**
 * Provision a real, approved tenant through the real API.
 *
 * Registration alone is not enough: a lab lands unapproved and cannot log in,
 * which is the fail-closed behaviour the platform is supposed to have. So this
 * registers, then approves as the platform admin would.
 */
async function provisionTenant(request: APIRequestContext): Promise<void> {
  const adminLogin = await request.post("/api/login", {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  });
  expect(
    adminLogin.status(),
    "the platform admin must be able to log in before this spec can provision anything",
  ).toBe(200);
  const adminToken = (await adminLogin.json()).access_token as string;
  const auth = { Authorization: `Bearer ${adminToken}` };

  const registered = await request.post("/api/register", {
    data: {
      lab_name: LAB_NAME,
      admin_name: `${LAB_NAME} Admin`,
      email: TENANT_EMAIL,
      password: TENANT_PASSWORD,
      lab_type: "clinic",
      city: "Baghdad",
      phone: "07700000000",
      license_number: `LIC-E2E-${RUN_TAG}`,
    },
  });
  // Never discard a response this depends on: a silently refused registration
  // surfaces later as "the lab is missing", which says nothing about why.
  expect(
    [200, 201].includes(registered.status()),
    `registration was refused: ${registered.status()} ${await registered.text()}`,
  ).toBe(true);

  const listing = await request.get("/api/admin/labs", { headers: auth });
  expect(listing.status(), "the admin must be able to list labs").toBe(200);
  const labs = await listing.json();
  const rows = (labs.labs ?? []) as { id: number; name: string }[];
  const lab = rows.find((row) => row.name === LAB_NAME);
  expect(
    lab,
    `${LAB_NAME} is not in the ${rows.length} labs the admin can see`,
  ).toBeTruthy();

  const activated = await request.put(`/api/admin/labs/${lab.id}/activate`, { headers: auth });
  expect(activated.status(), "the admin must be able to activate the new lab").toBe(200);
}

test.describe("login against a real backend", () => {
  test.skip(!LIVE, "requires a running backend; set GULA_LIVE_BACKEND=1");
  test.describe.configure({ mode: "serial" });

  test.beforeAll(async ({ playwright, baseURL }) => {
    // The backend refuses cross-origin-shaped writes without an Origin header
    // (POST /api/register answers 403 "Origin or Referer header required").
    // A browser always sends one; a bare API context does not, so this context
    // is given the same origin the page will use.
    const request = await playwright.request.newContext({
      baseURL,
      extraHTTPHeaders: { Origin: baseURL ?? "http://127.0.0.1:5173" },
    });
    try {
      await provisionTenant(request);
    } finally {
      await request.dispose();
    }
  });

  test("the real backend is what answers, not a mock", async ({ request }) => {
    // Positive control for the whole spec. If something were still
    // intercepting, this would not carry a real request id.
    const response = await request.post("/api/login", { data: {} });
    expect(response.status()).toBe(422);
    expect(await response.text()).toContain("detail");
  });

  test("a wrong password is refused by the backend, and the UI says so", async ({ page }) => {
    await page.goto("/login");
    await page.locator("#email").fill(TENANT_EMAIL);
    await page.locator("#password").fill("definitely-not-the-password");
    await page.locator('button[type="submit"]').click();

    // The form must still be there: a failed login may not navigate.
    await expect(page.locator("#password")).toBeVisible();
    await expect(page).not.toHaveURL(/\/dashboard/);
  });

  test("a real credential logs in and reaches the authenticated workspace", async ({ page }) => {
    const loginResponse = page.waitForResponse(
      (r) => r.url().includes("/api/login") && r.request().method() === "POST",
    );

    await page.goto("/login");
    await page.locator("#email").fill(TENANT_EMAIL);
    await page.locator("#password").fill(TENANT_PASSWORD);
    await page.locator('button[type="submit"]').click();

    const response = await loginResponse;
    expect(response.status(), "the real backend must accept this credential").toBe(200);
    const body = await response.json();
    expect(body.access_token, "the backend must mint a real token").toBeTruthy();
    expect(body.user?.email).toBe(TENANT_EMAIL);

    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("the workspace makes authorized calls the backend accepts", async ({ page }) => {
    const statuses: number[] = [];
    page.on("response", (r) => {
      if (r.url().includes("/api/") && !r.url().includes("/api/login")) {
        statuses.push(r.status());
      }
    });

    await page.goto("/login");
    await page.locator("#email").fill(TENANT_EMAIL);
    await page.locator("#password").fill(TENANT_PASSWORD);
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/\/dashboard/);
    await page.waitForLoadState("networkidle");

    expect(statuses.length, "the workspace must actually call the API").toBeGreaterThan(0);
    // 404 is the NR-131 signature: the proxy forwarding /api unstripped.
    expect(statuses.filter((s) => s === 404)).toEqual([]);
  });
});
