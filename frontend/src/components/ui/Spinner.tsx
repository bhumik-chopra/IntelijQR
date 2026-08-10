import React from "react";
import { cn } from "../../lib/cn";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeMap = {
  sm: "w-4 h-4 border-[1.5px]",
  md: "w-6 h-6 border-2",
  lg: "w-10 h-10 border-[3px]",
};

export const Spinner: React.FC<SpinnerProps> = ({ size = "md", className }) => {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn(
        "rounded-full border-violet-500 border-t-transparent animate-spin",
        sizeMap[size],
        className
      )}
    />
  );
};
