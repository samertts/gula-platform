/**
 * Two visible controls must never share one accessible name. IA-087.
 *
 * Below 768px the dashboard shows two buttons that open the same drawer:
 *
 *   DashboardLayout's header hamburger   `lg:hidden`  -> visible < 1024px
 *   MobileBottomNav's disclosure button  `md:hidden`  -> visible <  768px
 *
 * IA-085 gave the second one the first one's label, `mobileNav.openAllSections`.
 * Both were then announced identically, and `e2e/mobile-layout.spec.ts` failed
 * strict mode at 320px and 390px because
 * `getByRole('button', { name: 'فتح جميع الأقسام' })` resolved to 2 elements.
 * Measured on this tree: 2 failed / 1 passed with the shared label, 3 passed
 * without it.
 *
 * The e2e suite is the only place that caught it, it runs on a path filter, and
 * it needs a browser — so it is not a dependable guard. These assertions are,
 * and they are the ones a locale author will trip over first.
 *
 * Substring, not equality, is the rule being enforced. Playwright matches an
 * accessible name by case-insensitive substring unless `exact: true`, so
 * "More" and "More sections" collide just as surely as two identical strings;
 * and the same containment makes the pair ambiguous when read aloud one after
 * the other.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";
import ar from "./ar";
import en from "./en";
import ku from "./ku";
import syr from "./syr";
import tk from "./tk";

const resources = { ar, en, ku, tk, syr } as const;

/** Playwright's own normalisation: trim, collapse whitespace, case-fold. */
function normalise(value: string): string {
  return value.trim().replace(/\s+/g, " ").toLocaleLowerCase();
}

function contains(haystack: string, needle: string): boolean {
  return normalise(haystack).includes(normalise(needle));
}

describe("Navigation accessible names", () => {
  it("covers every shipped locale", () => {
    // Positive control. Without it a renamed or dropped locale would make the
    // loops below iterate over less and still pass.
    expect(Object.keys(resources).sort()).toEqual([
      "ar",
      "en",
      "ku",
      "syr",
      "tk",
    ]);
    expect(Object.keys(resources)).toHaveLength(5);
  });

  for (const [locale, resource] of Object.entries(resources)) {
    describe(locale, () => {
      const nav = resource.mobileNav;

      it("declares both drawer-opening names, non-empty", () => {
        expect(typeof nav.openAllSections).toBe("string");
        expect(typeof nav.moreSections).toBe("string");
        expect(nav.openAllSections.trim()).not.toBe("");
        expect(nav.moreSections.trim()).not.toBe("");
      });

      it("keeps the two drawer-opening names mutually unambiguous", () => {
        expect(normalise(nav.moreSections)).not.toBe(
          normalise(nav.openAllSections),
        );
        expect(
          contains(nav.openAllSections, nav.moreSections),
          `${locale}: the header hamburger's name ${JSON.stringify(
            nav.openAllSections,
          )} contains the bottom-nav button's name ${JSON.stringify(
            nav.moreSections,
          )}. Both buttons are on screen below 768px, so one accessible name ` +
            `would now select both — see IA-087.`,
        ).toBe(false);
        expect(
          contains(nav.moreSections, nav.openAllSections),
          `${locale}: the bottom-nav button's name ${JSON.stringify(
            nav.moreSections,
          )} contains the header hamburger's name ${JSON.stringify(
            nav.openAllSections,
          )}. That is the exact shape of the IA-087 regression.`,
        ).toBe(false);
      });

      it("keeps the bottom-nav button's visible label inside its accessible name", () => {
        // WCAG 2.5.3 Label in Name. The button renders `mobileNav.more` as its
        // visible text, so speech-input users say that word; an accessible
        // name that omits it is unreachable by voice.
        expect(
          contains(nav.moreSections, nav.more),
          `${locale}: visible text ${JSON.stringify(nav.more)} is not part of ` +
            `accessible name ${JSON.stringify(nav.moreSections)} (WCAG 2.5.3).`,
        ).toBe(true);
      });

      it("keeps the bottom-nav button's name from being only its visible label", () => {
        // The IA-085 defect in its original form: an accessible name equal to
        // the visible "More" says nothing about what the button does.
        expect(normalise(nav.moreSections)).not.toBe(normalise(nav.more));
      });
    });
  }
});

/**
 * The string-level assertions above cannot see which component uses which key.
 * This one can: it reads the two sources and checks that the drawer-opening
 * label is claimed by exactly one of them.
 */
describe("Ownership of the drawer-opening label", () => {
  const read = (relative: string) =>
    readFileSync(fileURLToPath(new URL(relative, import.meta.url)), "utf8");

  const header = read("../layouts/DashboardLayout.tsx");
  const bottomNav = read("../components/navigation/MobileBottomNav.tsx");

  it("reads both sources", () => {
    // Positive control: a moved or renamed file must fail here rather than
    // make the assertions below pass against empty strings.
    expect(header).toContain("mobileNav.");
    expect(bottomNav).toContain("mobileNav.");
  });

  it("gives mobileNav.openAllSections to the header hamburger alone", () => {
    expect(header).toContain('t("mobileNav.openAllSections")');
    expect(
      bottomNav.includes('t("mobileNav.openAllSections")'),
      "MobileBottomNav references mobileNav.openAllSections again. That key " +
        "names DashboardLayout's header hamburger, which is on screen at the " +
        "same viewports — this is IA-087.",
    ).toBe(false);
  });

  it("gives mobileNav.moreSections to the bottom-nav button alone", () => {
    expect(bottomNav).toContain('t("mobileNav.moreSections")');
    expect(header.includes('t("mobileNav.moreSections")')).toBe(false);
  });
});

export {};
