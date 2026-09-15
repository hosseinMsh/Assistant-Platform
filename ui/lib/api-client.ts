import type {
  ChatResponse,
  ConversationDetail,
  ConversationSummary,
  SessionResponse,
  ToolResultResponse,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
  });

  if (!res.ok) {
    let message = "خطا در ارتباط با سرور";
    try {
      const body = await res.json();
      message = body?.detail ?? body?.error?.message ?? body?.message ?? message;
    } catch {}
    throw new ApiError(res.status, message);
  }
  return res.json() as Promise<T>;
}

/** Normalize token: strip whitespace and "Bearer " prefix before sending. */
function normalizeToken(raw: string): string {
  const t = raw.trim();
  if (t.toLowerCase().startsWith("bearer ")) return t.slice(7).trim();
  return t;
}

// ── Auth ───────────────────────────────────────────────────────────────────────
export async function createSession(rawToken: string): Promise<SessionResponse> {
  return request<SessionResponse>("/api/v1/auth/session", {
    method: "POST",
    body: JSON.stringify({ access_token: normalizeToken(rawToken) }),
  });
}

export async function logout(): Promise<void> {
  await request("/api/v1/auth/logout", { method: "POST" });
}

// ── Chat ───────────────────────────────────────────────────────────────────────
export async function sendMessage(message: string, conversationId: string | null): Promise<ChatResponse> {
  return request<ChatResponse>("/api/v1/chat", {
    method: "POST",
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });
}

export async function confirmAction(confirmationId: string): Promise<ToolResultResponse> {
  return request<ToolResultResponse>("/api/v1/chat/confirm", {
    method: "POST",
    body: JSON.stringify({ confirmation_id: confirmationId }),
  });
}

export async function cancelAction(confirmationId: string): Promise<void> {
  await request("/api/v1/chat/cancel", {
    method: "POST",
    body: JSON.stringify({ confirmation_id: confirmationId }),
  });
}

// ── Conversations ──────────────────────────────────────────────────────────────
export async function getConversations(): Promise<ConversationSummary[]> {
  return request<ConversationSummary[]>("/api/v1/conversations");
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  return request<ConversationDetail>(`/api/v1/conversations/${id}`);
}

// ── WebSocket URL ──────────────────────────────────────────────────────────────
export function getWsUrl(conversationId?: string): string {
  const base = BASE_URL.replace(/^http/, "ws");
  const qs = conversationId ? `?conversation_id=${conversationId}` : "";
  return `${base}/ws${qs}`;
}
