import { Link } from 'react-router-dom';
import { ChevronRight, Download, FileJson, Hash, Tag } from 'lucide-react';
import { toast } from 'sonner';
import { useDatasetDetails } from '@/hooks/use-dataset-details';
import { findSection } from '@/data/datasets';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CodeBlock } from '@/components/code-block';
import { NotFoundPage } from '@/pages/not-found-page';

interface Sample {
  name?: string;
  instruction?: string;
  input?: string;
  output?: string;
}

/** Normalize the two snapshot shapes (flat vs. `instances[]`) into one sample. */
function parseSnapshot(snap: unknown): Sample {
  if (!snap || typeof snap !== 'object') return {};
  const s = snap as Record<string, unknown>;
  const instances = s.instances;
  const instance =
    Array.isArray(instances) && instances.length && typeof instances[0] === 'object'
      ? (instances[0] as Record<string, unknown>)
      : null;
  const str = (v: unknown) => (typeof v === 'string' ? v : undefined);
  return {
    name: str(s.name),
    instruction: str(s.instruction),
    input: str(instance?.input ?? s.input),
    output: str(instance?.output ?? s.output),
  };
}

const looksLikeCode = (text: string) =>
  /(^|\n)\s*(import |from \w|def |for \w|print\(|stream\s*=)/.test(text);

// Strip the leading "N. " index from category keys.
const cleanCategory = (key: string) => key.replace(/^\d+\.\s*/, '');

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <p className="eyebrow">{label}</p>
      {children}
    </div>
  );
}

export function DetailPage() {
  const { dataset, sectionId, handleDownload } = useDatasetDetails();

  if (!dataset) return <NotFoundPage />;

  const section = findSection(sectionId);
  const sample = parseSnapshot(dataset.jsonSnapshot);
  const categories = dataset.categories ? Object.entries(dataset.categories) : [];
  const isManualSeed = sectionId?.includes('manual');

  const download = async (url: string, fileId: string, fileType?: string) => {
    if (!url) {
      toast.error('This dataset has no downloadable file.');
      return;
    }
    try {
      await handleDownload(url, fileId, fileType);
    } catch {
      toast.error('Download failed. The backend may be offline.');
    }
  };

  return (
    <div className="container py-10">
      {/* Breadcrumb */}
      <nav className="mb-6 flex flex-wrap items-center gap-1.5 font-mono text-xs text-muted-foreground">
        <Link to="/dataset" className="hover:text-foreground">
          Datasets
        </Link>
        {section && (
          <>
            <ChevronRight className="h-3.5 w-3.5" />
            <span>{section.title}</span>
          </>
        )}
        <ChevronRight className="h-3.5 w-3.5" />
        <span className="text-foreground">{dataset.title}</span>
      </nav>

      {/* Header */}
      <div className="space-y-3">
        <p className="eyebrow">{section?.title ?? 'Dataset'}</p>
        <h1 className="font-display text-3xl font-bold tracking-tight md:text-4xl">
          {dataset.title}
        </h1>
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary" className="gap-1.5">
            <FileJson className="h-3 w-3" />
            {dataset.fileType}
          </Badge>
          <Badge variant="outline" className="gap-1.5">
            <Hash className="h-3 w-3" />
            {dataset.fileCount.toLocaleString()} instructions
          </Badge>
          <Badge variant="outline">{dataset.size}</Badge>
          {categories.length > 0 && (
            <Badge variant="outline" className="gap-1.5">
              <Tag className="h-3 w-3" />
              {categories.length} topics
            </Badge>
          )}
        </div>
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-3">
        {/* Main column */}
        <div className="space-y-10 lg:col-span-2">
          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold tracking-tight">Overview</h2>
            <p className="leading-relaxed text-muted-foreground">{dataset.description}</p>
          </section>

          {/* Sample record — the actual instruction/input/output shape */}
          {(sample.instruction || sample.output) && (
            <section className="space-y-4">
              <h2 className="font-display text-lg font-semibold tracking-tight">Sample record</h2>
              <div className="space-y-5 rounded-lg border border-border bg-card p-5">
                {sample.name && (
                  <p className="font-mono text-xs text-muted-foreground">{sample.name}</p>
                )}
                {sample.instruction && (
                  <Field label="Instruction">
                    <p className="text-sm leading-relaxed">{sample.instruction}</p>
                  </Field>
                )}
                {sample.input && (
                  <Field label="Input">
                    <pre className="overflow-x-auto rounded-md border border-border bg-background/60 p-3 font-mono text-xs leading-relaxed">
                      {sample.input}
                    </pre>
                  </Field>
                )}
                {sample.output && (
                  <Field label="Output">
                    {looksLikeCode(sample.output) ? (
                      <CodeBlock code={sample.output} language="python" />
                    ) : (
                      <p className="text-sm leading-relaxed text-muted-foreground">
                        {sample.output}
                      </p>
                    )}
                  </Field>
                )}
              </div>

              <details className="group rounded-lg border border-border bg-card">
                <summary className="flex cursor-pointer items-center gap-2 px-4 py-3 font-mono text-xs text-muted-foreground marker:content-none hover:text-foreground">
                  <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
                  View raw JSON
                </summary>
                <pre className="overflow-x-auto border-t border-border bg-[#0d1117] p-4 font-mono text-xs leading-relaxed text-[#e6edf3]">
                  {JSON.stringify(dataset.jsonSnapshot, null, 2)}
                </pre>
              </details>
            </section>
          )}

          {/* Topics — the rich, previously-hidden content */}
          {categories.length > 0 && (
            <section className="space-y-4">
              <h2 className="font-display text-lg font-semibold tracking-tight">
                Topics covered
                <span className="ml-2 font-mono text-sm font-normal text-muted-foreground">
                  {categories.length}
                </span>
              </h2>
              <div className="grid gap-3 sm:grid-cols-2">
                {categories.map(([key, desc], i) => (
                  <div key={key} className="rounded-lg border border-border bg-card p-4">
                    <div className="flex items-baseline gap-2">
                      <span className="font-mono text-xs text-primary">
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <h3 className="font-mono text-sm font-semibold">{cleanCategory(key)}</h3>
                    </div>
                    <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{desc}</p>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Sidebar: facts + downloads */}
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <div className="space-y-5 rounded-lg border border-border bg-card p-5">
            <div>
              <p className="eyebrow mb-3">Details</p>
              <dl className="space-y-2.5 font-mono text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">Instructions</dt>
                  <dd className="tabular-nums">{dataset.fileCount.toLocaleString()}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">Size</dt>
                  <dd>{dataset.size}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">Format</dt>
                  <dd>{dataset.fileType}</dd>
                </div>
                {categories.length > 0 && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted-foreground">Topics</dt>
                    <dd className="tabular-nums">{categories.length}</dd>
                  </div>
                )}
              </dl>
            </div>

            <div className="space-y-2 border-t border-border pt-4">
              <Button
                className="w-full gap-2 font-mono"
                onClick={() => download(dataset.fileUrl, dataset.id, dataset.fileType)}
              >
                <Download className="h-4 w-4" /> Download dataset
              </Button>
              {isManualSeed && dataset.promptType && (
                <Button
                  variant="outline"
                  className="w-full gap-2 font-mono"
                  onClick={() =>
                    download(dataset.promptUrl ?? '', `${dataset.id}-prompt`, dataset.promptType)
                  }
                >
                  <Download className="h-4 w-4" /> Base prompt
                </Button>
              )}
            </div>

            {dataset.fileUrl && (
              <p className="truncate border-t border-border pt-3 font-mono text-xs text-muted-foreground">
                {dataset.fileUrl.split('/').pop()}
              </p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
