import { cn } from '@/lib/utils';
import type { ChatModel } from '@/types';
import { MODEL_LABELS } from '@/components/chat/constants';

const MODELS: ChatModel[] = ['bgp_llama', 'gpt_5_4_mini'];

/** Segmented toggle between the fine-tuned LLaMA and the GPT-5.4-mini backend. */
export function ModelSwitch({
  value,
  onChange,
  disabled,
}: {
  value: ChatModel;
  onChange: (model: ChatModel) => void;
  disabled?: boolean;
}) {
  return (
    <div
      role="radiogroup"
      aria-label="Model"
      className="inline-flex items-center rounded-lg border border-border bg-muted p-1"
    >
      {MODELS.map((model) => {
        const active = value === model;
        return (
          <button
            key={model}
            role="radio"
            aria-checked={active}
            disabled={disabled}
            onClick={() => onChange(model)}
            className={cn(
              'rounded-md px-3 py-1 font-mono text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50',
              active
                ? 'bg-background text-foreground shadow'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {MODEL_LABELS[model]}
          </button>
        );
      })}
    </div>
  );
}
