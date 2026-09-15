/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

jest.mock("next/navigation", () => ({ useRouter: () => ({ push: jest.fn() }) }));

jest.mock("@/lib/api-client", () => ({
  createSession: jest.fn(),
  logout: jest.fn(),
  sendMessage: jest.fn(),
  confirmAction: jest.fn(),
  cancelAction: jest.fn(),
  getConversations: jest.fn().mockResolvedValue([]),
  getConversation: jest.fn(),
  getWsUrl: jest.fn().mockReturnValue("ws://localhost:8000/ws"),
  ApiError: class ApiError extends Error {
    constructor(public status: number, message: string) { super(message); }
  },
}));

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1;
  readyState = MockWebSocket.OPEN;
  onopen: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  send = jest.fn();
  close = jest.fn();
}
(global as any).WebSocket = MockWebSocket;

import * as api from "@/lib/api-client";
import { TokenForm } from "@/components/token-form";
import { ConfirmationCard } from "@/components/confirmation-card";
import { ConnectionBadge } from "@/components/connection-badge";

// ── Token normalization in UI ─────────────────────────────────────────────────

describe("TokenForm — token normalization", () => {
  it("renders input and connect button", () => {
    render(<TokenForm onSuccess={jest.fn()} />);
    expect(screen.getByPlaceholderText(/eyJ/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /اتصال/i })).toBeInTheDocument();
  });

  it("button disabled when input empty", () => {
    render(<TokenForm onSuccess={jest.fn()} />);
    expect(screen.getByRole("button", { name: /اتصال/i })).toBeDisabled();
  });

  it("calls createSession on submit", async () => {
    const mockCreate = api.createSession as jest.Mock;
    mockCreate.mockResolvedValueOnce({ authenticated: true, user: { username: "u" } });
    const onSuccess = jest.fn();
    render(<TokenForm onSuccess={onSuccess} />);
    fireEvent.change(screen.getByPlaceholderText(/eyJ/i), { target: { value: "validtoken123" } });
    fireEvent.click(screen.getByRole("button", { name: /اتصال/i }));
    await waitFor(() => expect(onSuccess).toHaveBeenCalled());
  });

  it("shows error on 400 response", async () => {
    const mockCreate = api.createSession as jest.Mock;
    const { ApiError } = jest.requireMock("@/lib/api-client");
    mockCreate.mockRejectedValueOnce(new ApiError(400, "bad token"));
    render(<TokenForm onSuccess={jest.fn()} />);
    fireEvent.change(screen.getByPlaceholderText(/eyJ/i), { target: { value: "badtoken12" } });
    fireEvent.click(screen.getByRole("button", { name: /اتصال/i }));
    await waitFor(() => expect(screen.getByText(/توکن نامعتبر/i)).toBeInTheDocument());
  });
});

// ── ConfirmationCard ──────────────────────────────────────────────────────────

const confirmationState = {
  confirmationId: "abc-123",
  executionId: "exec-456",
  tool: "notify.send_one",
  conversationId: "conv-1",
  preview: { userName: "1234567890", providerType: 1, channel: "SMS", message: "جلسه فردا ساعت ۱۰" },
};

describe("ConfirmationCard", () => {
  it("renders recipient, channel, message", () => {
    render(<ConfirmationCard confirmation={confirmationState} loading={false} onConfirm={jest.fn()} onCancel={jest.fn()} />);
    expect(screen.getByText("1234567890")).toBeInTheDocument();
    expect(screen.getByText("پیامک")).toBeInTheDocument();
    expect(screen.getByText("جلسه فردا ساعت ۱۰")).toBeInTheDocument();
  });

  it("calls onConfirm when confirm clicked", () => {
    const onConfirm = jest.fn();
    render(<ConfirmationCard confirmation={confirmationState} loading={false} onConfirm={onConfirm} onCancel={jest.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /تأیید و ارسال/i }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when cancel clicked", () => {
    const onCancel = jest.fn();
    render(<ConfirmationCard confirmation={confirmationState} loading={false} onConfirm={jest.fn()} onCancel={onCancel} />);
    fireEvent.click(screen.getByRole("button", { name: /لغو/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("disables buttons while loading", () => {
    render(<ConfirmationCard confirmation={confirmationState} loading={true} onConfirm={jest.fn()} onCancel={jest.fn()} />);
    screen.getAllByRole("button").forEach(btn => expect(btn).toBeDisabled());
  });
});

// ── ConnectionBadge ───────────────────────────────────────────────────────────

describe("ConnectionBadge", () => {
  it("shows connected label", () => {
    render(<ConnectionBadge status="connected" />);
    expect(screen.getByText("متصل")).toBeInTheDocument();
  });
  it("shows reconnecting label", () => {
    render(<ConnectionBadge status="reconnecting" />);
    expect(screen.getByText("اتصال مجدد…")).toBeInTheDocument();
  });
  it("shows disconnected label", () => {
    render(<ConnectionBadge status="disconnected" />);
    expect(screen.getByText("قطع اتصال")).toBeInTheDocument();
  });
});
