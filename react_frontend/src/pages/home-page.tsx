import { Hero } from '@/components/home/hero';
import { ChangelogTimeline } from '@/components/home/changelog-timeline';
import { CapabilitiesSection } from '@/components/home/capabilities-section';
import { HomeCardsSection } from '@/components/home/home-cards-section';

export function HomePage() {
  return (
    <>
      <Hero />
      <CapabilitiesSection />
      <ChangelogTimeline />
      <HomeCardsSection />
    </>
  );
}
