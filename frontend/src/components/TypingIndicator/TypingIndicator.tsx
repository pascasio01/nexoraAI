interface TypingIndicatorProps {
  show: boolean;
}

export function TypingIndicator({ show }: TypingIndicatorProps) {
  if (!show) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 text-xs text-slate-400">
      <span>NexoraAI is typing</span>
      <span className="inline-flex gap-1">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:0ms]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:120ms]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:240ms]" />
      </span>
    </div>
  );
}
