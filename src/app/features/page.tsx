'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Cpu, TrendingUp, Activity, Layers, Sliders } from 'lucide-react';
import { generateICTimeSeries, generateFactorReturns } from '@/lib/data';

const featureCategories = ['Price', 'Fundamental', 'Macro', 'Microstructure'];

const factors = {
  Price: [
    { name: 'Momentum 1M', ic: 0.072, sharpe: 1.31, decay: 21, turnover: 18 },
    { name: 'Momentum 3M', ic: 0.085, sharpe: 1.54, decay: 30, turnover: 12 },
    { name: 'Momentum 12M', ic: 0.091, sharpe: 1.67, decay: 60, turnover: 8 },
    { name: 'Mean Reversion 5D', ic: -0.062, sharpe: 1.22, decay: 5, turnover: 45 },
    { name: 'Volatility 21D', ic: -0.048, sharpe: 0.94, decay: 21, turnover: 20 },
    { name: 'Seasonality', ic: 0.038, sharpe: 0.82, decay: 252, turnover: 4 },
  ],
  Fundamental: [
    { name: 'EV/EBITDA Zscore', ic: 0.062, sharpe: 1.12, decay: 90, turnover: 3 },
    { name: 'P/B Ratio', ic: 0.055, sharpe: 1.04, decay: 90, turnover: 3 },
    { name: 'Gross Margin Trend', ic: 0.047, sharpe: 0.93, decay: 120, turnover: 2 },
    { name: 'ROE Surprise', ic: 0.071, sharpe: 1.28, decay: 45, turnover: 8 },
    { name: 'Debt/Equity', ic: -0.041, sharpe: 0.78, decay: 90, turnover: 2 },
    { name: 'Free Cash Flow Yield', ic: 0.058, sharpe: 1.08, decay: 90, turnover: 3 },
  ],
  Macro: [
    { name: 'Rate Sensitivity', ic: 0.035, sharpe: 0.72, decay: 60, turnover: 5 },
    { name: 'Credit Spread Beta', ic: 0.028, sharpe: 0.61, decay: 30, turnover: 10 },
    { name: 'Inflation Beta', ic: 0.031, sharpe: 0.67, decay: 90, turnover: 4 },
    { name: 'Carry', ic: 0.044, sharpe: 0.89, decay: 252, turnover: 2 },
    { name: 'Dispersion', ic: 0.052, sharpe: 1.01, decay: 21, turnover: 15 },
  ],
  Microstructure: [
    { name: 'Order Flow Imbalance', ic: 0.105, sharpe: 1.78, decay: 5, turnover: 60 },
    { name: 'Bid-Ask Spread', ic: -0.078, sharpe: 1.41, decay: 10, turnover: 30 },
    { name: 'Trade Size Imbalance', ic: 0.089, sharpe: 1.56, decay: 3, turnover: 80 },
    { name: 'Amihud Illiquidity', ic: -0.065, sharpe: 1.18, decay: 21, turnover: 12 },
    { name: 'Volume Surprise', ic: 0.073, sharpe: 1.32, decay: 5, turnover: 50 },
  ],
};

const radarData = [
  { factor: 'Momentum', value: 87 },
  { factor: 'Value', value: 62 },
  { factor: 'Quality', value: 71 },
  { factor: 'Carry', value: 55 },
  { factor: 'Volatility', value: 48 },
  { factor: 'Liquidity', value: 78 },
  { factor: 'Seasonality', value: 43 },
  { factor: 'Mean Rev', value: 65 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color || '#3b82f6' }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function FeaturesPage() {
  const [activeTab, setActiveTab] = useState('Price');
  const [icData, setIcData] = useState<any[]>([]);
  const [momentum, setMomentum] = useState(21);
  const [lookback, setLookback] = useState(60);
  const [featuresList, setFeaturesList] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/features/ic')
      .then(r => r.json())
      .then(json => {
        if (json && json.results) {
          setIcData(json.results.map((r: any, idx: number) => ({
            date: `W-${idx + 1}`,
            ic: r.ic,
            value: r.ic,
            ic_ir: r.ic_ir,
          })));
        } else {
          setIcData(generateICTimeSeries(52));
        }
      })
      .catch(() => {
        setIcData(generateICTimeSeries(52));
      });

    fetch('/api/features/list')
      .then(r => r.json())
      .then(json => {
        if (json && json.features) {
          setFeaturesList(json.features);
        }
      })
      .catch(() => {});
  }, []);

  const currentFactors = factors[activeTab as keyof typeof factors];

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge"><Cpu size={10} /> 02 — Feature / Signal Factory</div>
        <h1>Feature / Signal Factory</h1>
        <p>Generate and evaluate signals across price, fundamental, macro, and microstructure categories.</p>
      </div>

      {/* Stats */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {[
          { label: 'Total Features', value: '847', color: '#3b82f6' },
          { label: 'Active Signals', value: '124', color: '#10b981' },
          { label: 'Avg IC (60d)', value: '0.063', color: '#8b5cf6' },
          { label: 'IC Hit Rate', value: '67.3%', color: '#f59e0b' },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.4rem' }}>{m.label}</div>
            <div className="metric-value" style={{ color: m.color, fontSize: '1.6rem' }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Parameter Controls + IC Chart */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">Signal Parameters</span>
            <Sliders size={14} color="var(--text-muted)" />
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Momentum Window</span>
              <span style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: '#3b82f6' }}>{momentum}D</span>
            </div>
            <input type="range" min={5} max={252} value={momentum} onChange={e => setMomentum(+e.target.value)} />
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
              <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>5D</span>
              <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>252D</span>
            </div>
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>IC Lookback</span>
              <span style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: '#10b981' }}>{lookback}D</span>
            </div>
            <input type="range" min={20} max={252} value={lookback} onChange={e => setLookback(+e.target.value)} />
          </div>

          <div style={{ marginTop: '1rem' }}>
            <div className="section-title">Factor Scores (Radar)</div>
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.06)" />
                <PolarAngleAxis dataKey="factor" tick={{ fontSize: 10, fill: '#475569' }} />
                <Radar name="Score" dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} strokeWidth={1.5} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Rolling IC / Rank IC</span>
            <span className="badge badge-blue">52 weeks</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={icData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} interval={12} />
              <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="ic" name="IC" stroke="#3b82f6" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="rankIC" name="Rank IC" stroke="#10b981" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <div style={{ flex: 1, background: 'var(--bg-secondary)', borderRadius: 8, padding: '0.75rem', textAlign: 'center' }}>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#3b82f6', fontFamily: 'JetBrains Mono' }}>0.063</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Mean IC</div>
            </div>
            <div style={{ flex: 1, background: 'var(--bg-secondary)', borderRadius: 8, padding: '0.75rem', textAlign: 'center' }}>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#10b981', fontFamily: 'JetBrains Mono' }}>3.74</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>IC t-stat</div>
            </div>
            <div style={{ flex: 1, background: 'var(--bg-secondary)', borderRadius: 8, padding: '0.75rem', textAlign: 'center' }}>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#8b5cf6', fontFamily: 'JetBrains Mono' }}>0.41</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>IC IR</div>
            </div>
          </div>
        </div>
      </div>

      {/* Factor Table with Tabs */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Signal Library</span>
          <div className="tab-bar" style={{ marginBottom: 0 }}>
            {featureCategories.map(t => (
              <button key={t} className={`tab-btn ${activeTab === t ? 'active' : ''}`} onClick={() => setActiveTab(t)}>{t}</button>
            ))}
          </div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Signal Name</th>
              <th>IC (60d)</th>
              <th>Sharpe</th>
              <th>Decay (days)</th>
              <th>Turnover %</th>
              <th>Strength</th>
            </tr>
          </thead>
          <tbody>
            {currentFactors.map((f) => (
              <tr key={f.name}>
                <td style={{ color: 'var(--text-primary)', fontFamily: 'inherit', fontWeight: 500 }}>{f.name}</td>
                <td style={{ color: f.ic > 0 ? '#10b981' : '#f43f5e' }}>{f.ic.toFixed(3)}</td>
                <td style={{ color: '#3b82f6' }}>{f.sharpe.toFixed(2)}</td>
                <td>{f.decay}</td>
                <td>{f.turnover}%</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div className="progress-bar" style={{ flex: 1 }}>
                      <div className="progress-fill" style={{
                        width: `${Math.abs(f.ic) * 1000}%`,
                        background: f.ic > 0 ? '#10b981' : '#f43f5e',
                      }} />
                    </div>
                    <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', minWidth: 30 }}>
                      {(Math.abs(f.ic) * 100).toFixed(1)}%
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
