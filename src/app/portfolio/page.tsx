'use client';

import { useEffect, useState } from 'react';
import {
  AreaChart, Area, BarChart, Bar, ScatterChart, Scatter,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine
} from 'recharts';
import { PieChart, TrendingUp, TrendingDown, Sliders, Target } from 'lucide-react';
import { generatePortfolioWeights, generatePnL, generateDrawdown, generateTimeSeries } from '@/lib/data';

const positions = generatePortfolioWeights(10);

const optimizationMethods = ['Mean-Variance', 'Risk Parity', 'CVaR Min', 'Max Sharpe'];

const factorExposures = [
  { factor: 'Market Beta', current: 0.42, target: 0.50, limit: 0.8 },
  { factor: 'Size', current: -0.18, target: 0.0, limit: 0.5 },
  { factor: 'Value', current: 0.31, target: 0.25, limit: 0.6 },
  { factor: 'Momentum', current: 0.55, target: 0.40, limit: 0.7 },
  { factor: 'Quality', current: 0.22, target: 0.30, limit: 0.5 },
  { factor: 'Low Vol', current: 0.14, target: 0.20, limit: 0.4 },
];

const constraintStatus = [
  { constraint: 'Max Position Size', limit: '12%', current: '9.8%', status: 'pass' },
  { constraint: 'Min Position Size', limit: '0.5%', current: '2.1%', status: 'pass' },
  { constraint: 'Gross Leverage', limit: '2.0×', current: '1.0×', status: 'pass' },
  { constraint: 'Net Exposure', limit: '±30%', current: '+4%', status: 'pass' },
  { constraint: 'Sector Limit', limit: '25%', current: '22.3%', status: 'pass' },
  { constraint: 'Turnover Daily', limit: '15%', current: '6.7%', status: 'pass' },
  { constraint: 'VaR (95%)', limit: '-3%', current: '-2.34%', status: 'pass' },
  { constraint: 'CVaR (99%)', limit: '-6%', current: '-5.44%', status: 'pass' },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color || '#3b82f6' }}>
            {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function PortfolioPage() {
  const [method, setMethod] = useState('Mean-Variance');
  const [pnlData, setPnlData] = useState<any[]>([]);
  const [efficientFrontier, setEfficientFrontier] = useState<any[]>([]);

  useEffect(() => {
    const raw = generatePnL(120);
    setPnlData(generateDrawdown(raw).slice(-60));

    // Generate efficient frontier scatter points
    setEfficientFrontier(
      Array.from({ length: 40 }, (_, i) => ({
        risk: parseFloat((8 + i * 0.8 + (Math.random() - 0.5) * 1.2).toFixed(2)),
        ret: parseFloat((4 + i * 0.6 + (Math.random() - 0.5) * 1.5).toFixed(2)),
      }))
    );
  }, []);

  const totalWeight = positions.reduce((s, p) => s + p.weight, 0);

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge"><PieChart size={10} /> 08 — Portfolio Engine</div>
        <h1>Portfolio Engine</h1>
        <p>Multi-alpha portfolio construction with mean-variance, risk parity, and CVaR optimization. Full constraint management and real-time factor exposure monitoring.</p>
      </div>

      {/* Key Metrics */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {[
          { label: 'Portfolio Sharpe', value: '1.67', color: '#10b981' },
          { label: 'Active Positions', value: '10', color: '#3b82f6' },
          { label: 'Net Exposure', value: '+4.2%', color: '#f59e0b' },
          { label: 'Daily Turnover', value: '6.7%', color: '#8b5cf6' },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.4rem' }}>{m.label}</div>
            <div className="metric-value" style={{ color: m.color, fontSize: '1.6rem' }}>{m.value}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Positions table */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Current Positions</span>
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              {optimizationMethods.map(m => (
                <button
                  key={m}
                  className={`btn ${method === m ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ padding: '0.2rem 0.5rem', fontSize: '0.65rem' }}
                  onClick={() => setMethod(m)}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Weight</th>
                <th>Signal</th>
                <th>P&L</th>
                <th>Bar</th>
              </tr>
            </thead>
            <tbody>
              {positions.map(p => (
                <tr key={p.ticker}>
                  <td style={{ color: 'var(--text-primary)', fontFamily: 'inherit', fontWeight: 600 }}>{p.ticker}</td>
                  <td>{p.weight.toFixed(1)}%</td>
                  <td style={{ color: p.signal > 0 ? '#10b981' : '#f43f5e' }}>
                    {p.signal > 0 ? <TrendingUp size={10} style={{ display: 'inline', marginRight: 3 }} /> : <TrendingDown size={10} style={{ display: 'inline', marginRight: 3 }} />}
                    {p.signal.toFixed(3)}
                  </td>
                  <td style={{ color: p.pnl >= 0 ? '#10b981' : '#f43f5e' }}>${p.pnl.toLocaleString()}</td>
                  <td style={{ minWidth: 80 }}>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${p.weight / 15 * 100}%`, background: '#3b82f6' }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Right panel: PnL + Factor */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <div className="card-header">
              <span className="card-title">Portfolio P&L</span>
              <span className="badge badge-emerald">Live</span>
            </div>
            <ResponsiveContainer width="100%" height={140}>
              <AreaChart data={pnlData}>
                <defs>
                  <linearGradient id="portGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} interval={14} />
                <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="cumulative" name="P&L" stroke="#3b82f6" strokeWidth={2} fill="url(#portGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Factor Exposures</span>
              <span className="badge badge-violet"><Sliders size={10} /> Live</span>
            </div>
            <div style={{ display: 'grid', gap: '0.4rem' }}>
              {factorExposures.map(f => {
                const pct = Math.abs(f.current) / f.limit;
                const overTarget = Math.abs(f.current - f.target) > 0.1;
                return (
                  <div key={f.factor} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', minWidth: 90 }}>{f.factor}</span>
                    <div style={{ flex: 1, height: 6, background: 'var(--bg-secondary)', borderRadius: 3, overflow: 'hidden', position: 'relative' }}>
                      <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: 'rgba(255,255,255,0.2)' }} />
                      <div style={{
                        position: 'absolute',
                        left: f.current >= 0 ? '50%' : `${50 - pct * 50}%`,
                        width: `${pct * 50}%`,
                        height: '100%',
                        background: overTarget ? '#f59e0b' : '#3b82f6',
                        borderRadius: 3,
                      }} />
                    </div>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'JetBrains Mono', color: overTarget ? '#f59e0b' : 'var(--text-secondary)', minWidth: 32 }}>
                      {f.current.toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Efficient Frontier */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Efficient Frontier</span>
            <span className="badge badge-blue"><Target size={10} /> Optimization</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="risk" name="Risk (Vol%)" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} label={{ value: 'Volatility %', position: 'insideBottom', offset: -2, fontSize: 9, fill: '#475569' }} />
              <YAxis dataKey="ret" name="Return%" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} label={{ value: 'Return %', angle: -90, position: 'insideLeft', offset: 10, fontSize: 9, fill: '#475569' }} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
              <Scatter name="Portfolios" data={efficientFrontier} fill="#3b82f6" fillOpacity={0.6} />
              {/* Current Portfolio */}
              <Scatter name="Current" data={[{ risk: 14.7, ret: 18.3 }]} fill="#10b981" r={6} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Constraint Status */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Constraint Checks</span>
            <span className="badge badge-emerald">8 / 8 OK</span>
          </div>
          <table className="data-table">
            <thead>
              <tr><th>Constraint</th><th>Limit</th><th>Current</th><th>Status</th></tr>
            </thead>
            <tbody>
              {constraintStatus.map(c => (
                <tr key={c.constraint}>
                  <td style={{ color: 'var(--text-primary)', fontFamily: 'inherit' }}>{c.constraint}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{c.limit}</td>
                  <td>{c.current}</td>
                  <td><span className="badge badge-emerald">✓ OK</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
