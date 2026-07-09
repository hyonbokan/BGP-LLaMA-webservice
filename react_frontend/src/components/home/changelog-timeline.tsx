import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { whatsNew } from '@/data/whats-new';

// Homepage only previews the most recent updates; older ones expand in place.
// (A section inside the landing scroll — collapse beats pagination here.)
const PREVIEW_COUNT = 4;

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });

export function ChangelogTimeline() {
  const [expanded, setExpanded] = useState(false);
  const entries = expanded ? whatsNew : whatsNew.slice(0, PREVIEW_COUNT);
  const hiddenCount = whatsNew.length - PREVIEW_COUNT;

  return (
    <section className="container py-16">
      <div className="mb-10 space-y-2">
        <p className="eyebrow">Changelog</p>
        <h2 className="font-display text-2xl font-bold tracking-tight md:text-3xl">What's new</h2>
      </div>

      <ol className="relative border-l border-border pl-6">
        {entries.map((entry) => (
          <li key={entry.date} className="mb-8 last:mb-0">
            <span className="absolute -left-[6.5px] mt-1.5 h-3 w-3 rounded-full border-2 border-primary bg-background" />
            <time className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
              {formatDate(entry.date)}
            </time>
            <h3 className="mt-1 font-display text-lg font-semibold tracking-tight">
              {entry.title}
            </h3>
            <p className="mt-1 whitespace-pre-line text-sm leading-relaxed text-muted-foreground">
              {entry.detail}
            </p>
          </li>
        ))}
      </ol>

      {hiddenCount > 0 && (
        <div className="mt-4 pl-6">
          <Button
            variant="ghost"
            className="gap-2 font-mono"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
          >
            {expanded
              ? 'Show less'
              : `Show ${hiddenCount} older update${hiddenCount > 1 ? 's' : ''}`}
            <ChevronDown className={cn('h-4 w-4 transition-transform', expanded && 'rotate-180')} />
          </Button>
        </div>
      )}
    </section>
  );
}
