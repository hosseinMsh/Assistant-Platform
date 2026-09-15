"use client";
import type { ChatMessage, ExecutionStatus } from "@/types";

const STATUS_CONFIG: Record<ExecutionStatus, { label: string; color: string; icon: string }> = {
  pending:              { label: "در انتظار تأیید…",   color: "#fbbf24", icon: "⏳" },
  confirmed:            { label: "تأیید شد",           color: "#60a5fa", icon: "✓" },
  executing:            { label: "در حال اجرا…",       color: "#a78bfa", icon: "⚡" },
  success:              { label: "انجام شد",            color: "#4ade80", icon: "✓" },
  failed:               { label: "ناموفق",              color: "#f87171", icon: "✕" },
  cancelled:            { label: "لغو شد",             color: "#6b7280", icon: "–" },
};

function TypingDots() {
  return (
    <span className="dot-bounce inline-flex gap-1 items-center py-0.5">
      <span /><span /><span />
    </span>
  );
}

function StatusPill({ status }: { status: ExecutionStatus }) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span
      className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full mt-1.5"
      style={{ background: `${cfg.color}15`, color: cfg.color, border: `1px solid ${cfg.color}30` }}
    >
      <span>{cfg.icon}</span>
      {cfg.label}
    </span>
  );
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isEmpty = !message.content && !message.executionStatus;

  return (
    <div
      className={`flex gap-2.5 animate-fade-slide-up ${isUser ? "flex-row-reverse" : "flex-row"} mb-5`}
    >
      {/* Avatar */}
      {!isUser && (
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 self-end mb-1"
          style={{ background: "var(--accent)" }}
        >
          <svg width="13" height="13" fill="white" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-6h2v2h-2zm0-8h2v6h-2z"/>
          </svg>
        </div>
      )}

      <div className={`max-w-[75%] flex flex-col ${isUser ? "items-end" : "items-start"}`}>
        <div
          className="px-4 py-2.5 rounded-2xl text-sm leading-relaxed"
          style={isUser
            ? { background: "var(--accent)", color: "white", borderBottomLeftRadius: "4px" }
            : { background: "var(--bg-elevated)", color: "var(--text-primary)", borderBottomRightRadius: "4px" }
          }
        >
          {isEmpty ? <TypingDots /> : message.content}
        </div>
        {message.executionStatus && (
          <StatusPill status={message.executionStatus} />
        )}
      </div>

      {isUser && (
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 self-end mb-1"
          style={{ background: "var(--bg-hover)" }}
        >
          <svg width="13" height="13" fill="var(--text-secondary)" viewBox="0 0 24 24">
            <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
          </svg>
        </div>
      )}
    </div>
  );
}
