import { Link } from 'react-router-dom';
import logo from '@/logo/logo.png';
import { cn } from '@/lib/utils';

/** Wordmark + logo lockup. `to` makes it a home link when set. */
export function Brand({ className, to = '/' }: { className?: string; to?: string }) {
  return (
    <Link to={to} className={cn('flex items-center gap-2.5', className)}>
      <img src={logo} alt="" className="h-8 w-auto" />
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
