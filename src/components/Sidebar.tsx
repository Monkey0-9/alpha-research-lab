'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, Database, Cpu, FlaskConical, BarChart3,
  Brain, GitBranch, ShieldCheck, PieChart, Zap,
  AlertTriangle, Activity, Monitor, Terminal
} from 'lucide-react';

const MODULES = [
  { href: '/', label: 'Executive Dashboard', code: '00', icon: LayoutDashboard },
  { href: '/data', label: 'Data Infrastructure', code: '01', icon: Database },
  { href: '/features', label: 'Feature / Signal Factory', code: '02', icon: Cpu },
  { href: '/alpha-discovery', label: 'Alpha Discovery Lab', code: '03', icon: FlaskConical },
  { href: '/statistical-engine', label: 'Statistical Engine', code: '04', icon: BarChart3 },
  { href: '/model-lab', label: 'Model Research Lab', code: '05', icon: Brain },
  { href: '/validation', label: 'TS Validation Engine', code: '06', icon: GitBranch },
  { href: '/quality-gate', label: 'Alpha Quality Gate', code: '07', icon: ShieldCheck },
  { href: '/portfolio', label: 'Portfolio Construction', code: '08', icon: PieChart },
  { href: '/execution', label: 'Execution Research', code: '09', icon: Zap },
  { href: '/risk', label: 'Institutional Risk', code: '10', icon: AlertTriangle },
  { href: '/live-research', label: 'Live Paper Trading', code: '11', icon: Activity },
  { href: '/monitoring', label: 'Production Telemetry', code: '12', icon: Monitor },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ background: 'rgba(56, 189, 248, 0.15)', padding: '0.25rem', borderRadius: '3px', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
              <Terminal size={14} color="#38bdf8" />
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, letterSpacing: '0.04em', color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                QUANT<span style={{ color: '#38bdf8' }}>ALPHA</span>
              </div>
              <div style={{ fontSize: '0.62rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                HEDGE FUND WORKSTATION
              </div>
            </div>
          </div>
          <span className="badge-tag badge-live" style={{ fontSize: '0.6rem', padding: '0.1rem 0.3rem' }}>
            V2.4.1
          </span>
        </div>
      </div>

      <div className="sidebar-scroll">
        <div className="nav-section-title">Research Pipeline Modules</div>
        {MODULES.map((mod) => {
          const Icon = mod.icon;
          const isActive = pathname === mod.href;
          return (
            <Link
              key={mod.href}
              href={mod.href}
              className={`nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-code">[{mod.code}]</span>
              <Icon size={14} style={{ opacity: isActive ? 1 : 0.7 }} />
              <span style={{ flex: 1, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                {mod.label}
              </span>
              {isActive && (
                <span className="status-indicator-dot live" />
              )}
            </Link>
          );
        })}
      </div>

      <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid var(--border-terminal)', background: '#080b12' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span className="status-indicator-dot live" />
            <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
              FFI ENGINE: ACTIVE
            </span>
          </div>
          <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: '#34d399' }}>
            0.4ms
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.62rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
          <span>MEM: 384MB / 16GB</span>
          <span>AUM: $2.48M</span>
        </div>
      </div>
    </aside>
  );
}
