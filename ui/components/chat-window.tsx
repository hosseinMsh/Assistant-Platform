"use client";
import { useEffect, useRef } from "react";
import { ConfirmationCard } from "./confirmation-card";
import { MessageBubble } from "./message-bubble";
import { Composer } from "./composer";
import { ConnectionBadge } from "./connection-badge";
import { ProcessingTimeline } from "./processing-status";
import { useChat } from "@/hooks/use-chat";
import { useWebSocket } from "@/hooks/use-websocket";
import type { WsEvent } from "@/types";

interface ChatWindowProps {
  conversationId?: string | null;
  onConversationsChanged?: () => void;
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-8 animate-fade-in">
      <div
        className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
        style={{
          background: "var(--accent-dim)",
          border: "1px solid rgba(124,111,205,0.25)",
        }}
      >
        <svg
          width="30"
          height="30"
          fill="none"
          viewBox="0 0 24 24"
          stroke="var(--accent)"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
      </div>
      <h2
        className="text-base font-medium mb-2"
        style={{ color: "var(--text-primary)" }}
      >
        سلام! من توانا هستم
      </h2>
      <p className="text-sm max-w-xs" style={{ color: "var(--text-secondary)" }}>
        دستیار هوشمند دانشگاه صنعتی شریف — چطور می‌توانم کمک کنم؟
      </p>
    </div>
  );
}

export function ChatWindow({
  conversationId: initialConvId,
  onConversationsChanged,
}: ChatWindowProps) {
  const {
    messages,
    loading,
    error,
    confirmation,
    send,
    confirm,
    cancel,
    handleWsEvent,
    conversationId,
    processingStages,
    isProcessing,
  } = useChat(onConversationsChanged);

  const bottomRef = useRef<HTMLDivElement>(null);

  // WebSocket — scoped to the current conversation for state recovery
  const { status: wsStatus } = useWebSocket({
    conversationId: conversationId ?? undefined,
    onEvent: (event: WsEvent) => handleWsEvent(event),
    enabled: true,
  });

  // Auto-scroll on new messages or processing status change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, confirmation, processingStages]);

  const isEmpty = messages.length === 0 && !loading;

  return (
    <div className="flex flex-col h-full">
      {/* WS status bar — only visible when not connected */}
      {wsStatus !== "connected" && (
        <div
          className="flex items-center justify-center gap-2 py-1.5 text-xs animate-fade-in"
          style={{
            background: "rgba(251,191,36,0.08)",
            borderBottom: "1px solid rgba(251,191,36,0.15)",
          }}
        >
          <ConnectionBadge status={wsStatus} />
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {isEmpty ? (
          <EmptyState />
        ) : (
          <div className="px-4 pt-4 pb-2">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Real-time processing status indicator */}
            {isProcessing && processingStages.length > 0 && (
              <ProcessingTimeline stages={processingStages} />
            )}

            {/* Confirmation card — generic, works for any tool */}
            {confirmation && (
              <ConfirmationCard
                confirmation={confirmation}
                loading={loading}
                onConfirm={confirm}
                onCancel={cancel}
              />
            )}

            {/* Error bubble */}
            {error && !confirmation && (
              <div className="flex justify-end mb-4 animate-fade-slide-up">
                <div
                  className="mr-9 max-w-sm px-4 py-2.5 rounded-2xl text-sm"
                  style={{
                    background: "rgba(248,113,113,0.1)",
                    border: "1px solid rgba(248,113,113,0.25)",
                    color: "#f87171",
                  }}
                >
                  {error}
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Composer */}
      <Composer onSend={send} disabled={loading || !!confirmation} />
    </div>
  );
}
