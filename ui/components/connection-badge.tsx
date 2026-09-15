"use client";
import type { WsConnectionStatus } from "@/types";

const CONFIG: Record<WsConnectionStatus, { label: string; color: string; dot: string }> = {
  connected:    { label: "متصل",         color: "text-green-400",  dot: "bg-green-400" },
  connecting:   { label: "در حال اتصال…", color: "text-yellow-400", dot: "bg-yellow-400" },
  reconnecting: { label: "اتصال مجدد…",  color: "text-yellow-400", dot: "bg-yellow-400 animate-pulse-soft" },
  disconnected: { label: "قطع اتصال",    color: "text-red-400",    dot: "bg-red-400" },
};

export function ConnectionBadge({ status }: { status: WsConnectionStatus }) {
  const c = CONFIG[status];
  return (
    <span className={`flex items-center gap-1.5 text-xs ${c.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}
