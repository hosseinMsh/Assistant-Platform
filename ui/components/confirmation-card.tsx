"use client";
import type { ConfirmationState } from "@/types";

const CHANNEL_ICON: Record<string, string> = { SMS: "📱", Bale: "💬", Email: "📧" };
const PROVIDER_LABEL: Record<number, string> = { 1: "پیامک", 2: "پیام‌رسان بله", 3: "ایمیل" };

interface Props {
  confirmation: ConfirmationState;
  loading: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3 text-sm py-1.5 border-b last:border-0"
      style={{ borderColor: "rgba(255,255,255,0.05)" }}>
      <span className="text-xs font-medium min-w-[72px] flex-shrink-0 pt-0.5"
        style={{ color: "var(--text-muted)" }}>{label}</span>
      <span style={{ color: "var(--text-primary)" }}>{value}</span>
    </div>
  );
}

export function ConfirmationCard({ confirmation, loading, onConfirm, onCancel }: Props) {
  const { preview } = confirmation;
  const icon = CHANNEL_ICON[preview.channel] ?? "🔔";
  const channelLabel = PROVIDER_LABEL[preview.providerType] ?? preview.channel;

  return (
    <div className="mx-4 mb-4 animate-fade-slide-up">
      <div
        className="rounded-2xl p-5 max-w-md mr-9"
        style={{
          background: "var(--bg-surface)",
          border: "1px solid rgba(124,111,205,0.35)",
          boxShadow: "0 4px 24px rgba(0,0,0,0.3)",
        }}
      >
        {/* Header */}
        <div className="flex items-center gap-2.5 mb-4">
          <span className="text-xl">{icon}</span>
          <div>
            <p className="text-sm font-medium" style={{ color: "var(--accent)" }}>تأیید ارسال اعلان</p>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
              لطفاً جزئیات را بررسی و تأیید کنید
            </p>
          </div>
        </div>

        {/* Details */}
        <div
          className="rounded-xl px-4 py-1 mb-4"
          style={{ background: "var(--bg-elevated)" }}
        >
          <Row label="گیرنده" value={preview.userName} />
          <Row label="کانال" value={channelLabel} />
          {preview.subject && <Row label="موضوع" value={preview.subject} />}
          <Row label="متن پیام" value={preview.message} />
          {preview.sendingDate && (
            <Row
              label="زمان ارسال"
              value={new Date(preview.sendingDate).toLocaleString("fa-IR")}
            />
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
            onMouseEnter={e => (e.currentTarget.style.background = "var(--bg-elevated)")}
            onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
          >
            لغو
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 disabled:opacity-40 flex items-center justify-center gap-2"
            style={{ background: "var(--accent)", color: "white" }}
            onMouseEnter={e => (e.currentTarget.style.opacity = "0.88")}
            onMouseLeave={e => (e.currentTarget.style.opacity = "1")}
          >
            {loading ? (
              <>
                <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin-smooth inline-block" />
                در حال ارسال…
              </>
            ) : (
              "تأیید و ارسال"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
