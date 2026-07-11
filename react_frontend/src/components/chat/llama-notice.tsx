import { Info } from 'lucide-react';
import { MODEL_LABELS } from '@/components/chat/constants';

/**
 * Heads-up shown while BGP-LLaMA is selected: the fine-tuned model runs on a
 * locally hosted vLLM server (GPU-backed), so it only answers when that backend
 * is reachable. Deployments without a GPU should use BGP-GPT instead.
 */
export function LlamaNotice() {
  return (
    <div
      role="note"
      className="mx-auto flex max-w-3xl items-start gap-2 rounded-lg border border-border bg-muted px-3 py-2 text-xs text-muted-foreground"
    >
      <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
      <span>
        <span className="font-mono font-semibold text-foreground">
          {MODEL_LABELS.bgp_llama}
        </span>{' '}
        runs on a locally hosted model served by vLLM (GPU required). If requests fail, switch to{' '}
        <span className="font-mono font-semibold text-foreground">{MODEL_LABELS.gpt_5_4_mini}</span>{' '}
        instead.
      </span>
    </div>
  );
}
