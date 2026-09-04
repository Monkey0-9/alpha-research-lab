'use client';
import React from 'react';
import { AlphaHealthMetrics } from '@/lib/types';
import Badge from './Badge';

export default function AlphaHealthCard({ alpha }: { alpha: AlphaHealthMetrics }) {
  const isHealthy = alpha.status === 'HEALTHY';
  const isDegrading = alpha.status === 'DEGRADING';
  const icDecayPct = ((alpha.initial_ic - alpha.current_ic) / alpha.initial_ic) * 100;
  const statusColor = isHealthy ? '#00CC33' : isDegrading ? '#FF6600' : '#CC2222';
  const decayBarWidth = Math.max(0, Math.min(100, 100 - icDecayPct));

  return (
    <div style={{
      background: '#0a0a0a',
      border: `1px solid ${isHealthy ? '#2a2a2a' : statusColor}`,
      fontFamily: 'var(--font-mono)',
      padding: 0,
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0.3rem 0.5rem',
        background: isHealthy ? '#0d0d0d' : '#0d0600',
        borderBottom: `1px solid ${isHealthy ? '#2a2a2a' : statusColor}`,
      }}>
        <div>
          <span style={{ color: '#FF6600', fontSize: '0.58rem', fontWeight: 700 }}>{alpha.alpha_id}</span>
          <div style={{ fontSize: '0.68rem', fontWeight: 900, color: '#FFFFFF', marginTop: '1px' }}>
            {alpha.name.toUpperCase()}
          </div>
        </div>
        <span style={{
          background: statusColor, color: '#000',
          fontSize: '0.55rem', fontWeight: 900,
          padding: '0 0.35rem', height: '15px',
          display: 'inline-flex', alignItems: 'center',
        }}>
          {alpha.status}
        </span>
      </div>

      {/* Metrics grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', borderBottom: '1px solid #1a1a1a' }}>
        {[
          { label: 'CUR IC', value: alpha.current_ic.toFixed(3), color: alpha.current_ic > 0.04 ? '#00FF41' : '#FF6600' },
          { label: 'HALF-LIFE', value: `${alpha.half_life_days.toFixed(1)}D`, color: '#FFFFFF' },
          { label: 'PSI DRIFT', value: alpha.psi_drift_score.toFixed(3), color: alpha.psi_drift_score > 0.08 ? '#FF6600' : '#00FF41' },
          { label: 'DAYS LIVE', value: `${alpha.days_live}D`, color: '#AAAAAA' },
        ].map((m, i) => (
          <div key={i} style={{
            padding: '0.3rem 0.4rem',
            borderRight: i < 3 ? '1px solid #1a1a1a' : 'none',
          }}>
            <div style={{ fontSize: '0.55rem', color: '#444', fontWeight: 700, letterSpacing: '0.05em', marginBottom: '0.15rem' }}>{m.label}</div>
            <div style={{ fontSize: '0.82rem', fontWeight: 900, color: m.color }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* IC Decay bar */}
      <div style={{ padding: '0.3rem 0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.55rem', color: '#444', marginBottom: '0.2rem' }}>
          <span>IC DECAY TRAJECTORY</span>
          <span style={{ color: icDecayPct > 20 ? '#FF3333' : '#666' }}>-{icDecayPct.toFixed(1)}% DEGRADATION</span>
        </div>
        <div style={{ height: '5px', background: '#1a1a1a', width: '100%' }}>
          <div style={{
            height: '100%',
            width: `${decayBarWidth}%`,
            background: icDecayPct > 25 ? '#CC2222' : icDecayPct > 10 ? '#FF6600' : '#00CC33',
            transition: 'width 0.3s',
          }} />
        </div>
        <div style={{ fontSize: '0.55rem', color: '#333', marginTop: '0.15rem' }}>
          SHARPE: <span style={{ color: '#FF6600' }}>{alpha.sharpe_ratio.toFixed(2)}</span>
          &nbsp;·&nbsp;INITIAL IC: <span style={{ color: '#555' }}>{alpha.initial_ic.toFixed(3)}</span>
        </div>
      </div>
    </div>
  );
}
