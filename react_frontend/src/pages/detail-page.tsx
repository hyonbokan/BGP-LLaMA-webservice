import { Download } from 'lucide-react';
import { toast } from 'sonner';
import { useDatasetDetails } from '@/hooks/use-dataset-details';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { NotFoundPage } from '@/pages/not-found-page';

export function DetailPage() {
  const { dataset, sectionId, handleDownload } = useDatasetDetails();

  if (!dataset) return <NotFoundPage />;

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

  const isManualSeed = sectionId?.includes('manual');

  return (
    <div className="container py-12">
      <div className="grid gap-10 lg:grid-cols-2">
        {/* About */}
        <div className="space-y-6">
          <div className="space-y-2">
            <p className="eyebrow">Dataset</p>
            <h1 className="font-display text-3xl font-bold tracking-tight">{dataset.title}</h1>
            <div className="flex flex-wrap gap-2 pt-1 font-mono text-xs text-muted-foreground">
              <Badge variant="secondary">{dataset.fileType}</Badge>
              <Badge variant="outline">{dataset.fileCount.toLocaleString()} instructions</Badge>
              <Badge variant="outline">{dataset.size}</Badge>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button
              className="gap-2 font-mono"
              onClick={() => download(dataset.fileUrl, dataset.id, dataset.fileType)}
            >
              <Download className="h-4 w-4" /> Download dataset
            </Button>
            {isManualSeed && dataset.promptType && (
              <Button
                variant="outline"
                className="gap-2 font-mono"
                onClick={() =>
                  download(dataset.promptUrl ?? '', `${dataset.id}-prompt`, dataset.promptType)
                }
              >
                <Download className="h-4 w-4" /> Download base prompt
              </Button>
            )}
          </div>

          <p className="leading-relaxed text-muted-foreground">{dataset.description}</p>
        </div>

        {/* JSON structure */}
        <div className="space-y-3">
          <h2 className="font-display text-lg font-semibold tracking-tight">JSON structure</h2>
          <div className="max-h-[600px] overflow-auto rounded-lg border border-border bg-[#0d1117] p-4">
            <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-relaxed text-[#e6edf3]">
              {JSON.stringify(dataset.jsonSnapshot, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
