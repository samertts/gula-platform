import { expect, test } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

const invoice = {
  id: 501,
  patient_id: 41,
  encounter_ref: "ENC-E2E-001",
  invoice_number: "GULA-E2E-001",
  status: "draft",
  currency: "IQD",
  gross_amount: "180.00",
  covered_amount: "0.00",
  patient_due: "180.00",
  claim_reference: null,
  due_at: "2026-09-01",
  issued_at: "2026-08-14",
  created_at: "2026-08-14T09:00:00Z",
  lines: [{ id: 1, line_number: 1, service_code: "VISIT", description: "Synthetic visit", quantity: 1, unit_amount: "180.00", line_amount: "180.00" }],
  payments: [],
};

async function mockBillingApi(page: Parameters<typeof test>[0]["page"]) {
  await page.route("**/api/billing/invoices", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([invoice]) });
      return;
    }
    await route.fallback();
  });
  await page.route("**/api/billing/claims", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ id: 601, patient_id: 41, order_id: null, status: "rejected", total_amount: "90.00", currency: "IQD", external_ref: "CLM-E2E-001", submitted_at: "2026-08-14T09:02:00Z", created_at: "2026-08-14T09:00:00Z", updated_at: "2026-08-14T09:05:00Z" }]) });
  });
  await page.route("**/api/billing/coverages", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ id: 701, patient_id: 41, payer: "Synthetic Care Fund", plan: "Basic-A", member_id: "MBR-E2E-001", expires_on: "2026-12-31", state: "needs_verification", verification: "لم يُتحقق", last_checked_at: null, active: true }]) });
  });
  await page.route("**/api/billing/payments", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
  });
  await page.route("**/api/billing/alerts", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ type: "claim_rejected", severity: "high", reference: "601", message: "مطالبة تحتاج مراجعة" }]) });
  });
  await page.route("**/api/billing/invoices/501/simulate-settlement", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...invoice, status: "paid", payments: [{ id: 801, invoice_id: 501, patient_id: 41, amount: "180.00", currency: "IQD", method: "synthetic_settlement", reference: "GULA-E2E-PAY", kind: "patient_payment", created_at: "2026-08-14T09:10:00Z" }] }) });
  });
  await page.route("**/api/billing/claims/601/advance", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ id: 601, patient_id: 41, order_id: null, status: "submitted", total_amount: "90.00", currency: "IQD", external_ref: "CLM-E2E-001", submitted_at: "2026-08-14T09:12:00Z", created_at: "2026-08-14T09:00:00Z", updated_at: "2026-08-14T09:12:00Z" }) });
  });
  await page.route("**/api/billing/coverages/701/verify-local", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ id: 701, patient_id: 41, payer: "Synthetic Care Fund", plan: "Basic-A", member_id: "MBR-E2E-001", expires_on: "2026-12-31", state: "active", verification: "تمت المطابقة في سجل تجريبي محلي", last_checked_at: "2026-08-14T09:13:00Z", active: true }) });
  });
}

test.describe("billing and insurance workspace", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
    await mockBillingApi(page);
    await setupAuthenticatedPage(page);
    await page.goto("/billing-insurance");
    await expect(page.getByRole("heading", { name: "إدارة الفوترة والتأمين الصحي" })).toBeVisible();
  });

  test("hydrates live data and supports guarded backend actions", async ({ page }) => {
    await page.getByRole("button", { name: "الفواتير" }).click();
    await expect(page.getByText("GULA-E2E-001")).toBeVisible();
    await page.getByRole("button", { name: "محاكاة التسوية" }).click();
    await expect(page.getByText("تم تسجيل تسوية backend محاكاة فقط؛ لم يُستدعَ مزود دفع أو تحويل مالي.")).toBeVisible();

    await page.getByRole("button", { name: "المطالبات" }).click();
    await page.getByRole("button", { name: "إعادة معالجة محاكاة" }).click();
    await expect(page.getByText("تم تحديث حالة المطالبة عبر backend التجريبي فقط؛ لم يُرسل أي payload خارجي.")).toBeVisible();

    await page.getByRole("button", { name: "التأمين والتحقق" }).click();
    await page.getByRole("button", { name: "تحقق محلي" }).click();
    await expect(page.getByText("تم تسجيل التحقق المحلي عبر backend فقط؛ لم يتم الاتصال بجهة تأمين خارجية.")).toBeVisible();
  });
});
