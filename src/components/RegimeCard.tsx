'use client';

import React from 'react';
import { MARKET_REGIMES } from '@/lib/constants';
import { Compass, ShieldAlert, TrendingUp, BarChart2 } from 'lucide-react';

export default function RegimeCard({
  activeRegime = 'bull_low_vol',
  transitionProb = 0.58
}: {
  activeRegime?: string;
  transitionProb?: number;
}) {
  const current = MARKET_REGIMES.find((r) => r.id === activeRegime) || MARKET_REGIMES[0];

  return (
    <div className="terminal-card" style={{ padding: '0.85rem 1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Compass size={14} color="#38bdf8" />
          <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            MACRO REGIME CLASSIFIER (HMM)
          </span>
        </div>
        <span className="badge-tag badge-pass">ACTIVE REGIME</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
            {current.name}
          </div>
          <div style={{ fontSize: '0.68rem', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
            Regime State Probability: <span style={{ color: '#38bdf8', fontWeight: 600 }}>{(transitionProb * 100).toFixed(1)}%</span> · Vol: {current.vol}
          </div>
        </div>
        <div style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
          <div style={{ fontSize: '0.65rem', color: '#64748b' }}>RECOMMENDED FACTOR TILT</div>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#34d399' }}>
            BETA {current.betaTilt}x · MOM + VOL
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-terminal)' }}>
        {MARKET_REGIMES.map((r) => {
          const isSelected = r.id === activeRegime;
          return (
            <div
              key={r.id}
              style={{
                background: isSelected ? 'rgba(56, 189, 248, 0.08)' : '#0a0d14',
                border: `1px solid ${isSelected ? 'rgba(56, 189, 248, 0.4)' : 'var(--border-terminal)'}`,
                padding: '0.45rem',
                borderRadius: '3px'
              }}
            >
              <div style={{ fontSize: '0.62rem', fontFamily: 'var(--font-mono)', color: isSelected ? '#38bdf8' : '#64748b', fontWeight: 600 }}>
                {r.id.toUpperCase().replace(/_/g, ' ')}
              </div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: isSelected ? '#f8fafc' : '#94a3b8' }}>
                {(r.prob * 100).toFixed(0)}%
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
