"use client";

import {
  createContext,
  PropsWithChildren,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { WebSocketClient } from "@/services/websocketClient";
import {
  initialAssistantUIState,
  type AssistantUIState,
  upsertStreamingAssistantMessage,
} from "@/state/assistantState";
import type {
  AssistantStateEventData,
  ErrorEventData,
  MessageEventData,
} from "@/types/realtime";

interface RealtimeContextValue extends AssistantUIState {
  sendMessage: (content: string) => void;
  toggleVoicePlaceholder: () => void;
}

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

function generateMessageId(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}

function buildRealtimeUrl(): string {
  const explicitUrl = process.env.NEXT_PUBLIC_WS_URL;
  if (explicitUrl) {
    return explicitUrl;
  }

  const siteId = process.env.NEXT_PUBLIC_SITE_ID ?? "web";
  const roomId = process.env.NEXT_PUBLIC_ROOM_ID ?? "main";
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000";
  const wsBase = backendUrl.replace(/^http/, "ws").replace(/\/$/, "");
  return `${wsBase}/ws/${siteId}/${roomId}`;
}

export function RealtimeProvider({ children }: PropsWithChildren) {
  const [state, setState] = useState<AssistantUIState>({
    ...initialAssistantUIState,
    connectionStatus: "connecting",
  });

  const socketRef = useRef<WebSocketClient | null>(null);
  const visitorIdRef = useRef<string>(generateMessageId("visitor"));

  useEffect(() => {
    const socket = new WebSocketClient(buildRealtimeUrl(), {
      maxReconnectAttempts: 8,
      reconnectDelayMs: 1200,
      onConnectionStatusChange: (connectionStatus) => {
        setState((previous) => ({ ...previous, connectionStatus }));
      },
    });

    socketRef.current = socket;

    const clearErrorOnAnyMessage = socket.on("*", () => {
      setState((previous) => ({ ...previous, error: undefined }));
    });

    const handleUserMessage = socket.on<MessageEventData>("message.user", (event) => {
      const content = event.data?.content?.trim();
      if (!content) {
        return;
      }
      setState((previous) => ({
        ...previous,
        messages: previous.messages.some((message) => message.id === event.data?.id)
          ? previous.messages
          : [
              ...previous.messages,
              {
                id: event.data?.id ?? generateMessageId("user"),
                role: "user",
                content,
                createdAt: new Date().toISOString(),
              },
            ],
      }));
    });

    const handleAssistantMessage = socket.on<MessageEventData>("message.assistant", (event) => {
      const content = event.data?.content ?? "";
      const messageId = event.data?.id ?? "assistant-stream";
      const incomingMessage = {
        id: messageId,
        role: "assistant" as const,
        content,
        streaming: event.data?.streaming && !event.data?.done,
        createdAt: new Date().toISOString(),
      };

      setState((previous) => ({
        ...previous,
        typing: false,
        messages:
          incomingMessage.streaming || messageId === "assistant-stream"
            ? upsertStreamingAssistantMessage(previous.messages, incomingMessage)
            : [...previous.messages, incomingMessage],
      }));
    });

    const handleAssistantState = socket.on<AssistantStateEventData>("assistant.state", (event) => {
      const assistantState = event.data?.state;
      if (!assistantState) {
        return;
      }
      setState((previous) => ({ ...previous, assistantState }));
    });

    const handleTypingStart = socket.on("typing.start", () => {
      setState((previous) => ({ ...previous, typing: true }));
    });

    const handleTypingStop = socket.on("typing.stop", () => {
      setState((previous) => ({ ...previous, typing: false }));
    });

    const handleError = socket.on<ErrorEventData>("error", (event) => {
      const message = event.data?.message ?? "Unexpected realtime error.";
      setState((previous) => ({ ...previous, error: message, typing: false }));
    });

    socket.connect();

    return () => {
      clearErrorOnAnyMessage();
      handleUserMessage();
      handleAssistantMessage();
      handleAssistantState();
      handleTypingStart();
      handleTypingStop();
      handleError();
      socket.disconnect();
      socketRef.current = null;
    };
  }, []);

  const value = useMemo<RealtimeContextValue>(
    () => ({
      ...state,
      sendMessage: (content: string) => {
        const message = content.trim();
        if (!message) {
          return;
        }

        const messageId = generateMessageId("user-local");
        const messageSent = socketRef.current?.send({
          type: "message.user",
          id: messageId,
          visitor_id: visitorIdRef.current,
          content: message,
          timestamp: new Date().toISOString(),
        });

        if (!messageSent) {
          setState((previous) => ({
            ...previous,
            error: "Message was not sent. Realtime connection is not ready.",
            typing: false,
          }));
          return;
        }

        setState((previous) => ({
          ...previous,
          messages: [
            ...previous.messages,
            {
              id: messageId,
              role: "user",
              content: message,
              createdAt: new Date().toISOString(),
            },
          ],
          assistantState: "thinking",
          typing: true,
        }));
      },
      toggleVoicePlaceholder: () => {
        setState((previous) => ({
          ...previous,
          voiceMode: previous.voiceMode === "off" ? "placeholder" : "off",
          assistantState: previous.voiceMode === "off" ? "listening" : "idle",
        }));
      },
    }),
    [state],
  );

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error("useRealtime must be used within RealtimeProvider");
  }
  return context;
}
