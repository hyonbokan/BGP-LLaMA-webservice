import { useCallback, useRef, useState } from 'react';
import { apiUrl } from '@/config';
import type { AgentRun, AgentSseEvent } from '@/types';

let nextRunId = 1;

/** The most recent successful run's answer, threaded forward as prior findings. */
function lastFindings(runs: AgentRun[]): string | null {
  for (let i = runs.length - 1; i >= 0; i--) {
    const run = runs[i];
    if (run.status === 'done' && run.result && !run.result.isError) return run.result.text;
  }
  return null;
}

/**
 * Owns the BGP Agent console: a log of autonomous runs and the streamed
 * connection to the FastAPI agent endpoint. Each submit is one single-shot run —
 * the request POSTs the query plus the last run's distilled findings (the memory
 * unit that carries context forward without replaying a transcript), and the SSE
 * body is read with fetch + a stream reader. `running` frames are a heartbeat
 * while the pod works (no live token/tool trace yet); `result` fills the run's
 * result card; `error` marks it failed. The stream ending stops the spinner.
 */
export function useBgpAgent() {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [input, setInput] = useState('');
  const [isRunning, setIsRunning] = useState(false);

  const abortRef = useRef<AbortController | null>(null);

  const closeStream = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const patchRun = useCallback((id: number, updater: (run: AgentRun) => AgentRun) => {
    setRuns((prev) => prev.map((run) => (run.id === id ? updater(run) : run)));
  }, []);

  const handleEvent = useCallback(
    (id: number, data: AgentSseEvent) => {
      switch (data.status) {
        case 'agent_started':
        case 'running':
          // The pod is working; the run card shows a live "working" indicator.
          break;

        case 'result':
          patchRun(id, (run) => ({
            ...run,
            status: data.is_error ? 'error' : 'done',
            error: data.is_error ? (data.text ?? 'The run failed.') : undefined,
            result: {
              text: data.text ?? '',
              isError: Boolean(data.is_error),
              subtype: data.subtype ?? null,
              costUsd: data.cost_usd ?? null,
              durationMs: data.duration_ms ?? null,
              numTurns: data.num_turns ?? null,
              structuredOutput: data.structured_output ?? null,
            },
          }));
          break;

        case 'error':
          patchRun(id, (run) => ({ ...run, status: 'error', error: data.message }));
          break;
      }
    },
    [patchRun]
  );

  const submit = useCallback(() => {
    const query = input.trim();
    if (!query || isRunning) return;

    const priorFindings = lastFindings(runs);
    const id = nextRunId++;
    setRuns((prev) => [...prev, { id, query, status: 'running', startedAt: Date.now() }]);
    setInput('');
    setIsRunning(true);
    closeStream();

    const controller = new AbortController();
    abortRef.current = controller;

    // EventSource can't POST, so read the SSE body off a fetch stream, splitting
    // on the blank-line frame boundary and parsing each `data:` payload.
    (async () => {
      try {
        const res = await fetch(apiUrl('agent/run'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, prior_findings: priorFindings }),
          signal: controller.signal,
        });
        if (!res.ok || !res.body) throw new Error(`Request failed (${res.status})`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let boundary: number;
          while ((boundary = buffer.indexOf('\n\n')) !== -1) {
            const frame = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            const line = frame.split('\n').find((l) => l.startsWith('data:'));
            if (!line) continue; // skip `: keep-alive` comments
            try {
              handleEvent(id, JSON.parse(line.slice(5).trim()));
            } catch (err) {
              console.error('Failed to parse SSE message:', err);
            }
          }
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          console.error('Agent SSE error:', err);
          patchRun(id, (run) => ({ ...run, status: 'error', error: (err as Error).message }));
        }
      } finally {
        if (abortRef.current === controller) abortRef.current = null;
        setIsRunning(false);
      }
    })();
  }, [input, isRunning, runs, closeStream, handleEvent, patchRun]);

  const stop = useCallback(() => {
    setIsRunning(false);
    closeStream();
    // Mark whichever run is still in flight as stopped; a cut connection makes
    // the pod reap the run, so nothing keeps working server-side.
    setRuns((prev) =>
      prev.map((run) =>
        run.status === 'running' ? { ...run, status: 'error', error: 'Run stopped.' } : run
      )
    );
  }, [closeStream]);

  const reset = useCallback(() => {
    closeStream();
    setIsRunning(false);
    setRuns([]);
  }, [closeStream]);

  return { runs, input, setInput, isRunning, submit, stop, reset };
}
