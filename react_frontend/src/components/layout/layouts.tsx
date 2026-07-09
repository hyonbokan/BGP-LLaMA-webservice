import { Outlet } from 'react-router-dom';
import { Navbar } from '@/components/layout/navbar';
import { Footer } from '@/components/layout/footer';

/** Standard content pages: navbar, scrolling content, footer. */
export function RootLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

/** Full-height workspace (chat): navbar + a flex region that fills the viewport. */
export function ChatLayout() {
  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <Navbar />
      <main className="min-h-0 flex-1">
        <Outlet />
      </main>
    </div>
  );
}
