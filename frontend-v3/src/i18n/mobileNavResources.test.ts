import { describe, expect, it } from "vitest";
import ar from "./ar";
import en from "./en";
import fa from "./fa";
import ku from "./ku";
import syr from "./syr";
import tk from "./tk";
import { getLocaleDirection, localeOptions } from "./locales";

const resources = { ar, en, ku, tk, syr, fa } as const;

function flattenKeys(value: unknown, prefix = ""): string[] {
  if (!value || typeof value !== "object") return prefix ? [prefix] : [];
  return Object.entries(value as Record<string, unknown>).flatMap(
    ([key, child]) => flattenKeys(child, prefix ? `${prefix}.${key}` : key),
  );
}

const requiredMobileNavKeys = [
  "quickNavigation",
  "openAllSections",
  "more",
  "current",
  "skipToContent",
  "changeLanguage",
  "closeSections",
  "expandSidebar",
  "collapseSidebar",
  "operationsCenter",
  "userFallback",
  "readOnly",
  "syntheticReadOnly",
] as const;

const requiredGroupKeys = [
  "main",
  "lab",
  "admin",
  "tools",
  "niam",
  "enterprise",
  "clinical",
  "national",
  "systems",
  "settings",
] as const;

describe("Mobile Bottom Nav i18n resources", () => {
  it("provides every navigation and accessibility key in all local UI resources", () => {
    for (const [locale, resource] of Object.entries(resources)) {
      for (const key of requiredMobileNavKeys) {
        expect(resource.mobileNav[key], `${locale}.${key}`).toEqual(
          expect.any(String),
        );
        expect(resource.mobileNav[key], `${locale}.${key}`).not.toBe("");
      }

      for (const key of requiredGroupKeys) {
        expect(
          resource.mobileNav.groups[key],
          `${locale}.groups.${key}`,
        ).toEqual(expect.any(String));
      }
    }
  });

  it("keeps the local navigation resources aligned with their declared directions", () => {
    expect(Object.keys(resources).sort()).toEqual([
      "ar",
      "en",
      "fa",
      "ku",
      "syr",
      "tk",
    ]);
    expect(getLocaleDirection("ar")).toBe("rtl");
    expect(getLocaleDirection("en")).toBe("ltr");
    expect(getLocaleDirection("ku")).toBe("rtl");
    expect(getLocaleDirection("tk")).toBe("ltr");
    expect(getLocaleDirection("syr")).toBe("rtl");

    expect(getLocaleDirection("fa")).toBe("rtl");

    const supported = localeOptions.map((option) => option.code);
    expect(supported).toEqual(
      expect.arrayContaining(["ar", "en", "fa", "ku", "tk", "syr"]),
    );
  });

  it("keeps the complete Persian resource structurally aligned with English", () => {
    expect(flattenKeys(fa).sort()).toEqual(flattenKeys(en).sort());
    for (const key of flattenKeys(fa)) {
      const value = key
        .split(".")
        .reduce<unknown>(
          (current, segment) =>
            current && typeof current === "object"
              ? (current as Record<string, unknown>)[segment]
              : undefined,
          fa,
        );
      expect(value, `fa.${key}`).toEqual(expect.any(String));
      expect(value, `fa.${key}`).not.toBe("");
    }
  });
});

export {};
