import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Download, Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ModeToggle } from '@/components/mode-toggle';
import { Brand } from '@/components/layout/brand';
import { NAV_LINKS, MODEL_DOWNLOAD_URL } from '@/components/layout/nav-links';
import { cn } from '@/lib/utils';

const linkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'font-mono text-sm tracking-wide transition-colors hover:text-foreground',
    isActive ? 'text-foreground' : 'text-muted-foreground'
  );

export function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="container flex h-16 items-center gap-6">
        <Brand />

        <div className="hidden items-center gap-6 md:flex">
          {NAV_LINKS.map((item) => (
            <NavLink key={item.path} to={item.path} className={linkClass}>
              {item.title}
            </NavLink>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <ModeToggle />
          <Button asChild variant="outline" size="sm" className="hidden font-mono sm:inline-flex">
            <a href={MODEL_DOWNLOAD_URL} target="_blank" rel="noreferrer">
              <Download /> Download model
            </a>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Toggle menu"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X /> : <Menu />}
          </Button>
        </div>
      </nav>

      {/* Mobile menu */}
      {open && (
        <div className="border-t border-border/70 bg-background md:hidden">
          <div className="container flex flex-col py-3">
            {NAV_LINKS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  cn(
                    'rounded-md px-2 py-2 font-mono text-sm transition-colors hover:bg-accent',
                    isActive ? 'text-foreground' : 'text-muted-foreground'
                  )
                }
                onClick={() => setOpen(false)}
              >
                {item.title}
              </NavLink>
            ))}
            <a
              href={MODEL_DOWNLOAD_URL}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 rounded-md px-2 py-2 font-mono text-sm text-muted-foreground hover:bg-accent"
              onClick={() => setOpen(false)}
            >
              <Download className="h-4 w-4" /> Download model
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
