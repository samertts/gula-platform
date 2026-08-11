import { useEffect, useRef, useState, useCallback } from "react";

type RealtimeEvent = {
  type: string;
  payload: unknown;
  timestamp: string;
};

type ConnectionState = "disconnected" | "connecting" | "connected" | "reconnecting";

interface UseRealtimeOptions {
  url?: string;
  onEvent?: (event: RealtimeEvent) => void;
  onStatusChange?: (state: ConnectionState) => void;
  reconnectInterval?: number;
  maxReconnects?: number;
  heartbeatInterval?: number;
}

export function useRealtimeEvents(options: UseRealtimeOptions = {}) {
  const {
    url = `${import.meta.env.VITE_WS_URL ?? "ws://localhost:8000"}/ws/events`,
    onEvent,
    onStatusChange,
    reconnectInterval = 3000,
    maxReconnects = 10,
    heartbeatInterval = 30000,
  } = options;

  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);
  const onEventRef = useRef(onEvent);
  const onStatusChangeRef = useRef(onStatusChange);
  onEventRef.current = onEvent;
  onStatusChangeRef.current = onStatusChange;

  const updateState = useCallback((state: ConnectionState) => {
    setConnectionState(state);
    onStatusChangeRef.current?.(state);
  }, []);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    updateState("connecting");

    // Browser cookies are attached by the user agent; never put JWTs in URLs.
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) { ws.close(); return; }
        reconnectCountRef.current = 0;
        updateState("connected");

        heartbeatRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: "ping" }));
        }, heartbeatInterval);
      };

      ws.onmessage = (event) => {
        try {
          const data: RealtimeEvent = JSON.parse(event.data);
          if (data.type === "pong") return;
          setLastEvent(data);
          onEventRef.current?.(data);
        } catch {
          // Ignore non-JSON messages
        }
      };

      ws.onclose = () => {
        if (heartbeatRef.current !== null) clearInterval(heartbeatRef.current);
        wsRef.current = null;
        if (!mountedRef.current) return;

        if (reconnectCountRef.current < maxReconnects) {
          updateState("reconnecting");
          reconnectCountRef.current += 1;
          reconnectTimerRef.current = setTimeout(connect, reconnectInterval * reconnectCountRef.current);
        } else {
          updateState("disconnected");
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      updateState("disconnected");
    }
  }, [url, heartbeatInterval, maxReconnects, reconnectInterval, updateState]);

  const disconnect = useCallback(() => {
    mountedRef.current = false;
    if (heartbeatRef.current !== null) clearInterval(heartbeatRef.current);
    if (reconnectTimerRef.current !== null) clearTimeout(reconnectTimerRef.current);
    wsRef.current?.close();
    wsRef.current = null;
    updateState("disconnected");
  }, [updateState]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { connectionState, lastEvent, send, reconnect: connect, disconnect };
}

// ── SSE Hook ──
export function useServerSentEvents(options: { url?: string; onEvent?: (data: unknown) => void } = {}) {
  const url = options.url ?? `${import.meta.env.VITE_API_BASE_URL ?? "/api"}/sse/events`;
  const [connected, setConnected] = useState(false);
  const [lastData, setLastData] = useState<unknown>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = new EventSource(url, { withCredentials: true });
    eventSourceRef.current = es;

    es.onopen = () => setConnected(true);
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastData(data);
        options.onEvent?.(data);
      } catch {
        setLastData(event.data);
        options.onEvent?.(event.data);
      }
    };
    es.onerror = () => {
      setConnected(false);
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [url]);

  return { connected, lastData, close: () => eventSourceRef.current?.close() };
}

// ── SSE for lab events ──
export function useLabEventStream(labId?: number, onEvent?: (data: unknown) => void) {
  const url = labId
    ? `${import.meta.env.VITE_API_BASE_URL ?? "/api"}/sse/lab/${labId}`
    : undefined;

  return useServerSentEvents({
    url,
    onEvent,
  });
}

// ── SSE for critical alerts ──
export function useCriticalAlertStream(onAlert?: (data: unknown) => void) {
  return useServerSentEvents({
    url: `${import.meta.env.VITE_API_BASE_URL ?? "/api"}/sse/critical-alerts`,
    onEvent: onAlert,
  });
}
