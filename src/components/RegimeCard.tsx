'use client';
import React from 'react';
import { MARKET_REGIMES } from '@/lib/constants';

export default function RegimeCard({
  activeRegime = 'bull_low_vol',
  transitionProb = 0.58
}: {
  activeRegime?: string;
  transitionProb?: number;
}) {
  const current = MARKET_REGIMES.find((r) => r.id === activeRegime) || MARKET_REGIMES[0];

  return (
    <div style={{
      background: '#0a0500',
      border: '1px solid #FF6600',
      fontFamily: 'var(--font-mono)',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0.3rem 0.75rem',
        background: '#1a0d00',
        borderBottom: '1px solid #FF6600',
      }}>
        <span style={{ color: '#FF6600', fontSize: '0.65rem', fontWeight: 900, letterSpacing: '0.07em' }}>
          MACRO REGIME CLASSIFIER (HMM) — ACTIVE STATE
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ width: 7, height: 7, background: '#00FF41', boxShadow: '0 0 5px #00FF41', display: 'inline-block' }} />
          <span style={{ color: '#00FF41', fontSize: '0.6rem', fontWeight: 900 }}>CLASSIFIER ONLINE</span>
        </div>
      </div>

      <div style={{ padding: '0.5rem 0.75rem', display: 'grid', gridTemplateColumns: '1fr auto', gap: '1rem', alignItems: 'center' }}>
        {/* Active regime */}
        <div>
          <div style={{ fontSize: '1.1rem', fontWeight: 900, color: '#FFFF00', letterSpacing: '0.02em', lineHeight: 1.1 }}>
            {current.name.toUpperCase()}
          </div>
          <div style={{ fontSize: '0.62rem', color: '#666', marginTop: '0.2rem' }}>
            STATE PROBABILITY: <span style={{ color: '#FF6600', fontWeight: 700 }}>{(transitionProb * 100).toFixed(1)}%</span>
            &nbsp;·&nbsp;VOL REGIME: <span style={{ color: '#AAAAAA' }}>{current.vol}</span>
          </div>
          <div style={{ fontSize: '0.62rem', color: '#555', marginTop: '0.1rem' }}>
            RECOMMENDED TILT: <span style={{ color: '#00FF41', fontWeight: 700 }}>BETA {current.betaTilt}x · MOMENTUM + VOL</span>
          </div>
        </div>

        {/* Regime probabilities table */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '3px' }}>
          {MARKET_REGIMES.map((r) => {
            const isSelected = r.id === activeRegime;
            return (
              <div
                key={r.id}
                style={{
                  background: isSelected ? '#1a1100' : '#0a0a0a',
                  border: `1px solid ${isSelected ? '#FFFF00' : '#2a2a2a'}`,
                  padding: '0.3rem 0.5rem',
                  textAlign: 'center' as const,
                  minWidth: '70px',
                }}
              >
                <div style={{ fontSize: '0.55rem', color: isSelected ? '#FF6600' : '#444', fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase' as const, marginBottom: '0.15rem' }}>
                  {r.id.replace(/_/g, ' ')}
                </div>
                <div style={{ fontSize: '0.95rem', fontWeight: 900, color: isSelected ? '#FFFF00' : '#555' }}>
                  {(r.prob * 100).toFixed(0)}%
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
