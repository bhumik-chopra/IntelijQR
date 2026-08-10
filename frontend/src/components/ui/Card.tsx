import React from "react";
import { cn } from "../../lib/cn";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glass?: boolean;
  glow?: boolean;
  hover?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

const paddingMap = {
  none: "",
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ glass = false, glow = false, hover = false, padding = "md", className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "relative rounded-2xl border overflow-hidden",
          "transition-all duration-300",
          glass
            ? "bg-white/4 backdrop-blur-xl border-white/8"
            : "bg-[#141428] border-white/7",
          glow && "shadow-[0_0_40px_rgba(124,58,237,0.12)]",
          hover && [
            "cursor-pointer",
            "hover:border-white/15 hover:bg-white/6",
            glow && "hover:shadow-[0_0_60px_rgba(124,58,237,0.2)]",
          ],
          paddingMap[padding],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = "Card";
