import type { ChatMessage as ChatMessageType } from "@/types/realtime";

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm sm:max-w-[70%] ${
          isUser
            ? "rounded-br-sm bg-cyan-500 text-slate-950"
            : "rounded-bl-sm bg-slate-800 text-slate-100"
        }`}
      >
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        {message.streaming ? (
          <span className="mt-1 inline-block h-2 w-2 animate-pulse rounded-full bg-slate-200" />
        ) : null}
      </div>
    </div>
  );
}
