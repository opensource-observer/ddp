'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  Github,
  Database,
  ChevronRight,
  BarChart3,
  Rocket,
  Bot,
  Layers,
  TrendingUp,
  RefreshCw,
  Zap,
  Wallet,
  Repeat,
  Trophy,
  type LucideIcon,
} from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon?: LucideIcon;
  children?: NavItem[];
}

const navItems: NavItem[] = [
  { label: 'Quick Start', href: '/quick-start', icon: Rocket },
  { label: 'Agent Guide', href: '/agent-guide', icon: Bot },
  {
    label: 'Data',
    href: '/data',
    children: [
      {
        label: 'Sources',
        href: '/data/sources',
        icon: Database,
        children: [
          { label: 'Open Dev Data', href: '/data/sources/open-dev-data' },
          { label: 'GitHub Archive', href: '/data/sources/github-archive' },
          { label: 'OSS Directory', href: '/data/sources/oss-directory' },
        ],
      },
      {
        label: 'Models',
        href: '/data/models',
        icon: Layers,
        children: [
          { label: 'Ecosystems', href: '/data/models/ecosystems' },
          { label: 'Repositories', href: '/data/models/repositories' },
          { label: 'Developers', href: '/data/models/developers' },
          { label: 'Commits', href: '/data/models/commits' },
          { label: 'Events', href: '/data/models/events' },
          { label: 'Timeseries Metrics', href: '/data/models/timeseries-metrics' },
        ],
      },
      {
        label: 'Metric Definitions',
        href: '/data/metric-definitions',
        icon: BarChart3,
        children: [
          { label: 'Activity', href: '/data/metric-definitions/activity' },
          { label: 'Alignment', href: '/data/metric-definitions/alignment' },
          { label: 'Lifecycle', href: '/data/metric-definitions/lifecycle' },
          { label: 'Retention', href: '/data/metric-definitions/retention' },
        ],
      },
    ],
  },
  {
    label: 'Insights',
    href: '/insights',
    children: [
      { label: 'Ethereum Repo Rank', href: '/insights/ethereum-repo-rank', icon: Trophy },
      { label: 'DeFi Builder Journeys', href: '/insights/defi-builder-journeys', icon: Wallet },
      { label: 'Speedrun Ethereum', href: '/insights/speedrun-ethereum', icon: Zap },
      { label: '2025 Developer Trends', href: '/insights/developer-report-2025', icon: TrendingUp },
      { label: 'Lifecycle Analysis', href: '/insights/developer-lifecycle', icon: RefreshCw },
      { label: 'Retention Analysis', href: '/insights/developer-retention', icon: Repeat },
    ],
  },
];

function NavLeaf({ item, pathname }: { item: NavItem; pathname: string }) {
  const isActive = pathname === item.href;

  return (
    <li>
      <Link
        href={item.href}
        className={`flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors ${
          isActive
            ? 'bg-[var(--sidebar-accent)] text-[var(--sidebar-primary)] font-medium'
            : 'text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)] hover:text-[var(--sidebar-primary)]'
        }`}
      >
        {item.icon && <item.icon className="h-4 w-4 shrink-0" />}
        <span className="truncate">{item.label}</span>
      </Link>
    </li>
  );
}

function NavGroup({ item, pathname }: { item: NavItem; pathname: string }) {
  const isChildActive = item.children?.some(
    (child) =>
      child.href === pathname ||
      child.children?.some((gc) => gc.href === pathname)
  );
  const [isOpen, setIsOpen] = useState(isChildActive ?? false);

  return (
    <li>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors ${
          isChildActive
            ? 'text-[var(--sidebar-primary)] font-medium'
            : 'text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)] hover:text-[var(--sidebar-primary)]'
        }`}
      >
        {item.icon && <item.icon className="h-4 w-4 shrink-0" />}
        <span className="flex-1 truncate text-left">{item.label}</span>
        <ChevronRight
          className={`h-3.5 w-3.5 shrink-0 text-[var(--sidebar-muted)] transition-transform duration-200 ${
            isOpen ? 'rotate-90' : ''
          }`}
        />
      </button>
      {isOpen && (
        <ul className="mt-0.5 ml-3 border-l border-[var(--sidebar-border)] pl-2 space-y-0.5">
          {item.children!.map((child) =>
            child.children ? (
              <NavGroup key={child.href} item={child} pathname={pathname} />
            ) : (
              <NavLeaf key={child.href} item={child} pathname={pathname} />
            )
          )}
        </ul>
      )}
    </li>
  );
}

function NavSection({ item, pathname }: { item: NavItem; pathname: string }) {
  if (item.children) {
    return (
      <div className="px-3 py-1">
        <p className="px-2 pb-1.5 pt-3 text-xs font-medium text-[var(--sidebar-muted)] uppercase tracking-wider">
          {item.label}
        </p>
        <ul className="space-y-0.5">
          {item.children.map((child) =>
            child.children ? (
              <NavGroup key={child.href} item={child} pathname={pathname} />
            ) : (
              <NavLeaf key={child.href} item={child} pathname={pathname} />
            )
          )}
        </ul>
      </div>
    );
  }

  return (
    <div className="px-3">
      <ul>
        <NavLeaf item={item} pathname={pathname} />
      </ul>
    </div>
  );
}

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 bg-[var(--sidebar-bg)] border-r border-[var(--sidebar-border)] h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--sidebar-border)]">
        <Link href="/" className="flex items-center gap-2.5 rounded-lg px-1 py-1 hover:bg-[var(--sidebar-accent)] transition-colors">
          <div className="shrink-0">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 112 154"
              className="w-6 h-auto text-[var(--sidebar-primary)]"
            >
              <path d="M48.303 153.213c-10.797 0-21.457-2.796-31.1-8.277l5.078-8.934c12.275 6.977 26.536 8.756 40.153 5.008 13.616-3.749 24.963-12.576 31.94-24.863 6.976-12.28 8.756-26.542 5.008-40.158-3.749-13.617-12.577-24.958-24.863-31.94l5.073-8.934c14.67 8.337 25.211 21.882 29.693 38.142 4.476 16.266 2.353 33.294-5.983 47.957-8.337 14.669-21.883 25.212-38.143 29.687a63.538 63.538 0 01-16.857 2.295v.017z" fill="currentColor" />
              <path d="M48.338 132.661c-7.284 0-14.48-1.886-20.983-5.581l5.002-8.828c7.514 4.269 16.307 5.245 24.637 2.951 8.331-2.294 15.267-7.692 19.53-15.207 8.81-15.51 3.358-35.293-12.145-44.097l5.073-8.934c20.434 11.607 27.612 37.67 16.006 58.11-5.623 9.897-14.764 17.016-25.738 20.037a42.877 42.877 0 01-11.382 1.549z" fill="currentColor" />
              <path d="M32.357 118.258c-14.664-8.33-25.212-21.876-29.688-38.136-4.475-16.266-2.353-33.3 5.978-47.969C25.86 1.881 64.486-8.757 94.764 8.443l-5.073 8.935c-25.353-14.404-57.7-5.5-72.11 19.854-6.977 12.28-8.757 26.548-5.002 40.164 3.749 13.617 12.529 24.975 24.81 31.946l-5.026 8.916h-.006z" fill="currentColor" />
              <path d="M42.455 100.408C22.02 88.801 14.896 62.744 26.503 42.304c5.622-9.897 14.775-17.028 25.767-20.073 11.003-3.05 22.515-1.632 32.413 3.991l-5.085 8.91c-7.503-4.262-16.23-5.309-24.585-2.997-8.354 2.312-15.308 7.728-19.576 15.248-8.81 15.51-3.359 35.293 12.144 44.097l-5.126 8.928z" fill="currentColor" />
              <path d="M58.502 72.24c-5.872-3.334-7.894-10.08-4.79-15.544 1.686-2.962 3.986-4.783 6.835-5.41 2.768-.609 5.93-.012 8.905 1.68l5.061-8.911c-5.185-2.945-10.926-3.962-16.17-2.809-5.66 1.242-10.478 4.925-13.57 10.371-5.895 10.377-2.14 23.402 8.62 29.534 5.771 3.281 7.834 10.175 4.695 15.704-1.508 2.66-3.82 4.41-6.675 5.061-2.892.662-6.073.124-8.964-1.52l-5.073 8.934c3.642 2.07 7.621 3.134 11.565 3.134a21.61 21.61 0 004.766-.532c5.664-1.295 10.394-4.849 13.32-10.005 5.978-10.524 2.236-23.561-8.525-29.693v.006z" fill="currentColor" />
            </svg>
          </div>
          <p className="text-sm font-semibold text-[var(--sidebar-primary)] truncate">Developer<br></br>Data<br></br>Portal</p>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-1">
        {navItems.map((item) => (
          <NavSection key={item.href} item={item} pathname={pathname} />
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-[var(--sidebar-border)] px-4 py-3">
        <a
          href="https://github.com/opensource-observer/ddp"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-1 text-sm text-[var(--sidebar-muted)] hover:text-[var(--sidebar-primary)] transition-colors"
        >
          <Github className="h-4 w-4" />
          <span>GitHub</span>
        </a>
      </div>
    </aside>
  );
}
