import { Bot, Play, Terminal, Wrench } from 'lucide-react';

const STEPS = [
  { icon: Wrench, text: 'Writes a pybgpstream analysis script for your question' },
  { icon: Terminal, text: 'Runs it against staged BGP data and reads the output' },
  { icon: Play, text: 'Self-corrects on errors, then reports the result with its trace' },
];

/**
 * Placeholder for the agentic run-and-observe feature (opencode-agent-pod). The
 * backend execution path and data staging are not built yet; this reserves the
 * route and nav slot and explains what is coming.
 */
export function BgpAgentPage() {
  return (
    <div className="flex h-full items-center justify-center p-6">
      <div className="max-w-md text-center">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-xl border border-border bg-card text-primary">
          <Bot className="h-7 w-7" />
        </div>
        <h1 className="font-display text-2xl font-bold tracking-tight">BGP Agent</h1>
        <p className="mt-1 font-mono text-xs uppercase tracking-[0.18em] text-muted-foreground">
          Run &amp; observe · coming soon
        </p>
        <p className="mt-4 text-sm text-muted-foreground">
          Unlike BGP Chat, which hands you a script to run yourself, the agent runs the analysis for
          you — an autonomous loop that executes code and reports back.
        </p>

        <ul className="mt-6 flex flex-col gap-3 text-left">
          {STEPS.map(({ icon: Icon, text }) => (
            <li key={text} className="flex items-start gap-3 text-sm">
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border bg-card text-muted-foreground">
                <Icon className="h-4 w-4" />
              </span>
              <span className="text-muted-foreground">{text}</span>
            </li>
          ))}
        </ul>

        <p className="mt-6 text-xs text-muted-foreground/80">
          In development. Until then, use{' '}
          <span className="font-medium text-foreground">BGP Chat</span> to generate analysis code.
        </p>
      </div>
    </div>
  );
}
