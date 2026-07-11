import { useEffect, useRef } from 'react';
import { Bot, Play, RotateCcw, Terminal, Wrench } from 'lucide-react';
import { useBgpAgent } from '@/hooks/use-bgp-agent';
import { AgentRunCard } from '@/components/agent/agent-run-card';
import { ChatComposer } from '@/components/chat/chat-composer';
import { Button } from '@/components/ui/button';

const STEPS = [
  { icon: Wrench, text: 'Writes a pybgpstream analysis script for your question' },
  { icon: Terminal, text: 'Runs it against staged BGP data and reads the output' },
  { icon: Play, text: 'Self-corrects on errors, then reports the result with its metrics' },
];

/**
 * The BGP Agent run-and-observe console. Each question kicks off one autonomous
 * run on the agent pod: the card shows a live "working" indicator while the pod
 * runs, then a result card with the answer and run metadata. Follow-ups thread
 * the previous run's findings forward. The live per-step tool trace lands once
 * the pod ships token/tool events; today the console shows submit → running →
 * result.
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
    <div className="flex min-w-0 flex-1 flex-col">
      <header className="flex items-center justify-between gap-2 border-b border-border px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-primary" />
          <span className="font-display text-sm font-semibold tracking-tight">BGP Agent</span>
          <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
            Run &amp; observe
          </span>
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

      <ChatComposer
        value={agent.input}
        onChange={agent.setInput}
        onSend={agent.submit}
        onStop={agent.stop}
        isGenerating={agent.isRunning}
      />
    </div>
  );
}

const EXAMPLES = [
  'Analyze prefix 8.8.8.0/24 over the last 24 hours and flag any origin changes.',
  'Did AS3356 announce any more-specific prefixes for AS15169 recently?',
  'Check for MOAS conflicts on 1.1.1.0/24 in the latest RIB.',
];

function EmptyState({ onPick }: { onPick: (value: string) => void }) {
  return (
    <div className="flex h-full items-center justify-center p-6">
      <div className="max-w-md text-center">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-xl border border-border bg-card text-primary">
          <Bot className="h-7 w-7" />
        </div>
        <h1 className="font-display text-2xl font-bold tracking-tight">BGP Agent</h1>
        <p className="mt-4 text-sm text-muted-foreground">
          Unlike BGP Chat, which hands you a script to run yourself, the agent runs the analysis for
          you — an autonomous loop that executes code and reports back.
        </p>

        <ul className="mx-auto mt-6 flex max-w-sm flex-col gap-3 text-left">
          {STEPS.map(({ icon: Icon, text }) => (
            <li key={text} className="flex items-start gap-3 text-sm">
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border bg-card text-muted-foreground">
                <Icon className="h-4 w-4" />
              </span>
              <span className="text-muted-foreground">{text}</span>
            </li>
          ))}
        </ul>

        <div className="mt-8 flex flex-col gap-2">
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
            Try one
          </p>
          {EXAMPLES.map((example) => (
            <button
              key={example}
              onClick={() => onPick(example)}
              className="rounded-lg border border-border bg-card px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
