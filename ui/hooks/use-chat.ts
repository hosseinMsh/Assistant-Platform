"use client";

import { useCallback, useRef, useState } from "react";
import { cancelAction, confirmAction, getConversation, sendMessage } from "@/lib/api-client";
import type {
  ChatMessage,
  ConfirmationState,
  ConversationDetail,
  ExecutionStatus,
  ToolResultResponse,
  WsConfirmationCompleted,
  WsConfirmationCreated,
  WsConnectionState,
  WsEvent,
  WsToolExecutionUpdated,
} from "@/types";

function uid() {
  return Math.random().toString(36).slice(2);
}

export function useChat(onConversationsChanged?: () => void) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<ConfirmationState | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const confirmingRef = useRef(false);

  // ── Message helpers ──────────────────────────────────────────────────────────

  const addMessage = useCallback((msg: Omit<ChatMessage, "id">) => {
    setMessages((prev) => [...prev, { ...msg, id: uid() }]);
  }, []);

  const updateLastAssistant = useCallback(
    (content: string, patch?: Partial<Pick<ChatMessage, "executionStatus">>) => {
      setMessages((prev) => {
        const next = [...prev];
        for (let i = next.length - 1; i >= 0; i--) {
          if (next[i].role === "assistant") {
            next[i] = { ...next[i], content, ...patch };
            return next;
          }
        }
        return next;
      });
    },
    []
  );

  const updateExecutionStatus = useCallback((executionId: string, status: ExecutionStatus) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.executionId === executionId ? { ...m, executionStatus: status } : m
      )
    );
  }, []);

  // ── WebSocket event handler ──────────────────────────────────────────────────

  const handleWsEvent = useCallback(
    (event: WsEvent) => {
      switch (event.type) {
        case "connection.state": {
          const e = event as WsConnectionState;
          // Recover pending execution state after reconnect
          if (e.pending_execution && e.conversation_id) {
            const pe = e.pending_execution;
            if (pe.status === "pending" && pe.confirmation_id) {
              // Re-show confirmation if it was pending
              // We don't have preview here — UI will show generic state
              setConfirmation((prev) =>
                prev?.confirmationId === pe.confirmation_id
                  ? prev
                  : {
                      confirmationId: pe.confirmation_id!,
                      executionId: pe.execution_id,
                      tool: pe.tool,
                      preview: { userName: "", providerType: 1, channel: "SMS", message: "" },
                      conversationId: e.conversation_id!,
                    }
              );
            }
          }
          break;
        }
        case "tool_execution.updated": {
          const e = event as WsToolExecutionUpdated;
          updateExecutionStatus(e.execution_id, e.status);
          if (e.status === "success" || e.status === "failed" || e.status === "cancelled") {
            setConfirmation((prev) =>
              prev?.executionId === e.execution_id ? null : prev
            );
            if (e.status === "success") {
              addMessage({ role: "assistant", content: "اعلان با موفقیت ارسال شد.", executionStatus: "success" });
            } else if (e.status === "failed") {
              addMessage({
                role: "assistant",
                content: e.error ?? "عملیات ناموفق بود.",
                executionStatus: "failed",
              });
            }
          }
          break;
        }
        case "confirmation.created": {
          const e = event as WsConfirmationCreated;
          setConfirmation({
            confirmationId: e.confirmation_id,
            executionId: e.execution_id,
            tool: e.tool,
            preview: e.preview,
            conversationId: e.conversation_id ?? "",
          });
          break;
        }
        case "confirmation.completed": {
          const e = event as WsConfirmationCompleted;
          if (e.action === "cancelled") {
            setConfirmation(null);
            updateExecutionStatus(e.execution_id, "cancelled");
          }
          break;
        }
      }
    },
    [addMessage, updateExecutionStatus]
  );

  // ── Send ─────────────────────────────────────────────────────────────────────

  const send = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;
      setError(null);

      addMessage({ role: "user", content: text });
      const placeholderId = uid();
      setMessages((prev) => [
        ...prev,
        { id: placeholderId, role: "assistant", content: "", executionStatus: undefined },
      ]);
      setLoading(true);

      try {
        const res = await sendMessage(text, conversationId);
        if (!conversationId) setConversationId(res.conversation_id);
        onConversationsChanged?.();

        if (res.type === "message") {
          setMessages((prev) =>
            prev.map((m) => (m.id === placeholderId ? { ...m, content: res.message } : m))
          );
        } else if (res.type === "confirmation_required") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === placeholderId
                ? { ...m, content: "لطفاً جزئیات را تأیید کنید.", executionId: res.execution_id, executionStatus: "pending" }
                : m
            )
          );
          setConfirmation({
            confirmationId: res.confirmation_id,
            executionId: res.execution_id,
            tool: res.tool,
            preview: res.preview,
            conversationId: res.conversation_id,
          });
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "خطا در ارسال پیام";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === placeholderId ? { ...m, content: msg, executionStatus: "failed" } : m
          )
        );
        setError(msg);
      } finally {
        setLoading(false);
      }
    },
    [loading, conversationId, addMessage, onConversationsChanged]
  );

  // ── Confirm ───────────────────────────────────────────────────────────────────

  const confirm = useCallback(async () => {
    if (!confirmation || confirmingRef.current) return;
    confirmingRef.current = true;
    setLoading(true);
    setError(null);
    try {
      updateExecutionStatus(confirmation.executionId, "executing");
      const res: ToolResultResponse = await confirmAction(confirmation.confirmationId);
      // WS event will handle the final state update
      if (!res.success) {
        setError(res.message);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "خطا در تأیید عملیات";
      setError(msg);
      updateExecutionStatus(confirmation.executionId, "failed");
    } finally {
      confirmingRef.current = false;
      setLoading(false);
    }
  }, [confirmation, updateExecutionStatus]);

  // ── Cancel ────────────────────────────────────────────────────────────────────

  const cancel = useCallback(async () => {
    if (!confirmation) return;
    try {
      await cancelAction(confirmation.confirmationId);
    } catch {}
    setConfirmation(null);
    updateExecutionStatus(confirmation.executionId, "cancelled");
    addMessage({ role: "assistant", content: "عملیات لغو شد.", executionStatus: "cancelled" });
  }, [confirmation, updateExecutionStatus, addMessage]);

  // ── Load conversation ─────────────────────────────────────────────────────────

  const loadConversation = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    setConfirmation(null);
    setConversationId(id);
    try {
      const detail: ConversationDetail = await getConversation(id);
      setMessages(
        detail.messages.map((m) => ({
          id: m.id,
          role: m.role as "user" | "assistant",
          content: m.content,
          createdAt: m.created_at,
        }))
      );
    } catch {
      setError("خطا در بارگذاری مکالمه");
      setMessages([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Reset ─────────────────────────────────────────────────────────────────────

  const reset = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setConfirmation(null);
    setError(null);
    setLoading(false);
    confirmingRef.current = false;
  }, []);

  return {
    messages,
    loading,
    error,
    confirmation,
    conversationId,
    send,
    confirm,
    cancel,
    reset,
    loadConversation,
    handleWsEvent,
  };
}
