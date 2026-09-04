'use client';

import React from 'react';

interface ProgressBarProps {
  value: number; // 0 - 100
  targetThreshold?: number; // e.g. 80
  variant?: 'emerald' | 'blue' | 'amber' | 'rose' | 'auto';
  label?: string;
  showPercent?: boolean;
}

export default function ProgressBar({
  value,
  targetThreshold,
  variant = 'auto',
  label,
  showPercent = true
}: ProgressBarProps) {
  const clamped = Math.min(Math.max(value, 0), 100);

  let barColor = '#38bdf8';
  if (variant === 'auto') {
    if (clamped >= 80) barColor = '#10b981';
    else if (clamped >= 50) barColor = '#38bdf8';
    else if (clamped >= 30) barColor = '#f59e0b';
    else barColor = '#f43f5e';
  } else if (variant === 'emerald') barColor = '#10b981';
  else if (variant === 'amber') barColor = '#f59e0b';
  else if (variant === 'rose') barColor = '#f43f5e';

  return (
    <div style={{ width: '100%' }}>
      {(label || showPercent) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: '#94a3b8', marginBottom: '0.2rem' }}>
          {label && <span>{label}</span>}
          {showPercent && <span style={{ fontWeight: 600, color: '#f8fafc' }}>{clamped.toFixed(1)}%</span>}
        </div>
      )}
      <div style={{ position: 'relative', width: '100%', height: '6px', background: '#0a0d14', borderRadius: '2px', border: '1px solid var(--border-terminal)', overflow: 'hidden' }}>
        <div
          style={{
            height: '100%',
            width: `${clamped}%`,
            background: barColor,
            transition: 'width 0.3s ease'
          }}
        />
        {targetThreshold !== undefined && (
          <div
            style={{
              position: 'absolute',
              left: `${targetThreshold}%`,
              top: 0,
              bottom: 0,
              width: '2px',
              background: '#ffffff',
              boxShadow: '0 0 4px #ffffff',
              zIndex: 2
            }}
            title={`Threshold: ${targetThreshold}%`}
          />
        )}
      </div>
    </div>
  );
}
