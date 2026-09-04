'use client';

import { useEffect, useState } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine
} from 'recharts';
import { Monitor, AlertTriangle, CheckCircle2, TrendingDown, TrendingUp, Activity, Zap } from 'lucide-react';
import { generateICTimeSeries, generateMonitoringAlerts, generateTimeSeries } from '@/lib/data';

const liveAlerts = [
  { type: 'error', message: 'Alpha A003 decay accelerated — IC dropped 40% in 5 days', time: '2m ago', module: 'Alpha Monitor' },
  { type: 'warning', message: 'Data feed OHLCV latency +320ms above threshold', time: '8m ago', module: 'Data Feed' },
  { type: 'warning', message: 'Model drift detected: LightGBM feature distribution shift', time: '15m ago', module: 'Model Health' },
  { type: 'success', message: 'Risk limits within bounds: Vol 14.7% vs limit 20%', time: '22m ago', module: 'Risk Engine' },
  { type: 'error', message: 'Execution slippage breached: 3.8bps vs 2.5bps limit', time: '1h ago', module: 'Execution' },
  { type: 'success', message: 'PT-001 paper trading day 64 — Sharpe 1.42 (target 1.0)', time: '2h ago', module: 'Live Research' },
  { type: 'warning', message: 'Portfolio turnover elevated: 9.2% vs 7% avg', time: '3h ago', module: 'Portfolio' },
];

const alphaHealthRows = [
  { id: 'LIVE-001', name: 'Earnings Surprise Drift', ic30d: 0.078, ic7d: 0.071, decay: 'Stable', drift: 'None', status: 'healthy' },
  { id: 'LIVE-002', name: 'Momentum Reversal 14D', ic30d: 0.071, ic7d: 0.062, decay: 'Mild', drift: 'None', status: 'healthy' },
  { id: 'LIVE-003', name: 'Order Flow L2', ic30d: 0.092, ic7d: 0.055, decay: 'Fast ⚠', drift: 'Low', status: 'decay' },
  { id: 'LIVE-004', name: 'Value Factor Composite', ic30d: 0.058, ic7d: 0.041, decay: 'Moderate', drift: 'Medium', status: 'watch' },
  { id: 'LIVE-005', name: 'Insider Net Buy', ic30d: 0.031, ic7d: 0.018, decay: 'Severe ✕', drift: 'High', status: 'retire' },
];

const systemHealth = [
  { component: 'Data Pipeline', uptime: '99.98%', latency: '2ms', status: 'healthy' },
  { component: 'Feature Store', uptime: '100%', latency: '8ms', status: 'healthy' },
  { component: 'Model Server', uptime: '99.71%', latency: '45ms', status: 'healthy' },
  { component: 'Risk Engine', uptime: '100%', latency: '12ms', status: 'healthy' },
  { component: 'Order Router', uptime: '99.94%', latency: '1.8ms', status: 'healthy' },
  { component: 'OHLCV Feed', uptime: '98.2%', latency: '320ms', status: 'degraded' },
];

const driftData = Array.from({ length: 30 }, (_, i) => ({
  day: `D-${30 - i}`,
  psiScore: parseFloat((Math.random() * 0.15 + 0.05 + (i > 20 ? 0.1 : 0)).toFixed(3)),
  threshold: 0.2,
}));

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color || '#06b6d4' }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function MonitoringPage() {
  const [icData, setIcData] = useState<any[]>([]);
  const [priceData, setPriceData] = useState<any[]>([]);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setIcData(generateICTimeSeries(24));
    setPriceData(generateTimeSeries(60, 100, 0.01).slice(-30));

    // Simulate live ticking every 3s
    const interval = setInterval(() => setTick(t => t + 1), 3000);
    return () => clearInterval(interval);
  }, []);

  const errCount = liveAlerts.filter(a => a.type === 'error').length;
  const warnCount = liveAlerts.filter(a => a.type === 'warning').length;

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge">
          <span className="status-dot live" />
          12 — Production Monitor
        </div>
        <h1>Production Monitor</h1>
        <p>Real-time monitoring of all production systems: alpha decay, model drift, risk breaches, data feed health, and full system uptime.</p>
      </div>

      {/* Live Status Bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 1.2rem',
        background: 'rgba(6,182,212,0.06)', border: '1px solid rgba(6,182,212,0.2)',
        borderRadius: 10, marginBottom: '1.5rem', flexWrap: 'wrap',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span className="status-dot live" />
          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#06b6d4' }}>ALL SYSTEMS OPERATIONAL</span>
        </div>
        <div style={{ flex: 1 }} />
        {[
          { label: 'Errors', value: errCount, color: '#f43f5e' },
          { label: 'Warnings', value: warnCount, color: '#f59e0b' },
          { label: 'Live Alphas', value: 5, color: '#10b981' },
          { label: 'Uptime', value: '99.94%', color: '#06b6d4' },
        ].map(s => (
          <div key={s.label} style={{ textAlign: 'center', padding: '0 0.75rem', borderLeft: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, fontFamily: 'JetBrains Mono', color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Live Alerts Feed */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Live Alerts</span>
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              <span className="badge badge-rose">{errCount} Critical</span>
              <span className="badge badge-amber">{warnCount} Warn</span>
            </div>
          </div>
          <div style={{ display: 'grid', gap: '0.4rem' }}>
            {liveAlerts.map((a, i) => (
              <div key={i} className={`alert-strip ${a.type === 'error' ? 'danger' : a.type === 'warning' ? 'warning' : 'success'}`}>
                {a.type === 'error' ? <AlertTriangle size={13} /> : a.type === 'warning' ? <AlertTriangle size={13} /> : <CheckCircle2 size={13} />}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.78rem' }}>{a.message}</div>
                  <div style={{ fontSize: '0.65rem', opacity: 0.7, marginTop: '0.1rem' }}>{a.module}</div>
                </div>
                <span style={{ fontSize: '0.65rem', opacity: 0.7, whiteSpace: 'nowrap' }}>{a.time}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Alpha IC Monitoring */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <div className="card-header">
              <span className="card-title">IC Rolling Monitor (24w)</span>
              <span className="badge badge-violet"><Activity size={10} /> Decay Detect</span>
            </div>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={icData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" tick={{ fontSize: 8, fill: '#475569' }} tickLine={false} axisLine={false} interval={5} />
                <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} tickFormatter={v => v.toFixed(2)} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={0.05} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: 'min IC', fill: '#f59e0b', fontSize: 8 }} />
                <Line type="monotone" dataKey="ic" name="IC (30d)" stroke="#06b6d4" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="rankIC" name="Rank IC" stroke="#8b5cf6" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Model Drift */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Feature Drift (PSI Score)</span>
              <span className="badge badge-amber">LightGBM</span>
            </div>
            <ResponsiveContainer width="100%" height={120}>
              <AreaChart data={driftData}>
                <defs>
                  <linearGradient id="driftGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="day" tick={{ fontSize: 8, fill: '#475569' }} tickLine={false} axisLine={false} interval={4} />
                <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={0.2} stroke="#f43f5e" strokeDasharray="4 2" label={{ value: 'Threshold', fill: '#f43f5e', fontSize: 8 }} />
                <Area type="monotone" dataKey="psiScore" name="PSI Score" stroke="#8b5cf6" strokeWidth={2} fill="url(#driftGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Alpha Decay Table */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <span className="card-title">Alpha Health Monitor</span>
          <span className="badge badge-rose">1 Retiring · 1 Decay</span>
        </div>
        <table className="data-table">
          <thead>
            <tr><th>ID</th><th>Alpha</th><th>IC (30d)</th><th>IC (7d)</th><th>Decay Rate</th><th>Model Drift</th><th>Status</th></tr>
          </thead>
          <tbody>
            {alphaHealthRows.map(a => (
              <tr key={a.id}>
                <td style={{ fontFamily: 'JetBrains Mono', color: '#8b5cf6' }}>{a.id}</td>
                <td style={{ color: 'var(--text-primary)', fontFamily: 'inherit' }}>{a.name}</td>
                <td style={{ color: '#3b82f6' }}>{a.ic30d}</td>
                <td style={{ color: a.ic7d < a.ic30d * 0.7 ? '#f43f5e' : '#10b981' }}>{a.ic7d}</td>
                <td style={{ color: a.decay.includes('✕') ? '#f43f5e' : a.decay.includes('⚠') ? '#f59e0b' : 'var(--text-muted)' }}>{a.decay}</td>
                <td style={{ color: a.drift === 'High' ? '#f43f5e' : a.drift === 'Medium' ? '#f59e0b' : 'var(--text-muted)' }}>{a.drift}</td>
                <td>
                  <span className={`badge ${a.status === 'healthy' ? 'badge-emerald' : a.status === 'decay' ? 'badge-rose' : a.status === 'watch' ? 'badge-amber' : 'badge-rose'}`}>
                    {a.status === 'healthy' ? '● Healthy' : a.status === 'decay' ? '⚠ Decay' : a.status === 'watch' ? '⚑ Watch' : '↓ Retire'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* System Health */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">System Component Health</span>
          <span className="badge badge-emerald"><Zap size={10} /> 5 / 6 Healthy</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
          {systemHealth.map(s => (
            <div key={s.component} style={{
              padding: '0.75rem 1rem', borderRadius: 8,
              background: s.status === 'healthy' ? 'rgba(16,185,129,0.06)' : 'rgba(245,158,11,0.08)',
              border: `1px solid ${s.status === 'healthy' ? 'rgba(16,185,129,0.2)' : 'rgba(245,158,11,0.25)'}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem' }}>
                <span className={`status-dot ${s.status === 'healthy' ? 'live' : 'warning'}`} />
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>{s.component}</span>
              </div>
              <div style={{ display: 'flex', gap: '1rem', fontSize: '0.7rem', fontFamily: 'JetBrains Mono' }}>
                <span style={{ color: '#10b981' }}>↑ {s.uptime}</span>
                <span style={{ color: s.status === 'healthy' ? '#3b82f6' : '#f59e0b' }}>⏱ {s.latency}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
