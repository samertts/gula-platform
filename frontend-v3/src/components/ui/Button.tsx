import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const variants = {
  default:
    "bg-[#0D9488] text-white shadow-[0_10px_22px_-14px_rgba(13,148,136,0.9)] hover:bg-[#0F766E]",
  destructive:
    "bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-xs",
  outline:
    "border border-slate-200 bg-background hover:border-teal-200 hover:bg-teal-50/60 hover:text-[#0D9488] dark:border-white/10 dark:hover:border-teal-800 dark:hover:bg-teal-950/25",
  secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
  ghost: "hover:bg-accent hover:text-accent-foreground",
  link: "text-primary underline-offset-4 hover:underline",
} as const;

const sizes = {
  default: "h-10 rounded-xl px-4 py-2",
  sm: "h-8 rounded-lg px-3 text-xs",
  lg: "h-11 rounded-xl px-8",
  icon: "h-10 w-10 rounded-xl",
} as const;

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
  loading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "default",
      size = "default",
      loading,
      disabled,
      children,
      ...props
    },
    ref,
  ) => (
    <button
      ref={ref}
      className={cn(
        "gula-focus-ring inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-semibold motion-safe:transition-[color,background-color,border-color,box-shadow,transform,opacity] motion-safe:duration-150 motion-safe:ease-out active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
        variants[variant],
        sizes[size],
        className,
      )}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {children}
    </button>
  ),
);
Button.displayName = "Button";

export { Button, type ButtonProps };
