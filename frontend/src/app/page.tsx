"use client";

import { Avatar } from "@/components/Avatar/Avatar";
import { Chat } from "@/components/Chat/Chat";
import { ChatInput } from "@/components/ChatInput/ChatInput";
import { RealtimeProvider, useRealtime } from "@/components/RealtimeProvider/RealtimeProvider";

function AssistantExperience() {
  const {
    assistantState,
    connectionStatus,
    error,
    messages,
    typing,
    voiceMode,
    sendMessage,
    toggleVoicePlaceholder,
  } = useRealtime();

  return (
    <div className="relative mx-auto flex min-h-screen w-full max-w-4xl flex-col px-3 pb-4 sm:px-6 sm:pb-6">
      <header className="sticky top-0 z-20 mb-4 flex h-16 items-center justify-between border-b border-slate-800 bg-slate-950/95 backdrop-blur">
        <div>
          <h1 className="text-lg font-semibold tracking-wide text-cyan-300">NexoraAI</h1>
          <p className="text-xs text-slate-400">Realtime Personal Assistant MVP</p>
        </div>
        <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">
          {assistantState}
        </span>
      </header>

      <main className="flex flex-1 flex-col">
        <Chat
          messages={messages}
          showTyping={typing || assistantState === "responding"}
          connectionStatus={connectionStatus}
          error={error}
        />

        <ChatInput
          onSend={sendMessage}
          onVoiceToggle={toggleVoicePlaceholder}
          isVoicePlaceholderActive={voiceMode === "placeholder"}
          disabled={connectionStatus === "disconnected"}
        />
      </main>

      <Avatar state={assistantState} />
    </div>
  );
}

export default function Home() {
  return (
    <RealtimeProvider>
      <AssistantExperience />
    </RealtimeProvider>
  );
}
