import { describe, expect, it } from "vitest";
import { getLocaleDirection, isLocale, localeOptions } from "./locales";

describe("locale contract", () => {
  it("keeps every advertised locale valid and directionally explicit", () => {
    const codes = localeOptions.map((option) => option.code);
    expect(new Set(codes).size).toBe(codes.length);
    for (const option of localeOptions) {
      expect(isLocale(option.code)).toBe(true);
      expect(getLocaleDirection(option.code)).toBe(option.dir);
      expect(option.nativeName.length).toBeGreaterThan(0);
    }
  });

  it("rejects unsupported or empty locale values", () => {
    expect(isLocale("xx")).toBe(false);
    expect(isLocale(null)).toBe(false);
    expect(isLocale(undefined)).toBe(false);
  });
});
