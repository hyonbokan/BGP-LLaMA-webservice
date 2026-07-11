import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Bot, CircleCheck, CircleX, Clock, Coins, Repeat, User } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { AgentRun, AgentRunResult } from '@/types';
import 'highlight.js/styles/github-dark.css';

/** One run in the console: the question, then a live status or the result card. */
export function AgentRunCard({ run }: { run: AgentRun }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-row-reverse gap-3">
        <Avatar kind="user" />
        <div className="max-w-[85%] rounded-lg border border-primary/20 bg-primary/10 px-4 py-3 md:max-w-[75%]">
          <p className="text-sm leading-relaxed">{run.query}</p>
        </div>
      </div>

      <div className="flex gap-3">
        <Avatar kind="agent" />
        <div className="min-w-0 flex-1">
          {run.status === 'running' && <Working startedAt={run.startedAt} />}
          {run.status === 'error' && <ErrorCard message={run.error ?? 'The run failed.'} />}
          {run.status === 'done' && run.result && <ResultCard result={run.result} />}
        </div>
      </div>
    </div>
  );
}

function Avatar({ kind }: { kind: 'user' | 'agent' }) {
  const isUser = kind === 'user';
  return (
    <div
      className={
        'mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border ' +
        (isUser
          ? 'border-primary/30 bg-primary/10 text-primary'
          : 'border-border bg-card text-muted-foreground')
      }
    >
      {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
    </div>
  );
}

/** Live "the agent is working" indicator with an elapsed-seconds counter. */
function Working({ startedAt }: { startedAt: number }) {
  const elapsed = useElapsedSeconds(startedAt);
  return (
    <div className="flex w-fit items-center gap-2 rounded-lg border border-border bg-card px-4 py-3">
      <div className="flex gap-1" aria-hidden>
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary" />
      </div>
      <span className="font-mono text-xs text-muted-foreground">
        Running the analysis · {elapsed}s
      </span>
    </div>
  );
}

function ResultCard({ result }: { result: AgentRunResult }) {
  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="markdown px-4 py-3">
        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
          {result.text || '_The run produced no answer._'}
        </ReactMarkdown>
      </div>
      <div className="flex flex-wrap items-center gap-2 border-t border-border px-4 py-2.5">
        <SubtypeBadge subtype={result.subtype} />
        {result.numTurns != null && (
          <Meta
            icon={Repeat}
            label={`${result.numTurns} turn${result.numTurns === 1 ? '' : 's'}`}
          />
        )}
        {result.durationMs != null && (
          <Meta icon={Clock} label={`${(result.durationMs / 1000).toFixed(1)}s`} />
        )}
        {result.costUsd != null && <Meta icon={Coins} label={`$${result.costUsd.toFixed(4)}`} />}
      </div>
    </div>
  );
}

function ErrorCard({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
      <CircleX className="mt-0.5 h-4 w-4 shrink-0" />
      <span className="break-words">{message}</span>
    </div>
  );
}

/** The run's terminal subtype: green check for a clean success, else a plain tag. */
function SubtypeBadge({ subtype }: { subtype: string | null }) {
  if (subtype === 'success') {
    return (
      <Badge variant="outline" className="gap-1 text-foreground">
        <CircleCheck className="h-3 w-3 text-primary" />
        success
      </Badge>
    );
  }
  return <Badge variant="secondary">{subtype ?? 'done'}</Badge>;
}

function Meta({ icon: Icon, label }: { icon: typeof Clock; label: string }) {
  return (
    <span className="flex items-center gap-1 font-mono text-xs text-muted-foreground">
      <Icon className="h-3 w-3" />
      {label}
    </span>
  );
}

/** Seconds elapsed since `startedAt`, ticking once a second. */
function useElapsedSeconds(startedAt: number): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  return Math.max(0, Math.floor((now - startedAt) / 1000));
}
