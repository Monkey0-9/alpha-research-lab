'use client';
import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  change?: string;
  deltaBps?: number;
  positive?: boolean;
  benchmark?: string | number;
  benchmarkLabel?: string;
  subtext?: string;
  status?: 'pass' | 'warn' | 'fail' | 'live' | 'neutral';
  tooltip?: string;
  highlight?: boolean;  // Yellow highlight like Bloomberg
}

export default function MetricCard({
  label,
  value,
  change,
  deltaBps,
  positive,
  benchmark,
  benchmarkLabel = 'BMK',
  subtext,
  status = 'neutral',
  highlight = false,
}: MetricCardProps) {
  const isPositive = positive ?? (deltaBps !== undefined ? deltaBps >= 0 : undefined);
  const changeColor = isPositive === undefined ? '#AAAAAA' : isPositive ? '#00FF41' : '#FF3333';

  // Status dot color
  const dotColor =
    status === 'pass' || status === 'live' ? '#00FF41' :
    status === 'warn' ? '#FF6600' :
    status === 'fail' ? '#FF3333' : '#444444';

  return (
    <div
      className="bb-metric"
      style={highlight ? { border: '1px solid #FFFF00', background: '#0d0d00' } : {}}
    >
      {/* Label row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
        <span className="bb-metric-label">{label}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          {status !== 'neutral' && (
            <span style={{
              width: 7, height: 7, borderRadius: 0,
              background: dotColor,
              display: 'inline-block',
              boxShadow: `0 0 5px ${dotColor}`,
              flexShrink: 0,
            }} />
          )}
        </div>
      </div>

      {/* Main Value */}
      <div className="bb-metric-value">
        {value}
      </div>

      {/* Change */}
      {change && (
        <div className={`bb-metric-change ${isPositive ? 'pos' : isPositive === false ? 'neg' : 'neutral'}`}>
          {isPositive ? '▲' : isPositive === false ? '▼' : '—'} {change}
          {deltaBps !== undefined && (
            <span style={{ color: '#666', fontSize: '0.62rem', marginLeft: '0.3rem', fontWeight: 400 }}>
              ({deltaBps > 0 ? '+' : ''}{deltaBps.toFixed(0)}bp)
            </span>
          )}
        </div>
      )}

      {/* Sub-row */}
      {(subtext || benchmark !== undefined) && (
        <div className="bb-metric-sub">
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            {subtext && <span>{subtext}</span>}
            {benchmark !== undefined && (
              <span style={{ color: '#666' }}>
                {benchmarkLabel}: <span style={{ color: '#AAAAAA' }}>{benchmark}</span>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
