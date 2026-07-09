import { useState } from 'react';
import { Check, ChevronDown, Code2, Copy } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

/**
 * Read-only view of the code the model extracted from its reply. (Server-side
 * execution ran over a legacy WebSocket path that is no longer wired up, so
 * this surfaces the code for the user to copy and run themselves.)
 */
export function CodePanel({ code }: { code: string }) {
  const [open, setOpen] = useState(true);
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    toast.success('Code copied to clipboard');
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="mx-auto max-w-3xl overflow-hidden rounded-lg border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <button
          onClick={() => setOpen((v) => !v)}
          className="flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-wide text-muted-foreground"
        >
          <Code2 className="h-4 w-4 text-primary" />
          Extracted code
          <ChevronDown className={cn('h-4 w-4 transition-transform', !open && '-rotate-90')} />
        </button>
        <Button variant="ghost" size="sm" className="h-7 gap-1.5 font-mono text-xs" onClick={copy}>
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? 'Copied' : 'Copy'}
        </Button>
      </div>
      {open && (
        <pre className="overflow-x-auto bg-[#0d1117] p-4 font-mono text-[0.8rem] leading-relaxed text-[#e6edf3]">
          <code>{code}</code>
        </pre>
      )}
    </div>
  );
}
