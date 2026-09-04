'use client';

import { useEffect, useState } from 'react';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine
} from 'recharts';
import { Activity, CheckCircle2, Clock, GitBranch, TrendingUp, Play, Pause } from 'lucide-react';
import { generatePnL, generateDrawdown, generateICTimeSeries } from '@/lib/data';

const paperTrades = [
  { id: 'PT-001', alpha: 'Momentum Reversal 21D', started: '2026-07-01', days: 64, sharpe: 1.42, ic: 0.081, pnl: '+$12,840', status: 'promote', color: '#10b981' },
  { id: 'PT-002', alpha: 'Vol Surface Skew', started: '2026-07-15', days: 50, sharpe: 1.18, ic: 0.069, pnl: '+$7,220', status: 'promote', color: '#10b981' },
  { id: 'PT-003', alpha: 'Order Flow Imbalance', started: '2026-08-01', days: 33, sharpe: 1.61, ic: 0.097, pnl: '+$18,450', status: 'watching', color: '#3b82f6' },
  { id: 'PT-004', alpha: 'EV/EBITDA Zscore', started: '2026-08-10', days: 24, sharpe: 0.88, ic: 0.044, pnl: '+$1,240', status: 'watching', color: '#f59e0b' },
  { id: 'PT-005', alpha: 'Macro Beta Timing', started: '2026-08-20', days: 14, sharpe: 0.31, ic: 0.019, pnl: '-$820', status: 'abort', color: '#f43f5e' },
];

const productionAlphas = [
  { id: 'LIVE-001', name: 'Earnings Surprise Drift', live: '2026-03-01', aum: '$2.1M', sharpe: 1.44, ic: 0.078, status: 'healthy' },
  { id: 'LIVE-002', name: 'Momentum Reversal 14D', live: '2026-01-15', aum: '$3.4M', sharpe: 1.31, ic: 0.071, status: 'healthy' },
  { id: 'LIVE-003', name: 'Order Flow L2', live: '2025-11-01', aum: '$1.8M', sharpe: 1.67, ic: 0.092, status: 'healthy' },
  { id: 'LIVE-004', name: 'Value Factor Composite', live: '2025-08-20', aum: '$2.8M', sharpe: 1.12, ic: 0.058, status: 'decay' },
  { id: 'LIVE-005', name: 'Insider Net Buy', live: '2025-06-10', aum: '$1.2M', sharpe: 0.72, ic: 0.031, status: 'retire' },
];

const promotionCriteria = [
  { label: 'Paper Trading Days', required: '≥ 60', current: '64', pass: true },
  { label: 'OOS Sharpe', required: '≥ 1.0', current: '1.42', pass: true },
  { label: 'IC in Paper Period', required: '≥ 0.05', current: '0.081', pass: true },
  { label: 'Correlation to Live Alphas', required: '< 0.6', current: '0.34', pass: true },
  { label: 'Capacity Check', required: '$5M+', current: '$12M', pass: true },
  { label: 'Quality Gate Score', required: '≥ 7/9', required2: '', current: '8/9', pass: true },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color || '#8b5cf6' }}>
            {p.name}: {typeof p.value === 'number' ? p.value.toFixed(4) : p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function LiveResearchPage() {
  const [pnlData, setPnlData] = useState<any[]>([]);
  const [icData, setIcData] = useState<any[]>([]);
  const [selectedPaper, setSelectedPaper] = useState('PT-001');

  useEffect(() => {
    const raw = generatePnL(90);
    setPnlData(generateDrawdown(raw).slice(-60));
    setIcData(generateICTimeSeries(24));
  }, []);

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge"><Activity size={10} /> 11 — Live Research</div>
        <h1>Live Research</h1>
        <p>Manage the paper → production pipeline. Monitor paper trading experiments, track promotion criteria, and oversee production alpha health.</p>
      </div>

      {/* Stats */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {[
          { label: 'Paper Experiments', value: '5', color: '#8b5cf6' },
          { label: 'Ready to Promote', value: '2', color: '#10b981' },
          { label: 'Production Alphas', value: '5', color: '#3b82f6' },
          { label: 'Total AUM Managed', value: '$11.3M', color: '#f59e0b' },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.4rem' }}>{m.label}</div>
            <div className="metric-value" style={{ color: m.color, fontSize: '1.6rem' }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Pipeline Visual */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
        <div className="card-header">
          <span className="card-title">Paper → Production Pipeline</span>
          <span className="badge badge-violet"><GitBranch size={10} /> Research Lifecycle</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
          {[
            { stage: 'Hypothesis', count: 12, color: '#475569', icon: '💡' },
            { stage: 'Backtest', count: 8, color: '#3b82f6', icon: '📊' },
            { stage: 'Statistical Gate', count: 6, color: '#8b5cf6', icon: '🔬' },
            { stage: 'Quality Gate', count: 5, color: '#f59e0b', icon: '🛡️' },
            { stage: 'Paper Trading', count: 5, color: '#f97316', icon: '📝' },
            { stage: 'Production', count: 5, color: '#10b981', icon: '🚀' },
          ].map((s, i, arr) => (
            <div key={s.stage} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
              <div style={{
                padding: '0.6rem 1rem', borderRadius: 10, background: `${s.color}18`,
                border: `1px solid ${s.color}30`, textAlign: 'center', minWidth: 100,
              }}>
                <div style={{ fontSize: '1.2rem', marginBottom: '0.2rem' }}>{s.icon}</div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: s.color }}>{s.stage}</div>
                <div style={{ fontSize: '0.8rem', fontWeight: 800, color: s.color, fontFamily: 'JetBrains Mono' }}>{s.count}</div>
              </div>
              {i < arr.length - 1 && (
                <div style={{ color: 'var(--text-muted)', fontSize: '1.2rem' }}>→</div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Paper Trading Experiments */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Paper Trading Experiments</span>
            <span className="badge badge-blue"><Clock size={10} /> 5 Active</span>
          </div>
          <div style={{ display: 'grid', gap: '0.4rem' }}>
            {paperTrades.map(pt => (
              <div
                key={pt.id}
                onClick={() => setSelectedPaper(pt.id)}
                style={{
                  padding: '0.6rem 0.85rem', borderRadius: 8, cursor: 'pointer',
                  background: selectedPaper === pt.id ? `${pt.color}10` : 'var(--bg-secondary)',
                  border: `1px solid ${selectedPaper === pt.id ? `${pt.color}30` : 'var(--border-subtle)'}`,
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>{pt.alpha}</span>
                  <span className={`badge ${pt.status === 'promote' ? 'badge-emerald' : pt.status === 'abort' ? 'badge-rose' : 'badge-blue'}`}>
                    {pt.status === 'promote' ? '↑ Promote' : pt.status === 'abort' ? '✕ Abort' : '● Watching'}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '1.2rem', fontSize: '0.7rem', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>
                  <span>Day {pt.days}</span>
                  <span style={{ color: '#3b82f6' }}>Sharpe {pt.sharpe}</span>
                  <span style={{ color: '#8b5cf6' }}>IC {pt.ic}</span>
                  <span style={{ color: pt.pnl.startsWith('+') ? '#10b981' : '#f43f5e' }}>{pt.pnl}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Promotion Checklist */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Promotion Criteria — PT-001</span>
            <span className="badge badge-emerald"><CheckCircle2 size={10} /> 6 / 6 Pass</span>
          </div>
          <div style={{ display: 'grid', gap: '0.35rem', marginBottom: '1rem' }}>
            {promotionCriteria.map(c => (
              <div key={c.label} className={`checklist-item ${c.pass ? 'pass' : 'fail'}`}>
                <CheckCircle2 size={13} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>{c.label}</div>
                  <div style={{ fontSize: '0.68rem', opacity: 0.8 }}>Required: {c.required} · Current: {c.current}</div>
                </div>
              </div>
            ))}
          </div>
          <button className="btn btn-emerald" style={{ width: '100%', justifyContent: 'center' }}>
            <Play size={13} /> Promote PT-001 to Production
          </button>
        </div>
      </div>

      {/* Production Alpha Health */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Production Alpha Health</span>
          <span className="badge badge-emerald">5 Live Alphas</span>
        </div>
        <table className="data-table">
          <thead>
            <tr><th>ID</th><th>Alpha</th><th>Live Since</th><th>AUM</th><th>Sharpe</th><th>IC</th><th>Status</th></tr>
          </thead>
          <tbody>
            {productionAlphas.map(a => (
              <tr key={a.id}>
                <td style={{ fontFamily: 'JetBrains Mono', color: '#8b5cf6' }}>{a.id}</td>
                <td style={{ color: 'var(--text-primary)', fontFamily: 'inherit' }}>{a.name}</td>
                <td style={{ color: 'var(--text-muted)' }}>{a.live}</td>
                <td style={{ color: '#3b82f6' }}>{a.aum}</td>
                <td style={{ color: a.sharpe >= 1.2 ? '#10b981' : a.sharpe >= 0.8 ? '#f59e0b' : '#f43f5e' }}>{a.sharpe}</td>
                <td>{a.ic}</td>
                <td>
                  <span className={`badge ${a.status === 'healthy' ? 'badge-emerald' : a.status === 'decay' ? 'badge-amber' : 'badge-rose'}`}>
                    {a.status === 'healthy' ? '● Healthy' : a.status === 'decay' ? '⚠ Decay' : '↓ Retire'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
