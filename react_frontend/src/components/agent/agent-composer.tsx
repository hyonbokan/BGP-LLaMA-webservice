import { useLayoutEffect, useRef, type KeyboardEvent } from 'react';
import { Play, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';

const MAX_HEIGHT = 200;

/**
 * The agent's dispatch console: one mono command line that frames an autonomous
 * run. Distinct from the chat composer — a leading routing glyph, a monospace
 * field (prefixes and ASNs read cleaner in mono), and a labeled Run/Stop control.
 * Enter dispatches; Shift+Enter adds a line.
 */
export function AgentComposer({
  value,
  onChange,
  onSend,
  onStop,
  isRunning,
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  onStop: () => void;
  isRunning: boolean;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-grow: reset to content height each render, capped at MAX_HEIGHT (then scroll).
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
    el.style.overflowY = el.scrollHeight > MAX_HEIGHT ? 'auto' : 'hidden';
  }, [value]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSend();
      }}
      className="border-t border-border bg-background/80 p-4 backdrop-blur"
    >
      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-lg border border-input bg-card py-2 pl-3 pr-2 shadow-sm transition-colors focus-within:border-primary/60 focus-within:ring-1 focus-within:ring-ring">
        <span
          aria-hidden
          className="select-none pb-1.5 font-mono text-sm font-semibold leading-relaxed text-primary"
        >
          ⟩⟩
        </span>
        <textarea
          ref={ref}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="analyze prefix 8.8.8.0/24 on rrc00, flag origin & AS-path changes…"
          className="flex-1 resize-none self-center bg-transparent py-1.5 font-mono text-sm leading-relaxed caret-primary outline-none placeholder:text-muted-foreground/70"
        />
        {isRunning ? (
          <Button type="button" variant="secondary" onClick={onStop} className="gap-1.5">
            <Square className="h-3.5 w-3.5" /> Stop
          </Button>
        ) : (
          <Button type="submit" disabled={!value.trim()} className="gap-1.5">
            Run <Play className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>
      <p className="mx-auto mt-2 max-w-3xl px-1 font-mono text-[11px] text-muted-foreground">
        <span className="text-primary/70">⏎</span> to dispatch ·{' '}
        <span className="text-foreground/60">⇧⏎</span> for a new line
      </p>
    </form>
  );
}
