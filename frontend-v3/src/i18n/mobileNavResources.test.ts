import { describe, expect, it } from "vitest";
import ar from "./ar";
import en from "./en";
import ku from "./ku";
import syr from "./syr";
import tk from "./tk";
import { getLocaleDirection, localeOptions } from "./locales";

const resources = { ar, en, ku, tk, syr } as const;

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
    expect(Object.keys(resources).sort()).toEqual(["ar", "en", "ku", "syr", "tk"]);
    expect(getLocaleDirection("ar")).toBe("rtl");
    expect(getLocaleDirection("en")).toBe("ltr");
    expect(getLocaleDirection("ku")).toBe("rtl");
    expect(getLocaleDirection("tk")).toBe("ltr");
    expect(getLocaleDirection("syr")).toBe("rtl");


    const supported = localeOptions.map((option) => option.code);
    expect(supported).toEqual(["ar", "en", "ku", "tk", "syr"]);
  });

});

export {};
