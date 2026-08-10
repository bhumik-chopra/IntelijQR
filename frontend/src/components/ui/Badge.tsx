import React from "react";
import { cn } from "../../lib/cn";

type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "purple";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-white/8 text-slate-300 border-white/10",
  success: "bg-emerald-500/12 text-emerald-400 border-emerald-500/20",
  warning: "bg-amber-500/12 text-amber-400 border-amber-500/20",
  danger:  "bg-red-500/12 text-red-400 border-red-500/20",
  info:    "bg-blue-500/12 text-blue-400 border-blue-500/20",
  purple:  "bg-violet-500/12 text-violet-300 border-violet-500/20",
};

const dotStyles: Record<BadgeVariant, string> = {
  default: "bg-slate-400",
  success: "bg-emerald-400",
  warning: "bg-amber-400",
  danger:  "bg-red-400",
  info:    "bg-blue-400",
  purple:  "bg-violet-400",
};

export const Badge: React.FC<BadgeProps> = ({
  variant = "default",
  dot = false,
  className,
  children,
  ...props
}) => {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5",
        "text-xs font-medium rounded-full border",
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            "w-1.5 h-1.5 rounded-full flex-shrink-0",
            dotStyles[variant]
          )}
        />
      )}
      {children}
    </span>
  );
};
