"use client";
import { useState } from "react";
import { createSession, ApiError } from "@/lib/api-client";

export function TokenForm({ onSuccess }: { onSuccess: () => void }) {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await createSession(token.trim());
      onSuccess();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.status === 400 ? "توکن نامعتبر است." : err.status === 401 ? "دسترسی رد شد." : "خطا در اتصال. دوباره تلاش کنید.");
      } else {
        setError("خطای ناشناخته.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: "var(--bg-base)" }}>
      <div className="w-full max-w-sm animate-fade-slide-up">
        <div className="text-center mb-8">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ background: "var(--accent)" }}
          >
            <svg width="26" height="26" fill="white" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-6h2v2h-2zm0-8h2v6h-2z"/>
            </svg>
          </div>
          <h1 className="text-lg font-semibold mb-1" style={{ color: "var(--text-primary)" }}>دستیار هوشمند</h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>توکن دسترسی خود را وارد کنید</p>
        </div>

        <div className="rounded-2xl p-6" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
                Access Token
              </label>
              <input
                type="password"
                value={token}
                onChange={e => setToken(e.target.value)}
                placeholder="eyJ... یا Bearer eyJ..."
                disabled={loading}
                autoComplete="off"
                dir="ltr"
                className="w-full text-sm px-4 py-2.5 rounded-xl focus:outline-none transition-all duration-150 disabled:opacity-50"
                style={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border-mid)",
                  color: "var(--text-primary)",
                }}
                onFocus={e => (e.currentTarget.style.borderColor = "var(--accent)")}
                onBlur={e => (e.currentTarget.style.borderColor = "var(--border-mid)")}
              />
              <p className="text-[11px] mt-1.5" style={{ color: "var(--text-muted)" }}>
                پیشوند Bearer اختیاری است
              </p>
            </div>

            {error && (
              <div
                className="text-sm px-3 py-2.5 rounded-xl animate-fade-in"
                style={{ background: "rgba(248,113,113,0.1)", color: "#f87171", border: "1px solid rgba(248,113,113,0.2)" }}
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !token.trim()}
              className="w-full py-2.5 rounded-xl text-sm font-medium transition-all duration-150 disabled:opacity-40 flex items-center justify-center gap-2"
              style={{ background: "var(--accent)", color: "white" }}
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin-smooth inline-block" />
                  در حال اتصال…
                </>
              ) : "اتصال"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
