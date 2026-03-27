"use client";

import { FormEvent, useState } from "react";

interface ChatInputProps {
  onSend: (content: string) => void;
  onVoiceToggle: () => void;
  isVoicePlaceholderActive: boolean;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  onVoiceToggle,
  isVoicePlaceholderActive,
  disabled,
}: ChatInputProps) {
  const [content, setContent] = useState("");

  const submitMessage = (event?: FormEvent) => {
    event?.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || disabled) {
      return;
    }
    onSend(trimmed);
    setContent("");
  };

  return (
    <form
      onSubmit={submitMessage}
      className="sticky bottom-0 z-20 mt-4 flex items-center gap-2 rounded-2xl border border-slate-800 bg-slate-900/95 p-2"
    >
      <button
        type="button"
        onClick={onVoiceToggle}
        className={`h-10 w-10 shrink-0 rounded-xl border text-sm transition ${
          isVoicePlaceholderActive
            ? "border-emerald-400 bg-emerald-400/20 text-emerald-300"
            : "border-slate-700 bg-slate-800 text-slate-300 hover:border-slate-500"
        }`}
        aria-label="Toggle voice placeholder"
      >
        🎙️
      </button>

      <input
        value={content}
        onChange={(event) => setContent(event.target.value)}
        placeholder={isVoicePlaceholderActive ? "Voice input placeholder enabled…" : "Message NexoraAI…"}
        className="h-10 flex-1 rounded-xl border border-slate-700 bg-slate-950 px-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-400"
        disabled={disabled}
      />

      <button
        type="submit"
        disabled={disabled || content.trim().length === 0}
        className="h-10 rounded-xl bg-cyan-500 px-4 text-sm font-semibold text-slate-950 transition disabled:cursor-not-allowed disabled:opacity-40"
      >
        Send
      </button>
    </form>
  );
}
