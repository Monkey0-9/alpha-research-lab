'use client';

import React, { useState } from 'react';

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
  rightLabel?: string;
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
  actions,
  rightLabel,
}: ChartContainerProps) {
  const [internalTf, setInternalTf] = useState('1Y');
  const currentTf = controlledTf || internalTf;

  const handleTfSelect = (tf: string) => {
    setInternalTf(tf);
    if (onTimeframeChange) onTimeframeChange(tf);
  };

  const badgeColors: Record<string, string> = {
    pass: '#00CC33',
    warn: '#CC8800',
    fail: '#CC2222',
    live: '#FF6600',
    paper: '#888800',
    neutral: '#444444',
  };

  return (
    <div className="bb-panel">
      {/* Bloomberg panel header */}
      <div className="bb-panel-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="bb-panel-title">{title}</span>
            {badge && (
              <span style={{
                background: badgeColors[badgeType] || '#444',
                color: '#000',
                fontSize: '0.58rem',
                fontWeight: 900,
                padding: '0 0.35rem',
                height: '16px',
                display: 'inline-flex',
                alignItems: 'center',
                letterSpacing: '0.06em',
                fontFamily: 'var(--font-mono)',
              }}>
                {badge}
              </span>
            )}
          </div>
          {subtitle && (
            <div className="bb-panel-subtitle" style={{ marginTop: '1px' }}>{subtitle}</div>
          )}
        </div>

        {/* Right side: timeframe picker + extras */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {rightLabel && (
            <span style={{ color: '#555', fontSize: '0.6rem', fontFamily: 'var(--font-mono)' }}>{rightLabel}</span>
          )}

          {timeframes && timeframes.length > 0 && (
            <div className="bb-tf-bar">
              {timeframes.map((tf) => (
                <button
                  key={tf}
                  onClick={() => handleTfSelect(tf)}
                  className={`bb-tf-btn ${currentTf === tf ? 'active' : ''}`}
                >
                  {tf}
                </button>
              ))}
            </div>
          )}

          {actions}
        </div>
      </div>

      {/* Chart body */}
      <div className="bb-panel-body" style={{ padding: '0.75rem' }}>
        {children}
      </div>
    </div>
  );
}
