'use client';

import { useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Brain, TrendingUp, Layers, Cpu } from 'lucide-react';
import { generateModelComparison } from '@/lib/data';

const models = generateModelComparison();

const trainingCurves: Record<string, any[]> = {
  'LightGBM': Array.from({ length: 50 }, (_, i) => ({
    epoch: i + 1,
    train: parseFloat((0.42 - 0.32 * (1 - Math.exp(-i * 0.1)) + Math.random() * 0.01).toFixed(4)),
    val: parseFloat((0.48 - 0.28 * (1 - Math.exp(-i * 0.09)) + Math.random() * 0.015).toFixed(4)),
  })),
  'LSTM': Array.from({ length: 100 }, (_, i) => ({
    epoch: i + 1,
    train: parseFloat((0.55 - 0.38 * (1 - Math.exp(-i * 0.05)) + Math.random() * 0.012).toFixed(4)),
    val: parseFloat((0.62 - 0.31 * (1 - Math.exp(-i * 0.04)) + Math.random() * 0.02).toFixed(4)),
  })),
  'Transformer': Array.from({ length: 200 }, (_, i) => ({
    epoch: i + 1,
    train: parseFloat((0.61 - 0.44 * (1 - Math.exp(-i * 0.03)) + Math.random() * 0.01).toFixed(4)),
    val: parseFloat((0.69 - 0.36 * (1 - Math.exp(-i * 0.025)) + Math.random() * 0.018).toFixed(4)),
  })),
};

const ensembleWeights = [
  { model: 'LightGBM', weight: 0.35 },
  { model: 'XGBoost', weight: 0.25 },
  { model: 'Transformer', weight: 0.20 },
  { model: 'LSTM', weight: 0.12 },
  { model: 'Ridge', weight: 0.08 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color || '#f59e0b' }}>
            {p.name}: {typeof p.value === 'number' ? p.value.toFixed(4) : p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function ModelLabPage() {
  const [selectedModel, setSelectedModel] = useState('LightGBM');
  const [weights, setWeights] = useState(ensembleWeights.map(e => e.weight));

  const curveData = (trainingCurves[selectedModel] || trainingCurves['LightGBM']).slice(0, 50);

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge"><Brain size={10} /> 05 — Model Research Lab</div>
        <h1>Model Research Lab</h1>
        <p>Train, compare, and ensemble multiple model architectures from linear baselines to transformers.</p>
      </div>

      {/* Stats */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {[
          { label: 'Models Trained', value: '8', color: '#f59e0b' },
          { label: 'Best Sharpe', value: '1.67', color: '#10b981' },
          { label: 'Best OOS Acc', value: '78.4%', color: '#3b82f6' },
          { label: 'Ensemble Lift', value: '+22%', color: '#8b5cf6' },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.4rem' }}>{m.label}</div>
            <div className="metric-value" style={{ color: m.color, fontSize: '1.6rem' }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Model Comparison Table */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <span className="card-title">Model Comparison — All Architectures</span>
          <span className="badge badge-amber"><Layers size={10} /> 8 Models</span>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Sharpe</th>
              <th>IC (60d)</th>
              <th>OOS Score</th>
              <th>Train Time</th>
              <th>Params</th>
              <th>Rank</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m, i) => (
              <tr key={m.model}
                onClick={() => setSelectedModel(m.model)}
                style={{ cursor: 'pointer', background: selectedModel === m.model ? 'rgba(245,158,11,0.05)' : undefined }}
              >
                <td style={{ color: 'var(--text-primary)', fontFamily: 'inherit', fontWeight: 500 }}>
                  {m.model === 'Ensemble' && <span style={{ color: '#f59e0b', marginRight: '0.4rem' }}>★</span>}
                  {m.model}
                </td>
                <td style={{ color: '#10b981' }}>{m.sharpe}</td>
                <td style={{ color: '#3b82f6' }}>{m.ic}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div className="progress-bar" style={{ flex: 1 }}>
                      <div className="progress-fill" style={{ width: `${m.oos * 100}%`, background: '#8b5cf6' }} />
                    </div>
                    <span>{(m.oos * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td>{m.trainTime}</td>
                <td style={{ fontFamily: 'JetBrains Mono', fontSize: '0.7rem' }}>{m.params}</td>
                <td>
                  <span className={`badge ${i === 0 ? 'badge-amber' : i === 1 ? 'badge-blue' : i === 2 ? 'badge-violet' : 'badge-muted'}`}>
                    #{i + 1}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Training Curves */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Training Curves — {selectedModel}</span>
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              {Object.keys(trainingCurves).map(m => (
                <button key={m} className={`btn ${selectedModel === m ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ padding: '0.25rem 0.6rem', fontSize: '0.7rem' }}
                  onClick={() => setSelectedModel(m)}>
                  {m}
                </button>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={curveData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="epoch" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} label={{ value: 'Epoch', position: 'insideBottom', offset: -2, fontSize: 9, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="train" name="Train Loss" stroke="#3b82f6" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="val" name="Val Loss" stroke="#f43f5e" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Ensemble Builder */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Ensemble Weight Builder</span>
            <span className="badge badge-amber">Meta Model</span>
          </div>
          {ensembleWeights.map((e, i) => (
            <div key={e.model} style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{e.model}</span>
                <span style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: '#f59e0b' }}>{(weights[i] * 100).toFixed(0)}%</span>
              </div>
              <input type="range" min={0} max={100} value={weights[i] * 100}
                onChange={ev => {
                  const newW = [...weights];
                  newW[i] = +ev.target.value / 100;
                  setWeights(newW);
                }}
              />
            </div>
          ))}
          <div style={{ marginTop: '0.5rem', padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 8 }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Ensemble Performance (Projected)</div>
            <div style={{ display: 'flex', gap: '1.5rem' }}>
              <div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f59e0b', fontFamily: 'JetBrains Mono' }}>1.67</div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Sharpe</div>
              </div>
              <div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#10b981', fontFamily: 'JetBrains Mono' }}>0.108</div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>IC</div>
              </div>
              <div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#3b82f6', fontFamily: 'JetBrains Mono' }}>78%</div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>OOS</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
