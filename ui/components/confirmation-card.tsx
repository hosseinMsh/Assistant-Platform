"use client";
import type { ConfirmationState } from "@/types";

// ── Tool-specific display config (extensible) ──────────────────────────────────
// Add new entries here when new tools are added — no other file needs to change.

interface ToolDisplayConfig {
  icon: string;
  headerColor: string;
  /** Fields to show in the preview, in order. null = skip */
  fields: Array<{
    key: string;
    label: string;
    format?: (v: unknown) => string;
  }>;
}

const TOOL_DISPLAY: Record<string, ToolDisplayConfig> = {
  "notify.send_one": {
    icon: "🔔",
    headerColor: "var(--accent)",
    fields: [
      { key: "userName", label: "گیرنده" },
      {
        key: "providerType",
        label: "کانال",
        format: (v) => {
          const map: Record<number, string> = { 1: "پیامک", 2: "پیام‌رسان بله", 3: "ایمیل" };
          return map[v as number] ?? String(v);
        },
      },
      { key: "subject", label: "موضوع" },
      { key: "message", label: "متن پیام" },
      {
        key: "sendingDate",
        label: "زمان ارسال",
        format: (v) => new Date(v as string).toLocaleString("fa-IR"),
      },
    ],
  },
  "notify.send_bulk": {
    icon: "📢",
    headerColor: "#f97316",
    fields: [
      { key: "message", label: "متن پیام" },
      {
        key: "providerType",
        label: "کانال",
        format: (v) => {
          const map: Record<number, string> = { 1: "پیامک", 2: "بله", 3: "ایمیل" };
          return map[v as number] ?? String(v);
        },
      },
      { key: "subject", label: "موضوع" },
    ],
  },
  "email.send": {
    icon: "📧",
    headerColor: "#60a5fa",
    fields: [
      { key: "to", label: "گیرنده" },
      { key: "subject", label: "موضوع" },
      { key: "body", label: "متن" },
    ],
  },
  "calendar.create_event": {
    icon: "📅",
    headerColor: "#34d399",
    fields: [
      { key: "title", label: "عنوان" },
      { key: "start_time", label: "شروع" },
      { key: "end_time", label: "پایان" },
      { key: "location", label: "مکان" },
      { key: "description", label: "توضیحات" },
    ],
  },
  "document.publish": {
    icon: "📄",
    headerColor: "#c084fc",
    fields: [
      { key: "title", label: "عنوان" },
      { key: "category", label: "دسته‌بندی" },
      { key: "url", label: "آدرس" },
    ],
  },
};

// ── Fallback renderer for unknown tools ────────────────────────────────────────

const DEFAULT_CONFIG: ToolDisplayConfig = {
  icon: "⚙️",
  headerColor: "var(--accent)",
  fields: [], // will use generic key-value rendering
};

// ── Field row ──────────────────────────────────────────────────────────────────

function Row({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div
      className="flex gap-3 text-sm py-1.5 border-b last:border-0"
      style={{ borderColor: "rgba(255,255,255,0.05)" }}
    >
      <span
        className="text-xs font-medium min-w-[80px] flex-shrink-0 pt-0.5"
        style={{ color: "var(--text-muted)" }}
      >
        {label}
      </span>
      <span style={{ color: "var(--text-primary)", wordBreak: "break-word" }}>{value}</span>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

interface ConfirmationCardProps {
  confirmation: ConfirmationState;
  loading: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "boolean") return value ? "بله" : "خیر";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

export function ConfirmationCard({
  confirmation,
  loading,
  onConfirm,
  onCancel,
}: ConfirmationCardProps) {
  const { preview, tool, actionTitle } = confirmation;
  const config = TOOL_DISPLAY[tool] ?? DEFAULT_CONFIG;
  const { icon, headerColor, fields } = config;

  // Determine which fields to show:
  // 1. If tool has config → use configured fields
  // 2. Otherwise → render all scalar argument fields generically
  const hasConfig = fields.length > 0;
  const args = preview.arguments ?? {};

  return (
    <div className="mx-4 mb-4 animate-fade-slide-up">
      <div
        className="rounded-2xl p-5 max-w-md mr-9"
        style={{
          background: "var(--bg-surface)",
          border: `1px solid ${headerColor}55`,
          boxShadow: "0 4px 24px rgba(0,0,0,0.3)",
        }}
      >
        {/* Header */}
        <div className="flex items-center gap-2.5 mb-4">
          <span className="text-xl">{icon}</span>
          <div>
            <p className="text-sm font-medium" style={{ color: headerColor }}>
              {actionTitle}
            </p>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
              لطفاً جزئیات را بررسی و تأیید کنید
            </p>
          </div>
        </div>

        {/* Tool badge */}
        <div className="mb-3">
          <span
            className="text-[11px] px-2 py-0.5 rounded-full font-mono"
            style={{
              background: `${headerColor}18`,
              color: headerColor,
              border: `1px solid ${headerColor}30`,
            }}
          >
            {tool}
          </span>
        </div>

        {/* Details */}
        <div
          className="rounded-xl px-4 py-1 mb-4"
          style={{ background: "var(--bg-elevated)" }}
        >
          {hasConfig
            ? /* Configured fields for known tools */
              fields.map(({ key, label, format }) => {
                const raw = args[key] ?? preview[key];
                if (raw === undefined || raw === null || raw === "") return null;
                const value = format ? format(raw) : renderValue(raw);
                return <Row key={key} label={label} value={value} />;
              })
            : /* Generic fallback for unknown tools */
              Object.entries(args)
                .filter(([, v]) => v !== undefined && v !== null && v !== "")
                .map(([key, value]) => (
                  <Row
                    key={key}
                    label={key.replace(/_/g, " ")}
                    value={renderValue(value)}
                  />
                ))}

          {/* If nothing rendered, show raw JSON */}
          {Object.keys(args).length === 0 && (
            <p className="text-xs py-2" style={{ color: "var(--text-muted)" }}>
              بدون پارامتر
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={onCancel}
            disabled={loading}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 disabled:opacity-40"
            style={{
              color: "var(--text-secondary)",
              border: "1px solid var(--border-mid)",
              background: "transparent",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = "var(--bg-elevated)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "transparent")
            }
          >
            لغو
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 disabled:opacity-40 flex items-center justify-center gap-2"
            style={{ background: headerColor, color: "white" }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.88")}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
          >
            {loading ? (
              <>
                <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin-smooth inline-block" />
                در حال ارسال…
              </>
            ) : (
              "تأیید و اجرا"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
