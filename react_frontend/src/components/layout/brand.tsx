import { Link } from 'react-router-dom';
import { Logo } from '@/components/logo';
import { cn } from '@/lib/utils';

/** Wordmark + logo lockup. `to` makes it a home link when set. */
export function Brand({ className, to = '/' }: { className?: string; to?: string }) {
  return (
    <Link to={to} className={cn('flex items-center gap-2.5', className)}>
      <Logo className="h-8 w-8 shrink-0 text-foreground" />
      <span className="flex flex-col leading-none">
        <span className="font-display text-base font-bold tracking-tight text-foreground">
          BGP-LLaMA
        </span>
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          control plane
        </span>
      </span>
    </Link>
  );
}
