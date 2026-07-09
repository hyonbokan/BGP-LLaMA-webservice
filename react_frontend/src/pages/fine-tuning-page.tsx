import { useRef, useState } from 'react';
import { Loader2, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import { findSection } from '@/data/datasets';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const MODELS = [
  { value: 'meta-llama/Llama-2-7b-chat-hf', label: 'LLaMA 2 7B' },
  { value: 'meta-llama/Llama-2-13b-chat-hf', label: 'LLaMA 2 13B' },
  { value: 'meta-llama/Llama-2-70b-chat-hf', label: 'LLaMA 2 70B' },
  { value: 'Other', label: 'Other' },
];

const HYPERPARAMETER_FIELDS = [
  { label: 'Lora Alpha', name: 'lora_alpha', type: 'number' },
  { label: 'Lora Dropout', name: 'lora_dropout', type: 'number' },
  { label: 'Lora R', name: 'lora_r', type: 'number' },
  { label: 'Per Device Train Batch Size', name: 'per_device_train_batch_size', type: 'number' },
  { label: 'Gradient Accumulation Steps', name: 'gradient_accumulation_steps', type: 'number' },
  { label: 'Optimizer', name: 'optim', type: 'text' },
  { label: 'Save Steps', name: 'save_steps', type: 'number' },
  { label: 'Logging Steps', name: 'logging_steps', type: 'number' },
  { label: 'Learning Rate', name: 'learning_rate', type: 'number' },
  { label: 'Max Grad Norm', name: 'max_grad_norm', type: 'number' },
  { label: 'Max Steps', name: 'max_steps', type: 'number' },
  { label: 'Warmup Ratio', name: 'warmup_ratio', type: 'number' },
  { label: 'LR Scheduler Type', name: 'lr_scheduler_type', type: 'text' },
] as const;

const DEFAULT_HYPERPARAMETERS: Record<string, string> = {
  lora_alpha: '16',
  lora_dropout: '0.1',
  lora_r: '64',
  per_device_train_batch_size: '4',
  gradient_accumulation_steps: '1',
  optim: 'paged_adamw_32bit',
  save_steps: '200',
  logging_steps: '500',
  learning_rate: '0.0001',
  max_grad_norm: '0.3',
  max_steps: '10000',
  warmup_ratio: '0.05',
  lr_scheduler_type: 'cosine',
};

export function FineTuningPage() {
  const [model, setModel] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [finetunedModelName, setFinetunedModelName] = useState('');
  const [selectedDatasets, setSelectedDatasets] = useState<string[]>([]);
  const [testSamples, setTestSamples] = useState('');
  const [userDataset, setUserDataset] = useState<File | null>(null);
  const [hyperparameters, setHyperparameters] =
    useState<Record<string, string>>(DEFAULT_HYPERPARAMETERS);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const selfInstruct = findSection('self-instruct-generated-dataset');

  const toggleDataset = (fileUrl: string, checked: boolean) => {
    setSelectedDatasets((prev) =>
      checked ? [...prev, fileUrl] : prev.filter((url) => url !== fileUrl)
    );
  };

  const setHyperparameter = (name: string, value: string) =>
    setHyperparameters((prev) => ({ ...prev, [name]: value }));

  const validate = (): string | null => {
    const errors: string[] = [];
    if (!model) errors.push('Please select a model.');
    if (model === 'Other' && !customModel) errors.push('Please enter a custom model id.');
    if (!finetunedModelName) errors.push('Please name the fine-tuned model.');
    if (selectedDatasets.length === 0 && !userDataset)
      errors.push('Please select at least one dataset or upload your own.');
    for (const [key, value] of Object.entries(hyperparameters)) {
      if (value === '') errors.push(`Please fill in ${key.replace(/_/g, ' ')}.`);
    }
    return errors.length ? errors.join(' ') : null;
  };

  const startFineTuning = async () => {
    const error = validate();
    if (error) {
      toast.error(error);
      return;
    }

    setIsLoading(true);
    setStatus('');
    const formData = new FormData();
    formData.append('model_id', model === 'Other' ? customModel : model);
    formData.append('finetuned_model_name', finetunedModelName);
    formData.append('datasets', JSON.stringify(selectedDatasets));
    formData.append('test_samples', testSamples);
    formData.append('hyperparameters', JSON.stringify(hyperparameters));
    if (userDataset) formData.append('user_dataset', userDataset);

    try {
      await api.post('finetuning', formData);
      setStatus('Fine-tuning started successfully.');
      toast.success('Fine-tuning started.');
    } catch (err) {
      console.error('Error starting fine-tuning:', err);
      setStatus('Error starting fine-tuning.');
      toast.error('Could not start fine-tuning. The backend may be offline.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container py-12">
      <div className="mb-8 space-y-2">
        <p className="eyebrow">Training</p>
        <h1 className="font-display text-3xl font-bold tracking-tight md:text-4xl">
          Fine-tune an LLM
        </h1>
        <p className="max-w-2xl text-muted-foreground">
          Configure a LoRA fine-tuning run over the BGP instruction datasets or your own upload.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="font-mono text-base">Model</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Base model</Label>
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a base model" />
                </SelectTrigger>
                <SelectContent>
                  {MODELS.map((m) => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {model === 'Other' && (
              <div className="space-y-2">
                <Label htmlFor="custom-model">Custom model id</Label>
                <Input
                  id="custom-model"
                  placeholder="org/model-name"
                  value={customModel}
                  onChange={(e) => setCustomModel(e.target.value)}
                />
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="ft-name">Fine-tuned model name</Label>
              <Input
                id="ft-name"
                placeholder="bgp-llama-my-run"
                value={finetunedModelName}
                onChange={(e) => setFinetunedModelName(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="font-mono text-base">Datasets</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              {selfInstruct?.datasets.map((d) => (
                <label key={d.id} className="flex items-center gap-3 text-sm">
                  <Checkbox
                    checked={selectedDatasets.includes(d.fileUrl)}
                    onCheckedChange={(checked) => toggleDataset(d.fileUrl, checked === true)}
                  />
                  {d.title}
                </label>
              ))}
            </div>

            <div className="space-y-2 border-t border-border pt-4">
              <Label>Your dataset</Label>
              <input
                ref={fileRef}
                type="file"
                hidden
                onChange={(e) => setUserDataset(e.target.files?.[0] ?? null)}
              />
              <Button
                type="button"
                variant="outline"
                className="gap-2 font-mono"
                onClick={() => fileRef.current?.click()}
              >
                <Upload className="h-4 w-4" /> Upload file
              </Button>
              {userDataset && (
                <p className="font-mono text-xs text-muted-foreground">{userDataset.name}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Upload instruction data as JSON/JSONL with instruction / input / output fields.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="font-mono text-base">Train / test split</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-w-xs space-y-2">
              <Label htmlFor="test-samples">Number of test samples</Label>
              <Input
                id="test-samples"
                type="number"
                value={testSamples}
                onChange={(e) => setTestSamples(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="font-mono text-base">Hyperparameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {HYPERPARAMETER_FIELDS.map((field) => (
                <div key={field.name} className="space-y-2">
                  <Label htmlFor={field.name}>{field.label}</Label>
                  <Input
                    id={field.name}
                    type={field.type}
                    value={hyperparameters[field.name]}
                    onChange={(e) => setHyperparameter(field.name, e.target.value)}
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8 flex flex-col items-center gap-3">
        <Button
          size="lg"
          className="gap-2 font-mono"
          onClick={startFineTuning}
          disabled={isLoading}
        >
          {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
          {isLoading ? 'Starting…' : 'Start fine-tuning'}
        </Button>
        {status && <p className="font-mono text-sm text-muted-foreground">{status}</p>}
      </div>
    </div>
  );
}
