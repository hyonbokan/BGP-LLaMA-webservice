import { whatsNew } from '@/data/whats-new';

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });

export function ChangelogTimeline() {
  return (
    <section className="container py-16">
      <div className="mb-10 space-y-2">
        <p className="eyebrow">Changelog</p>
        <h2 className="font-display text-2xl font-bold tracking-tight md:text-3xl">What's new</h2>
      </div>

      <ol className="relative border-l border-border pl-6">
        {whatsNew.map((entry) => (
          <li key={entry.date} className="mb-8 last:mb-0">
            {/* Node on the timeline */}
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
    </section>
  );
}
