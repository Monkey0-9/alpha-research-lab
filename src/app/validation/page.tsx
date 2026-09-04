'use client';

import { useState } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from 'recharts';
import { GitBranch, CheckCircle2, AlertTriangle } from 'lucide-react';

const walkForwardFolds = Array.from({ length: 12 }, (_, i) => ({
  fold: `WF-${String(i + 1).padStart(2, '0')}`,
  trainStart: `${2019 + Math.floor(i / 4)}-Q${(i % 4) + 1}`,
  trainMonths: 24 + i * 2,
  oosReturn: parseFloat(((Math.random() - 0.35) * 8).toFixed(2)),
  sharpe: parseFloat((Math.random() * 1.5 + 0.4).toFixed(2)),
  ic: parseFloat((Math.random() * 0.1 + 0.02).toFixed(3)),
}));

const regimes = [
  { name: 'Bull Market', period: '2021-01 → 2021-12', sharpe: 2.14, ic: 0.095, return: '+18.4%', status: 'pass', color: '#10b981' },
  { name: 'Bear Market', period: '2022-01 → 2022-10', sharpe: 1.32, ic: 0.071, return: '+4.2%', status: 'pass', color: '#10b981' },
  { name: 'Crisis', period: '2020-02 → 2020-04', sharpe: 0.71, ic: 0.042, return: '+1.1%', status: 'warn', color: '#f59e0b' },
  { name: 'High Vol', period: '2022-09 → 2023-03', sharpe: 1.54, ic: 0.083, return: '+9.7%', status: 'pass', color: '#10b981' },
  { name: 'Low Vol', period: '2021-06 → 2021-12', sharpe: 1.87, ic: 0.104, return: '+13.2%', status: 'pass', color: '#10b981' },
  { name: 'Structural Break', period: '2020-03 → 2020-06', sharpe: 0.45, ic: 0.028, return: '-0.3%', status: 'fail', color: '#f43f5e' },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color || '#f97316' }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function ValidationPage() {
  const [activeView, setActiveView] = useState<'walkforward' | 'purged' | 'regime'>('walkforward');

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge"><GitBranch size={10} /> 06 — Time-Series Validation</div>
        <h1>Time-Series Validation</h1>
        <p>Rigorous OOS testing with walk-forward CV, purged cross-validation, embargo periods, and regime testing.</p>
      </div>

      {/* Key Rule Banner */}
      <div style={{
        padding: '0.9rem 1.2rem', marginBottom: '1.5rem',
        background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.2)',
        borderRadius: 10, display: 'flex', alignItems: 'center', gap: '0.75rem',
      }}>
        <AlertTriangle size={16} color="#f43f5e" />
        <div>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f43f5e' }}>NEVER use random train/test splits for time-series data</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            All splits respect temporal ordering. Embargo periods prevent leakage. Purging removes overlapping return periods.
          </div>
        </div>
      </div>

      {/* Train/Val/Test Splits Visualization */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <span className="card-title">Train → Validation → Test Split Structure</span>
          <div className="tab-bar" style={{ marginBottom: 0 }}>
            {(['walkforward', 'purged', 'regime'] as const).map(v => (
              <button key={v} className={`tab-btn ${activeView === v ? 'active' : ''}`} onClick={() => setActiveView(v)}>
                {v === 'walkforward' ? 'Walk-Forward' : v === 'purged' ? 'Purged CV' : 'Regime Test'}
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Visualization */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', gap: '0.25rem', height: 40, borderRadius: 8, overflow: 'hidden' }}>
            <div style={{ flex: 3, background: 'rgba(59,130,246,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: '#3b82f6' }}>
              TRAIN (60%)
            </div>
            <div style={{ width: 4, background: 'rgba(244,63,94,0.5)' }} />
            <div style={{ flex: 1, background: 'rgba(245,158,11,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: '#f59e0b' }}>
              VAL (20%)
            </div>
            <div style={{ width: 4, background: 'rgba(244,63,94,0.5)' }} />
            <div style={{ width: 20, background: 'rgba(244,63,94,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.6rem', color: '#f43f5e', writingMode: 'vertical-rl' }}>
              EMBARGO
            </div>
            <div style={{ flex: 1, background: 'rgba(16,185,129,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: '#10b981' }}>
              TEST OOS (20%)
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono' }}>
            <span>Jan 2018</span><span>Jan 2021</span><span>Jan 2022</span><span>Mar 2022</span><span>Sep 2026</span>
          </div>
        </div>

        {activeView === 'walkforward' && (
          <div>
            <div className="section-title">Walk-Forward OOS Returns by Fold</div>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={walkForwardFolds}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="fold" tick={{ fontSize: 8, fill: '#475569' }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} tickFormatter={v => `${v}%`} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" />
                <Bar dataKey="oosReturn" name="OOS Return %" radius={[3, 3, 0, 0]}
                  fill="#f97316"
                />
              </BarChart>
            </ResponsiveContainer>
            <table className="data-table" style={{ marginTop: '1rem' }}>
              <thead>
                <tr><th>Fold</th><th>Train Start</th><th>Train (mo.)</th><th>OOS Return</th><th>Sharpe</th><th>IC</th></tr>
              </thead>
              <tbody>
                {walkForwardFolds.slice(0, 6).map(f => (
                  <tr key={f.fold}>
                    <td>{f.fold}</td><td>{f.trainStart}</td><td>{f.trainMonths}</td>
                    <td style={{ color: f.oosReturn >= 0 ? '#10b981' : '#f43f5e' }}>{f.oosReturn}%</td>
                    <td style={{ color: '#3b82f6' }}>{f.sharpe}</td>
                    <td>{f.ic}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeView === 'purged' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
              <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8 }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>CV Strategy</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f97316' }}>Purged K-Fold</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>k=5 · Purge=21d · Embargo=5d</div>
              </div>
              <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8 }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>Purge Window</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#3b82f6' }}>21 Days</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Removes overlapping return labels</div>
              </div>
              <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8 }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>Embargo Period</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f43f5e' }}>5 Days</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Gap between train/test splits</div>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={walkForwardFolds.slice(0, 5).map((f, i) => ({ ...f, fold: `CV-${i + 1}` }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="fold" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="sharpe" name="Sharpe" fill="#f97316" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {activeView === 'regime' && (
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            {regimes.map(r => (
              <div key={r.name} className="regime-card">
                <div style={{ minWidth: 120 }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, color: r.color }}>{r.name}</div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono' }}>{r.period}</div>
                </div>
                <div style={{ flex: 1, display: 'flex', gap: '1.5rem', justifyContent: 'center' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#3b82f6', fontFamily: 'JetBrains Mono' }}>{r.sharpe}</div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Sharpe</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#8b5cf6', fontFamily: 'JetBrains Mono' }}>{r.ic}</div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>IC</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700, color: r.status === 'fail' ? '#f43f5e' : '#10b981', fontFamily: 'JetBrains Mono' }}>{r.return}</div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Return</div>
                  </div>
                </div>
                <span className={`badge ${r.status === 'pass' ? 'badge-emerald' : r.status === 'warn' ? 'badge-amber' : 'badge-rose'}`}>
                  {r.status.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
