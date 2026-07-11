import { Outlet } from 'react-router-dom';
import { SideRail } from '@/components/layout/side-rail';
import { MobileBar } from '@/components/layout/mobile-bar';
import { Footer } from '@/components/layout/footer';

/** Standard content pages: side rail, scrolling content, footer. */
export function ContentLayout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <SideRail />
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <MobileBar />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
          <Footer />
        </main>
      </div>
    </div>
  );
}

/** Full-height feature workspace (chat / agent): fills the viewport, no footer. */
export function WorkspaceLayout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <SideRail />
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <MobileBar />
        <main className="min-h-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
