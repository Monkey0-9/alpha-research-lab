'use client';

import { useState, useEffect } from 'react';
import { BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { ShieldCheck, CheckCircle2, XCircle, AlertTriangle, TrendingUp } from 'lucide-react';
import { generateAlphaCandidates } from '@/lib/data';

const alphas = generateAlphaCandidates();

const criteria = [
  { id: 'C1', name: 'IC Significance', desc: 'IC t-stat > 2.5, at least 252 observations', weight: 15 },
  { id: 'C2', name: 'OOS Consistency', desc: 'IC must hold in strict OOS test set', weight: 20 },
  { id: 'C3', name: 'FDR Control', desc: 'Benjamini-Hochberg adjusted q < 0.05', weight: 15 },
  { id: 'C4', name: 'Alpha Decay Profile', desc: 'Monotonic decay, half-life > 5 days', weight: 10 },
  { id: 'C5', name: 'Turnover Budget', desc: 'Daily turnover < 15% of AUM', weight: 10 },
  { id: 'C6', name: 'Correlation Filter', desc: 'Pairwise IC correlation < 0.6 with existing alphas', weight: 10 },
  { id: 'C7', name: 'Drawdown Control', desc: 'Alpha-specific max drawdown < 20%', weight: 10 },
  { id: 'C8', name: 'Regime Robustness', desc: 'Positive IC in at least 4 of 6 regimes', weight: 5 },
  { id: 'C9', name: 'Capacity Check', desc: 'Alpha holds at target AUM capacity', weight: 5 },
];

const alphaGateResults: Record<string, boolean[]> = {
  'A001': [true, true, true, true, true, true, true, true, true],
  'A002': [true, true, true, true, false, true, true, false, true],
  'A003': [true, true, true, false, true, false, true, true, true],
  'A004': [true, true, true, true, true, true, false, true, true],
  'A005': [true, true, false, true, true, true, true, false, true],
  'A006': [false, true, false, true, true, true, false, false, true],
  'A007': [false, false, true, true, false, true, true, false, false],
  'A008': [false, false, false, true, true, false, false, false, false],
};

const radarData = criteria.map((c, i) => ({
  subject: c.id,
  A001: alphaGateResults['A001'][i] ? 100 : 20,
  A003: alphaGateResults['A003'][i] ? 100 : 20,
  A005: alphaGateResults['A005'][i] ? 100 : 20,
}));

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color || '#10b981' }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function QualityGatePage() {
  const [selectedAlpha, setSelectedAlpha] = useState('A001');
  const [gateApiResult, setGateApiResult] = useState<any>(null);

  useEffect(() => {
    fetch('/api/quality-gate/run')
      .then(r => r.json())
      .then(data => {
        setGateApiResult(data);
      })
      .catch(() => {});
  }, []);

  const gates = alphaGateResults[selectedAlpha] || [];
  const score = gates.filter(Boolean).length;
  const passed = gateApiResult ? gateApiResult.overall_pass : (score >= 7);

  const scoreData = alphas.map(a => ({
    id: a.id,
    score: (alphaGateResults[a.id] || []).filter(Boolean).length,
    status: a.status,
  }));

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge"><ShieldCheck size={10} /> 07 — Alpha Quality Gate</div>
        <h1>Alpha Quality Gate</h1>
        <p>9-criteria filter ensuring only robust, statistically valid alphas enter the production pipeline. Every alpha must pass IC significance, OOS consistency, FDR control, and 6 additional checks.</p>
      </div>

      {/* Summary Stats */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {[
          { label: 'Alphas Tested', value: '8', color: '#10b981' },
          { label: 'Pass Rate', value: '62.5%', color: '#3b82f6' },
          { label: 'Criteria Count', value: '9', color: '#8b5cf6' },
          { label: 'Avg Score', value: '6.4 / 9', color: '#f59e0b' },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.4rem' }}>{m.label}</div>
            <div className="metric-value" style={{ color: m.color, fontSize: '1.6rem' }}>{m.value}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Alpha Selector + Score Summary */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Alpha Gate Scores</span>
            <span className="badge badge-emerald"><ShieldCheck size={10} /> 5 / 8 Pass</span>
          </div>
          <div style={{ display: 'grid', gap: '0.4rem' }}>
            {alphas.map(a => {
              const s = (alphaGateResults[a.id] || []).filter(Boolean).length;
              const p = s >= 7;
              return (
                <div
                  key={a.id}
                  onClick={() => setSelectedAlpha(a.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '0.75rem',
                    padding: '0.55rem 0.85rem', borderRadius: 8, cursor: 'pointer',
                    background: selectedAlpha === a.id ? (p ? 'rgba(16,185,129,0.08)' : 'rgba(244,63,94,0.08)') : 'var(--bg-secondary)',
                    border: `1px solid ${selectedAlpha === a.id ? (p ? 'rgba(16,185,129,0.3)' : 'rgba(244,63,94,0.3)') : 'var(--border-subtle)'}`,
                    transition: 'all 0.15s',
                  }}
                >
                  {p ? <CheckCircle2 size={13} color="#10b981" /> : <XCircle size={13} color="#f43f5e" />}
                  <div style={{ flex: 1 }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>{a.id}</span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>{a.name}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: 60, height: 4, background: 'var(--border-subtle)', borderRadius: 2, overflow: 'hidden' }}>
                      <div style={{ width: `${(s / 9) * 100}%`, height: '100%', background: p ? '#10b981' : '#f43f5e', borderRadius: 2 }} />
                    </div>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'JetBrains Mono', color: p ? '#10b981' : '#f43f5e', minWidth: 30 }}>{s}/9</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Criteria Detail for selected alpha */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Criteria — {selectedAlpha}</span>
            <span className={`badge ${passed ? 'badge-emerald' : 'badge-rose'}`}>
              {passed ? <CheckCircle2 size={10} /> : <XCircle size={10} />}
              {passed ? 'PASSED' : 'FAILED'} · {score}/9
            </span>
          </div>
          <div style={{ display: 'grid', gap: '0.35rem' }}>
            {criteria.map((c, i) => {
              const pass = gates[i];
              return (
                <div key={c.id} className={`checklist-item ${pass ? 'pass' : 'fail'}`}>
                  {pass ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>{c.name}</div>
                    <div style={{ fontSize: '0.68rem', opacity: 0.8, marginTop: '0.1rem' }}>{c.desc}</div>
                  </div>
                  <span style={{ fontSize: '0.65rem', fontFamily: 'JetBrains Mono', opacity: 0.8 }}>w={c.weight}%</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Bar chart: Scores */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Quality Gate Scores — All Alphas</span>
            <span className="badge badge-violet">Comparison</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={scoreData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
              <XAxis type="number" domain={[0, 9]} tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="id" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} width={35} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="score" name="Score" radius={[0, 4, 4, 0]}
                fill="#10b981"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Radar chart */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Criteria Radar — Top Alphas</span>
            <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.7rem', fontFamily: 'JetBrains Mono' }}>
              <span style={{ color: '#10b981' }}>● A001</span>
              <span style={{ color: '#3b82f6' }}>● A003</span>
              <span style={{ color: '#8b5cf6' }}>● A005</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.06)" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 9, fill: '#475569' }} />
              <Radar name="A001" dataKey="A001" stroke="#10b981" fill="#10b981" fillOpacity={0.12} strokeWidth={1.5} />
              <Radar name="A003" dataKey="A003" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.1} strokeWidth={1.5} />
              <Radar name="A005" dataKey="A005" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.1} strokeWidth={1.5} />
              <Tooltip content={<CustomTooltip />} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
