import {
  Bot,
  Database,
  Download,
  MessagesSquare,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  /** Full name — shown in the tooltip and the mobile drawer. */
  title: string;
  /** Compact label shown under the icon in the rail. */
  short: string;
  icon: LucideIcon;
  /** Internal route, or `href` for an external link (exactly one is set). */
  to?: string;
  href?: string;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

const MODEL_DOWNLOAD_URL =
  'https://huggingface.co/hyonbokan/bgp-llama-3.1-instruct-10kSteps-2kDataset';

/** Feature nav, grouped by category — rendered in the side rail and mobile drawer. */
export const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Analyze',
    items: [
      { title: 'BGP Chat', short: 'Chat', icon: MessagesSquare, to: '/bgp_chat' },
      { title: 'BGP Agent', short: 'Agent', icon: Bot, to: '/bgp_agent' },
    ],
  },
  {
    label: 'Explore',
    items: [
      { title: 'Dataset', short: 'Dataset', icon: Database, to: '/dataset' },
      { title: 'Download model', short: 'Model', icon: Download, href: MODEL_DOWNLOAD_URL },
    ],
  },
];
