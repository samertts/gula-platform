import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api/client";
import {
  clinicalAppointmentApi,
  clinicalDiagnosticReportApi,
} from "@/api/endpoints";

describe("canonical clinical endpoint contracts", () => {
  afterEach(() => vi.restoreAllMocks());

  it("uses the server-authoritative Appointment lifecycle paths", async () => {
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: { id: "appointment-1" } } as never);
    const getSpy = vi.spyOn(api, "get").mockResolvedValue({ data: { items: [], limit: 100, offset: 0, workspace_id: "workspace-1" } } as never);

    await clinicalAppointmentApi.create({
      patient_id: "patient-1",
      appointment_type: "consultation",
      start_at: "2026-08-22T09:00:00Z",
      end_at: "2026-08-22T09:30:00Z",
      idempotency_key: "appointment-key-1",
    });
    await clinicalAppointmentApi.list({ status: "booked", limit: 20, offset: 0 });
    await clinicalAppointmentApi.reschedule("appointment-1", {
      start_at: "2026-08-22T10:00:00Z",
      end_at: "2026-08-22T10:30:00Z",
      expected_version: 1,
    });
    await clinicalAppointmentApi.cancel("appointment-1", { expected_version: 2, reason: "patient request" });

    expect(postSpy).toHaveBeenNthCalledWith(
      1,
      "/api/v1/clinical/appointments",
      expect.not.objectContaining({ practitioner_id: expect.anything(), facility_id: expect.anything() }),
    );
    expect(getSpy).toHaveBeenCalledWith("/api/v1/clinical/appointments", {
      params: { status: "booked", limit: 20, offset: 0 },
    });
    expect(postSpy).toHaveBeenCalledWith(
      "/api/v1/clinical/appointments/appointment-1/cancel",
      { expected_version: 2, reason: "patient request" },
    );
  });

  it("uses the canonical DiagnosticReport source, review, and amendment paths", async () => {
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: { id: "report-1" } } as never);
    const getSpy = vi.spyOn(api, "get").mockResolvedValue({ data: { id: "report-1" } } as never);

    await clinicalDiagnosticReportApi.createFromLabOrder(41);
    await clinicalDiagnosticReportApi.createFromRadiologyReport("radiology/42");
    await clinicalDiagnosticReportApi.get("report-1");
    await clinicalDiagnosticReportApi.finalize("report-1", { expected_version: 1 });
    await clinicalDiagnosticReportApi.amend("report-1", { expected_version: 2, reason: "corrected interpretation" });

    expect(postSpy).toHaveBeenNthCalledWith(1, "/api/v1/clinical/diagnostic-reports/from-lab-orders/41");
    expect(postSpy).toHaveBeenNthCalledWith(2, "/api/v1/clinical/diagnostic-reports/from-radiology-reports/radiology%2F42");
    expect(postSpy).toHaveBeenNthCalledWith(3, "/api/v1/clinical/diagnostic-reports/report-1/finalize", { expected_version: 1 });
    expect(postSpy).toHaveBeenNthCalledWith(4, "/api/v1/clinical/diagnostic-reports/report-1/amend", {
      expected_version: 2,
      reason: "corrected interpretation",
    });
    expect(getSpy).toHaveBeenCalledWith("/api/v1/clinical/diagnostic-reports/report-1");
  });
});
