import type { RealtimeEnvelope, RealtimeEventType } from "@/types/realtime";

type Handler<T = unknown> = (event: RealtimeEnvelope<T>) => void;

interface WebSocketClientOptions {
  maxReconnectAttempts?: number;
  reconnectDelayMs?: number;
  onConnectionStatusChange?: (status: "disconnected" | "connecting" | "connected") => void;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners = new Map<RealtimeEventType | "*", Set<Handler>>();
  private reconnectAttempts = 0;
  private manuallyClosed = false;

  constructor(
    private readonly url: string,
    private readonly options: WebSocketClientOptions = {},
  ) {
    if (!/^wss?:\/\//i.test(url)) {
      throw new Error("WebSocket URL must start with ws:// or wss://");
    }
  }

  connect(): void {
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    this.manuallyClosed = false;
    this.options.onConnectionStatusChange?.("connecting");
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.options.onConnectionStatusChange?.("connected");
    };

    this.ws.onmessage = (event) => {
      const parsed = this.safeParse(event.data);
      if (!parsed) {
        return;
      }
      this.emit(parsed.type, parsed);
      this.emit("*", parsed);
    };

    this.ws.onerror = () => {
      this.options.onConnectionStatusChange?.("disconnected");
      this.emit("error", { type: "error", data: { message: "WebSocket connection error." } });
    };

    this.ws.onclose = () => {
      this.options.onConnectionStatusChange?.("disconnected");
      if (this.manuallyClosed) {
        return;
      }

      const maxReconnectAttempts = this.options.maxReconnectAttempts ?? 6;
      if (this.reconnectAttempts >= maxReconnectAttempts) {
        this.emit("error", {
          type: "error",
          data: { message: "Unable to reconnect to realtime server." },
        });
        return;
      }

      this.reconnectAttempts += 1;
      const reconnectDelayMs = this.options.reconnectDelayMs ?? 1000;
      const delay = reconnectDelayMs * this.reconnectAttempts;
      setTimeout(() => this.connect(), delay);
    };
  }

  disconnect(): void {
    this.manuallyClosed = true;
    this.ws?.close();
    this.options.onConnectionStatusChange?.("disconnected");
    this.ws = null;
  }

  send(payload: Record<string, unknown>): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.emit("error", {
        type: "error",
        data: { message: "Message not sent: realtime connection is not ready." },
      });
      return false;
    }

    this.ws.send(JSON.stringify(payload));
    return true;
  }

  on<T = unknown>(event: RealtimeEventType | "*", handler: Handler<T>): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }

    this.listeners.get(event)?.add(handler as Handler);

    return () => {
      this.listeners.get(event)?.delete(handler as Handler);
    };
  }

  getReadyState(): number | undefined {
    return this.ws?.readyState;
  }

  private safeParse(raw: string): RealtimeEnvelope | null {
    try {
      const parsed: unknown = JSON.parse(raw);
      if (!isRealtimeEnvelope(parsed)) {
        this.emit("error", { type: "error", data: { message: "Realtime event missing type." } });
        return null;
      }
      return parsed;
    } catch {
      this.emit("error", { type: "error", data: { message: "Invalid realtime message payload." } });
      return null;
    }
  }

  private emit<T = unknown>(event: RealtimeEventType | "*", payload: RealtimeEnvelope<T>): void {
    this.listeners.get(event)?.forEach((handler) => handler(payload));
  }
}

function isRealtimeEnvelope(value: unknown): value is RealtimeEnvelope {
  if (!value || typeof value !== "object" || !("type" in value)) {
    return false;
  }

  const type = (value as { type?: unknown }).type;
  return (
    type === "message.user" ||
    type === "message.assistant" ||
    type === "assistant.state" ||
    type === "typing.start" ||
    type === "typing.stop" ||
    type === "error"
  );
}
