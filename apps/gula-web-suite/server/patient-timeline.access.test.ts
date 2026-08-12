import { describe, expect, it } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";
import { getPatientUnifiedTimeline, sortPatientTimelineEntries, type PatientTimelineEntry } from "./db";

function createContext(role: "lab_staff" | "patient"): TrpcContext {
  return {
    user: {
      id: 71,
      openId: "timeline-access-test",
      institutionId: 8,
      laboratoryId: 3,
      name: "Access Test",
      email: "access@example.test",
      loginMethod: "manus",
      role,
      accountStatus: "active",
      staffIdentifier: null,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

describe("lis.patientTimeline authorization", () => {
  it("returns an empty timeline immediately for an unavailable identity", async () => {
    await expect(getPatientUnifiedTimeline(-1, null)).resolves.toEqual([]);
  });

  it("preserves every supported source and orders events most-recent-first", () => {
    const now = new Date("2026-08-11T12:00:00.000Z");
    const sources: PatientTimelineEntry["source"][] = ["laboratory", "clinical", "alerts", "radiology", "pharmacy", "hospital", "emergency"];
    const entries = sources.map((source, index): PatientTimelineEntry => ({
      id: source,
      source,
      kind: "test",
      title: source,
      detail: null,
      status: "documented",
      isCritical: false,
      occurredAt: new Date(now.getTime() - index * 60_000),
    }));

    const ordered = sortPatientTimelineEntries([...entries].reverse());

    expect(new Set(ordered.map((entry) => entry.source))).toEqual(new Set(sources));
    expect(ordered.map((entry) => entry.id)).toEqual(sources);
  });

  it("rejects a clinical staff account before accessing any patient history", async () => {
    const caller = appRouter.createCaller(createContext("lab_staff"));

    await expect(caller.lis.patientTimeline()).rejects.toMatchObject({ code: "FORBIDDEN" });
  });
});
