"use client";
import { useCallback, useEffect, useState } from "react";
import { getConversations, logout } from "@/lib/api-client";
import type { ConversationSummary } from "@/types";
import { useRouter } from "next/navigation";

interface SidebarProps {
  activeId?: string | null;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
  refreshKey?: number;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "همین الان";
  if (m < 60) return `${m} دقیقه پیش`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} ساعت پیش`;
  return `${Math.floor(h / 24)} روز پیش`;
}

export function Sidebar({ activeId, onNewChat, onSelectConversation, refreshKey }: SidebarProps) {
  const router = useRouter();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);

  const loadConversations = useCallback(async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch {
      setConversations([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadConversations(); }, [loadConversations, refreshKey]);

  const handleLogout = async () => {
    setLoggingOut(true);
    try { await logout(); } finally { router.push("/"); }
  };

  return (
    <aside
      className="w-64 flex flex-col h-full border-l"
      style={{ background: "var(--bg-surface)", borderColor: "var(--border)" }}
    >
      {/* Header */}
      <div className="p-4 border-b" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: "var(--accent)" }}>
            <svg width="16" height="16" fill="white" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-6h2v2h-2zm0-8h2v6h-2z"/>
            </svg>
          </div>
          <span className="font-medium" style={{ color: "var(--text-primary)" }}>دستیار</span>
        </div>
      </div>

      {/* New chat */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150"
          style={{
            background: "var(--accent-dim)",
            color: "var(--accent)",
            border: "1px solid rgba(124,111,205,0.3)",
          }}
          onMouseEnter={e => (e.currentTarget.style.background = "rgba(124,111,205,0.22)")}
          onMouseLeave={e => (e.currentTarget.style.background = "var(--accent-dim)")}
        >
          <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
          </svg>
          گفتگوی جدید
        </button>
      </div>

      {/* Conversations */}
      <div className="flex-1 overflow-y-auto px-2 py-1">
        {loading ? (
          <div className="flex flex-col gap-2 px-2 pt-2">
            {[1,2,3].map(i => (
              <div key={i} className="h-10 rounded-lg animate-pulse-soft" style={{ background: "var(--bg-elevated)" }} />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="px-3 py-6 text-center">
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>هنوز گفتگویی ندارید</p>
          </div>
        ) : (
          <div className="flex flex-col gap-0.5">
            {conversations.map(conv => (
              <button
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className="w-full text-right px-3 py-2.5 rounded-lg transition-all duration-100 group"
                style={{
                  background: activeId === conv.id ? "var(--bg-hover)" : "transparent",
                  color: activeId === conv.id ? "var(--text-primary)" : "var(--text-secondary)",
                }}
                onMouseEnter={e => { if (activeId !== conv.id) e.currentTarget.style.background = "var(--bg-elevated)"; }}
                onMouseLeave={e => { if (activeId !== conv.id) e.currentTarget.style.background = "transparent"; }}
              >
                <p className="text-xs font-medium truncate leading-5">
                  {conv.title ?? "گفتگو"}
                </p>
                <p className="text-[11px] mt-0.5" style={{ color: "var(--text-muted)" }}>
                  {timeAgo(conv.updated_at)}
                </p>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t" style={{ borderColor: "var(--border)" }}>
        <button
          onClick={handleLogout}
          disabled={loggingOut}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all duration-150 disabled:opacity-50"
          style={{ color: "var(--text-secondary)" }}
          onMouseEnter={e => { e.currentTarget.style.color = "#f87171"; e.currentTarget.style.background = "rgba(248,113,113,0.08)"; }}
          onMouseLeave={e => { e.currentTarget.style.color = "var(--text-secondary)"; e.currentTarget.style.background = "transparent"; }}
        >
          <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75"/>
          </svg>
          {loggingOut ? "خروج…" : "خروج از حساب"}
        </button>
      </div>
    </aside>
  );
}
