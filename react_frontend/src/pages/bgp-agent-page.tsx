import { useEffect, useRef } from 'react';
import { RotateCcw, Waypoints } from 'lucide-react';
import { useBgpAgent } from '@/hooks/use-bgp-agent';
import { AgentRunCard } from '@/components/agent/agent-run-card';
import { AgentComposer } from '@/components/agent/agent-composer';
import { Button } from '@/components/ui/button';

/**
 * The BGP Agent dispatch console. Each question dispatches one autonomous run on
 * the agent pod: the card streams a live step trace — the agent's tool calls and
 * its answer as they arrive — then a result card with run metadata. Follow-ups
 * thread the previous run's findings forward.
 */
export function BgpAgentPage() {
  const agent = useBgpAgent();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Keep the newest run in view as it streams.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [agent.runs]);

  const hasRuns = agent.runs.length > 0;

  return (
    <div className="flex h-full min-w-0 flex-col">
      <header className="flex items-center justify-between gap-2 border-b border-border px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Waypoints className="h-4 w-4 text-primary" />
          <span className="font-display text-sm font-semibold tracking-tight">BGP Agent</span>
          <span className="eyebrow hidden sm:inline">Autonomous analyst</span>
        </div>
        {hasRuns && (
          <Button
            variant="ghost"
            size="sm"
            className="gap-2 font-mono"
            onClick={agent.reset}
            disabled={agent.isRunning}
          >
            <RotateCcw className="h-4 w-4" /> New session
          </Button>
        )}
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {hasRuns ? (
          <div className="mx-auto flex max-w-3xl flex-col gap-8 px-4 py-6">
            {agent.runs.map((run) => (
              <AgentRunCard key={run.id} run={run} />
            ))}
          </div>
        ) : (
          <EmptyState onPick={agent.setInput} />
        )}
      </div>

      <AgentComposer
        value={agent.input}
        onChange={agent.setInput}
        onSend={agent.submit}
        onStop={agent.stop}
        isRunning={agent.isRunning}
      />
    </div>
  );
}

// Preset investigations. Each fills the composer with a fully-specified task —
// the agent is autonomous and won't ask follow-ups, so the prefix, window,
// collector, and expected origin are all named up front.
const PRESETS = [
  {
    title: 'Origin & AS-path changes',
    scope: '8.8.8.0/24 · rrc00',
    query:
      'Analyze prefix 8.8.8.0/24 on RIPE RIS collector rrc00 between 2026-07-11 00:00 and ' +
      '00:20 UTC. Treat AS15169 as the expected origin and flag any origin or AS-path changes.',
  },
  {
    title: 'MOAS conflict check',
    scope: '1.1.1.0/24 · rrc00',
    query:
      'Over the last 30 minutes on RIPE RIS (rrc00), check whether the origin AS for 1.1.1.0/24 ' +
      'changed from AS13335, and report any MOAS conflicts.',
  },
];

function EmptyState({ onPick }: { onPick: (value: string) => void }) {
  return (
    <div className="bg-grid flex h-full items-center justify-center p-6">
      <div className="w-full max-w-xl py-8">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-md border border-border bg-card text-primary">
            <Waypoints className="h-5 w-5" />
          </span>
          <span className="eyebrow">Autonomous analyst</span>
        </div>

        <h1 className="mt-5 font-display text-3xl font-bold tracking-tight">
          Dispatch a routing investigation
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
          Frame a prefix, ASN, and window. The agent gathers the BGP updates, writes and runs the
          analysis in Python, self-corrects, and reports what changed — you watch each step as it
          runs. Unlike BGP Chat, it runs the analysis instead of handing you a script.
        </p>

        <p className="eyebrow mt-9">Preset tasks</p>
        <div className="mt-3 flex flex-col gap-2">
          {PRESETS.map((preset) => (
            <button
              key={preset.query}
              onClick={() => onPick(preset.query)}
              className="group flex items-center gap-3 rounded-lg border border-border bg-card/60 px-4 py-3 text-left transition-colors hover:border-primary/40 hover:bg-card"
            >
              <span
                aria-hidden
                className="select-none font-mono text-sm text-primary/50 transition-colors group-hover:text-primary"
              >
                ⟩
              </span>
              <span className="text-sm font-medium text-foreground">{preset.title}</span>
              <span className="ml-auto shrink-0 font-mono text-[11px] text-primary/80">
                {preset.scope}
              </span>
            </button>
          ))}
        </div>

        <p className="mt-6 font-mono text-[11px] leading-relaxed text-muted-foreground/80">
          The agent won't ask follow-ups — name the prefix, window, collector, and expected origin.
        </p>
      </div>
    </div>
  );
}
