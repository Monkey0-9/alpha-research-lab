'use client';

import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

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
  status = 'neutral'
}: MetricCardProps) {
  const isPositive = positive ?? (deltaBps !== undefined ? deltaBps >= 0 : undefined);

  return (
    <div className="terminal-card" style={{ padding: '0.85rem 1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
        <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>
          {label}
        </span>
        {status !== 'neutral' && (
          <span className={`status-indicator-dot ${status === 'pass' || status === 'live' ? 'live' : status === 'warn' ? 'warn' : 'fail'}`} />
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: '0.5rem', marginBottom: '0.35rem' }}>
        <div style={{ fontSize: '1.45rem', fontWeight: 700, fontFamily: 'var(--font-mono)', letterSpacing: '-0.02em', color: '#f8fafc' }} className="tabular-nums">
          {value}
        </div>

        {change && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.15rem',
            fontSize: '0.72rem',
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
            color: isPositive ? '#34d399' : '#fb7185'
          }}>
            {isPositive ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
            <span>{change}</span>
            {deltaBps !== undefined && (
              <span style={{ opacity: 0.8, fontSize: '0.65rem' }}>({deltaBps > 0 ? '+' : ''}{deltaBps.toFixed(0)} bps)</span>
            )}
          </div>
        )}
      </div>

      {(benchmark !== undefined || subtext) && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)', paddingTop: '0.25rem', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
          {subtext && <span>{subtext}</span>}
          {benchmark !== undefined && (
            <span>{benchmarkLabel}: <span style={{ color: 'var(--text-secondary)' }}>{benchmark}</span></span>
          )}
        </div>
      )}
    </div>
  );
}
