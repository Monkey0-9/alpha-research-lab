'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from 'recharts';
import { BarChart3, CheckCircle2, AlertTriangle, XCircle, TrendingDown } from 'lucide-react';
import { generateICTimeSeries, generateAlphaDecay } from '@/lib/data';

const defenses = [
  { name: 'Multiple Testing Correction', method: 'Bonferroni + BH-FDR', result: 'q < 0.05 for 31/48 candidates', status: 'pass' },
  { name: 'False Discovery Rate', method: 'Benjamini-Hochberg', result: 'FDR = 3.2% (threshold 5%)', status: 'pass' },
  { name: 'Data Snooping Bias', method: 'Deflated Sharpe Ratio', result: 'DSR = 1.21 (> 1.0 threshold)', status: 'pass' },
  { name: 'Selection Bias', method: 'Bootstrap resampling', result: 'Bias-corrected Sharpe: 1.54 → 1.41', status: 'pass' },
  { name: 'Survivorship Bias', method: 'Delisted stock inclusion', result: 'Universe includes 100% of delisted tickers', status: 'pass' },
  { name: 'Look-Ahead Bias', method: 'Point-in-time data audit', result: '0 violations detected in PIT audit', status: 'pass' },
  { name: 'Backtest Overfitting', method: 'CSCV + Combinatorial CV', result: 'PBO = 0.18 (< 0.5 acceptable)', status: 'pass' },
];

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

export default function StatisticalEnginePage() {
  const [icSeries, setIcSeries] = useState<any[]>([]);
  const [decayCurve, setDecayCurve] = useState<any[]>([]);
  const [tstatDist, setTstatDist] = useState<any[]>([]);

  useEffect(() => {
    setIcSeries(generateICTimeSeries(52));
    setDecayCurve(generateAlphaDecay(30));
    // Generate t-stat distribution
    const bins = Array.from({ length: 20 }, (_, i) => {
      const x = i * 0.5 - 2;
      const count = Math.floor(Math.exp(-x * x / 2) * 80 + Math.random() * 10);
      return { tstat: x.toFixed(1), count, significant: Math.abs(x) >= 2 };
    });
    setTstatDist(bins);
  }, []);

  const metrics = [
    { label: 'Mean IC', value: '0.087', sub: 'vs 0 null', color: '#06b6d4' },
    { label: 'IC t-stat', value: '4.21', sub: '> 2.0 threshold', color: '#10b981' },
    { label: 'Sharpe Ratio', value: '1.67', sub: 'Annualized', color: '#3b82f6' },
    { label: 'IC IR', value: '0.52', sub: 'IC / StdDev(IC)', color: '#8b5cf6' },
    { label: 'IC Hit Rate', value: '67.3%', sub: 'Positive IC weeks', color: '#f59e0b' },
    { label: 'Alpha Decay', value: '21d', sub: 'Half-life estimate', color: '#f43f5e' },
    { label: 'Breadth', value: '2,400', sub: 'Bets per year', color: '#06b6d4' },
    { label: 'Capacity (AUM)', value: '$820M', sub: 'At 5bps impact', color: '#10b981' },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge"><BarChart3 size={10} /> 04 — Statistical Research Engine</div>
        <h1>Statistical Research Engine</h1>
        <p>Signal-return relationship analysis with comprehensive statistical defenses against overfitting and bias.</p>
      </div>

      {/* Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '1.5rem' }}>
        {metrics.map(m => (
          <div key={m.label} className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.4rem' }}>{m.label}</div>
            <div className="metric-value" style={{ color: m.color, fontSize: '1.5rem' }}>{m.value}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>{m.sub}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">Rolling IC / Rank IC (52 Weeks)</span>
            <span className="badge badge-blue">Weekly</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={icSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} interval={12} />
              <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="rgba(255,255,255,0.15)" strokeDasharray="3 3" />
              <Line type="monotone" dataKey="ic" name="IC" stroke="#06b6d4" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="rankIC" name="Rank IC" stroke="#8b5cf6" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Alpha Decay Curve</span>
            <span className="badge badge-rose">Half-life: 21d</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={decayCurve}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="lag" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} label={{ value: 'Lag (days)', position: 'insideBottom', offset: -2, fontSize: 9, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="rgba(255,255,255,0.15)" strokeDasharray="3 3" />
              <Line type="monotone" dataKey="ic" name="IC at Lag" stroke="#f43f5e" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">t-Statistic Distribution</span>
            <span className="badge badge-emerald">p &lt; 0.05 threshold at |t| = 2</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={tstatDist}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="tstat" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine x="2.0" stroke="#10b981" strokeDasharray="4 2" />
              <ReferenceLine x="-2.0" stroke="#10b981" strokeDasharray="4 2" />
              <Bar dataKey="count" name="Count" radius={[2, 2, 0, 0]}
                fill="#06b6d4"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Autocorrelation — IC Stability</span>
            <span className="badge badge-blue">20-lag ACF</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={Array.from({ length: 20 }, (_, i) => ({
              lag: i + 1,
              acf: parseFloat((0.35 * Math.pow(0.85, i) + (Math.random() - 0.5) * 0.08).toFixed(3)),
            }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="lag" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" />
              <Bar dataKey="acf" name="ACF" fill="#8b5cf6" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Statistical Defense */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Statistical Defense — Bias & Overfitting Controls</span>
          <span className="badge badge-emerald"><CheckCircle2 size={10} /> 7/7 Passing</span>
        </div>
        <div style={{ display: 'grid', gap: '0.35rem' }}>
          {defenses.map((d) => (
            <div key={d.name} style={{
              display: 'flex', alignItems: 'center', gap: '0.75rem',
              padding: '0.65rem 0.9rem',
              background: 'var(--bg-secondary)', border: '1px solid rgba(16,185,129,0.15)',
              borderRadius: 8,
            }}>
              <CheckCircle2 size={14} color="#10b981" />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{d.name}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>{d.method} → {d.result}</div>
              </div>
              <span className="badge badge-emerald">PASS</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
