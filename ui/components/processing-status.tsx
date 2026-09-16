"use client";
import { useEffect, useState } from "react";
import type { ProcessingStage } from "@/types";

interface ProcessingStatusProps {
  stage: ProcessingStage;
  label: string;
  detail?: string;
}

const STAGE_ICONS: Record<ProcessingStage, string> = {
  thinking:      "🧠",
  fetching_tools:"🔌",
  calling_llm:   "⚡",
  tool_selected: "🛠️",
  confirming:    "⏳",
  executing:     "⚙️",
  done:          "✓",
  error:         "✕",
};

const STAGE_COLORS: Record<ProcessingStage, string> = {
  thinking:      "#a78bfa",
  fetching_tools:"#60a5fa",
  calling_llm:   "#c084fc",
  tool_selected: "#34d399",
  confirming:    "#fbbf24",
  executing:     "#f97316",
  done:          "#4ade80",
  error:         "#f87171",
};

export function ProcessingStatusIndicator({ stage, label, detail }: ProcessingStatusProps) {
  const [visible, setVisible] = useState(false);
  const color = STAGE_COLORS[stage] ?? "#a78bfa";
  const icon = STAGE_ICONS[stage] ?? "•";
  const isDone = stage === "done";
  const isError = stage === "error";

  useEffect(() => {
    setVisible(false);
    const t = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(t);
  }, [stage]);

  return (
    <div
      className="flex items-start gap-3 px-4 py-3 animate-fade-slide-up"
      style={{
        opacity: visible ? 1 : 0,
        transition: "opacity 0.2s ease",
      }}
    >
      {/* Avatar placeholder */}
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 self-start mt-0.5"
        style={{ background: "var(--accent)" }}
      >
        <svg width="13" height="13" fill="white" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-6h2v2h-2zm0-8h2v6h-2z" />
        </svg>
      </div>

      {/* Status bubble */}
      <div
        className="rounded-2xl px-4 py-2.5 max-w-xs"
        style={{
          background: "var(--bg-elevated)",
          borderBottomRightRadius: "4px",
          border: `1px solid ${color}30`,
        }}
      >
        <div className="flex items-center gap-2">
          {/* Spinner or icon */}
          {!isDone && !isError ? (
            <span
              className="w-3.5 h-3.5 rounded-full border-2 flex-shrink-0 animate-spin-smooth"
              style={{
                borderColor: `${color}40`,
                borderTopColor: color,
              }}
            />
          ) : (
            <span className="text-sm flex-shrink-0">{icon}</span>
          )}

          <span className="text-xs font-medium" style={{ color }}>
            {label}
          </span>
        </div>

        {detail && (
          <div
            className="mt-1 text-[11px] font-mono truncate max-w-[180px]"
            style={{ color: "var(--text-muted)" }}
          >
            {detail}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Processing history timeline (shows all stages) ────────────────────────────

interface StageRecord {
  stage: ProcessingStage;
  label: string;
  detail?: string;
  ts: number;
}

interface ProcessingTimelineProps {
  stages: StageRecord[];
}

export function ProcessingTimeline({ stages }: ProcessingTimelineProps) {
  if (stages.length === 0) return null;

  // Show only latest stage as the active indicator
  const latest = stages[stages.length - 1];
  const isDone = latest.stage === "done";

  // Once done, fade out quickly
  if (isDone) return null;

  return (
    <ProcessingStatusIndicator
      stage={latest.stage}
      label={latest.label}
      detail={latest.detail}
    />
  );
}

export type { StageRecord };
