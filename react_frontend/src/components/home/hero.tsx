import { Link } from 'react-router-dom';
import { ArrowRight, TriangleAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AsPath } from '@/components/as-path';

export function Hero() {
  return (
    <section className="bg-grid border-b border-border/70">
      <div className="container grid items-center gap-12 py-16 md:py-24 lg:grid-cols-[1.1fr_1fr]">
        {/* Thesis */}
        <div className="flex flex-col items-start gap-6">
          <p className="eyebrow">BGP control plane intelligence</p>
          <h1 className="font-display text-4xl font-bold leading-[1.05] tracking-tight md:text-5xl lg:text-6xl">
            Read the routing table
            <br />
            in <span className="text-primary">plain language</span>.
          </h1>
          <p className="max-w-xl text-base leading-relaxed text-muted-foreground md:text-lg">
            BGP-LLaMA is an instruction fine-tuned, open-source LLM that automates and scales BGP
            routing analysis — turning natural-language questions into reports, generated analysis
            code, and anomaly detection.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Button asChild size="lg" className="gap-2 font-mono">
              <Link to="/bgp_chat">
                Open the chat <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="font-mono">
              <Link to="/dataset">Browse datasets</Link>
            </Button>
          </div>
        </div>

        {/* Signature: a looking-glass readout with a flagged anomaly hop */}
        <div className="w-full overflow-hidden rounded-xl border border-border bg-card shadow-lg">
          <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-destructive/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-anomaly/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-primary/70" />
            <span className="ml-2 font-mono text-xs text-muted-foreground">looking-glass</span>
          </div>
          <div className="space-y-4 p-5 font-mono text-sm">
            <p className="text-muted-foreground">
              <span className="text-primary">?</span> origin &amp; AS-path for{' '}
              <span className="text-foreground">8.8.8.0/24</span>, Oct 28 13:00–13:15
            </p>
            <div className="space-y-1">
              <p className="text-xs uppercase tracking-widest text-muted-foreground">
                observed path
              </p>
              <AsPath
                hops={[
                  { asn: 4766, label: 'KIXS' },
                  { asn: 3356, label: 'Level3' },
                  { asn: 15169, label: 'Google' },
                ]}
              />
            </div>
            <div className="flex items-start gap-2 rounded-md border border-anomaly/40 bg-anomaly/10 px-3 py-2 text-anomaly">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
              <span className="text-xs leading-relaxed text-foreground">
                <span className="font-semibold text-anomaly">Anomaly:</span> unexpected origin{' '}
                <span className="font-semibold">AS9009</span> announcing this prefix — possible
                origin hijack.
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
