'use client';

import React, { useState } from 'react';
import { Maximize2, Download } from 'lucide-react';

interface ChartContainerProps {
  title: string;
  subtitle?: string;
  badge?: string;
  badgeType?: 'pass' | 'warn' | 'fail' | 'live' | 'paper' | 'neutral';
  timeframes?: string[];
  activeTimeframe?: string;
  onTimeframeChange?: (tf: string) => void;
  children: React.ReactNode;
  actions?: React.ReactNode;
}

export default function ChartContainer({
  title,
  subtitle,
  badge,
  badgeType = 'live',
  timeframes = ['1M', '3M', '6M', '1Y', 'YTD', 'ALL'],
  activeTimeframe: controlledTf,
  onTimeframeChange,
  children,
  actions
}: ChartContainerProps) {
  const [internalTf, setInternalTf] = useState('1Y');
  const currentTf = controlledTf || internalTf;

  const handleTfSelect = (tf: string) => {
    setInternalTf(tf);
    if (onTimeframeChange) onTimeframeChange(tf);
  };

  return (
    <div className="terminal-card">
      <div className="terminal-card-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc', letterSpacing: '0.04em' }}>
              {title}
            </span>
            {badge && (
              <span className={`badge-tag badge-${badgeType}`}>
                {badge}
              </span>
            )}
          </div>
          {subtitle && (
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '0.1rem' }}>
              {subtitle}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {timeframes && timeframes.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', background: '#0a0d14', padding: '0.15rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
              {timeframes.map((tf) => (
                <button
                  key={tf}
                  onClick={() => handleTfSelect(tf)}
                  style={{
                    padding: '0.15rem 0.45rem',
                    fontSize: '0.65rem',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 600,
                    border: 'none',
                    borderRadius: '2px',
                    cursor: 'pointer',
                    background: currentTf === tf ? '#1e293b' : 'transparent',
                    color: currentTf === tf ? '#38bdf8' : '#64748b'
                  }}
                >
                  {tf}
                </button>
              ))}
            </div>
          )}

          {actions}
        </div>
      </div>

      <div className="terminal-card-body" style={{ padding: '0.85rem' }}>
        {children}
      </div>
    </div>
  );
}
