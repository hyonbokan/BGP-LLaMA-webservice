import { Link } from 'react-router-dom';
import { Github, Linkedin, Globe, Facebook, Instagram } from 'lucide-react';
import { Brand } from '@/components/layout/brand';

const SOCIALS = [
  { icon: Github, href: 'https://github.com/hyonbokan/', label: 'GitHub' },
  { icon: Linkedin, href: 'https://www.linkedin.com/in/khen-bo-kan-2909a716b/', label: 'LinkedIn' },
  { icon: Globe, href: 'https://dnlab.cs-cnu.org/', label: 'Lab website' },
  { icon: Facebook, href: 'https://www.facebook.com', label: 'Facebook' },
  { icon: Instagram, href: 'https://www.instagram.com', label: 'Instagram' },
];

const FEATURES = [
  { label: 'BGP Chat', to: '/bgp_chat' as const },
  { label: 'BGP Agent', to: '/bgp_agent' as const },
  { label: 'Dataset', to: '/dataset' as const },
];

const LEARN = [
  {
    label: 'Fine-tuning',
    href: 'https://github.com/hyonbokan/LLM-research/blob/main/finetune_main/finetuning_base/llama_bgpstream_finetune.ipynb',
  },
  { label: 'Paper', href: 'https://ieeexplore.ieee.org/document/10583947/authors#authors' },
  { label: 'Documentation', href: 'https://github.com/hyonbokan/LLM-research' },
];

const linkClass = 'text-sm text-muted-foreground transition-colors hover:text-foreground';

export function Footer() {
  return (
    <footer className="mt-16 border-t border-border/70 bg-card/40">
      <div className="container grid grid-cols-2 gap-8 py-12 md:grid-cols-4">
        <div className="col-span-2 flex flex-col gap-4 md:col-span-1">
          <Brand />
          <p className="max-w-xs text-sm text-muted-foreground">
            Natural-language analysis and anomaly detection for the internet's routing control
            plane.
          </p>
          <div className="flex gap-1">
            {SOCIALS.map(({ icon: Icon, href, label }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noreferrer"
                aria-label={label}
                className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              >
                <Icon className="h-4 w-4" />
              </a>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <h3 className="eyebrow">Features</h3>
          {FEATURES.map((f) => (
            <Link key={f.label} to={f.to} className={linkClass}>
              {f.label}
            </Link>
          ))}
        </div>

        <div className="flex flex-col gap-3">
          <h3 className="eyebrow">Learn</h3>
          {LEARN.map((l) => (
            <a key={l.label} href={l.href} target="_blank" rel="noreferrer" className={linkClass}>
              {l.label}
            </a>
          ))}
        </div>

        <div className="flex flex-col gap-3">
          <h3 className="eyebrow">Contact</h3>
          <p className="text-sm text-muted-foreground">
            99 Daehak-ro, Yuseong-gu, Daejeon, Republic of Korea
          </p>
          <a href="mailto:hyonbokan@cs-cnu.org" className={linkClass}>
            hyonbokan@cs-cnu.org
          </a>
        </div>
      </div>

      <div className="border-t border-border/70">
        <div className="container flex h-14 items-center justify-between text-xs text-muted-foreground">
          <span className="font-mono">© {new Date().getFullYear()} DNLab · CNU</span>
          <span className="font-mono">BGP-LLaMA</span>
        </div>
      </div>
    </footer>
  );
}
