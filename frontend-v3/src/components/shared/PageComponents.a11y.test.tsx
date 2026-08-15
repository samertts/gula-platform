import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";
import { LoadingSpinner, PageLoadingSkeleton } from "./PageComponents";

describe("Page loading states accessibility", () => {
  it("exposes an accessible live status for the page skeleton", async () => {
    const { container } = render(<PageLoadingSkeleton />);

    expect(screen.getByRole("status", { name: "جارٍ تحميل الصفحة" })).toHaveAttribute("aria-busy", "true");
    expect(screen.getByText("جارٍ تحميل الصفحة")).toBeInTheDocument();

    const results = await axe(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });

  it("keeps the compact spinner discoverable to assistive technology", () => {
    render(<LoadingSpinner />);

    expect(screen.getByRole("status", { name: "جارٍ التحميل" })).toHaveAttribute("aria-live", "polite");
  });
});
