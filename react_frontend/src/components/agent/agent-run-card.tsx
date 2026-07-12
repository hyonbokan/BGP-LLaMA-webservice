import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import {
  CircleCheck,
  CircleX,
  Clock,
  Coins,
  FileText,
  Loader2,
  Repeat,
  Terminal,
  User,
  Waypoints,
  Wrench,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type {
  AgentRun,
  AgentRunResult,
  AgentTextTrace,
  AgentToolTrace,
  AgentTraceItem,
} from '@/types';
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
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <ToolTrace trace={run.trace} />
          {run.status === 'running' && <LiveText trace={run.trace} startedAt={run.startedAt} />}
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
      {isUser ? <User className="h-4 w-4" /> : <Waypoints className="h-4 w-4" />}
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

/** The live tool-call trace: one card per tool, updated in place as it runs. */
function ToolTrace({ trace }: { trace?: AgentTraceItem[] }) {
  const tools = (trace ?? []).filter((item): item is AgentToolTrace => item.kind === 'tool');
  if (tools.length === 0) return null;
  return (
    <div className="flex flex-col gap-2">
      {tools.map((tool) => (
        <ToolStep key={tool.id} tool={tool} />
      ))}
    </div>
  );
}

function ToolStep({ tool }: { tool: AgentToolTrace }) {
  const Icon = toolIcon(tool.name);
  const command = asText(tool.input, 'command');
  const output = asText(tool.output);
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border/60 px-3 py-2">
        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="font-mono text-xs text-foreground">{tool.name}</span>
        <div className="ml-auto">
          <ToolStateBadge state={tool.state} />
        </div>
      </div>
      {command && (
        <pre className="overflow-x-auto whitespace-pre-wrap break-words px-3 py-2 font-mono text-xs text-muted-foreground">
          {command}
        </pre>
      )}
      {output && (
        <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-words border-t border-border/60 px-3 py-2 font-mono text-xs text-muted-foreground">
          {output}
        </pre>
      )}
    </div>
  );
}

/** A tool's live state: a spinner while it runs, a check when done, a cross on error. */
function ToolStateBadge({ state }: { state: string }) {
  if (state === 'completed') {
    return (
      <Badge variant="outline" className="gap-1 text-foreground">
        <CircleCheck className="h-3 w-3 text-primary" />
        done
      </Badge>
    );
  }
  if (state === 'error') {
    return (
      <Badge variant="outline" className="gap-1 text-destructive">
        <CircleX className="h-3 w-3" />
        error
      </Badge>
    );
  }
  return (
    <Badge variant="secondary" className="gap-1">
      <Loader2 className="h-3 w-3 animate-spin" />
      {state || 'running'}
    </Badge>
  );
}

/** The agent's answer as it streams; falls back to the working indicator before any text. */
function LiveText({ trace, startedAt }: { trace?: AgentTraceItem[]; startedAt: number }) {
  const text = (trace ?? [])
    .filter((item): item is AgentTextTrace => item.kind === 'text')
    .map((item) => item.text)
    .join('');
  if (!text) return <Working startedAt={startedAt} />;
  return (
    <div className="rounded-lg border border-border bg-card px-4 py-3">
      <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-foreground">
        {text}
        <span className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse bg-primary align-middle" />
      </p>
    </div>
  );
}

function toolIcon(name: string): typeof Clock {
  const lower = name.toLowerCase();
  if (lower === 'bash') return Terminal;
  if (lower === 'read' || lower === 'write' || lower === 'edit') return FileText;
  return Wrench;
}

/** Render a tool's input/output for display: a named field, a bare string, else compact JSON. */
function asText(value: unknown, field?: string): string {
  if (value == null) return '';
  if (typeof value === 'string') return value;
  if (field && typeof value === 'object') {
    const inner = (value as Record<string, unknown>)[field];
    if (typeof inner === 'string') return inner;
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
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
