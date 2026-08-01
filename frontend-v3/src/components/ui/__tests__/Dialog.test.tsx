import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Dialog } from "@/components/ui/Dialog";
import { Button } from "@/components/ui/Button";

describe("Dialog", () => {
  it("renders nothing when closed", () => {
    render(<Dialog open={false} onClose={() => {}} title="T">body</Dialog>);
    expect(screen.queryByText("T")).not.toBeInTheDocument();
  });

  it("renders title, description and children when open", () => {
    render(
      <Dialog open onClose={() => {}} title="Create" description="A new thing">
        <p>field</p>
      </Dialog>,
    );
    expect(screen.getByText("Create")).toBeInTheDocument();
    expect(screen.getByText("A new thing")).toBeInTheDocument();
    expect(screen.getByText("field")).toBeInTheDocument();
  });

  it("renders footer", () => {
    render(
      <Dialog open onClose={() => {}} title="T" footer={<Button>Save</Button>}>
        body
      </Dialog>,
    );
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
  });

  it("calls onClose when Escape pressed", () => {
    const onClose = vi.fn();
    render(<Dialog open onClose={onClose} title="T">body</Dialog>);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("does not close on Escape when closed", () => {
    const onClose = vi.fn();
    render(<Dialog open={false} onClose={onClose} title="T">body</Dialog>);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).not.toHaveBeenCalled();
  });

  it("restores body overflow after closing", () => {
    const { rerender } = render(<Dialog open onClose={() => {}} title="T">body</Dialog>);
    expect(document.body.style.overflow).toBe("hidden");
    rerender(<Dialog open={false} onClose={() => {}} title="T">body</Dialog>);
    expect(document.body.style.overflow).toBe("");
  });
});
