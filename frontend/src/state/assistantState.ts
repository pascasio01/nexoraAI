import type { AssistantState, ChatMessage } from "@/types/realtime";

export interface AssistantUIState {
  assistantState: AssistantState;
  typing: boolean;
  messages: ChatMessage[];
  voiceMode: "off" | "placeholder";
  connectionStatus: "disconnected" | "connecting" | "connected";
  error?: string;
}

export const initialAssistantUIState: AssistantUIState = {
  assistantState: "idle",
  typing: false,
  messages: [],
  voiceMode: "off",
  connectionStatus: "disconnected",
};

export function upsertStreamingAssistantMessage(
  messages: ChatMessage[],
  incoming: ChatMessage,
): ChatMessage[] {
  const existingIndex = messages.findIndex((message) => message.id === incoming.id);

  if (existingIndex >= 0) {
    const updated = [...messages];
    updated[existingIndex] = {
      ...updated[existingIndex],
      content: `${updated[existingIndex].content}${incoming.content}`,
      streaming: incoming.streaming,
    };
    return updated;
  }

  return [...messages, incoming];
}
