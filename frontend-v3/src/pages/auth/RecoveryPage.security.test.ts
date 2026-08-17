import { describe, expect, it } from "vitest";
import { sanitizeRecoveryUrl } from "./RecoveryPage";

describe("recovery deep-link safety", () => {
  it("removes recovery query and fragment material while preserving the path", () => {
    expect(
      sanitizeRecoveryUrl(
        "https://gula.example/recover?token=secret&request_id=req-1#fragment",
      ),
    ).toBe("/recover");
  });

  it("uses the recovery path for relative URLs and never returns query material", () => {
    expect(sanitizeRecoveryUrl("/recover?token=secret")).toBe("/recover");
    expect(sanitizeRecoveryUrl("/recover#token=secret")).toBe("/recover");
  });
});
