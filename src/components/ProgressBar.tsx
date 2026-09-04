'use client';
import React from 'react';

interface ProgressBarProps {
  value: number;
  targetThreshold?: number;
  variant?: 'emerald' | 'blue' | 'amber' | 'rose' | 'auto' | 'orange';
  label?: string;
  showPercent?: boolean;
}

export default function ProgressBar({
  value,
  targetThreshold,
  variant = 'auto',
  label,
  showPercent = true,
}: ProgressBarProps) {
  const clamped = Math.min(Math.max(value, 0), 100);

  let barColor = '#FF6600';
  if (variant === 'auto') {
    if (clamped >= 80) barColor = '#00CC33';
    else if (clamped >= 50) barColor = '#FF6600';
    else if (clamped >= 30) barColor = '#CC8800';
    else barColor = '#CC2222';
  } else if (variant === 'emerald') barColor = '#00CC33';
  else if (variant === 'blue')    barColor = '#0099CC';
  else if (variant === 'amber')   barColor = '#CC8800';
  else if (variant === 'rose')    barColor = '#CC2222';
  else if (variant === 'orange')  barColor = '#FF6600';

  return (
    <div style={{ width: '100%' }}>
      {(label || showPercent) && (
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
          color: '#555', marginBottom: '0.15rem',
        }}>
          {label && <span>{label}</span>}
          {showPercent && <span style={{ fontWeight: 700, color: '#AAAAAA' }}>{clamped.toFixed(1)}%</span>}
        </div>
      )}
      <div style={{
        position: 'relative', width: '100%', height: '5px',
        background: '#1a1a1a', overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', width: `${clamped}%`,
          background: barColor, transition: 'width 0.3s ease',
        }} />
        {targetThreshold !== undefined && (
          <div style={{
            position: 'absolute', left: `${targetThreshold}%`,
            top: 0, bottom: 0, width: '1px',
            background: '#FFFFFF', zIndex: 2,
          }} />
        )}
      </div>
    </div>
  );
}
