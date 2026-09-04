'use client';

import React from 'react';
import { AlphaHealthMetrics } from '@/lib/types';
import Badge from './Badge';
import ProgressBar from './ProgressBar';

export default function AlphaHealthCard({ alpha }: { alpha: AlphaHealthMetrics }) {
  const isHealthy = alpha.status === 'HEALTHY';
  const icDecayPct = ((alpha.initial_ic - alpha.current_ic) / alpha.initial_ic) * 100;

  return (
    <div
      className="terminal-card"
      style={{
        padding: '0.85rem 1rem',
        borderColor: isHealthy ? 'var(--border-terminal)' : 'rgba(245, 158, 11, 0.4)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.45rem' }}>
        <div>
          <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: '#38bdf8', fontWeight: 600 }}>
            {alpha.alpha_id}
          </span>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
            {alpha.name}
          </div>
        </div>
        <Badge label={alpha.status} type={isHealthy ? 'pass' : 'warn'} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', marginBottom: '0.65rem', background: '#0a0d14', padding: '0.5rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
        <div>
          <div style={{ fontSize: '0.6rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>CURRENT IC</div>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#34d399' }}>{alpha.current_ic.toFixed(3)}</div>
        </div>
        <div>
          <div style={{ fontSize: '0.6rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>HALF-LIFE</div>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#f8fafc' }}>{alpha.half_life_days.toFixed(1)}d</div>
        </div>
        <div>
          <div style={{ fontSize: '0.6rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>PSI DRIFT</div>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: alpha.psi_drift_score > 0.08 ? '#fbbf24' : '#34d399' }}>{alpha.psi_drift_score.toFixed(3)}</div>
        </div>
        <div>
          <div style={{ fontSize: '0.6rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>DAYS LIVE</div>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>{alpha.days_live}d</div>
        </div>
      </div>

      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: '#94a3b8', marginBottom: '0.2rem' }}>
          <span>IC Decay Trajectory</span>
          <span style={{ color: icDecayPct > 20 ? '#fb7185' : '#34d399' }}>-{icDecayPct.toFixed(1)}% degradation</span>
        </div>
        <ProgressBar value={Math.max(0, 100 - icDecayPct)} showPercent={false} variant={icDecayPct > 25 ? 'rose' : icDecayPct > 10 ? 'amber' : 'emerald'} />
      </div>
    </div>
  );
}
