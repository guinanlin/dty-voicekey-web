"use client";

import { useEffect, useRef } from "react";
import type { RelayMessageRead } from "@/lib/relay-types";

type RelayEventHandlers = {
  onMessageNew: (message: RelayMessageRead) => void;
  onMessageUpdated: (message: RelayMessageRead) => void;
};

export function useRelayEvents(token: string, handlers: RelayEventHandlers) {
  const handlersRef = useRef(handlers);

  useEffect(() => {
    handlersRef.current = handlers;
  }, [handlers]);

  useEffect(() => {
    if (!token) return;

    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let closed = false;

    const connect = () => {
      if (closed) return;
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const base =
        process.env.NEXT_PUBLIC_RELAY_WS_URL ||
        `${protocol}//${window.location.host}/relay/ws`;
      const url = `${base}?token=${encodeURIComponent(token)}`;
      ws = new WebSocket(url);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data as string) as {
            type?: string;
            message?: RelayMessageRead;
          };
          if (data.type === "message_new" && data.message) {
            handlersRef.current.onMessageNew(data.message);
          } else if (data.type === "message_updated" && data.message) {
            handlersRef.current.onMessageUpdated(data.message);
          }
        } catch {
          // ignore malformed payloads
        }
      };

      ws.onclose = () => {
        if (!closed) {
          retryTimer = setTimeout(connect, 3000);
        }
      };
    };

    connect();

    return () => {
      closed = true;
      if (retryTimer) clearTimeout(retryTimer);
      ws?.close();
    };
  }, [token]);
}
