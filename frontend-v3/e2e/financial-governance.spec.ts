import { expect, test } from "@playwright/test";
import { mockLogin, setupAuthenticatedPage } from "./helpers";

test.describe("financial governance workspace", () => {
  test("loads tenant-scoped control summary without external operations", async ({ page }) => {
    await mockLogin(page);
    await page.route("**/api/payments/controls/summary**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          institution_id: 1,
          as_of: "2026-08-14T09:00:00Z",
          currency: "IQD",
          billed_amount: "1000.00",
          collected_amount: "700.00",
          outstanding_amount: "300.00",
          refunded_amount: "0.00",
          invoice_count: 4,
          control_requests: { REQUESTED: 1, APPROVED: 0, APPLIED: 2 },
          open_reconciliation_cases: 0,
          cash_variance_cases: 0,
          live_operation_enabled: false,
          external_provider_calls: 0,
          data_basis: "PaymentInvoice facts",
          limitations: ["No forecast, valuation, ROI, or investment return is calculated"],
        }),
      });
    });
    await page.route("**/api/payments/controls/requests**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          count: 1,
          items: [{
            id: "ctl-e2e-001",
            institution_id: 1,
            control_type: "provider_approval",
            resource_type: "payment_provider",
            resource_id: "sandbox-provider",
            requested_action: "approve_for_advisory_routing",
            status: "REQUESTED",
            reason: "Quarterly control review",
            requested_by: 11,
            approved_by: null,
            applied_by: null,
            external_operation: false,
            requested_at: "2026-08-14T09:00:00Z",
          }],
        }),
      });
    });

    await setupAuthenticatedPage(page);
    await page.goto("/financial-governance");
    await expect(page.getByRole("heading", { name: "الحوكمة المالية والجاهزية الاستثمارية" })).toBeVisible();
    await expect(page.getByText("١٬٠٠٠ IQD")).toBeVisible();
    await expect(page.getByText("approve_for_advisory_routing")).toBeVisible();
    await expect(page.getByText("استدعاءات مزود خارجي")).toBeVisible();
    await expect(page.getByText("لا تحسب valuation أو ROI أو توقعات نمو")).toBeVisible();
  });
});
