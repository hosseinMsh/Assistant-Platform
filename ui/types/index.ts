// ── Message & Chat ─────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant";

export type ExecutionStatus =
  | "pending"
  | "confirmed"
  | "executing"
  | "success"
  | "failed"
  | "cancelled";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt?: string;
  // If this message is linked to a tool execution
  executionId?: string;
  executionStatus?: ExecutionStatus;
}

// ── Notification Preview ───────────────────────────────────────────────────────

export interface NotificationPreview {
  userName: string;
  providerType: number;
  channel: string;
  subject?: string;
  message: string;
  sendingDate?: string;
}

// ── Confirmation ───────────────────────────────────────────────────────────────

export interface ConfirmationState {
  confirmationId: string;
  executionId: string;
  tool: string;
  preview: NotificationPreview;
  conversationId: string;
}

// ── Conversation ───────────────────────────────────────────────────────────────

export interface ConversationSummary {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: MessageOut[];
}

export interface MessageOut {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

// ── API Response Types ─────────────────────────────────────────────────────────

export type ChatResponse = MessageApiResponse | ConfirmationRequiredResponse;

export interface MessageApiResponse {
  type: "message";
  conversation_id: string;
  message: string;
}

export interface ConfirmationRequiredResponse {
  type: "confirmation_required";
  conversation_id: string;
  confirmation_id: string;
  execution_id: string;
  tool: string;
  preview: NotificationPreview;
}

export interface ToolResultResponse {
  type: "tool_result";
  success: boolean;
  message: string;
}

export interface SessionResponse {
  authenticated: boolean;
  user: { username: string };
}

// ── WebSocket Events ───────────────────────────────────────────────────────────

export type WsConnectionStatus =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected";

export interface WsEvent {
  type: string;
  timestamp: string;
  conversation_id?: string;
  [key: string]: unknown;
}

export interface WsToolExecutionUpdated extends WsEvent {
  type: "tool_execution.updated";
  execution_id: string;
  status: ExecutionStatus;
  result?: string;
  error?: string;
  duration_ms?: number;
}

export interface WsConfirmationCreated extends WsEvent {
  type: "confirmation.created";
  execution_id: string;
  confirmation_id: string;
  tool: string;
  preview: NotificationPreview;
}

export interface WsConfirmationCompleted extends WsEvent {
  type: "confirmation.completed";
  execution_id: string;
  confirmation_id: string;
  action: "confirmed" | "cancelled";
}

export interface WsConnectionState extends WsEvent {
  type: "connection.state";
  status: string;
  pending_execution?: {
    execution_id: string;
    tool: string;
    status: ExecutionStatus;
    confirmation_id?: string;
  } | null;
}
