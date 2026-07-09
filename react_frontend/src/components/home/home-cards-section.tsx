import { Link } from 'react-router-dom';
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  FlaskConical,
  Github,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { homeCards, type HomeCard, type HomeCardKind } from '@/data/home-cards';

const KIND: Record<HomeCardKind, { icon: LucideIcon; label: string }> = {
  docs: { icon: BookOpen, label: 'Docs' },
  code: { icon: Github, label: 'Source' },
  research: { icon: FlaskConical, label: 'Research' },
};

function ResourceCard({ card }: { card: HomeCard }) {
  const { icon: Icon, label } = KIND[card.kind];
  const isExternal = card.link.startsWith('http');
  const disabled = !card.link;

  const inner = (
    <>
      <div className="flex items-start justify-between">
        <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background text-primary transition-colors group-hover:border-primary/40">
          <Icon className="h-5 w-5" />
        </span>
        <span className="eyebrow">{label}</span>
      </div>

      <h3 className="mt-4 font-display text-lg font-semibold tracking-tight">{card.title}</h3>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-muted-foreground">
        {card.description}
      </p>

      <div className="mt-5 flex items-center gap-1.5 border-t border-border pt-4 font-mono text-xs font-medium">
        {disabled ? (
          <span className="text-muted-foreground">{card.buttonText}</span>
        ) : (
          <span className="flex items-center gap-1.5 text-primary">
            {card.buttonText}
            {isExternal ? (
              <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
            ) : (
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            )}
          </span>
        )}
      </div>
    </>
  );

  const className = cn(
    'flex flex-col rounded-lg border border-border bg-card p-5 transition-all',
    disabled
      ? 'opacity-80'
      : 'group hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5'
  );

  if (disabled) return <div className={className}>{inner}</div>;
  if (isExternal)
    return (
      <a href={card.link} target="_blank" rel="noreferrer" className={className}>
        {inner}
      </a>
    );
  return (
    <Link to={card.link} className={className}>
      {inner}
    </Link>
  );
}

export function HomeCardsSection() {
  return (
    <section className="container py-16">
      <div className="mb-10 space-y-2">
        <p className="eyebrow">Resources</p>
        <h2 className="font-display text-2xl font-bold tracking-tight md:text-3xl">Go deeper</h2>
      </div>
      <div className="grid gap-6 md:grid-cols-3">
        {homeCards.map((card) => (
          <ResourceCard key={card.title} card={card} />
        ))}
      </div>
    </section>
  );
}
