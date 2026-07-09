import { ArrowRight, Database } from 'lucide-react';
import { AsPath } from '@/components/as-path';
import { Badge } from '@/components/ui/badge';
import { DATA_WINDOW, EXAMPLE_QUERIES } from '@/components/chat/constants';
import { MODEL_LABELS } from '@/components/chat/constants';
import type { ChatModel } from '@/types';

export function ChatEmptyState({
  model,
  onPick,
}: {
  model: ChatModel;
  onPick: (prompt: string) => void;
}) {
  return (
    <div className="mx-auto flex max-w-3xl flex-col items-start gap-6 px-2 py-10">
      <div className="space-y-3">
        <p className="eyebrow">Welcome to {MODEL_LABELS[model]}</p>
        <h1 className="font-display text-2xl font-bold tracking-tight md:text-3xl">
          Ask the control plane a question.
        </h1>
        <AsPath
          hops={[
            { asn: 4766, label: 'KIXS' },
            { asn: 3356, label: 'Level3' },
            { asn: 15169, label: 'Google', anomaly: true },
          ]}
          className="text-xs"
        />
      </div>

      <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-xs text-muted-foreground">
        <Database className="h-4 w-4 text-primary" />
        <span>
          Queries run against pre-processed updates from{' '}
          <span className="font-mono text-foreground">{DATA_WINDOW.collector}</span> ·{' '}
          <Badge variant="outline" className="ml-1">
            {DATA_WINDOW.range}
          </Badge>
        </span>
      </div>

      <div className="grid w-full gap-3 sm:grid-cols-2">
        {EXAMPLE_QUERIES.map((q) => (
          <button
            key={q.title}
            onClick={() => onPick(q.prompt)}
            className="group flex flex-col gap-2 rounded-lg border border-border bg-card p-4 text-left transition-colors hover:border-primary/50 hover:bg-accent"
          >
            <span className="flex items-center justify-between font-mono text-xs font-semibold uppercase tracking-wide text-primary">
              {q.title}
              <ArrowRight className="h-4 w-4 opacity-0 transition-opacity group-hover:opacity-100" />
            </span>
            <span className="line-clamp-3 text-sm text-muted-foreground">{q.prompt}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
