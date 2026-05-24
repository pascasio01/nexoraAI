export type AssistantState = "idle" | "listening" | "thinking" | "responding";

export type RealtimeEventType =
  | "message.user"
  | "message.assistant"
  | "assistant.state"
  | "typing.start"
  | "typing.stop"
  | "error";

export interface RealtimeEnvelope<T = unknown> {
  type: RealtimeEventType;
  data?: T;
  timestamp?: string;
}

export interface MessageEventData {
  id?: string;
  content: string;
  role?: "user" | "assistant";
  streaming?: boolean;
  done?: boolean;
}

export interface AssistantStateEventData {
  state: AssistantState;
}

export interface ErrorEventData {
  message: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  createdAt: string;
}
