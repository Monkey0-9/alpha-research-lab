'use client';

import { useEffect, useState } from 'react';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine
} from 'recharts';
import { AlertTriangle, TrendingDown, ShieldCheck, Activity } from 'lucide-react';
import { generatePnL, generateDrawdown, generateRiskMetrics } from '@/lib/data';

const riskMetrics = generateRiskMetrics();

const factorRisk = [
  { factor: 'Market', contribution: 38.2, color: '#3b82f6' },
  { factor: 'Momentum', contribution: 22.4, color: '#8b5cf6' },
  { factor: 'Value', contribution: 14.1, color: '#10b981' },
  { factor: 'Size', contribution: 10.8, color: '#f59e0b' },
  { factor: 'Quality', contribution: 8.3, color: '#f97316' },
  { factor: 'Idiosyncratic', contribution: 6.2, color: '#06b6d4' },
];

const stressScenarios = [
  { name: 'COVID Crash (2020-02)', portfolioReturn: '-6.8%', benchReturn: '-34%', maxDD: '-9.1%', status: 'pass' },
  { name: 'Rate Shock (2022-01)', portfolioReturn: '+2.3%', benchReturn: '-18%', maxDD: '-4.2%', status: 'pass' },
  { name: 'GFC Replay (2008)', portfolioReturn: '-18.4%', benchReturn: '-57%', maxDD: '-22.1%', status: 'warn' },
  { name: 'Flash Crash (2010)', portfolioReturn: '-1.2%', benchReturn: '-9%', maxDD: '-2.8%', status: 'pass' },
  { name: '1987 Black Monday', portfolioReturn: '-24.1%', benchReturn: '-22%', maxDD: '-28.3%', status: 'fail' },
  { name: 'Tech Bubble (2000)', portfolioReturn: '+4.1%', benchReturn: '-49%', maxDD: '-5.2%', status: 'pass' },
];

const varData = Array.from({ length: 252 }, (_, i) => {
  const ret = (Math.random() - 0.5) * 6;
  return { ret: parseFloat(ret.toFixed(2)), freq: 1 };
});

const histData = (() => {
  const bins: Record<string, number> = {};
  varData.forEach(d => {
    const bin = (Math.round(d.ret * 2) / 2).toFixed(1);
    bins[bin] = (bins[bin] || 0) + 1;
  });
  return Object.entries(bins)
    .map(([ret, freq]) => ({ ret: parseFloat(ret), freq }))
    .sort((a, b) => a.ret - b.ret);
})();

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color || '#f43f5e' }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function RiskPage() {
  const [drawdownData, setDrawdownData] = useState<any[]>([]);

  useEffect(() => {
    const raw = generatePnL(180);
    setDrawdownData(generateDrawdown(raw).slice(-90));
  }, []);

  const riskRows = [
    { label: 'VaR (95%, 1d)', value: `${riskMetrics.var95}%`, color: '#f59e0b' },
    { label: 'VaR (99%, 1d)', value: `${riskMetrics.var99}%`, color: '#f97316' },
    { label: 'CVaR (95%, 1d)', value: `${riskMetrics.cvar95}%`, color: '#f43f5e' },
    { label: 'CVaR (99%, 1d)', value: `${riskMetrics.cvar99}%`, color: '#dc2626' },
    { label: 'Beta vs SPX', value: riskMetrics.beta, color: '#8b5cf6' },
    { label: 'Annualized Vol', value: `${riskMetrics.volatility}%`, color: '#3b82f6' },
    { label: 'Sharpe Ratio', value: riskMetrics.sharpe, color: '#10b981' },
    { label: 'Max Drawdown', value: `${riskMetrics.maxDrawdown}%`, color: '#f43f5e' },
    { label: 'Calmar Ratio', value: riskMetrics.calmar, color: '#10b981' },
    { label: 'Sortino Ratio', value: riskMetrics.sortino, color: '#06b6d4' },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge"><AlertTriangle size={10} /> 10 — Risk Engine</div>
        <h1>Risk Engine</h1>
        <p>Comprehensive risk analytics including VaR, CVaR, factor attribution, drawdown monitoring, and historical stress testing across multiple market regimes.</p>
      </div>

      {/* Key Risk Metrics */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {[
          { label: 'Portfolio VaR (95%)', value: '-2.34%', color: '#f59e0b' },
          { label: 'CVaR (99%)', value: '-5.44%', color: '#f43f5e' },
          { label: 'Max Drawdown', value: '-8.3%', color: '#f43f5e' },
          { label: 'Sharpe Ratio', value: '1.67', color: '#10b981' },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.4rem' }}>{m.label}</div>
            <div className="metric-value" style={{ color: m.color, fontSize: '1.6rem' }}>{m.value}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Drawdown Chart */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Drawdown Curve (90d)</span>
            <span className="badge badge-rose"><TrendingDown size={10} /> Max -8.3%</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={drawdownData}>
              <defs>
                <linearGradient id="ddRiskGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} interval={19} />
              <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} tickFormatter={v => `${v}%`} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={-8.3} stroke="#f43f5e" strokeDasharray="4 2" label={{ value: '-8.3% Limit', fill: '#f43f5e', fontSize: 9 }} />
              <Area type="monotone" dataKey="drawdown" name="Drawdown %" stroke="#f43f5e" strokeWidth={2} fill="url(#ddRiskGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Return Distribution / VaR Histogram */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Return Distribution & VaR</span>
            <span className="badge badge-amber">252d Historical</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={histData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="ret" tick={{ fontSize: 8, fill: '#475569' }} tickLine={false} axisLine={false} tickFormatter={v => `${v}%`} interval={2} />
              <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine x={riskMetrics.var95} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: 'VaR95', fill: '#f59e0b', fontSize: 8 }} />
              <ReferenceLine x={riskMetrics.var99} stroke="#f43f5e" strokeDasharray="4 2" label={{ value: 'VaR99', fill: '#f43f5e', fontSize: 8 }} />
              <Bar dataKey="freq" name="Frequency" radius={[2, 2, 0, 0]} fill="#3b82f6" fillOpacity={0.7} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Full Risk Table */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Risk Metrics Summary</span>
            <span className="badge badge-emerald"><ShieldCheck size={10} /> Within Limits</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            {riskRows.map(r => (
              <div key={r.label} style={{ padding: '0.6rem 0.75rem', background: 'var(--bg-secondary)', borderRadius: 8 }}>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{r.label}</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, fontFamily: 'JetBrains Mono', color: r.color }}>{r.value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Factor Risk Attribution */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Risk Attribution by Factor</span>
            <span className="badge badge-violet"><Activity size={10} /> Barra-Style</span>
          </div>
          <div style={{ display: 'grid', gap: '0.5rem', marginBottom: '1rem' }}>
            {factorRisk.map(f => (
              <div key={f.factor} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', minWidth: 100 }}>{f.factor}</span>
                <div className="progress-bar" style={{ flex: 1 }}>
                  <div className="progress-fill" style={{ width: `${f.contribution}%`, background: f.color }} />
                </div>
                <span style={{ fontSize: '0.72rem', fontFamily: 'JetBrains Mono', color: f.color, minWidth: 40, textAlign: 'right' }}>{f.contribution}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Stress Test Scenarios */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Stress Test Scenarios</span>
          <span className="badge badge-amber">6 Historical Scenarios</span>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Scenario</th>
              <th>Portfolio Return</th>
              <th>Benchmark Return</th>
              <th>Max Drawdown</th>
              <th>Verdict</th>
            </tr>
          </thead>
          <tbody>
            {stressScenarios.map(s => (
              <tr key={s.name}>
                <td style={{ color: 'var(--text-primary)', fontFamily: 'inherit' }}>{s.name}</td>
                <td style={{ color: s.portfolioReturn.startsWith('+') ? '#10b981' : '#f43f5e' }}>{s.portfolioReturn}</td>
                <td style={{ color: s.benchReturn.startsWith('+') ? '#10b981' : '#f43f5e' }}>{s.benchReturn}</td>
                <td style={{ color: '#f59e0b' }}>{s.maxDD}</td>
                <td>
                  <span className={`badge ${s.status === 'pass' ? 'badge-emerald' : s.status === 'warn' ? 'badge-amber' : 'badge-rose'}`}>
                    {s.status.toUpperCase()}
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
