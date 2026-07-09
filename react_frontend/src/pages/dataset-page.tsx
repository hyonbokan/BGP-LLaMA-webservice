import { Link } from 'react-router-dom';
import { ArrowRight, FileJson, Layers, Tag } from 'lucide-react';
import { datasetSections } from '@/data/datasets';
import { Badge } from '@/components/ui/badge';
import type { DatasetItem, DatasetSection } from '@/types';

function DatasetCard({ sectionId, dataset }: { sectionId: string; dataset: DatasetItem }) {
  const categoryCount = dataset.categories ? Object.keys(dataset.categories).length : 0;
  const fileName = dataset.fileUrl ? dataset.fileUrl.split('/').pop() : null;

  return (
    <Link
      to={`/dataset/${sectionId}/${dataset.id}`}
      className="group flex flex-col rounded-lg border border-border bg-card p-5 transition-all hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5"
    >
      <div className="flex items-center justify-between">
        <Badge variant="secondary" className="gap-1.5">
          <FileJson className="h-3 w-3" />
          {dataset.fileType}
        </Badge>
        <span className="font-mono text-xs text-muted-foreground">{dataset.size}</span>
      </div>

      <h3 className="mt-4 font-display text-lg font-semibold leading-tight tracking-tight">
        {dataset.title}
      </h3>

      {/* Hero stat — datasets are about scale */}
      <div className="mt-3 flex items-baseline gap-2">
        <span className="font-mono text-3xl font-semibold tabular-nums text-primary">
          {dataset.fileCount.toLocaleString()}
        </span>
        <span className="font-mono text-xs uppercase tracking-wide text-muted-foreground">
          instructions
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {categoryCount > 0 && (
          <Badge variant="outline" className="gap-1.5">
            <Tag className="h-3 w-3" />
            {categoryCount} topics
          </Badge>
        )}
        {dataset.promptType && (
          <Badge variant="outline" className="gap-1.5">
            <Layers className="h-3 w-3" />
            base prompt
          </Badge>
        )}
      </div>

      <p className="mt-3 line-clamp-3 flex-1 text-sm leading-relaxed text-muted-foreground">
        {dataset.description}
      </p>

      <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
        {fileName ? (
          <span className="truncate font-mono text-xs text-muted-foreground">{fileName}</span>
        ) : (
          <span className="font-mono text-xs text-muted-foreground">—</span>
        )}
        <span className="flex shrink-0 items-center gap-1 font-mono text-xs font-medium text-primary">
          View
          <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
        </span>
      </div>
    </Link>
  );
}

function Section({ section }: { section: DatasetSection }) {
  const totalInstructions = section.datasets.reduce((sum, d) => sum + d.fileCount, 0);
  return (
    <section>
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-xl font-semibold tracking-tight">{section.title}</h2>
        <span className="font-mono text-xs text-muted-foreground">
          {section.datasets.length} datasets · {totalInstructions.toLocaleString()} instructions
        </span>
      </div>
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {section.datasets.map((dataset) => (
          <DatasetCard key={dataset.id} sectionId={section.id} dataset={dataset} />
        ))}
      </div>
    </section>
  );
}

export function DatasetPage() {
  return (
    <div className="container py-12">
      <div className="mb-10 space-y-2">
        <p className="eyebrow">Fine-tuning corpus</p>
        <h1 className="font-display text-3xl font-bold tracking-tight md:text-4xl">Datasets</h1>
        <p className="max-w-2xl text-muted-foreground">
          Instruction-tuning data behind BGP-LLaMA — self-instruct generated sets and the manually
          curated seed tasks they grew from.
        </p>
      </div>

      <div className="space-y-12">
        {datasetSections.map((section) => (
          <Section key={section.id} section={section} />
        ))}
      </div>
    </div>
  );
}
