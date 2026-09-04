'use client';

import { useEffect, useState } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar, LineChart, Line } from 'recharts';
import { FlaskConical, Dna, Cpu, Search, CheckCircle2, XCircle, ChevronRight, Layers } from 'lucide-react';
import { generateAlphaCandidates } from '@/lib/data';

const hypotheses = [
  { id: 'H001', hypothesis: 'Short-term momentum reversal after earnings surprise', category: 'Event + Price', status: 'testing', priority: 'high' },
  { id: 'H002', hypothesis: 'Vol surface skew predicts equity returns in small-caps', category: 'Options + Price', status: 'validated', priority: 'high' },
  { id: 'H003', hypothesis: 'Order flow imbalance at open signals intraday direction', category: 'Microstructure', status: 'testing', priority: 'medium' },
  { id: 'H004', hypothesis: 'Credit spread beta timing for sector rotation', category: 'Macro + Fundamental', status: 'archive', priority: 'low' },
  { id: 'H005', hypothesis: 'NLP sentiment shift + price momentum combination', category: 'Alt + Price', status: 'new', priority: 'high' },
];

const geneticProgress = [
  { gen: 1, best: 0.31, avg: 0.22 },
  { gen: 5, best: 0.48, avg: 0.34 },
  { gen: 10, best: 0.61, avg: 0.42 },
  { gen: 20, best: 0.73, avg: 0.51 },
  { gen: 35, best: 0.82, avg: 0.58 },
  { gen: 50, best: 0.89, avg: 0.63 },
  { gen: 75, best: 0.94, avg: 0.68 },
  { gen: 100, best: 0.97, avg: 0.71 },
];

const expressions = [
  { expr: 'rank(momentum_21d) - rank(volatility_21d)', ic: 0.087, sharpe: 1.43 },
  { expr: 'zscore(ev_ebitda) * sign(earnings_surprise)', ic: 0.071, sharpe: 1.21 },
  { expr: 'log(order_flow_imb) * rank(volume_surprise)', ic: 0.105, sharpe: 1.78 },
  { expr: 'delta(bid_ask_spread, 5) / volatility_5d', ic: -0.062, sharpe: 1.22 },
  { expr: 'momentum_63d * (1 - volatility_63d/mean_vol)', ic: 0.091, sharpe: 1.54 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color || '#8b5cf6' }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function AlphaDiscoveryPage() {
  const [candidates, setCandidates] = useState<any[]>([]);
  const [scatterData, setScatterData] = useState<any[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<'factors' | 'ml' | 'symbolic'>('symbolic');

  useEffect(() => {
    setCandidates(generateAlphaCandidates());
    setScatterData(
      Array.from({ length: 40 }, () => ({
        ic: parseFloat((Math.random() * 0.15 - 0.02).toFixed(3)),
        sharpe: parseFloat((Math.random() * 2 + 0.3).toFixed(2)),
        decay: Math.floor(Math.random() * 60 + 3),
        size: Math.floor(Math.random() * 20 + 5),
      }))
    );
  }, []);

  const statusColor: Record<string, string> = {
    validated: '#10b981', testing: '#3b82f6', new: '#8b5cf6', archive: '#475569'
  };
  const statusBadge: Record<string, string> = {
    validated: 'badge-emerald', testing: 'badge-blue', new: 'badge-violet', archive: 'badge-muted'
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge"><FlaskConical size={10} /> 03 — Alpha Discovery Lab</div>
        <h1>Alpha Discovery Lab</h1>
        <p>Hypothesis engine with genetic programming, ML-based search, and symbolic expression generation.</p>
      </div>

      {/* Stats */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {[
          { label: 'Hypotheses Tested', value: '2,847', color: '#8b5cf6' },
          { label: 'Alpha Candidates', value: '48', color: '#3b82f6' },
          { label: 'Pass Rate', value: '12.4%', color: '#10b981' },
          { label: 'GP Generations', value: '100', color: '#f59e0b' },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.4rem' }}>{m.label}</div>
            <div className="metric-value" style={{ color: m.color, fontSize: '1.6rem' }}>{m.value}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Candidate Generator */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Candidate Generator</span>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              {(['factors', 'ml', 'symbolic'] as const).map(m => (
                <button key={m} className={`btn ${selectedMethod === m ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ padding: '0.25rem 0.6rem', fontSize: '0.7rem' }}
                  onClick={() => setSelectedMethod(m)}>
                  {m === 'factors' ? <><Layers size={10} /> Factors</> : m === 'ml' ? <><Cpu size={10} /> ML</> : <><Dna size={10} /> Symbolic</>}
                </button>
              ))}
            </div>
          </div>

          {selectedMethod === 'symbolic' && (
            <div>
              <div className="section-title">Genetic Programming — Expression Search</div>
              <ResponsiveContainer width="100%" height={140}>
                <LineChart data={geneticProgress}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="gen" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} label={{ value: 'Generation', position: 'insideBottom', offset: -2, fontSize: 9, fill: '#475569' }} />
                  <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line type="monotone" dataKey="best" name="Best IC" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="avg" name="Avg IC" stroke="#06b6d4" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
                </LineChart>
              </ResponsiveContainer>

              <div className="section-title" style={{ marginTop: '1rem' }}>Top Expressions Found</div>
              {expressions.map((e, i) => (
                <div key={i} style={{
                  padding: '0.6rem 0.75rem', marginBottom: '0.35rem',
                  background: 'var(--bg-secondary)', borderRadius: 8,
                  border: '1px solid var(--border-subtle)',
                }}>
                  <div style={{ fontFamily: 'JetBrains Mono', fontSize: '0.72rem', color: '#8b5cf6', marginBottom: '0.3rem' }}>{e.expr}</div>
                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>IC: <span style={{ color: e.ic > 0 ? '#10b981' : '#f43f5e', fontFamily: 'JetBrains Mono' }}>{e.ic}</span></span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Sharpe: <span style={{ color: '#3b82f6', fontFamily: 'JetBrains Mono' }}>{e.sharpe}</span></span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {selectedMethod === 'ml' && (
            <div>
              <div className="section-title">ML Feature Importance</div>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart layout="vertical" data={[
                  { feature: 'momentum_21d', importance: 0.18 },
                  { feature: 'order_flow_imb', importance: 0.15 },
                  { feature: 'bid_ask_spread', importance: 0.12 },
                  { feature: 'earnings_surprise', importance: 0.11 },
                  { feature: 'volume_surprise', importance: 0.09 },
                  { feature: 'ev_ebitda_zscore', importance: 0.08 },
                  { feature: 'vol_skew', importance: 0.07 },
                  { feature: 'insider_ratio', importance: 0.06 },
                ]}>
                  <XAxis type="number" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
                  <YAxis dataKey="feature" type="category" tick={{ fontSize: 9, fill: '#475569', fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} width={110} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="importance" name="Importance" fill="#8b5cf6" radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {selectedMethod === 'factors' && (
            <div>
              <div className="section-title">Traditional Factor Scores</div>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={[
                  { factor: 'Momentum', score: 87 },
                  { factor: 'Value', score: 62 },
                  { factor: 'Quality', score: 71 },
                  { factor: 'Carry', score: 55 },
                  { factor: 'Volatility', score: 48 },
                  { factor: 'Liquidity', score: 78 },
                  { factor: 'Dispersion', score: 65 },
                  { factor: 'Seasonality', score: 43 },
                ]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="factor" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="score" name="Score" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* IC vs Sharpe Scatter */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <div className="card-header">
              <span className="card-title">Alpha Candidates — IC vs Sharpe</span>
              <span className="badge badge-violet">{candidates.length} candidates</span>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="ic" name="IC" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} label={{ value: 'IC', position: 'insideBottom', offset: -2, fontSize: 9, fill: '#475569' }} />
                <YAxis dataKey="sharpe" name="Sharpe" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} label={{ value: 'Sharpe', angle: -90, position: 'insideLeft', fontSize: 9, fill: '#475569' }} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
                <Scatter data={scatterData} fill="#8b5cf6" fillOpacity={0.7} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          {/* Hypothesis Pipeline */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Hypothesis Pipeline</span>
              <button className="btn btn-primary" style={{ fontSize: '0.72rem', padding: '0.3rem 0.6rem' }}>+ New</button>
            </div>
            {hypotheses.map((h) => (
              <div key={h.id} style={{
                display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
                padding: '0.6rem 0.75rem', marginBottom: '0.35rem',
                background: 'var(--bg-secondary)', borderRadius: 8,
                border: `1px solid ${statusColor[h.status]}22`,
              }}>
                <span className={`badge ${statusBadge[h.status]}`} style={{ marginTop: '0.1rem' }}>{h.status}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>{h.hypothesis}</div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{h.id} · {h.category}</div>
                </div>
                <ChevronRight size={12} color="var(--text-muted)" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
