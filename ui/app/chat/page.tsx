"use client";
import { useCallback, useRef, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { ChatWindow } from "@/components/chat-window";
import { ConnectionBadge } from "@/components/connection-badge";
import { useWebSocket } from "@/hooks/use-websocket";
import type { WsEvent } from "@/types";

export default function ChatPage() {
  const [chatKey, setChatKey] = useState(0);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);

  const handleNewChat = useCallback(() => {
    setActiveConvId(null);
    setChatKey(k => k + 1);
  }, []);

  const handleSelectConversation = useCallback((id: string) => {
    setActiveConvId(id);
    setChatKey(k => k + 1);
  }, []);

  const handleConversationsChanged = useCallback(() => {
    setSidebarRefreshKey(k => k + 1);
  }, []);

  // Top-level WS for connection badge (chat-window has its own scoped WS)
  const { status: wsStatus } = useWebSocket({
    conversationId: activeConvId ?? undefined,
    onEvent: (_: WsEvent) => {}, // handled inside ChatWindow
    enabled: true,
  });

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "var(--bg-base)" }}>
      <Sidebar
        activeId={activeConvId}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        refreshKey={sidebarRefreshKey}
      />

      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header
          className="flex items-center justify-between px-6 py-3 border-b flex-shrink-0"
          style={{ borderColor: "var(--border)", background: "var(--bg-base)" }}
        >
          <h1 className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            {activeConvId ? "مکالمه" : "گفتگوی جدید"}
          </h1>
          <ConnectionBadge status={wsStatus} />
        </header>

        {/* Chat */}
        <div className="flex-1 min-h-0">
          <ChatWindow
            key={chatKey}
            conversationId={activeConvId}
            onConversationsChanged={handleConversationsChanged}
          />
        </div>
      </main>
    </div>
  );
}
