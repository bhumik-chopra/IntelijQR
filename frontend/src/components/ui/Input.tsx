import React from "react";
import { cn } from "../../lib/cn";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  onIconRightClick?: () => void;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, icon, iconRight, onIconRightClick, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-slate-300"
          >
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          {icon && (
            <span className="absolute left-3.5 flex items-center text-slate-500 pointer-events-none">
              {icon}
            </span>
          )}

          <input
            ref={ref}
            id={inputId}
            className={cn(
              "w-full h-11 bg-white/4 border border-white/8 rounded-xl",
              "text-sm text-slate-200 placeholder:text-slate-600",
              "transition-all duration-200",
              "focus:outline-none focus:border-violet-500/60 focus:bg-white/6 focus:ring-2 focus:ring-violet-500/15",
              "hover:border-white/12 hover:bg-white/5",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              icon ? "pl-10" : "pl-4",
              iconRight ? "pr-10" : "pr-4",
              error && "border-red-500/50 focus:border-red-500/70 focus:ring-red-500/15",
              className
            )}
            {...props}
          />

          {iconRight && (
            <button
              type="button"
              onClick={onIconRightClick}
              className="absolute right-3.5 flex items-center text-slate-500 hover:text-slate-300 transition-colors duration-150 cursor-pointer"
              tabIndex={-1}
            >
              {iconRight}
            </button>
          )}
        </div>

        {error && (
          <p className="text-xs text-red-400 flex items-center gap-1.5">
            <span className="w-1 h-1 rounded-full bg-red-400 inline-block flex-shrink-0" />
            {error}
          </p>
        )}

        {hint && !error && (
          <p className="text-xs text-slate-500">{hint}</p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";
