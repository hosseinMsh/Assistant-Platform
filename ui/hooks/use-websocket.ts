"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getWsUrl } from "@/lib/api-client";
import type { WsConnectionStatus, WsEvent } from "@/types";

const RECONNECT_DELAY_MS = 2000;
const MAX_RECONNECT_DELAY_MS = 30000;
const PING_INTERVAL_MS = 25000;

interface UseWebSocketOptions {
  conversationId?: string;
  onEvent: (event: WsEvent) => void;
  enabled?: boolean;
}

export function useWebSocket({ conversationId, onEvent, enabled = true }: UseWebSocketOptions) {
  const [status, setStatus] = useState<WsConnectionStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectDelay = useRef(RECONNECT_DELAY_MS);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const clearTimers = () => {
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    if (pingTimer.current) clearInterval(pingTimer.current);
    reconnectTimer.current = null;
    pingTimer.current = null;
  };

  const connect = useCallback(() => {
    if (!mountedRef.current || !enabled) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus((s) => (s === "disconnected" ? "connecting" : "reconnecting"));

    const url = getWsUrl(conversationId);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) { ws.close(); return; }
      setStatus("connected");
      reconnectDelay.current = RECONNECT_DELAY_MS;

      // Ping to keep alive
      pingTimer.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, PING_INTERVAL_MS);
    };

    ws.onmessage = (ev) => {
      try {
        const event = JSON.parse(ev.data) as WsEvent;
        if (event.type === "pong") return; // ignore keepalive
        onEventRef.current(event);
      } catch {}
    };

    ws.onclose = (ev) => {
      clearTimers();
      if (!mountedRef.current) return;
      // 4001 = auth failure — don't reconnect
      if (ev.code === 4001) { setStatus("disconnected"); return; }
      setStatus("reconnecting");
      reconnectTimer.current = setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 1.5, MAX_RECONNECT_DELAY_MS);
        connect();
      }, reconnectDelay.current);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [conversationId, enabled]);

  useEffect(() => {
    mountedRef.current = true;
    if (enabled) connect();
    return () => {
      mountedRef.current = false;
      clearTimers();
      wsRef.current?.close();
    };
  }, [connect, enabled]);

  const disconnect = useCallback(() => {
    clearTimers();
    wsRef.current?.close();
    setStatus("disconnected");
  }, []);

  return { status, disconnect };
}
