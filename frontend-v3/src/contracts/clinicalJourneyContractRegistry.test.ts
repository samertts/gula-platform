import { describe, expect, it } from "vitest";
import { canAdvertiseCompleted, GOLDEN_PATH_STAGES, PREVIOUS_WORKSTREAMS, summarizeRemainingWork } from "./clinicalJourneyContractRegistry";

describe("clinicalJourneyContractRegistry", () => {
  it("يوثق جميع مسارات العمل الاثني عشر ويمنع اعتبار المسار الجزئي مكتملًا", () => {
    expect(PREVIOUS_WORKSTREAMS).toHaveLength(12);
    expect(PREVIOUS_WORKSTREAMS.map((workstream) => workstream.id)).toEqual([
      "citizen-identity", "doctor-workspace", "organization", "laboratory", "pharmacy", "radiology",
      "clinic", "hospital", "acute-care", "design-system", "screen-gallery", "master-golden-path",
    ]);
    expect(canAdvertiseCompleted(PREVIOUS_WORKSTREAMS[11])).toBe(false);
    expect(summarizeRemainingWork()).toEqual({ total: 12, complete: 0, partial: 4, blocked: 8 });
  });

  it("يبقي مراحل Golden Path غير المتعاقد عليها في maintenance", () => {
    expect(GOLDEN_PATH_STAGES).toHaveLength(12);
    expect(GOLDEN_PATH_STAGES.filter((stage) => stage.state === "maintenance").map((stage) => stage.id)).toEqual([
      "appointment", "encounter", "lab-order", "specimen", "result", "review", "audit",
    ]);
  });
});
