"use client";
import { useRef, useState } from "react";

interface ComposerProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function Composer({ onSend, disabled }: ComposerProps) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
    if (ref.current) { ref.current.style.height = "auto"; }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const canSend = !!text.trim() && !disabled;

  return (
    <div className="px-4 pb-4 pt-2">
      <div
        className="flex items-end gap-3 rounded-2xl px-4 py-3 transition-all duration-150"
        style={{
          background: "var(--bg-elevated)",
          border: "1px solid var(--border-mid)",
        }}
        onFocusCapture={e => (e.currentTarget.style.borderColor = "var(--accent)")}
        onBlurCapture={e => (e.currentTarget.style.borderColor = "var(--border-mid)")}
      >
        <textarea
          ref={ref}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="پیام خود را بنویسید…"
          rows={1}
          dir="auto"
          className="flex-1 bg-transparent text-sm resize-none focus:outline-none disabled:opacity-40"
          style={{
            color: "var(--text-primary)",
            minHeight: "24px",
            maxHeight: "160px",
            lineHeight: "1.6",
            caretColor: "var(--accent)",
          }}
        />
        <button
          onClick={handleSend}
          disabled={!canSend}
          className="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-150 disabled:opacity-30"
          style={{ background: canSend ? "var(--accent)" : "var(--bg-hover)" }}
          title="ارسال (Enter)"
        >
          <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth={2.2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"/>
          </svg>
        </button>
      </div>
      <p className="text-center text-[11px] mt-2" style={{ color: "var(--text-muted)" }}>
        Enter برای ارسال · Shift+Enter برای خط جدید
      </p>
    </div>
  );
}
