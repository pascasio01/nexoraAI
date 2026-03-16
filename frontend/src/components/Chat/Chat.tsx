"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage as ChatMessageType } from "@/types/realtime";
import { ChatMessage } from "@/components/ChatMessage/ChatMessage";
import { TypingIndicator } from "@/components/TypingIndicator/TypingIndicator";

interface ChatProps {
  messages: ChatMessageType[];
  showTyping: boolean;
  connectionStatus: "disconnected" | "connecting" | "connected";
  error?: string;
}

export function Chat({ messages, showTyping, connectionStatus, error }: ChatProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, showTyping]);

  return (
    <section className="flex flex-1 flex-col rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
      <div className="mb-3 flex items-center justify-between text-xs text-slate-400">
        <span>Realtime chat</span>
        <span
          className={`rounded-full px-2 py-0.5 ${
            connectionStatus === "connected"
              ? "bg-emerald-500/20 text-emerald-300"
              : connectionStatus === "connecting"
                ? "bg-amber-500/20 text-amber-300"
                : "bg-rose-500/20 text-rose-300"
          }`}
        >
          {connectionStatus}
        </span>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {messages.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-700 p-4 text-sm text-slate-400">
            Start a conversation with NexoraAI.
          </div>
        ) : (
          messages.map((message) => <ChatMessage key={message.id} message={message} />)
        )}
        <TypingIndicator show={showTyping} />
        {error ? <p className="text-xs text-rose-300">{error}</p> : null}
        <div ref={bottomRef} />
      </div>
    </section>
  );
}
