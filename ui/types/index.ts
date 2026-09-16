// ── Message & Chat ─────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant";

export type ExecutionStatus =
  | "pending"
  | "confirmed"
  | "executing"
  | "success"
  | "failed"
  | "cancelled";

export type ProcessingStage =
  | "thinking"
  | "fetching_tools"
  | "calling_llm"
  | "tool_selected"
  | "confirming"
  | "executing"
  | "done"
  | "error";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt?: string;
  executionId?: string;
  executionStatus?: ExecutionStatus;
}

// ── Generic Tool Preview ───────────────────────────────────────────────────────
// Works for any current or future tool — not tied to notify schema.
// The `arguments` field holds the raw tool arguments.
// Top-level scalar fields are also flattened for easy UI access.

export interface GenericToolPreview {
  tool: string;
  tool_label: string;
  arguments: Record<string, unknown>;
  // Flattened scalar fields (e.g. userName, message, providerType, etc.)
  [key: string]: unknown;
}

// ── Confirmation ───────────────────────────────────────────────────────────────

export interface ConfirmationState {
  confirmationId: string;
  executionId: string;
  tool: string;
  /** Human-readable Persian title for the dialog header */
  actionTitle: string;
  /** Generic preview — works for any tool */
  preview: GenericToolPreview;
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
  action_title: string;
  preview: GenericToolPreview;
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

/** Real-time processing transparency event */
export interface WsProcessingStatus extends WsEvent {
  type: "processing.status";
  /** Stage identifier */
  stage: ProcessingStage;
  /** Human-readable Persian label */
  label: string;
  /** Optional detail, e.g. tool name */
  detail?: string;
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
  action_title: string;
  preview: GenericToolPreview;
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
