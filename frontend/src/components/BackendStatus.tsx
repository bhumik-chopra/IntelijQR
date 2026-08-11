import React from "react";
import { RefreshCw, Server, ServerOff } from "lucide-react";

import { useBackendStatus } from "../hooks/useBackendStatus";
import { cn } from "../lib/cn";

interface BackendStatusProps {
  compact?: boolean;
  className?: string;
}

const styles = {
  online: {
    shell: "border-emerald-500/25 bg-emerald-500/8 text-emerald-300 hover:bg-emerald-500/12",
    icon: "bg-emerald-500/12 text-emerald-300",
    dot: "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)]",
    label: "Online",
  },
  offline: {
    shell: "border-red-500/25 bg-red-500/8 text-red-300 hover:bg-red-500/12",
    icon: "bg-red-500/12 text-red-300",
    dot: "bg-red-400 shadow-[0_0_10px_rgba(248,113,113,0.75)]",
    label: "Offline",
  },
  checking: {
    shell: "border-amber-500/25 bg-amber-500/8 text-amber-300",
    icon: "bg-amber-500/12 text-amber-300",
    dot: "bg-amber-400",
    label: "Checking",
  },
} as const;

export const BackendStatus: React.FC<BackendStatusProps> = ({ compact = false, className }) => {
  const { status, lastChecked, checkNow } = useBackendStatus();
  const appearance = styles[status];
  const Icon = status === "offline" ? ServerOff : Server;
  const checkedLabel = lastChecked ? `Last checked ${lastChecked.toLocaleTimeString()}` : "Checking backend now";

  return (
    <button
      type="button"
      onClick={() => void checkNow()}
      className={cn(
        "group inline-flex h-9 items-center rounded-xl border transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/60",
        compact ? "gap-2 px-2.5" : "gap-2.5 px-2 pr-3",
        appearance.shell,
        className,
      )}
      aria-label={`Backend ${appearance.label}. Click to check again.`}
      title={`${appearance.label} · ${checkedLabel} · Click to retry`}
    >
      {!compact && (
        <span className={cn("flex h-6 w-6 items-center justify-center rounded-lg", appearance.icon)}>
          <Icon className="h-3.5 w-3.5" />
        </span>
      )}
      <span className="relative flex h-2.5 w-2.5 items-center justify-center">
        {status === "online" && <span className="absolute h-full w-full animate-ping rounded-full bg-emerald-400/35" />}
        <span className={cn("relative h-2 w-2 rounded-full", appearance.dot)} />
      </span>
      <span className={cn("whitespace-nowrap font-semibold", compact ? "text-xs" : "text-[11px]")}>
        {compact ? appearance.label : `Backend ${appearance.label}`}
      </span>
      {status === "checking" && <RefreshCw className="h-3 w-3 animate-spin" />}
    </button>
  );
};
