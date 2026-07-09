import { Link } from 'react-router-dom';
import { datasetSections } from '@/data/datasets';
import { Badge } from '@/components/ui/badge';

const cropWords = (text: string, limit: number) => {
  const words = text.split(' ');
  return words.length > limit ? words.slice(0, limit).join(' ') + '…' : text;
};

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
          <section key={section.id}>
            <h2 className="mb-4 font-display text-xl font-semibold tracking-tight">
              {section.title}
            </h2>
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full min-w-[720px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border bg-card/60 text-left">
                    <th className="px-4 py-3 font-mono text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Title
                    </th>
                    <th className="px-4 py-3 font-mono text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Description
                    </th>
                    <th className="px-4 py-3 text-right font-mono text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Instructions
                    </th>
                    <th className="px-4 py-3 text-right font-mono text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Size
                    </th>
                    <th className="px-4 py-3 font-mono text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Type
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {section.datasets.map((dataset) => (
                    <tr
                      key={dataset.id}
                      className="border-b border-border transition-colors last:border-0 hover:bg-accent/40"
                    >
                      <td className="px-4 py-3 align-top">
                        <Link
                          to={`/dataset/${section.id}/${dataset.id}`}
                          className="font-mono font-medium text-primary hover:underline"
                        >
                          {dataset.title}
                        </Link>
                      </td>
                      <td className="max-w-md px-4 py-3 align-top text-muted-foreground">
                        {cropWords(dataset.description, 20)}
                      </td>
                      <td className="px-4 py-3 text-right align-top font-mono tabular-nums">
                        {dataset.fileCount.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right align-top font-mono tabular-nums text-muted-foreground">
                        {dataset.size}
                      </td>
                      <td className="px-4 py-3 align-top">
                        <Badge variant="secondary">{dataset.fileType}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
