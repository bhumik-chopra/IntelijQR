import React from "react";
import * as AvatarPrimitive from "@radix-ui/react-avatar";
import { cn } from "../../lib/cn";

interface AvatarProps {
  src?: string;
  name?: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
}

const sizeMap = {
  xs: "w-6 h-6 text-xs",
  sm: "w-8 h-8 text-sm",
  md: "w-10 h-10 text-sm",
  lg: "w-12 h-12 text-base",
  xl: "w-16 h-16 text-lg",
};

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export const Avatar: React.FC<AvatarProps> = ({ src, name, size = "md", className }) => {
  return (
    <AvatarPrimitive.Root
      className={cn(
        "relative flex shrink-0 overflow-hidden rounded-full select-none",
        "ring-2 ring-white/10",
        sizeMap[size],
        className
      )}
    >
      {src && (
        <AvatarPrimitive.Image
          src={src}
          alt={name ?? "Avatar"}
          className="h-full w-full object-cover"
        />
      )}
      <AvatarPrimitive.Fallback
        className={cn(
          "flex h-full w-full items-center justify-center rounded-full font-semibold",
          "bg-gradient-to-br from-violet-600 to-blue-500 text-white"
        )}
      >
        {name ? getInitials(name) : "?"}
      </AvatarPrimitive.Fallback>
    </AvatarPrimitive.Root>
  );
};
