import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button } from "./Button";

describe("Button visual accessibility states", () => {
  it("exposes a busy state while loading", () => {
    render(
      <Button loading type="button">
        حفظ
      </Button>,
    );

    const button = screen.getByRole("button", { name: "حفظ" });
    expect(button).toHaveAttribute("aria-busy", "true");
    expect(button).toBeDisabled();
  });

  it("does not expose a busy state when idle", () => {
    render(<Button type="button">متابعة</Button>);

    expect(screen.getByRole("button", { name: "متابعة" })).not.toHaveAttribute(
      "aria-busy",
    );
  });
});
