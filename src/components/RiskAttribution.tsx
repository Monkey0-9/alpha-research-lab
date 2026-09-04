'use client';

import React from 'react';
import { FactorAttributionItem } from '@/lib/types';
import ProgressBar from './ProgressBar';

export default function RiskAttribution({
  factors,
  totalRiskPct = 6.85,
  systematicPct = 5.42,
  idiosyncraticPct = 4.18
}: {
  factors: FactorAttributionItem[];
  totalRiskPct?: number;
  systematicPct?: number;
  idiosyncraticPct?: number;
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      {/* Top summary row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', background: '#0a0d14', padding: '0.65rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
        <div>
          <div style={{ fontSize: '0.62rem', fontFamily: 'var(--font-mono)', color: '#64748b' }}>TOTAL ACTIVE RISK</div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#f8fafc' }}>{totalRiskPct.toFixed(2)}%</div>
        </div>
        <div>
          <div style={{ fontSize: '0.62rem', fontFamily: 'var(--font-mono)', color: '#64748b' }}>SYSTEMATIC (FACTOR) RISK</div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>{systematicPct.toFixed(2)}%</div>
        </div>
        <div>
          <div style={{ fontSize: '0.62rem', fontFamily: 'var(--font-mono)', color: '#64748b' }}>IDIOSYNCRATIC (SPECIFIC)</div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#c084fc' }}>{idiosyncraticPct.toFixed(2)}%</div>
        </div>
      </div>

      {/* Factor breakdown list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
        {factors.map((f) => (
          <div key={f.factor} style={{ background: '#0d1117', padding: '0.5rem 0.75rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', fontFamily: 'var(--font-mono)', marginBottom: '0.25rem' }}>
              <span style={{ fontWeight: 600, color: '#f8fafc' }}>{f.factor}</span>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <span style={{ color: '#94a3b8' }}>Exposure: <strong style={{ color: '#38bdf8' }}>{f.exposure.toFixed(2)}</strong></span>
                <span style={{ color: '#94a3b8' }}>Contribution: <strong style={{ color: f.contribution_bps >= 0 ? '#34d399' : '#fb7185' }}>{f.contribution_bps > 0 ? '+' : ''}{f.contribution_bps.toFixed(1)} bps</strong></span>
                <span style={{ color: '#f8fafc', fontWeight: 700 }}>{f.pct_of_total_risk.toFixed(1)}% of Risk</span>
              </div>
            </div>
            <ProgressBar value={f.pct_of_total_risk} showPercent={false} variant={f.pct_of_total_risk > 30 ? 'rose' : f.pct_of_total_risk > 15 ? 'amber' : 'blue'} />
          </div>
        ))}
      </div>
    </div>
  );
}
