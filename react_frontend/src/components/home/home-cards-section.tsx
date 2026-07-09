import { Link } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardTitle } from '@/components/ui/card';
import { homeCards } from '@/data/home-cards';

export function HomeCardsSection() {
  return (
    <section className="container py-16">
      <div className="grid gap-6 md:grid-cols-3">
        {homeCards.map((card) => {
          const isExternal = card.link.startsWith('http');
          return (
            <Card key={card.title} className="flex flex-col">
              <CardContent className="flex-1 pt-6">
                <CardTitle className="font-mono">{card.title}</CardTitle>
                <CardDescription className="mt-2 leading-relaxed">
                  {card.description}
                </CardDescription>
              </CardContent>
              <CardFooter>
                {!card.link ? (
                  <Button variant="outline" size="sm" className="font-mono" disabled>
                    {card.buttonText}
                  </Button>
                ) : isExternal ? (
                  <Button asChild variant="outline" size="sm" className="gap-1.5 font-mono">
                    <a href={card.link} target="_blank" rel="noreferrer">
                      {card.buttonText} <ArrowUpRight className="h-4 w-4" />
                    </a>
                  </Button>
                ) : (
                  <Button asChild variant="outline" size="sm" className="font-mono">
                    <Link to={card.link}>{card.buttonText}</Link>
                  </Button>
                )}
              </CardFooter>
            </Card>
          );
        })}
      </div>
    </section>
  );
}
