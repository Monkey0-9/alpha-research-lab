'use client';
import React from 'react';
import { FactorAttributionItem } from '@/lib/types';

export default function RiskAttribution({
  factors,
  totalRiskPct = 6.85,
  systematicPct = 5.42,
  idiosyncraticPct = 4.18,
}: {
  factors: FactorAttributionItem[];
  totalRiskPct?: number;
  systematicPct?: number;
  idiosyncraticPct?: number;
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', fontFamily: 'var(--font-mono)' }}>
      {/* Summary metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '3px' }}>
        {[
          { label: 'TOTAL ACTIVE RISK', value: `${totalRiskPct.toFixed(2)}%`, color: '#FFFFFF' },
          { label: 'SYSTEMATIC (FACTOR)', value: `${systematicPct.toFixed(2)}%`, color: '#FF6600' },
          { label: 'IDIOSYNCRATIC (SPECIFIC)', value: `${idiosyncraticPct.toFixed(2)}%`, color: '#AAAAAA' },
        ].map((m, i) => (
          <div key={i} style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', padding: '0.4rem 0.6rem' }}>
            <div style={{ fontSize: '0.58rem', color: '#555', fontWeight: 700, marginBottom: '0.15rem', letterSpacing: '0.05em' }}>{m.label}</div>
            <div style={{ fontSize: '1.0rem', fontWeight: 900, color: m.color }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Factor breakdown */}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.68rem' }}>
        <thead>
          <tr>
            {['FACTOR', 'EXPOSURE', 'FACTOR RET%', 'CONTRIB (BPS)', '% OF RISK', 'RISK BAR'].map((h) => (
              <th key={h} style={{
                background: '#1a0d00', color: '#FF6600', fontSize: '0.58rem',
                fontWeight: 700, padding: '0.25rem 0.5rem', textAlign: 'left' as const,
                borderBottom: '1px solid #FF6600', letterSpacing: '0.04em',
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {factors.map((f, idx) => (
            <tr key={f.factor} style={{ borderBottom: '1px solid #1a1a1a' }}>
              <td style={{ padding: '0.3rem 0.5rem', color: '#FFFFFF', fontWeight: 700 }}>{f.factor.toUpperCase()}</td>
              <td style={{ padding: '0.3rem 0.5rem', color: '#FF6600', textAlign: 'right' as const }}>{f.exposure.toFixed(2)}</td>
              <td style={{ padding: '0.3rem 0.5rem', color: f.factor_return_pct >= 0 ? '#00FF41' : '#FF3333', textAlign: 'right' as const, fontWeight: 700 }}>
                {f.factor_return_pct > 0 ? '+' : ''}{f.factor_return_pct.toFixed(1)}%
              </td>
              <td style={{ padding: '0.3rem 0.5rem', color: f.contribution_bps >= 0 ? '#00FF41' : '#FF3333', textAlign: 'right' as const, fontWeight: 700 }}>
                {f.contribution_bps > 0 ? '+' : ''}{f.contribution_bps.toFixed(1)}
              </td>
              <td style={{ padding: '0.3rem 0.5rem', color: '#AAAAAA', textAlign: 'right' as const }}>{f.pct_of_total_risk.toFixed(1)}%</td>
              <td style={{ padding: '0.3rem 0.5rem', width: '120px' }}>
                <div style={{ height: '6px', background: '#1a1a1a', width: '100%' }}>
                  <div style={{
                    height: '100%',
                    width: `${f.pct_of_total_risk}%`,
                    background: f.pct_of_total_risk > 30 ? '#CC2222' : f.pct_of_total_risk > 15 ? '#FF6600' : '#004400',
                  }} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
