import React from "react";
import { cn } from "../../lib/cn";

type ButtonVariant = "primary" | "ghost" | "outline" | "danger" | "secondary";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  fullWidth?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: [
    "relative overflow-hidden text-white font-semibold",
    "bg-gradient-to-r from-violet-600 to-blue-500",
    "shadow-lg shadow-violet-900/40",
    "before:absolute before:inset-0 before:bg-white/0 before:transition-all before:duration-300",
    "hover:before:bg-white/10 hover:shadow-violet-700/50 hover:scale-[1.02]",
    "active:scale-[0.98]",
  ].join(" "),

  secondary: [
    "bg-white/5 text-slate-200 font-medium border border-white/8",
    "hover:bg-white/10 hover:border-white/15 hover:text-white",
    "active:scale-[0.98]",
  ].join(" "),

  ghost: [
    "text-slate-400 font-medium",
    "hover:text-white hover:bg-white/6",
    "active:scale-[0.98]",
  ].join(" "),

  outline: [
    "border border-white/12 text-slate-300 font-medium",
    "hover:border-violet-500/60 hover:text-violet-300 hover:bg-violet-500/5",
    "active:scale-[0.98]",
  ].join(" "),

  danger: [
    "bg-red-500/10 text-red-400 font-medium border border-red-500/20",
    "hover:bg-red-500/20 hover:border-red-500/40 hover:text-red-300",
    "active:scale-[0.98]",
  ].join(" "),
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-sm rounded-lg gap-1.5",
  md: "h-10 px-5 text-sm rounded-xl gap-2",
  lg: "h-12 px-7 text-base rounded-xl gap-2.5",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      icon,
      iconRight,
      fullWidth = false,
      className,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          "inline-flex items-center justify-center",
          "cursor-pointer select-none",
          "transition-all duration-200",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/60 focus-visible:ring-offset-2 focus-visible:ring-offset-transparent",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:scale-100",
          variantStyles[variant],
          sizeStyles[size],
          fullWidth && "w-full",
          className
        )}
        {...props}
      >
        {loading ? (
          <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        ) : (
          icon && <span className="flex-shrink-0">{icon}</span>
        )}
        {children && <span>{children}</span>}
        {!loading && iconRight && <span className="flex-shrink-0">{iconRight}</span>}
      </button>
    );
  }
);
Button.displayName = "Button";
