import type { AssistantState } from "@/types/realtime";

interface AvatarProps {
  state: AssistantState;
}

const stateStyles: Record<AssistantState, string> = {
  idle: "bg-cyan-500/70 shadow-cyan-400/60",
  listening: "bg-emerald-400 shadow-emerald-300 animate-pulse",
  thinking: "bg-violet-500 shadow-violet-300 animate-[pulse_1s_ease-in-out_infinite]",
  responding: "bg-sky-400 shadow-sky-200 animate-[ping_1.2s_ease-in-out_infinite]",
};

export function Avatar({ state }: AvatarProps) {
  return (
    <div className="pointer-events-none fixed right-5 bottom-24 z-30 sm:right-8">
      <div className="relative flex h-16 w-16 items-center justify-center rounded-full border border-white/20 bg-slate-950/80 backdrop-blur">
        <div className={`h-8 w-8 rounded-full shadow-lg ${stateStyles[state]}`} />
      </div>
      <p className="mt-2 text-center text-xs text-slate-300">{state}</p>
    </div>
  );
}
