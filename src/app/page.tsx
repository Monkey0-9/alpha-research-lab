'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import {
  Database, Cpu, FlaskConical, BarChart3, Brain, GitBranch,
  ShieldCheck, PieChart, Zap, AlertTriangle, Activity, Monitor,
  TrendingUp, TrendingDown, ArrowRight, CheckCircle2
} from 'lucide-react';
import { generatePnL, generateTimeSeries, generateDrawdown, generateMonitoringAlerts } from '@/lib/data';

const modules = [
  { num: '01', href: '/data', label: 'Data Infrastructure', icon: Database, color: '#3b82f6', desc: 'Tick, OHLCV, Fundamentals, PIT Store', status: 'live' },
  { num: '02', href: '/features', label: 'Feature Factory', icon: Cpu, color: '#10b981', desc: 'Price, Fundamental, Macro, Microstructure', status: 'live' },
  { num: '03', href: '/alpha-discovery', label: 'Alpha Discovery', icon: FlaskConical, color: '#8b5cf6', desc: 'Hypothesis Engine, Genetic Programming', status: 'live' },
  { num: '04', href: '/statistical-engine', label: 'Statistical Engine', icon: BarChart3, color: '#06b6d4', desc: 'IC, t-stat, FDR, Bias Detection', status: 'live' },
  { num: '05', href: '/model-lab', label: 'Model Research Lab', icon: Brain, color: '#f59e0b', desc: 'Ensemble, Meta-Model, Transformers', status: 'live' },
  { num: '06', href: '/validation', label: 'TS Validation', icon: GitBranch, color: '#f97316', desc: 'Walk-Forward, Purged CV, Embargo', status: 'live' },
  { num: '07', href: '/quality-gate', label: 'Alpha Quality Gate', icon: ShieldCheck, color: '#10b981', desc: '9-Criteria Quality Filter', status: 'live' },
  { num: '08', href: '/portfolio', label: 'Portfolio Engine', icon: PieChart, color: '#3b82f6', desc: 'MV, Risk Parity, CVaR Optimization', status: 'live' },
  { num: '09', href: '/execution', label: 'Execution Research', icon: Zap, color: '#f43f5e', desc: 'Market Impact, Slippage, Fill Quality', status: 'live' },
  { num: '10', href: '/risk', label: 'Risk Engine', icon: AlertTriangle, color: '#f59e0b', desc: 'VaR, CVaR, Factor Risk, Drawdown', status: 'live' },
  { num: '11', href: '/live-research', label: 'Live Research', icon: Activity, color: '#8b5cf6', desc: 'Paper → Production Pipeline', status: 'live' },
  { num: '12', href: '/monitoring', label: 'Production Monitor', icon: Monitor, color: '#06b6d4', desc: 'Drift, Decay, Risk Breaches', status: 'live' },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color }}>
            {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [pnl, setPnl] = useState<any[]>([]);
  const [price, setPrice] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    const rawPnl = generatePnL(120);
    setPnl(generateDrawdown(rawPnl).slice(-60));
    setPrice(generateTimeSeries(90, 100, 0.012).slice(-60));
    setAlerts(generateMonitoringAlerts());
  }, []);

  const metrics = [
    { label: 'Portfolio Sharpe', value: '1.67', change: '+0.14', positive: true, color: '#10b981' },
    { label: 'Alpha IC (30d)', value: '0.089', change: '+0.012', positive: true, color: '#3b82f6' },
    { label: 'Max Drawdown', value: '-8.3%', change: '+1.2%', positive: false, color: '#f43f5e' },
    { label: 'Active Alphas', value: '5', change: '+1 this week', positive: true, color: '#8b5cf6' },
    { label: 'Model Accuracy', value: '76.4%', change: '+0.8%', positive: true, color: '#f59e0b' },
    { label: 'VaR (95%)', value: '-2.34%', change: '-0.2%', positive: true, color: '#06b6d4' },
  ];

  return (
    <div className="page-container" style={{ paddingTop: '2rem' }}>
      {/* Hero */}
      <div style={{ marginBottom: '2rem', position: 'relative' }}>
        <div className="hero-glow" style={{ width: 400, height: 400, background: '#3b82f6', top: -100, left: '20%' }} />
        <div className="hero-glow" style={{ width: 300, height: 300, background: '#8b5cf6', top: -50, right: '10%' }} />
        <div className="page-header-badge">
          <span className="status-dot live" /> Research Mode Active · Sep 2026
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1.1, marginBottom: '0.5rem' }}>
          <span className="text-gradient-blue">QuantAlpha</span> Research Platform
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', maxWidth: 600 }}>
          End-to-end quantitative alpha research — from raw market data to live production monitoring. 12 integrated modules, one unified platform.
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid-6" style={{ marginBottom: '1.5rem' }}>
        {metrics.map((m) => (
          <div key={m.label} className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.07em' }}>{m.label}</div>
            <div className="metric-value" style={{ fontSize: '1.4rem', color: m.color }}>{m.value}</div>
            <div className={`metric-change ${m.positive ? 'positive' : 'negative'}`} style={{ marginTop: '0.25rem' }}>
              {m.positive ? <TrendingUp size={10} style={{ display: 'inline', marginRight: 3 }} /> : <TrendingDown size={10} style={{ display: 'inline', marginRight: 3 }} />}
              {m.change}
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">Cumulative P&L</span>
            <span className="badge badge-emerald">Live</span>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={pnl}>
              <defs>
                <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#475569' }} tickLine={false} axisLine={false} interval={19} />
              <YAxis tick={{ fontSize: 10, fill: '#475569' }} tickLine={false} axisLine={false} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="cumulative" name="P&L" stroke="#10b981" strokeWidth={2} fill="url(#pnlGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Drawdown</span>
            <span className="badge badge-rose">Risk</span>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={pnl}>
              <defs>
                <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#475569' }} tickLine={false} axisLine={false} interval={19} />
              <YAxis tick={{ fontSize: 10, fill: '#475569' }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v.toFixed(1)}%`} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="drawdown" name="Drawdown %" stroke="#f43f5e" strokeWidth={2} fill="url(#ddGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Modules Grid */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Research Pipeline</h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>12 Modules · All Active</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
          {modules.map((m) => {
            const Icon = m.icon;
            return (
              <Link
                key={m.href}
                href={m.href}
                style={{ textDecoration: 'none' }}
              >
                <div className="card" style={{
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  borderColor: 'var(--border-subtle)',
                  padding: '1rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{
                        width: 30, height: 30, borderRadius: 8,
                        background: `${m.color}18`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        border: `1px solid ${m.color}30`,
                      }}>
                        <Icon size={14} color={m.color} />
                      </div>
                      <span style={{ fontFamily: 'JetBrains Mono', fontSize: '0.65rem', color: 'var(--text-muted)' }}>{m.num}</span>
                    </div>
                    <ArrowRight size={12} color="var(--text-muted)" />
                  </div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>{m.label}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>{m.desc}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.5rem' }}>
                    <span className="status-dot live" />
                    <span style={{ fontSize: '0.65rem', color: 'var(--accent-emerald)' }}>Active</span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Alerts + Research Loop */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <span className="card-title">System Alerts</span>
            <span className="badge badge-rose">{alerts.filter(a => a.type === 'error').length} Critical</span>
          </div>
          {alerts.map((a, i) => (
            <div key={i} className={`alert-strip ${a.type === 'error' ? 'danger' : a.type === 'warning' ? 'warning' : 'success'}`}>
              {a.type === 'error' ? <AlertTriangle size={13} /> : a.type === 'warning' ? <AlertTriangle size={13} /> : <CheckCircle2 size={13} />}
              <div style={{ flex: 1, fontSize: '0.78rem' }}>{a.message}</div>
              <span style={{ fontSize: '0.65rem', opacity: 0.7, whiteSpace: 'nowrap' }}>{a.time}</span>
            </div>
          ))}
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Research Loop</span>
            <span className="badge badge-violet">Continuous</span>
          </div>
          {[
            { label: 'New Hypothesis Generated', status: 'done', detail: 'Vol surface skew decay in small-caps' },
            { label: 'Experiment Running', status: 'active', detail: 'Walk-forward CV · 48 folds · LightGBM' },
            { label: 'Statistical Validation', status: 'active', detail: 'IC t-stat = 3.7 · FDR q < 0.05' },
            { label: 'Quality Gate Review', status: 'pending', detail: 'Awaiting OOS evidence (2 weeks)' },
            { label: 'Alpha Library', status: 'pending', detail: '5 alphas live · 3 in review' },
          ].map((s, i) => (
            <div key={i} className={`pipeline-step ${s.status}`} style={{ marginBottom: '0.35rem' }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>{s.label}</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>{s.detail}</div>
              </div>
              <span className={`badge ${s.status === 'done' ? 'badge-emerald' : s.status === 'active' ? 'badge-blue' : 'badge-muted'}`}>
                {s.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
