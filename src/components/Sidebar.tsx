'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Database, Cpu, FlaskConical, BarChart3, Brain,
  GitBranch, ShieldCheck, PieChart, Zap, AlertTriangle,
  Activity, Monitor, LayoutDashboard, TrendingUp
} from 'lucide-react';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard, num: '00' },
  { href: '/data', label: 'Data Infrastructure', icon: Database, num: '01' },
  { href: '/features', label: 'Feature Factory', icon: Cpu, num: '02' },
  { href: '/alpha-discovery', label: 'Alpha Discovery', icon: FlaskConical, num: '03' },
  { href: '/statistical-engine', label: 'Statistical Engine', icon: BarChart3, num: '04' },
  { href: '/model-lab', label: 'Model Research Lab', icon: Brain, num: '05' },
  { href: '/validation', label: 'TS Validation', icon: GitBranch, num: '06' },
  { href: '/quality-gate', label: 'Alpha Quality Gate', icon: ShieldCheck, num: '07' },
  { href: '/portfolio', label: 'Portfolio Engine', icon: PieChart, num: '08' },
  { href: '/execution', label: 'Execution Research', icon: Zap, num: '09' },
  { href: '/risk', label: 'Risk Engine', icon: AlertTriangle, num: '10' },
  { href: '/live-research', label: 'Live Research', icon: Activity, num: '11' },
  { href: '/monitoring', label: 'Production Monitor', icon: Monitor, num: '12' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <TrendingUp size={16} color="#3b82f6" />
          <h1>QuantAlpha</h1>
        </div>
        <p>Alpha Research Platform</p>
      </div>

      <div className="nav-section">
        <div className="nav-section-label">Modules</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-number">{item.num}</span>
              <Icon size={14} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div style={{ marginTop: 'auto', padding: '1rem', borderTop: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem' }}>
          <span className="status-dot live" />
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Research Mode Active</span>
        </div>
        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
          v2.4.1 · Sep 2026
        </div>
      </div>
    </nav>
  );
}
