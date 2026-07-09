import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { capabilities } from '@/data/capabilities';

export function CapabilitiesSection() {
  return (
    <section className="border-t border-border/70 bg-card/30">
      <div className="container py-16">
        <div className="mb-10 max-w-2xl space-y-2">
          <p className="eyebrow">Capabilities</p>
          <h2 className="font-display text-2xl font-bold tracking-tight md:text-3xl">
            What you can ask it to analyze
          </h2>
          <p className="text-sm text-muted-foreground md:text-base">
            Across routing, policy, anomaly detection, and topology — grouped by analysis domain.
          </p>
        </div>

        <Accordion type="single" collapsible defaultValue={capabilities[0].category}>
          {capabilities.map((group) => (
            <AccordionItem key={group.category} value={group.category}>
              <AccordionTrigger className="text-base">
                <span className="flex items-center gap-3">
                  {group.category}
                  <Badge variant="secondary">{group.subcapabilities.length}</Badge>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="grid gap-3 sm:grid-cols-2">
                  {group.subcapabilities.map((cap) => (
                    <div
                      key={cap.title}
                      className="rounded-lg border border-border bg-background p-4"
                    >
                      <h4 className="font-mono text-sm font-semibold text-foreground">
                        {cap.title}
                      </h4>
                      <p className="mt-1 text-sm text-muted-foreground">{cap.description}</p>
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
