/**
 * The BGP-LLaMA mark: an AS-path climbing hop-by-hop to its destination node.
 * Theme-aware — edges/relay nodes use `currentColor`, the destination node uses
 * the primary accent — so it tracks light/dark and doubles as the favicon.
 */
export function Logo({ className, title = 'BGP-LLaMA' }: { className?: string; title?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} role="img" aria-label={title} fill="none">
      <g stroke="currentColor" strokeWidth={2} strokeLinecap="round">
        <line x1="6.5" y1="24" x2="16" y2="16" />
        <line x1="16" y1="16" x2="25.5" y2="8" />
      </g>
      <circle cx="6.5" cy="24" r="2.7" fill="hsl(var(--background))" stroke="currentColor" strokeWidth={2} />
      <circle cx="16" cy="16" r="2.7" fill="hsl(var(--background))" stroke="currentColor" strokeWidth={2} />
      <circle cx="25.5" cy="8" r="3.7" fill="hsl(var(--primary))" />
    </svg>
  );
}
