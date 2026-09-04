'use client';

import React from 'react';
import { useStationStore } from '@/lib/store';
import { Sliders, CheckCircle2 } from 'lucide-react';

export default function EnsembleBuilder() {
  const { ensembleWeights, setEnsembleWeight } = useStationStore();

  const totalWeight = Object.values(ensembleWeights).reduce((a, b) => a + b, 0);

  // Simulated expected Sharpe based on current weights
  const simulatedSharpe = (
    ensembleWeights.lightgbm * 1.94 +
    ensembleWeights.xgboost * 1.88 +
    ensembleWeights.ridge * 1.45 +
    ensembleWeights.mlp * 1.76 +
    // Diversification boost from non-correlation
    (1.0 - Math.abs(ensembleWeights.lightgbm - ensembleWeights.ridge)) * 0.25
  ).toFixed(2);

  const models: Array<{ id: 'lightgbm' | 'xgboost' | 'ridge' | 'mlp'; name: string; family: string; indSharpe: number }> = [
    { id: 'lightgbm', name: 'LightGBM Regressor', family: 'Tree-based Boosting', indSharpe: 1.94 },
    { id: 'xgboost', name: 'XGBoost Robust', family: 'Gradient Boosting', indSharpe: 1.88 },
    { id: 'ridge', name: 'ElasticNet / Ridge', family: 'Regularized Linear', indSharpe: 1.45 },
    { id: 'mlp', name: 'Temporal MLP DeepNet', family: 'Deep Learning', indSharpe: 1.76 },
  ];

  return (
    <div className="terminal-card" style={{ padding: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Sliders size={14} color="#38bdf8" />
          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
            ALPHA ENSEMBLE WEIGHT ALLOCATOR
          </span>
        </div>
        <div style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
          TOTAL WEIGHT: <span style={{ color: Math.abs(totalWeight - 1.0) < 0.01 ? '#34d399' : '#f43f5e', fontWeight: 700 }}>{(totalWeight * 100).toFixed(0)}%</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
        {models.map((m) => {
          const weight = ensembleWeights[m.id];
          return (
            <div key={m.id} style={{ background: '#0a0d14', padding: '0.65rem 0.85rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
                <div>
                  <span style={{ fontWeight: 600, color: '#f8fafc' }}>{m.name}</span>
                  <span style={{ color: '#64748b', marginLeft: '0.5rem' }}>({m.family})</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ color: '#94a3b8' }}>IS Sharpe: {m.indSharpe.toFixed(2)}</span>
                  <span style={{ color: '#38bdf8', fontWeight: 700, width: '45px', textAlign: 'right' }}>{(weight * 100).toFixed(0)}%</span>
                </div>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weight}
                onChange={(e) => setEnsembleWeight(m.id, parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: '#38bdf8', cursor: 'pointer' }}
              />
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(56, 189, 248, 0.06)', padding: '0.65rem 0.85rem', borderRadius: '3px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
          <CheckCircle2 size={13} color="#34d399" />
          <span>ESTIMATED DIVERSIFIED ENSEMBLE SHARPE:</span>
        </div>
        <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
          {simulatedSharpe}
        </div>
      </div>
    </div>
  );
}
