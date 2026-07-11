import { Bot } from 'lucide-react';

/**
 * Assistant-styled placeholder shown while a request is in flight but no tokens
 * have streamed yet — classification and generation start-up take a moment, and
 * without this the user sees no sign the agent is working. Three bouncing dots.
 */
export function ChatThinking({ label = 'Analyzing' }: { label?: string }) {
  return (
    <div className="flex gap-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border bg-card text-muted-foreground">
        <Bot className="h-4 w-4" />
      </div>
      <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-3">
        <div className="flex gap-1" aria-hidden>
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary" />
        </div>
        <span className="font-mono text-xs text-muted-foreground">{label}…</span>
      </div>
    </div>
  );
}
