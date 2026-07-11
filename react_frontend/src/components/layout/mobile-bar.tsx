import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { Brand } from '@/components/layout/brand';
import { ModeToggle } from '@/components/mode-toggle';
import { NAV_GROUPS } from '@/components/layout/nav-links';
import { cn } from '@/lib/utils';

/** Compact top bar + slide-down drawer for the grouped feature nav (mobile only). */
export function MobileBar() {
  const [open, setOpen] = useState(false);

  return (
    <div className="md:hidden">
      <header className="sticky top-0 z-40 flex h-14 items-center gap-2 border-b border-border bg-background/90 px-3 backdrop-blur">
        <button
          aria-label="Toggle menu"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          className="flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
        <Brand />
        <div className="ml-auto">
          <ModeToggle />
        </div>
      </header>

      {open && (
        <div className="border-b border-border bg-background">
          <div className="flex flex-col gap-1 px-3 py-3">
            {NAV_GROUPS.map((group) => (
              <div key={group.label} className="flex flex-col">
                <span className="px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">
                  {group.label}
                </span>
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const cls =
                    'flex items-center gap-3 rounded-md px-2 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent';
                  return item.href ? (
                    <a
                      key={item.title}
                      href={item.href}
                      target="_blank"
                      rel="noreferrer"
                      onClick={() => setOpen(false)}
                      className={cls}
                    >
                      <Icon className="h-4 w-4" /> {item.title}
                    </a>
                  ) : (
                    <NavLink
                      key={item.title}
                      to={item.to ?? '/'}
                      onClick={() => setOpen(false)}
                      className={({ isActive }) => cn(cls, isActive && 'text-foreground')}
                    >
                      <Icon className="h-4 w-4" /> {item.title}
                    </NavLink>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
