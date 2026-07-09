import { cn } from '@/lib/utils';

export interface Hop {
  /** Autonomous System number, e.g. 15169. */
  asn: number;
  /** Optional short label (network name) shown under the ASN. */
  label?: string;
  /** Marks this hop as the anomalous one (route leak / hijack). */
  anomaly?: boolean;
}

/**
 * The signature motif: a BGP AS-path rendered as a connected hop-chain.
 * One hop can be flagged as an anomaly, which is the only place amber appears —
 * mirroring the product's job of surfacing route leaks and hijacks.
 */
export function AsPath({
  hops,
  className,
  animated = true,
}: {
  hops: Hop[];
  className?: string;
  animated?: boolean;
}) {
  return (
    <ol className={cn('flex flex-wrap items-center gap-y-3 font-mono text-sm', className)}>
      {hops.map((hop, i) => (
        <li key={`${hop.asn}-${i}`} className="flex items-center">
          {i > 0 && (
            <span
              aria-hidden
              className={cn(
                'mx-1.5 h-px w-6 bg-gradient-to-r from-border via-primary/60 to-border sm:w-9',
                animated && 'animate-hop-pulse',
                hop.anomaly && 'via-anomaly/70'
              )}
              style={animated ? { animationDelay: `${i * 180}ms` } : undefined}
            />
          )}
          <div
            className={cn(
              'flex flex-col items-center rounded-md border px-2.5 py-1 transition-colors',
              hop.anomaly
                ? 'border-anomaly/50 bg-anomaly/10 text-anomaly'
                : 'border-border bg-card/60 text-foreground'
            )}
          >
            <span className="font-medium leading-tight">AS{hop.asn}</span>
            {hop.label && (
              <span className="text-[10px] leading-tight text-muted-foreground">{hop.label}</span>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}

/** Thin decorative hop-chain used as a section divider. */
export function HopDivider({ className }: { className?: string }) {
  return (
    <div aria-hidden className={cn('flex items-center gap-2 text-muted-foreground/50', className)}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      <span className="h-px flex-1 bg-gradient-to-r from-border via-border to-transparent" />
      <span className="h-1.5 w-1.5 rounded-full bg-primary/60" />
      <span className="h-px w-10 bg-border" />
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
    </div>
  );
}
