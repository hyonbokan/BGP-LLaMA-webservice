import { Fragment } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Logo } from '@/components/logo';
import { ModeToggle } from '@/components/mode-toggle';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { NAV_GROUPS, type NavItem } from '@/components/layout/nav-links';
import { cn } from '@/lib/utils';

/**
 * Global feature nav: a narrow vertical rail of grouped, labelled icons (desktop
 * only). Each feature page renders its own contextual sidebar to the right.
 */
export function SideRail() {
  return (
    <TooltipProvider delayDuration={300}>
      <aside className="hidden h-full w-20 shrink-0 flex-col items-center border-r border-border bg-card/40 py-3 md:flex">
        <Link to="/" aria-label="Home" className="mb-1 text-foreground">
          <Logo className="h-8 w-8" />
        </Link>

        <nav className="flex flex-1 flex-col items-stretch gap-0.5 self-stretch px-2">
          {NAV_GROUPS.map((group) => (
            <Fragment key={group.label}>
              <span className="mt-3 px-1 text-center text-[9px] font-medium uppercase tracking-wider text-muted-foreground/60">
                {group.label}
              </span>
              {group.items.map((item) => (
                <RailLink key={item.title} item={item} />
              ))}
            </Fragment>
          ))}
        </nav>

        <div className="mt-auto flex flex-col items-center pt-2">
          <ModeToggle />
        </div>
      </aside>
    </TooltipProvider>
  );
}

// Static className only. NavLink is rendered inside the tooltip's asChild slot,
// which can't merge a function className — so the active state is expressed with
// aria-current variants (react-router sets aria-current="page" when active).
const RAIL_LINK =
  'relative flex flex-col items-center justify-center gap-1.5 rounded-md py-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground';
const RAIL_ACTIVE =
  'aria-[current=page]:bg-accent aria-[current=page]:text-foreground ' +
  'aria-[current=page]:before:absolute aria-[current=page]:before:left-0 aria-[current=page]:before:top-1/2 ' +
  'aria-[current=page]:before:h-6 aria-[current=page]:before:w-0.5 aria-[current=page]:before:-translate-y-1/2 ' +
  'aria-[current=page]:before:rounded-full aria-[current=page]:before:bg-primary';

function RailLink({ item }: { item: NavItem }) {
  const Icon = item.icon;
  const body = (
    <>
      <Icon className="h-[18px] w-[18px]" />
      <span className="text-[10px] leading-none">{item.short}</span>
    </>
  );

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        {item.href ? (
          <a
            href={item.href}
            target="_blank"
            rel="noreferrer"
            aria-label={item.title}
            className={RAIL_LINK}
          >
            {body}
          </a>
        ) : (
          <NavLink
            to={item.to ?? '/'}
            aria-label={item.title}
            className={cn(RAIL_LINK, RAIL_ACTIVE)}
          >
            {body}
          </NavLink>
        )}
      </TooltipTrigger>
      <TooltipContent side="right">{item.title}</TooltipContent>
    </Tooltip>
  );
}
