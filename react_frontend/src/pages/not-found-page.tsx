import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { HopDivider } from '@/components/as-path';

export function NotFoundPage() {
  return (
    <div className="container flex min-h-[60vh] flex-col items-center justify-center gap-6 py-20 text-center">
      <p className="font-mono text-sm uppercase tracking-[0.3em] text-anomaly">404</p>
      <h1 className="font-display text-4xl font-bold tracking-tight md:text-5xl">
        No route to this prefix.
      </h1>
      <p className="max-w-md text-muted-foreground">
        The page you're looking for isn't in the table. It may have been withdrawn or never
        announced.
      </p>
      <HopDivider className="w-full max-w-xs" />
      <Button asChild className="font-mono">
        <Link to="/">Return to origin</Link>
      </Button>
    </div>
  );
}
