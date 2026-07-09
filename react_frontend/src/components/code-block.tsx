import { useState } from 'react';
import hljs from 'highlight.js';
import { Check, Copy } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import 'highlight.js/styles/github-dark.css';

/** Syntax-highlighted, copyable code block. */
export function CodeBlock({
  code,
  language = 'python',
  className,
}: {
  code: string;
  language?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);
  const html = hljs.getLanguage(language)
    ? hljs.highlight(code, { language }).value
    : hljs.highlightAuto(code).value;

  const copy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    toast.success('Copied to clipboard');
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div
      className={cn(
        'group relative overflow-hidden rounded-lg border border-border bg-[#0d1117]',
        className
      )}
    >
      <button
        onClick={copy}
        aria-label="Copy code"
        className="absolute right-2 top-2 z-10 rounded-md border border-border/60 bg-background/40 p-1.5 text-muted-foreground opacity-0 backdrop-blur transition-opacity hover:text-foreground group-hover:opacity-100"
      >
        {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      </button>
      <pre className="overflow-x-auto p-4 font-mono text-[0.8rem] leading-relaxed text-[#e6edf3]">
        {/* Safe: highlight.js HTML-escapes the source (only its own <span> markup is
            added), and callers pass static, bundled data — never user input. */}
        <code className="hljs bg-transparent p-0" dangerouslySetInnerHTML={{ __html: html }} />
      </pre>
    </div>
  );
}
